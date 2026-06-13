import asyncio
import io
import zipfile
from uuid import UUID

import httpx
from httpx import Response

from app.workers.archive_exports import _ArchiveExportGenerator

EXPORT_ID = UUID("88888888-8888-4888-8888-888888888888")
PROJECT_ID = UUID("33333333-3333-4333-8333-333333333333")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
ROOT_FOLDER_ID = UUID("44444444-4444-4444-8444-444444444444")
DOCUMENT_FOLDER_ID = UUID("55555555-5555-4555-8555-555555555555")
EMPTY_FOLDER_ID = UUID("66666666-6666-4666-8666-666666666666")
DOCUMENT_ID = UUID("77777777-7777-4777-8777-777777777777")
VERSION_ID = UUID("99999999-9999-4999-8999-999999999999")


def test_generator_skips_cancelled_exports_before_marking_generating() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/archive_exports":
            return Response(
                200,
                json=[
                    {
                        "id": str(EXPORT_ID),
                        "project_id": str(PROJECT_ID),
                        "requested_by": str(EMPLOYEE_ID),
                        "status": "CANCELLED",
                        "expires_at": None,
                    }
                ],
            )
        return Response(500)

    generator = _ArchiveExportGenerator(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        timeout_seconds=5,
        archive_bucket="generated-archives",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(generator.generate(EXPORT_ID))

    assert result == str(EXPORT_ID)
    assert [request.method for request in seen_requests] == ["GET"]


def test_generator_preserves_empty_folders_as_zip_directory_entries() -> None:
    archive_status = {"value": "QUEUED"}
    uploaded_content: dict[str, bytes] = {}

    def handler(request: httpx.Request) -> Response:
        if request.url.path == "/rest/v1/archive_exports":
            if request.method == "PATCH":
                archive_status["value"] = "GENERATING"
                return Response(204)
            return Response(
                200,
                json=[
                    {
                        "id": str(EXPORT_ID),
                        "project_id": str(PROJECT_ID),
                        "requested_by": str(EMPLOYEE_ID),
                        "status": archive_status["value"],
                        "expires_at": None,
                    }
                ],
            )
        if request.url.path == "/rest/v1/documents":
            return Response(
                200,
                json=[
                    {
                        "id": str(DOCUMENT_ID),
                        "folder_id": str(DOCUMENT_FOLDER_ID),
                        "display_name": "brief.pdf",
                    }
                ],
            )
        if request.url.path == "/rest/v1/document_versions":
            return Response(
                200,
                json=[
                    {
                        "id": str(VERSION_ID),
                        "document_id": str(DOCUMENT_ID),
                        "version_number": 1,
                        "storage_bucket": "project-documents",
                        "storage_key": "documents/brief.pdf",
                        "original_filename": "brief.pdf",
                        "checksum_sha256": "a" * 64,
                    }
                ],
            )
        if request.url.path == "/rest/v1/folders":
            return Response(
                200,
                json=[
                    {
                        "id": str(ROOT_FOLDER_ID),
                        "parent_folder_id": None,
                        "name": "Project Root",
                        "sort_order": 0,
                    },
                    {
                        "id": str(DOCUMENT_FOLDER_ID),
                        "parent_folder_id": str(ROOT_FOLDER_ID),
                        "name": "Documents",
                        "sort_order": 10,
                    },
                    {
                        "id": str(EMPTY_FOLDER_ID),
                        "parent_folder_id": str(ROOT_FOLDER_ID),
                        "name": "Empty Folder",
                        "sort_order": 20,
                    },
                ],
            )
        if request.url.path == "/storage/v1/object/project-documents/documents/brief.pdf":
            return Response(200, content=b"%PDF-1\n")
        if request.url.path.startswith("/storage/v1/object/generated-archives/"):
            uploaded_content["archive"] = request.content
            return Response(200, json={"Key": "archive.zip"})
        if request.url.path == "/rest/v1/rpc/complete_archive_export_audited":
            return Response(200, json={})
        return Response(500)

    generator = _ArchiveExportGenerator(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        timeout_seconds=5,
        archive_bucket="generated-archives",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(generator.generate(EXPORT_ID))

    assert result == str(EXPORT_ID)
    with zipfile.ZipFile(io.BytesIO(uploaded_content["archive"])) as archive:
        names = set(archive.namelist())

    assert "Project Root/" in names
    assert "Project Root/Documents/" in names
    assert "Project Root/Empty Folder/" in names
    assert "Project Root/Documents/brief.pdf" in names
