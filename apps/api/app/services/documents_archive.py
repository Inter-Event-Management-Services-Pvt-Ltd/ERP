import hashlib
import re
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote
from uuid import UUID, uuid4

import httpx
from pydantic import ValidationError

from app.core.audit import AuditContext
from app.schemas.clients_projects import ReferenceSummary
from app.schemas.current_user import CurrentUser
from app.schemas.documents_archive import (
    ArchiveExportCreate,
    ArchiveExportResponse,
    DocumentResponse,
    DocumentVersionResponse,
    FolderCreate,
    FolderResponse,
    FolderUpdate,
    SignedUrlResponse,
)

FOLDER_SELECT = (
    "id,project_id,parent_folder_id,name,sort_order,created_by,created_at,updated_at,deleted_at"
)
DOCUMENT_SELECT = (
    "id,project_id,folder_id,document_type_id,confidentiality_level_id,display_name,status,"
    "created_by,created_at,updated_at,deleted_at,"
    "document_type:document_types(id,code,name),"
    "confidentiality_level:confidentiality_levels(id,code,name),"
    "latest_version:document_versions("
    "id,document_id,version_number,storage_bucket,storage_key,original_filename,mime_type,"
    "size_bytes,checksum_sha256,change_note,uploaded_by,uploaded_at"
    ")"
)
ARCHIVE_EXPORT_SELECT = (
    "id,project_id,export_number,requested_by,status,storage_bucket,storage_key,"
    "manifest_checksum_sha256,requested_at,completed_at,expires_at"
)
PROJECT_MEMBER_SELECT = "project_id,employee_id,access_level,removed_at"
REFERENCE_SELECT = "id,code,name"
SAFE_FILENAME_PATTERN = re.compile(r"^[^\\/\x00-\x1f\x7f]{1,255}$")


