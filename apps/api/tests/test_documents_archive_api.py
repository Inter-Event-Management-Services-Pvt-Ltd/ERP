import asyncio
from datetime import UTC, datetime
from uuid import UUID

from httpx import ASGITransport, AsyncClient, Response

from app.api.dependencies import get_current_user, get_documents_archive_service
from app.core.audit import AuditContext
from app.main import app
from app.schemas.clients_projects import ReferenceSummary
from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount
from app.schemas.documents_archive import (
    ArchiveExportCreate,
    ArchiveExportResponse,
    DocumentResponse,
    DocumentVersionResponse,
    FolderCreate,
    FolderResponse,
    SignedUrlResponse,
)

AUTH_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
PROJECT_ID = UUID("33333333-3333-4333-8333-333333333333")
FOLDER_ID = UUID("44444444-4444-4444-8444-444444444444")
DOCUMENT_ID = UUID("55555555-5555-4555-8555-555555555555")
VERSION_ID = UUID("66666666-6666-4666-8666-666666666666")
CONFIDENTIALITY_LEVEL_ID = UUID("77777777-7777-4777-8777-777777777777")
EXPORT_ID = UUID("88888888-8888-4888-8888-888888888888")
DOCUMENT_TYPE_ID = UUID("99999999-9999-4999-8999-999999999999")
CREATED_AT = datetime(2026, 6, 6, 8, 0, tzinfo=UTC)


