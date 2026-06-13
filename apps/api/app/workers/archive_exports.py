import asyncio
import io
import json
import zipfile
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote
from uuid import UUID

import httpx

from app.core.config import get_settings
from app.workers.celery_app import celery_app


@celery_app.task(name="iems.archive_exports.generate")  # type: ignore[untyped-decorator]
def generate_archive_export_task(export_id: str) -> str:
    return asyncio.run(_ArchiveExportGenerator.from_settings().generate(UUID(export_id)))


def enqueue_archive_export(export_id: UUID) -> None:
    generate_archive_export_task.delay(str(export_id))


class _ArchiveExportGenerator:
    def __init__(
        self,
        *,
        supabase_url: str,
        service_role_key: str,
        timeout_seconds: float,
        archive_bucket: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._supabase_url = supabase_url.rstrip("/")
        self._service_role_key = service_role_key
        self._timeout_seconds = timeout_seconds
        self._archive_bucket = archive_bucket
        self._transport = transport

    @classmethod
    def from_settings(cls) -> "_ArchiveExportGenerator":
        settings = get_settings()
        if settings.supabase_url is None or settings.supabase_service_role_key is None:
            raise RuntimeError("Supabase service-role settings are required for archive exports")
        return cls(
            supabase_url=settings.supabase_url,
            service_role_key=settings.supabase_service_role_key,
            timeout_seconds=settings.supabase_request_timeout_seconds,
            archive_bucket=settings.generated_archives_bucket,
        )

    async def generate(self, export_id: UUID) -> str:
        export = await self._get_object(
            "/rest/v1/archive_exports",
            params={
                "select": "id,project_id,requested_by,status,expires_at",
                "id": f"eq.{export_id}",
                "limit": "1",
            },
        )
        project_id = UUID(str(export["project_id"]))
        requested_by = UUID(str(export["requested_by"]))
        if str(export["status"]) == "CANCELLED":
            return str(export_id)

        try:
            await self._patch_rows(
                "/rest/v1/archive_exports",
                params={"id": f"eq.{export_id}", "status": "eq.QUEUED"},
                json_body={"status": "GENERATING"},
            )
            export = await self._get_object(
                "/rest/v1/archive_exports",
                params={
                    "select": "id,project_id,requested_by,status,expires_at",
                    "id": f"eq.{export_id}",
                    "limit": "1",
                },
            )
            if str(export["status"]) == "CANCELLED":
                return str(export_id)
            versions = await self._latest_document_versions(project_id)
            folders = await self._project_folders(project_id)
            folder_paths = _folder_paths(folders)

            items: list[dict[str, str]] = []
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                _write_folder_entries(archive, folder_paths.values())
                for version in versions:
                    folder_id = UUID(str(version["document"]["folder_id"]))
                    relative_path = _safe_relative_path(
                        folder_paths.get(folder_id, ""),
                        str(version["original_filename"]),
                    )
                    content = await self._download_storage_object(
                        bucket=str(version["storage_bucket"]),
                        key=str(version["storage_key"]),
                    )
                    archive.writestr(relative_path, content)
                    items.append(
                        {
                            "document_version_id": str(version["id"]),
                            "relative_path": relative_path,
                            "checksum_sha256": str(version["checksum_sha256"]).lower(),
                        }
                    )

                manifest = {
                    "archive_export_id": str(export_id),
                    "project_id": str(project_id),
                    "generated_at": datetime.now(UTC).isoformat(),
                    "items": items,
                }
                manifest_bytes = json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")
                archive.writestr("manifest.json", manifest_bytes)
                archive.writestr("document-index.pdf", _minimal_pdf_index(items))

            storage_key = f"{project_id}/{export_id}/archive.zip"
            await self._upload_storage_object(
                bucket=self._archive_bucket,
                key=storage_key,
                content=zip_buffer.getvalue(),
                mime_type="application/zip",
            )
            manifest_checksum = _sha256_hex(manifest_bytes)
            await self._rpc(
                "complete_archive_export_audited",
                {
                    "p_archive_export_id": str(export_id),
                    "p_storage_bucket": self._archive_bucket,
                    "p_storage_key": storage_key,
                    "p_manifest_checksum_sha256": manifest_checksum,
                    "p_items": items,
                    "p_actor_user_account_id": None,
                    "p_actor_employee_id": str(requested_by),
                    "p_request_id": None,
                    "p_ip_address": None,
                    "p_user_agent": "celery/archive-export",
                },
            )
            return str(export_id)
        except Exception as exc:
            await self._mark_failed(export_id=export_id, requested_by=requested_by, error=exc)
            raise

    async def _latest_document_versions(self, project_id: UUID) -> list[dict[str, Any]]:
        documents = await self._get_rows(
            "/rest/v1/documents",
            params={
                "select": "id,folder_id,display_name",
                "project_id": f"eq.{project_id}",
                "deleted_at": "is.null",
                "order": "display_name.asc",
                "limit": "10000",
            },
        )
        if not documents:
            return []
        document_map = {str(document["id"]): document for document in documents}
        versions = await self._get_rows(
            "/rest/v1/document_versions",
            params={
                "select": (
                    "id,document_id,version_number,storage_bucket,storage_key,"
                    "original_filename,checksum_sha256"
                ),
                "document_id": "in.(" + ",".join(document_map) + ")",
                "order": "document_id.asc,version_number.desc",
                "limit": "10000",
            },
        )
        latest_by_document: dict[str, dict[str, Any]] = {}
        for version in versions:
            document_id = str(version["document_id"])
            if document_id not in latest_by_document:
                latest_by_document[document_id] = {**version, "document": document_map[document_id]}
        return list(latest_by_document.values())

    async def _project_folders(self, project_id: UUID) -> list[dict[str, Any]]:
        return await self._get_rows(
            "/rest/v1/folders",
            params={
                "select": "id,parent_folder_id,name,sort_order",
                "project_id": f"eq.{project_id}",
                "deleted_at": "is.null",
                "order": "sort_order.asc,name.asc",
                "limit": "10000",
            },
        )

    async def _download_storage_object(self, *, bucket: str, key: str) -> bytes:
        response = await self._request(
            "GET",
            f"/storage/v1/object/{bucket}/{quote(key, safe='/')}",
        )
        return response.content

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

    async def _mark_failed(self, *, export_id: UUID, requested_by: UUID, error: Exception) -> None:
        await self._rpc(
            "fail_archive_export_audited",
            {
                "p_archive_export_id": str(export_id),
                "p_error_message": str(error)[:500],
                "p_actor_user_account_id": None,
                "p_actor_employee_id": str(requested_by),
                "p_request_id": None,
                "p_ip_address": None,
                "p_user_agent": "celery/archive-export",
            },
        )

    async def _get_object(self, path: str, *, params: dict[str, str]) -> dict[str, Any]:
        rows = await self._get_rows(path, params=params)
        if not rows:
            raise RuntimeError("Archive export resource not found")
        return rows[0]

    async def _get_rows(self, path: str, *, params: dict[str, str]) -> list[dict[str, Any]]:
        response = await self._request("GET", path, params=params)
        payload = response.json()
        if not isinstance(payload, list):
            raise RuntimeError("Supabase returned an invalid list payload")
        return [row for row in payload if isinstance(row, dict)]

    async def _patch_rows(
        self,
        path: str,
        *,
        params: dict[str, str],
        json_body: dict[str, object],
    ) -> None:
        await self._request("PATCH", path, params=params, json_body=json_body)

    async def _rpc(self, function_name: str, payload: dict[str, object]) -> dict[str, Any]:
        response = await self._request(
            "POST",
            f"/rest/v1/rpc/{function_name}",
            json_body=payload,
        )
        result = response.json()
        if isinstance(result, dict):
            return result
        if isinstance(result, list) and result and isinstance(result[0], dict):
            return result[0]
        return {}

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
        response.raise_for_status()
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


def _folder_paths(folders: list[dict[str, Any]]) -> dict[UUID, str]:
    by_id = {UUID(str(folder["id"])): folder for folder in folders}
    cache: dict[UUID, str] = {}

    def resolve(folder_id: UUID) -> str:
        if folder_id in cache:
            return cache[folder_id]
        folder = by_id[folder_id]
        parent_id = folder.get("parent_folder_id")
        name = _safe_path_part(str(folder["name"]))
        if parent_id is None:
            cache[folder_id] = name
            return name
        parent_path = resolve(UUID(str(parent_id)))
        cache[folder_id] = f"{parent_path}/{name}"
        return cache[folder_id]

    for folder_id in by_id:
        resolve(folder_id)
    return cache


def _safe_relative_path(folder_path: str, filename: str) -> str:
    safe_name = _safe_path_part(filename)
    if not folder_path:
        return safe_name
    return f"{folder_path}/{safe_name}"


def _write_folder_entries(archive: zipfile.ZipFile, folder_paths: Iterable[str]) -> None:
    seen: set[str] = set()
    for folder_path in sorted(folder_paths):
        cleaned_path = folder_path.strip("/")
        if not cleaned_path:
            continue
        entry_name = f"{cleaned_path}/"
        if entry_name in seen:
            continue
        info = zipfile.ZipInfo(entry_name)
        info.external_attr = 0o40775 << 16
        archive.writestr(info, b"")
        seen.add(entry_name)


def _safe_path_part(value: str) -> str:
    return value.replace("\\", "_").replace("/", "_").strip() or "unnamed"


def _minimal_pdf_index(items: list[dict[str, str]]) -> bytes:
    lines = ["IEMS Archive Document Index", ""]
    lines.extend(f"{index}. {item['relative_path']}" for index, item in enumerate(items, start=1))
    escaped_lines = [_pdf_escape(line) for line in lines[:40]]
    text_commands = ["BT", "/F1 11 Tf", "50 780 Td"]
    for line in escaped_lines:
        text_commands.append(f"({line}) Tj")
        text_commands.append("0 -16 Td")
    text_commands.append("ET")
    stream = "\n".join(text_commands).encode("latin-1", errors="replace")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        b"5 0 obj << /Length " + str(len(stream)).encode("ascii") + b" >> stream\n"
        + stream
        + b"\nendstream endobj\n",
    ]
    output = io.BytesIO()
    output.write(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(output.tell())
        output.write(obj)
    xref_offset = output.tell()
    output.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.write(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.write(
        (
            f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    return output.getvalue()


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _sha256_hex(content: bytes) -> str:
    import hashlib

    return hashlib.sha256(content).hexdigest()