class DocumentsArchiveError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class DocumentsArchiveService:
    def __init__(
        self,
        *,
        supabase_url: str,
        service_role_key: str,
        timeout_seconds: float = 5.0,
        signed_url_ttl_seconds: int = 900,
        archive_export_ttl_hours: int = 24,
        max_upload_bytes: int = 104_857_600,
        allowed_upload_mime_types: frozenset[str] | None = None,
        project_documents_bucket: str = "project-documents",
        generated_archives_bucket: str = "generated-archives",
        enqueue_archive_export: Callable[[UUID], None] | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._supabase_url = supabase_url.rstrip("/")
        self._service_role_key = service_role_key
        self._timeout_seconds = timeout_seconds
        self._signed_url_ttl_seconds = signed_url_ttl_seconds
        self._archive_export_ttl_hours = archive_export_ttl_hours
        self._max_upload_bytes = max_upload_bytes
        self._allowed_upload_mime_types = allowed_upload_mime_types or frozenset()
        self._project_documents_bucket = project_documents_bucket
        self._generated_archives_bucket = generated_archives_bucket
        self._enqueue_archive_export = enqueue_archive_export
        self._transport = transport

    async def create_folder(
        self,
        *,
        project_id: UUID,
        payload: FolderCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> FolderResponse:
        await self._require_project_access(
            project_id=project_id,
            current_user=current_user,
            allowed_levels={"MANAGE"},
            error_message="Project manage access denied",
        )
        row = await self._rpc(
            "create_folder_audited",
            {
                "p_project_id": str(project_id),
                "p_parent_folder_id": _uuid_or_none(payload.parent_folder_id),
                "p_name": payload.name,
                "p_sort_order": payload.sort_order,
                **_actor_context_payload(current_user, context),
            },
        )
        return _folder_from_row(row)

    async def update_folder(
        self,
        *,
        folder_id: UUID,
        payload: FolderUpdate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> FolderResponse:
        folder = await self._get_folder_row(folder_id)
        await self._require_project_access(
            project_id=UUID(str(folder["project_id"])),
            current_user=current_user,
            allowed_levels={"MANAGE"},
            error_message="Project manage access denied",
        )
        row = await self._rpc(
            "update_folder_audited",
            {
                "p_folder_id": str(folder_id),
                "p_patch": payload.model_dump(mode="json", exclude_unset=True),
                **_actor_context_payload(current_user, context),
            },
        )
        return _folder_from_row(row)

    async def delete_folder(
        self,
        *,
        folder_id: UUID,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> None:
        folder = await self._get_folder_row(folder_id)
        await self._require_project_access(
            project_id=UUID(str(folder["project_id"])),
            current_user=current_user,
            allowed_levels={"MANAGE"},
            error_message="Project manage access denied",
        )
        await self._rpc(
            "soft_delete_folder_audited",
            {
                "p_folder_id": str(folder_id),
                **_actor_context_payload(current_user, context),
            },
        )

    async def upload_document(
        self,
        *,
        folder_id: UUID,
        filename: str,
        mime_type: str,
        content: bytes,
        display_name: str | None,
        document_type_id: UUID | None,
        confidentiality_level_id: UUID,
        change_note: str | None,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> DocumentResponse:
        validated = self._validate_upload(filename=filename, mime_type=mime_type, content=content)
        folder = await self._get_folder_row(folder_id)
        project_id = UUID(str(folder["project_id"]))
        await self._require_project_access(
            project_id=project_id,
            current_user=current_user,
            allowed_levels={"CONTRIBUTE", "MANAGE"},
            error_message="Project document upload access denied",
        )
        document_id = uuid4()
        version_id = uuid4()
        storage_key = _document_storage_key(
            project_id=project_id,
            document_id=document_id,
            version_id=version_id,
            filename=validated["filename"],
        )
        await self._upload_storage_object(
            bucket=self._project_documents_bucket,
            key=storage_key,
            content=content,
            mime_type=mime_type,
        )
        try:
            row = await self._rpc(
                "create_document_with_version_audited",
                {
                    "p_document_id": str(document_id),
                    "p_document_version_id": str(version_id),
                    "p_folder_id": str(folder_id),
                    "p_document_type_id": _uuid_or_none(document_type_id),
                    "p_confidentiality_level_id": str(confidentiality_level_id),
                    "p_display_name": display_name or validated["filename"],
                    "p_storage_bucket": self._project_documents_bucket,
                    "p_storage_key": storage_key,
                    "p_original_filename": validated["filename"],
                    "p_mime_type": mime_type,
                    "p_size_bytes": len(content),
                    "p_checksum_sha256": validated["checksum_sha256"],
                    "p_change_note": change_note,
                    **_actor_context_payload(current_user, context),
                },
            )
        except Exception:
            await self._delete_storage_object(
                bucket=self._project_documents_bucket,
                key=storage_key,
            )
            raise
        return _document_from_row(row)

    async def create_document_version(
        self,
        *,
        document_id: UUID,
        filename: str,
        mime_type: str,
        content: bytes,
        change_note: str | None,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> DocumentResponse:
        validated = self._validate_upload(filename=filename, mime_type=mime_type, content=content)
        document = await self._get_document_row(document_id)
        project_id = UUID(str(document["project_id"]))
        await self._require_project_access(
            project_id=project_id,
            current_user=current_user,
            allowed_levels={"CONTRIBUTE", "MANAGE"},
            error_message="Project document upload access denied",
        )
        version_id = uuid4()
        storage_key = _document_storage_key(
            project_id=project_id,
            document_id=document_id,
            version_id=version_id,
            filename=validated["filename"],
        )
        await self._upload_storage_object(
            bucket=self._project_documents_bucket,
            key=storage_key,
            content=content,
            mime_type=mime_type,
        )
        try:
            row = await self._rpc(
                "create_document_version_audited",
                {
                    "p_document_id": str(document_id),
                    "p_document_version_id": str(version_id),
                    "p_storage_bucket": self._project_documents_bucket,
                    "p_storage_key": storage_key,
                    "p_original_filename": validated["filename"],
                    "p_mime_type": mime_type,
                    "p_size_bytes": len(content),
                    "p_checksum_sha256": validated["checksum_sha256"],
                    "p_change_note": change_note,
                    **_actor_context_payload(current_user, context),
                },
            )
        except Exception:
            await self._delete_storage_object(
                bucket=self._project_documents_bucket,
                key=storage_key,
            )
            raise
        return _document_from_row(row)

    async def get_document(
        self,
        *,
        document_id: UUID,
        current_user: CurrentUser,
    ) -> DocumentResponse:
        document = await self._get_document_row(document_id)
        await self._require_project_access(
            project_id=UUID(str(document["project_id"])),
            current_user=current_user,
            allowed_levels=None,
            error_message="Project document access denied",
        )
        return _document_from_row(_normalize_document_row(document))

    async def search_documents(
        self,
        *,
        current_user: CurrentUser,
        project_id: UUID | None = None,
        folder_id: UUID | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DocumentResponse]:
        scoped_project_ids: list[UUID] = []
        if project_id is not None:
            await self._require_project_access(
                project_id=project_id,
                current_user=current_user,
                allowed_levels=None,
                error_message="Project document access denied",
            )
        elif not current_user.account.is_super_user:
            scoped_project_ids = await self._list_active_project_ids_for_user(current_user)
            if not scoped_project_ids:
                return []

        params = {
            "select": DOCUMENT_SELECT,
            "deleted_at": "is.null",
            "order": "updated_at.desc",
            "limit": str(limit),
            "offset": str(offset),
        }
        if project_id is not None:
            params["project_id"] = f"eq.{project_id}"
        elif scoped_project_ids:
            params["project_id"] = _postgrest_in(scoped_project_ids)
        if folder_id is not None:
            params["folder_id"] = f"eq.{folder_id}"
        if search is not None:
            params["display_name"] = f"ilike.{_postgrest_pattern(search)}"

        rows = await self._get_rows("/rest/v1/documents", params=params)
        return [_document_from_row(_normalize_document_row(row)) for row in rows]

    async def get_document_version_download_url(
        self,
        *,
        version_id: UUID,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> SignedUrlResponse:
        version = await self._get_document_version_row(version_id)
        document = await self._get_document_row(UUID(str(version["document_id"])))
        await self._require_project_access(
            project_id=UUID(str(document["project_id"])),
            current_user=current_user,
            allowed_levels=None,
            error_message="Project document access denied",
        )
        version_row = await self._rpc(
            "record_document_download_audited",
            {
                "p_document_version_id": str(version_id),
                **_actor_context_payload(current_user, context),
            },
        )
        audited_version = _document_version_from_row(version_row)
        return await self._signed_url(
            bucket=audited_version.storage_bucket,
            key=audited_version.storage_key,
            expires_in_seconds=self._signed_url_ttl_seconds,
        )

    async def list_confidentiality_levels(
        self,
        *,
        current_user: CurrentUser,
    ) -> list[ReferenceSummary]:
        self._require_document_reference_access(current_user)
        rows = await self._get_rows(
            "/rest/v1/confidentiality_levels",
            params={
                "select": REFERENCE_SELECT,
                "order": "rank.asc,name.asc",
            },
        )
        return [_reference_from_row(row) for row in rows]

    async def list_document_types(
        self,
        *,
        current_user: CurrentUser,
    ) -> list[ReferenceSummary]:
        self._require_document_reference_access(current_user)
        rows = await self._get_rows(
            "/rest/v1/document_types",
            params={
                "select": REFERENCE_SELECT,
                "order": "name.asc",
            },
        )
        return [_reference_from_row(row) for row in rows]

    async def create_archive_export(
        self,
        *,
        project_id: UUID,
        payload: ArchiveExportCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ArchiveExportResponse:
        await self._require_project_access(
            project_id=project_id,
            current_user=current_user,
            allowed_levels={"MANAGE"},
            error_message="Project archive export access denied",
        )
        expires_in_hours = payload.expires_in_hours or self._archive_export_ttl_hours
        export_id = uuid4()
        row = await self._rpc(
            "create_archive_export_audited",
            {
                "p_archive_export_id": str(export_id),
                "p_project_id": str(project_id),
                "p_requested_by": str(current_user.employee.id),
                "p_expires_at": (datetime.now(UTC) + timedelta(hours=expires_in_hours)).isoformat(),
                **_actor_context_payload(current_user, context),
            },
        )
        export = _archive_export_from_row(row)
        if self._enqueue_archive_export is not None:
            self._enqueue_archive_export(export.id)
        return export

    async def cancel_archive_export(
        self,
        *,
        export_id: UUID,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ArchiveExportResponse:
        export = await self._get_archive_export_row(export_id)
        await self._require_project_access(
            project_id=UUID(str(export["project_id"])),
            current_user=current_user,
            allowed_levels={"MANAGE"},
            error_message="Project archive export cancellation access denied",
        )
        if str(export["status"]) != "QUEUED":
            raise DocumentsArchiveError(
                422,
                "INVALID_STATE",
                "Only queued exports can be cancelled",
            )
        row = await self._rpc(
            "cancel_archive_export_audited",
            {
                "p_archive_export_id": str(export_id),
                **_actor_context_payload(current_user, context),
            },
        )
        return _archive_export_from_row(row)

    async def list_archive_exports(
        self,
        *,
        project_id: UUID,
        current_user: CurrentUser,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ArchiveExportResponse]:
        await self._require_project_access(
            project_id=project_id,
            current_user=current_user,
            allowed_levels=None,
            error_message="Project archive export access denied",
        )
        rows = await self._get_rows(
            "/rest/v1/archive_exports",
            params={
                "select": ARCHIVE_EXPORT_SELECT,
                "project_id": f"eq.{project_id}",
                "order": "requested_at.desc",
                "limit": str(limit),
                "offset": str(offset),
            },
        )
        return [_archive_export_from_row({**row, "item_count": 0}) for row in rows]

    async def get_archive_export(
        self,
        *,
        export_id: UUID,
        current_user: CurrentUser,
    ) -> ArchiveExportResponse:
        export = await self._get_archive_export_row(export_id)
        await self._require_project_access(
            project_id=UUID(str(export["project_id"])),
            current_user=current_user,
            allowed_levels=None,
            error_message="Project archive export access denied",
        )
        return _archive_export_from_row({**export, "item_count": 0})

    async def get_archive_export_download_url(
        self,
        *,
        export_id: UUID,
        current_user: CurrentUser,
    ) -> SignedUrlResponse:
        export = await self.get_archive_export(export_id=export_id, current_user=current_user)
        if export.status != "READY" or export.storage_bucket is None or export.storage_key is None:
            raise DocumentsArchiveError(422, "INVALID_STATE", "Archive export is not ready")
        if export.expires_at is not None and export.expires_at <= datetime.now(UTC):
            raise DocumentsArchiveError(422, "INVALID_STATE", "Archive export has expired")
        return await self._signed_url(
            bucket=export.storage_bucket,
            key=export.storage_key,
            expires_in_seconds=self._signed_url_ttl_seconds,
        )

    async def _get_folder_row(self, folder_id: UUID) -> dict[str, Any]:
        rows = await self._get_rows(
            "/rest/v1/folders",
            params={
                "select": FOLDER_SELECT,
                "id": f"eq.{folder_id}",
                "deleted_at": "is.null",
                "limit": "1",
            },
        )
        if not rows:
            raise DocumentsArchiveError(404, "NOT_FOUND", "Folder not found")
        return rows[0]

    async def _get_document_row(self, document_id: UUID) -> dict[str, Any]:
        rows = await self._get_rows(
            "/rest/v1/documents",
            params={
                "select": DOCUMENT_SELECT,
                "id": f"eq.{document_id}",
                "deleted_at": "is.null",
                "limit": "1",
            },
        )
        if not rows:
            raise DocumentsArchiveError(404, "NOT_FOUND", "Document not found")
        return rows[0]

    async def _get_document_version_row(self, version_id: UUID) -> dict[str, Any]:
        rows = await self._get_rows(
            "/rest/v1/document_versions",
            params={
                "select": (
                    "id,document_id,version_number,storage_bucket,storage_key,"
                    "original_filename,mime_type,size_bytes,checksum_sha256,change_note,"
                    "uploaded_by,uploaded_at"
                ),
                "id": f"eq.{version_id}",
                "limit": "1",
            },
        )
        if not rows:
            raise DocumentsArchiveError(404, "NOT_FOUND", "Document version not found")
        return rows[0]

    async def _get_archive_export_row(self, export_id: UUID) -> dict[str, Any]:
        rows = await self._get_rows(
            "/rest/v1/archive_exports",
            params={
                "select": ARCHIVE_EXPORT_SELECT,
                "id": f"eq.{export_id}",
                "limit": "1",
            },
        )
        if not rows:
            raise DocumentsArchiveError(404, "NOT_FOUND", "Archive export not found")
        return rows[0]

    async def _require_project_access(
        self,
        *,
        project_id: UUID,
        current_user: CurrentUser,
        allowed_levels: set[str] | None,
        error_message: str,
    ) -> None:
        if current_user.account.is_super_user:
            return
        rows = await self._get_rows(
            "/rest/v1/project_members",
            params={
                "select": PROJECT_MEMBER_SELECT,
                "project_id": f"eq.{project_id}",
                "employee_id": f"eq.{current_user.employee.id}",
                "removed_at": "is.null",
                "limit": "1",
            },
        )
        if not rows:
            raise DocumentsArchiveError(403, "ABAC_DENIED", error_message)
        if allowed_levels is not None and str(rows[0].get("access_level")) not in allowed_levels:
            raise DocumentsArchiveError(403, "ABAC_DENIED", error_message)

    def _require_document_reference_access(self, current_user: CurrentUser) -> None:
        if current_user.account.is_super_user:
            return
        if {
            "document.view",
            "document.download",
            "document.upload",
        }.intersection(current_user.permissions):
            return
        raise DocumentsArchiveError(403, "PERMISSION_DENIED", "Permission denied")

    async def _list_active_project_ids_for_user(self, current_user: CurrentUser) -> list[UUID]:
        rows = await self._get_rows(
            "/rest/v1/project_members",
            params={
                "select": "project_id",
                "employee_id": f"eq.{current_user.employee.id}",
                "removed_at": "is.null",
                "limit": "1000",
            },
        )
        return [UUID(str(row["project_id"])) for row in rows]

    def _validate_upload(
        self,
        *,
        filename: str,
        mime_type: str,
        content: bytes,
    ) -> dict[str, str]:
        cleaned_filename = filename.strip()
        if not SAFE_FILENAME_PATTERN.match(cleaned_filename):
            raise DocumentsArchiveError(422, "INVALID_FILE_NAME", "File name is invalid")
        if self._allowed_upload_mime_types and mime_type not in self._allowed_upload_mime_types:
            raise DocumentsArchiveError(422, "INVALID_MIME_TYPE", "File type is not allowed")
        if not content:
            raise DocumentsArchiveError(422, "INVALID_FILE_SIZE", "File must not be empty")
        if len(content) > self._max_upload_bytes:
            raise DocumentsArchiveError(422, "INVALID_FILE_SIZE", "File is too large")
        return {
            "filename": cleaned_filename,
            "checksum_sha256": hashlib.sha256(content).hexdigest(),
        }

    async def _get_rows(self, path: str, *, params: dict[str, str]) -> list[dict[str, Any]]:
        response = await self._request("GET", path, params=params)
        return _json_list(response)

    async def _rpc(self, function_name: str, payload: dict[str, object]) -> dict[str, Any]:
        response = await self._request(
            "POST",
            f"/rest/v1/rpc/{function_name}",
            json_body=payload,
        )
        return _json_object(response)

    async def _upload_storage_object(
        self,
        *,
        bucket: str,
        key: str,
        content: bytes,
        mime_type: str,
    ) -> None:
        await self._request(
            "POST",
            f"/storage/v1/object/{bucket}/{quote(key, safe='/')}",
            content=content,
            headers={"Content-Type": mime_type, "x-upsert": "false"},
        )

    async def _delete_storage_object(self, *, bucket: str, key: str) -> None:
        try:
            await self._request(
                "DELETE",
                f"/storage/v1/object/{bucket}/{quote(key, safe='/')}",
            )
        except DocumentsArchiveError:
            return

    async def _signed_url(
        self,
        *,
        bucket: str,
        key: str,
        expires_in_seconds: int,
    ) -> SignedUrlResponse:
        response = await self._request(
            "POST",
            f"/storage/v1/object/sign/{bucket}/{quote(key, safe='/')}",
            json_body={"expiresIn": expires_in_seconds},
        )
        payload = _json_object(response)
        signed_url = _optional_str(payload.get("signedURL")) or _optional_str(
            payload.get("signedUrl")
        )
        if signed_url is None:
            raise DocumentsArchiveError(
                503,
                "DATA_SERVICE_INVALID_RESPONSE",
                "Storage service did not return a signed URL",
            )
        signed_url = self._normalize_signed_url(signed_url)
        return SignedUrlResponse(
            url=signed_url,
            expires_in_seconds=expires_in_seconds,
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_in_seconds),
        )

    def _normalize_signed_url(self, signed_url: str) -> str:
        if signed_url.startswith("/storage/v1/"):
            return f"{self._supabase_url}{signed_url}"
        if signed_url.startswith("/object/"):
            return f"{self._supabase_url}/storage/v1{signed_url}"
        if signed_url.startswith("/"):
            return f"{self._supabase_url}{signed_url}"
        return signed_url

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json_body: dict[str, object] | None = None,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        request_headers = self._supabase_headers()
        if headers is not None:
            request_headers.update(headers)
        async with httpx.AsyncClient(
            timeout=self._timeout_seconds,
            transport=self._transport,
        ) as client:
            response = await client.request(
                method,
                f"{self._supabase_url}{path}",
                headers=request_headers,
                params=params,
                json=json_body,
                content=content,
            )
        if response.status_code >= 300:
            _raise_supabase_error(response)
        return response

    def _supabase_headers(self) -> dict[str, str]:
        headers = {
            "apikey": self._service_role_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if not self._service_role_key.startswith("sb_secret_"):
            headers["Authorization"] = f"Bearer {self._service_role_key}"
        return headers


def _actor_context_payload(current_user: CurrentUser, context: AuditContext) -> dict[str, object]:
    return {
        "p_actor_user_account_id": str(current_user.auth_user_id),
        "p_actor_employee_id": str(current_user.employee.id),
        "p_request_id": _uuid_or_none(context.request_id),
        "p_ip_address": context.ip_address,
        "p_user_agent": context.user_agent,
    }


def _folder_from_row(row: dict[str, Any]) -> FolderResponse:
    try:
        return FolderResponse.model_validate(row)
    except ValidationError as exc:
        raise DocumentsArchiveError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Folder data service returned invalid data",
        ) from exc


def _document_from_row(row: dict[str, Any]) -> DocumentResponse:
    try:
        return DocumentResponse.model_validate(row)
    except ValidationError as exc:
        raise DocumentsArchiveError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Document data service returned invalid data",
        ) from exc


def _document_version_from_row(row: dict[str, Any]) -> DocumentVersionResponse:
    try:
        return DocumentVersionResponse.model_validate(row)
    except ValidationError as exc:
        raise DocumentsArchiveError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Document version data service returned invalid data",
        ) from exc


def _archive_export_from_row(row: dict[str, Any]) -> ArchiveExportResponse:
    try:
        return ArchiveExportResponse.model_validate(row)
    except ValidationError as exc:
        raise DocumentsArchiveError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Archive export data service returned invalid data",
        ) from exc


def _reference_from_row(row: dict[str, Any]) -> ReferenceSummary:
    try:
        return ReferenceSummary.model_validate(row)
    except ValidationError as exc:
        raise DocumentsArchiveError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Reference data service returned invalid data",
        ) from exc


def _normalize_document_row(row: dict[str, Any]) -> dict[str, Any]:
    latest_version = row.get("latest_version")
    if isinstance(latest_version, list):
        row = {**row, "latest_version": latest_version[0] if latest_version else None}
    if (
        isinstance(row.get("latest_version"), dict)
        and "preview_supported" not in row["latest_version"]
    ):
        row = {
            **row,
            "latest_version": {
                **row["latest_version"],
                "preview_supported": row["latest_version"].get("mime_type")
                in {"application/pdf", "image/jpeg", "image/png", "text/plain"},
            },
        }
    return row


def _json_list(response: httpx.Response) -> list[dict[str, Any]]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise DocumentsArchiveError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid JSON",
        ) from exc
    if not isinstance(payload, list):
        raise DocumentsArchiveError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid payload",
        )
    for item in payload:
        if not isinstance(item, dict):
            raise DocumentsArchiveError(
                503,
                "DATA_SERVICE_INVALID_RESPONSE",
                "Data service returned invalid payload",
            )
    return payload


def _json_object(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise DocumentsArchiveError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid JSON",
        ) from exc
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        return payload[0]
    raise DocumentsArchiveError(
        503,
        "DATA_SERVICE_INVALID_RESPONSE",
        "Data service returned invalid payload",
    )


def _raise_supabase_error(response: httpx.Response) -> None:
    payload = _error_payload(response)
    pg_code = _optional_str(payload.get("code"))
    message = _optional_str(payload.get("message")) or "Supabase data service request failed"

    if message in {
        "IEMS_PROJECT_NOT_FOUND",
        "IEMS_FOLDER_NOT_FOUND",
        "IEMS_DOCUMENT_NOT_FOUND",
        "IEMS_DOCUMENT_VERSION_NOT_FOUND",
        "IEMS_ARCHIVE_EXPORT_NOT_FOUND",
    }:
        raise DocumentsArchiveError(404, "NOT_FOUND", "Resource not found")
    if message in {"IEMS_PARENT_FOLDER_NOT_FOUND"}:
        raise DocumentsArchiveError(422, "INVALID_REFERENCE", "Referenced resource is invalid")
    if message in {
        "IEMS_FOLDER_CYCLE",
        "IEMS_FOLDER_NOT_EMPTY",
        "IEMS_ARCHIVE_EXPORT_NOT_CANCELLABLE",
        "IEMS_ARCHIVE_EXPORT_CANCELLED",
    }:
        raise DocumentsArchiveError(422, "INVALID_STATE", message)
    if pg_code == "23505":
        raise DocumentsArchiveError(409, "RESOURCE_CONFLICT", "Resource already exists")
    if pg_code == "23503":
        raise DocumentsArchiveError(422, "INVALID_REFERENCE", "Referenced resource is invalid")
    if pg_code == "23514":
        raise DocumentsArchiveError(422, "INVALID_STATE", "Resource violates a constraint")
    if response.status_code == 404:
        raise DocumentsArchiveError(404, "NOT_FOUND", "Resource not found")

    raise DocumentsArchiveError(503, "DATA_SERVICE_ERROR", message)


def _error_payload(response: httpx.Response) -> dict[str, object]:
    try:
        payload = response.json()
    except ValueError:
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _document_storage_key(
    *,
    project_id: UUID,
    document_id: UUID,
    version_id: UUID,
    filename: str,
) -> str:
    return f"{project_id}/{document_id}/{version_id}/{quote(filename, safe='')}"


def _postgrest_pattern(raw_value: str) -> str:
    cleaned = (
        raw_value.strip()
        .replace("*", "")
        .replace(",", " ")
        .replace("(", " ")
        .replace(")", " ")
    )
    return f"*{cleaned}*"


def _postgrest_in(values: list[UUID]) -> str:
    return "in.(" + ",".join(str(value) for value in values) + ")"


def _uuid_or_none(value: UUID | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_str(value: object) -> str | None:
    if isinstance(value, str):
        return value
    return None