class RecordingDocumentsArchiveService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object, CurrentUser, AuditContext | None]] = []

    async def create_folder(
        self,
        *,
        project_id: UUID,
        payload: FolderCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> FolderResponse:
        self.calls.append(("create_folder", (project_id, payload), current_user, context))
        return _folder_response()

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
        self.calls.append(
            (
                "upload_document",
                (
                    folder_id,
                    filename,
                    mime_type,
                    content,
                    display_name,
                    document_type_id,
                    confidentiality_level_id,
                    change_note,
                ),
                current_user,
                context,
            )
        )
        return _document_response()

    async def get_document_version_download_url(
        self,
        *,
        version_id: UUID,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> SignedUrlResponse:
        self.calls.append(("download_url", version_id, current_user, context))
        return SignedUrlResponse(
            url="http://127.0.0.1:54321/storage/v1/signed/document.pdf",
            expires_in_seconds=900,
            expires_at=CREATED_AT,
        )

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
        self.calls.append(
            ("search_documents", (project_id, folder_id, search, limit, offset), current_user, None)
        )
        return [_document_response()]

    async def list_confidentiality_levels(
        self,
        *,
        current_user: CurrentUser,
    ) -> list[ReferenceSummary]:
        self.calls.append(("list_confidentiality_levels", None, current_user, None))
        return [_reference_summary(CONFIDENTIALITY_LEVEL_ID, "GENERAL", "General")]

    async def list_document_types(
        self,
        *,
        current_user: CurrentUser,
    ) -> list[ReferenceSummary]:
        self.calls.append(("list_document_types", None, current_user, None))
        return [_reference_summary(DOCUMENT_TYPE_ID, "CONTRACT", "Contract")]

    async def create_archive_export(
        self,
        *,
        project_id: UUID,
        payload: ArchiveExportCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ArchiveExportResponse:
        self.calls.append(("create_archive_export", (project_id, payload), current_user, context))
        return _archive_export_response()

    async def cancel_archive_export(
        self,
        *,
        export_id: UUID,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ArchiveExportResponse:
        self.calls.append(("cancel_archive_export", export_id, current_user, context))
        return _archive_export_response(status="CANCELLED")


def _current_user(*, permissions: list[str], is_super_user: bool = False) -> CurrentUser:
    return CurrentUser(
        auth_user_id=AUTH_USER_ID,
        account=UserAccount(is_active=True, is_super_user=is_super_user),
        employee=EmployeeProfile(
            id=EMPLOYEE_ID,
            employee_code="IEMS-001",
            full_name="Example Employee",
            official_email="employee@iemsnewdelhi.com",
            designation="Manager",
            employment_status="ACTIVE",
        ),
        roles=["EMPLOYEE"],
        permissions=permissions,
    )


def _folder_response() -> FolderResponse:
    return FolderResponse(
        id=FOLDER_ID,
        project_id=PROJECT_ID,
        parent_folder_id=None,
        name="Client Brief",
        sort_order=10,
        created_by=EMPLOYEE_ID,
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
        deleted_at=None,
    )


def _document_response() -> DocumentResponse:
    return DocumentResponse(
        id=DOCUMENT_ID,
        project_id=PROJECT_ID,
        folder_id=FOLDER_ID,
        document_type_id=None,
        confidentiality_level_id=CONFIDENTIALITY_LEVEL_ID,
        display_name="brief.pdf",
        status="ACTIVE",
        created_by=EMPLOYEE_ID,
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
        deleted_at=None,
        latest_version=DocumentVersionResponse(
            id=VERSION_ID,
            document_id=DOCUMENT_ID,
            version_number=1,
            storage_bucket="project-documents",
            storage_key=f"{PROJECT_ID}/{DOCUMENT_ID}/{VERSION_ID}/brief.pdf",
            original_filename="brief.pdf",
            mime_type="application/pdf",
            size_bytes=7,
            checksum_sha256="a" * 64,
            change_note=None,
            uploaded_by=EMPLOYEE_ID,
            uploaded_at=CREATED_AT,
            preview_supported=True,
        ),
    )


def _archive_export_response(status: str = "QUEUED") -> ArchiveExportResponse:
    return ArchiveExportResponse(
        id=EXPORT_ID,
        project_id=PROJECT_ID,
        export_number=1,
        requested_by=EMPLOYEE_ID,
        status=status,
        storage_bucket=None,
        storage_key=None,
        manifest_checksum_sha256=None,
        requested_at=CREATED_AT,
        completed_at=None,
        expires_at=CREATED_AT,
        item_count=0,
    )


def _reference_summary(reference_id: UUID, code: str, name: str) -> ReferenceSummary:
    return ReferenceSummary(id=reference_id, code=code, name=name)


async def _request(
    method: str,
    path: str,
    *,
    json: dict[str, object] | None = None,
    data: dict[str, object] | None = None,
    files: dict[str, tuple[str, bytes, str]] | None = None,
    headers: dict[str, str] | None = None,
) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.request(
            method,
            path,
            json=json,
            data=data,
            files=files,
            headers=headers,
        )


def _install_overrides(
    *,
    current_user: CurrentUser,
    service: RecordingDocumentsArchiveService | None = None,
) -> RecordingDocumentsArchiveService:
    installed_service = service or RecordingDocumentsArchiveService()

    async def override_current_user() -> CurrentUser:
        return current_user

    async def override_documents_archive_service() -> RecordingDocumentsArchiveService:
        return installed_service

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_documents_archive_service] = override_documents_archive_service
    return installed_service


def test_create_folder_requires_project_manage() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.view"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                f"/v1/projects/{PROJECT_ID}/folders",
                json={"name": "Client Brief"},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert service.calls == []


def test_upload_document_passes_multipart_file_to_service() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["document.upload"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                f"/v1/folders/{FOLDER_ID}/documents",
                data={
                    "confidentiality_level_id": str(CONFIDENTIALITY_LEVEL_ID),
                    "display_name": "Client Brief",
                },
                files={"file": ("brief.pdf", b"%PDF-1\n", "application/pdf")},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["latest_version"]["preview_supported"] is True
    assert service.calls[0][0] == "upload_document"
    assert service.calls[0][1][1] == "brief.pdf"


def test_download_url_requires_document_download_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["document.view"]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                f"/v1/document-versions/{VERSION_ID}/download-url",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert service.calls == []


def test_search_documents_accepts_q_alias() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["document.view"]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                f"/v1/documents/search?project_id={PROJECT_ID}&folder_id={FOLDER_ID}&q=brief",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert service.calls[0][0] == "search_documents"
    assert service.calls[0][1] == (PROJECT_ID, FOLDER_ID, "brief", 50, 0)


def test_list_confidentiality_levels_returns_reference_options() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["document.upload"]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/confidentiality-levels",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(CONFIDENTIALITY_LEVEL_ID),
            "code": "GENERAL",
            "name": "General",
        }
    ]
    assert service.calls[0][0] == "list_confidentiality_levels"


def test_list_document_types_returns_reference_options() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["document.upload"]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/document-types",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(DOCUMENT_TYPE_ID),
            "code": "CONTRACT",
            "name": "Contract",
        }
    ]
    assert service.calls[0][0] == "list_document_types"


def test_create_archive_export_returns_accepted() -> None:
    service = _install_overrides(
        current_user=_current_user(permissions=["archive.export"]),
    )
    try:
        response = asyncio.run(
            _request(
                "POST",
                f"/v1/projects/{PROJECT_ID}/exports",
                json={"expires_in_hours": 24},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    assert response.json()["status"] == "QUEUED"
    assert service.calls[0][0] == "create_archive_export"


def test_cancel_archive_export_returns_cancelled_export() -> None:
    service = _install_overrides(
        current_user=_current_user(permissions=["archive.export"]),
    )
    try:
        response = asyncio.run(
            _request(
                "POST",
                f"/v1/exports/{EXPORT_ID}/cancel",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"
    assert service.calls[0][0] == "cancel_archive_export"
