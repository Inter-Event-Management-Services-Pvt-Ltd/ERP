import asyncio
import json
from datetime import UTC, datetime
from uuid import UUID

import httpx
import pytest
from httpx import Response

from app.core.audit import AuditContext
from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount
from app.schemas.documents_archive import ArchiveExportCreate
from app.services.documents_archive import DocumentsArchiveError, DocumentsArchiveService

AUTH_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
PROJECT_ID = UUID("33333333-3333-4333-8333-333333333333")
FOLDER_ID = UUID("44444444-4444-4444-8444-444444444444")
DOCUMENT_ID = UUID("55555555-5555-4555-8555-555555555555")
VERSION_ID = UUID("66666666-6666-4666-8666-666666666666")
CONFIDENTIALITY_LEVEL_ID = UUID("77777777-7777-4777-8777-777777777777")
REQUEST_ID = UUID("99999999-9999-4999-8999-999999999999")
CREATED_AT = "2026-06-06T08:00:00+00:00"


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
        roles=["MANAGER"],
        permissions=permissions,
    )


def _folder_row() -> dict[str, object]:
    return {
        "id": str(FOLDER_ID),
        "project_id": str(PROJECT_ID),
        "parent_folder_id": None,
        "name": "Client Brief",
        "sort_order": 10,
        "created_by": str(EMPLOYEE_ID),
        "created_at": CREATED_AT,
        "updated_at": CREATED_AT,
        "deleted_at": None,
    }


def _membership_row() -> dict[str, object]:
    return {
        "project_id": str(PROJECT_ID),
        "employee_id": str(EMPLOYEE_ID),
        "access_level": "MANAGE",
        "removed_at": None,
    }


def _version_row() -> dict[str, object]:
    return {
        "id": str(VERSION_ID),
        "document_id": str(DOCUMENT_ID),
        "version_number": 1,
        "storage_bucket": "project-documents",
        "storage_key": f"{PROJECT_ID}/{DOCUMENT_ID}/{VERSION_ID}/brief.pdf",
        "original_filename": "brief.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 7,
        "checksum_sha256": "a" * 64,
        "change_note": None,
        "uploaded_by": str(EMPLOYEE_ID),
        "uploaded_at": CREATED_AT,
        "preview_supported": True,
    }


def _document_row() -> dict[str, object]:
    return {
        "id": str(DOCUMENT_ID),
        "project_id": str(PROJECT_ID),
        "folder_id": str(FOLDER_ID),
        "document_type_id": None,
        "document_type": None,
        "confidentiality_level_id": str(CONFIDENTIALITY_LEVEL_ID),
        "confidentiality_level": {
            "id": str(CONFIDENTIALITY_LEVEL_ID),
            "code": "GENERAL",
            "name": "General",
        },
        "display_name": "brief.pdf",
        "status": "ACTIVE",
        "created_by": str(EMPLOYEE_ID),
        "created_at": CREATED_AT,
        "updated_at": CREATED_AT,
        "deleted_at": None,
        "latest_version": _version_row(),
    }


def test_upload_document_validates_mime_type() -> None:
    service = DocumentsArchiveService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        allowed_upload_mime_types=frozenset({"application/pdf"}),
        transport=httpx.MockTransport(lambda request: Response(500)),
    )

    with pytest.raises(DocumentsArchiveError) as exc_info:
        asyncio.run(
            service.upload_document(
                folder_id=FOLDER_ID,
                filename="brief.exe",
                mime_type="application/x-msdownload",
                content=b"MZ",
                display_name=None,
                document_type_id=None,
                confidentiality_level_id=CONFIDENTIALITY_LEVEL_ID,
                change_note=None,
                current_user=_current_user(permissions=["document.upload"]),
                context=AuditContext(request_id=REQUEST_ID),
            )
        )

    assert exc_info.value.code == "INVALID_MIME_TYPE"


def test_upload_document_stores_object_then_creates_audited_rows() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/folders":
            return Response(200, json=[_folder_row()])
        if request.url.path == "/rest/v1/project_members":
            return Response(200, json=[_membership_row()])
        if request.url.path.startswith("/storage/v1/object/project-documents/"):
            return Response(200, json={"Key": "stored"})
        if request.url.path == "/rest/v1/rpc/create_document_with_version_audited":
            return Response(200, json=_document_row())
        return Response(500)

    service = DocumentsArchiveService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        allowed_upload_mime_types=frozenset({"application/pdf"}),
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.upload_document(
            folder_id=FOLDER_ID,
            filename="brief.pdf",
            mime_type="application/pdf",
            content=b"%PDF-1\n",
            display_name=None,
            document_type_id=None,
            confidentiality_level_id=CONFIDENTIALITY_LEVEL_ID,
            change_note="Initial",
            current_user=_current_user(permissions=["document.upload"]),
            context=AuditContext(request_id=REQUEST_ID),
        )
    )

    assert result.latest_version is not None
    assert result.latest_version.checksum_sha256 == "a" * 64
    storage_request = seen_requests[2]
    assert storage_request.method == "POST"
    assert storage_request.headers["content-type"] == "application/pdf"
    rpc_body = json.loads(seen_requests[3].content)
    assert (
        rpc_body["p_checksum_sha256"]
        == "5946a597e177b3e11902081b8b5e98a49dcd47c7354e4c1e8af37529a9fe8736"
    )


def test_download_url_checks_access_before_audit_and_sign() -> None:
    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> Response:
        seen_paths.append(request.url.path)
        if request.url.path == "/rest/v1/document_versions":
            return Response(200, json=[_version_row()])
        if request.url.path == "/rest/v1/documents":
            return Response(200, json=[_document_row()])
        if request.url.path == "/rest/v1/project_members":
            return Response(200, json=[_membership_row()])
        if request.url.path == "/rest/v1/rpc/record_document_download_audited":
            return Response(200, json=_version_row())
        if request.url.path.startswith("/storage/v1/object/sign/project-documents/"):
            return Response(
                200,
                json={
                    "signedURL": (
                        "/object/sign/project-documents/"
                        f"{PROJECT_ID}/{DOCUMENT_ID}/{VERSION_ID}/brief.pdf?token=test"
                    )
                },
            )
        return Response(500)

    service = DocumentsArchiveService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.get_document_version_download_url(
            version_id=VERSION_ID,
            current_user=_current_user(permissions=["document.download"]),
            context=AuditContext(request_id=REQUEST_ID),
        )
    )

    assert result.url == (
        "http://localhost:54321/storage/v1/object/sign/project-documents/"
        f"{PROJECT_ID}/{DOCUMENT_ID}/{VERSION_ID}/brief.pdf?token=test"
    )
    assert seen_paths[:4] == [
        "/rest/v1/document_versions",
        "/rest/v1/documents",
        "/rest/v1/project_members",
        "/rest/v1/rpc/record_document_download_audited",
    ]


def test_list_confidentiality_levels_fetches_active_reference_rows() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/confidentiality_levels":
            return Response(
                200,
                json=[
                    {
                        "id": str(CONFIDENTIALITY_LEVEL_ID),
                        "code": "GENERAL",
                        "name": "General",
                    }
                ],
            )
        return Response(500)

    service = DocumentsArchiveService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.list_confidentiality_levels(
            current_user=_current_user(permissions=["document.upload"]),
        )
    )

    assert result[0].code == "GENERAL"
    assert seen_requests[0].url.params["order"] == "rank.asc,name.asc"


def test_list_document_types_fetches_active_reference_rows() -> None:
    document_type_id = UUID("88888888-8888-4888-8888-888888888888")
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/document_types":
            return Response(
                200,
                json=[
                    {
                        "id": str(document_type_id),
                        "code": "CONTRACT",
                        "name": "Contract",
                    }
                ],
            )
        return Response(500)

    service = DocumentsArchiveService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.list_document_types(
            current_user=_current_user(permissions=["document.upload"]),
        )
    )

    assert result[0].code == "CONTRACT"
    assert seen_requests[0].url.params["order"] == "name.asc"


def test_archive_export_creation_enqueues_worker() -> None:
    enqueued: list[UUID] = []

    def handler(request: httpx.Request) -> Response:
        if request.url.path == "/rest/v1/project_members":
            return Response(200, json=[_membership_row()])
        if request.url.path == "/rest/v1/rpc/create_archive_export_audited":
            return Response(
                200,
                json={
                    "id": "88888888-8888-4888-8888-888888888888",
                    "project_id": str(PROJECT_ID),
                    "export_number": 1,
                    "requested_by": str(EMPLOYEE_ID),
                    "status": "QUEUED",
                    "storage_bucket": None,
                    "storage_key": None,
                    "manifest_checksum_sha256": None,
                    "requested_at": datetime.now(UTC).isoformat(),
                    "completed_at": None,
                    "expires_at": datetime.now(UTC).isoformat(),
                    "item_count": 0,
                },
            )
        return Response(500)

    service = DocumentsArchiveService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        enqueue_archive_export=enqueued.append,
        transport=httpx.MockTransport(handler),
    )

    export = asyncio.run(
        service.create_archive_export(
            project_id=PROJECT_ID,
            payload=ArchiveExportCreate(expires_in_hours=24),
            current_user=_current_user(permissions=["archive.export"]),
            context=AuditContext(request_id=REQUEST_ID),
        )
    )

    assert export.status == "QUEUED"
    assert enqueued == [export.id]


def test_cancel_archive_export_requires_manage_access_and_calls_rpc() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/archive_exports":
            return Response(
                200,
                json=[
                    {
                        "id": "88888888-8888-4888-8888-888888888888",
                        "project_id": str(PROJECT_ID),
                        "export_number": 1,
                        "requested_by": str(EMPLOYEE_ID),
                        "status": "QUEUED",
                        "storage_bucket": None,
                        "storage_key": None,
                        "manifest_checksum_sha256": None,
                        "requested_at": datetime.now(UTC).isoformat(),
                        "completed_at": None,
                        "expires_at": datetime.now(UTC).isoformat(),
                    }
                ],
            )
        if request.url.path == "/rest/v1/project_members":
            return Response(200, json=[_membership_row()])
        if request.url.path == "/rest/v1/rpc/cancel_archive_export_audited":
            return Response(
                200,
                json={
                    "id": "88888888-8888-4888-8888-888888888888",
                    "project_id": str(PROJECT_ID),
                    "export_number": 1,
                    "requested_by": str(EMPLOYEE_ID),
                    "status": "CANCELLED",
                    "storage_bucket": None,
                    "storage_key": None,
                    "manifest_checksum_sha256": None,
                    "requested_at": datetime.now(UTC).isoformat(),
                    "completed_at": None,
                    "expires_at": datetime.now(UTC).isoformat(),
                    "item_count": 0,
                },
            )
        return Response(500)

    service = DocumentsArchiveService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    export = asyncio.run(
        service.cancel_archive_export(
            export_id=UUID("88888888-8888-4888-8888-888888888888"),
            current_user=_current_user(permissions=["archive.export"]),
            context=AuditContext(request_id=REQUEST_ID),
        )
    )

    assert export.status == "CANCELLED"
    rpc_body = json.loads(seen_requests[2].content)
    assert rpc_body["p_archive_export_id"] == "88888888-8888-4888-8888-888888888888"
    assert rpc_body["p_actor_employee_id"] == str(EMPLOYEE_ID)


def test_cancel_archive_export_rejects_ready_export_before_rpc() -> None:
    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> Response:
        seen_paths.append(request.url.path)
        if request.url.path == "/rest/v1/archive_exports":
            return Response(
                200,
                json=[
                    {
                        "id": "88888888-8888-4888-8888-888888888888",
                        "project_id": str(PROJECT_ID),
                        "export_number": 1,
                        "requested_by": str(EMPLOYEE_ID),
                        "status": "READY",
                        "storage_bucket": "generated-archives",
                        "storage_key": "archive.zip",
                        "manifest_checksum_sha256": "b" * 64,
                        "requested_at": datetime.now(UTC).isoformat(),
                        "completed_at": datetime.now(UTC).isoformat(),
                        "expires_at": datetime.now(UTC).isoformat(),
                    }
                ],
            )
        if request.url.path == "/rest/v1/project_members":
            return Response(200, json=[_membership_row()])
        return Response(500)

    service = DocumentsArchiveService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(DocumentsArchiveError) as exc_info:
        asyncio.run(
            service.cancel_archive_export(
                export_id=UUID("88888888-8888-4888-8888-888888888888"),
                current_user=_current_user(permissions=["archive.export"]),
                context=AuditContext(request_id=REQUEST_ID),
            )
        )

    assert exc_info.value.code == "INVALID_STATE"
    assert "/rest/v1/rpc/cancel_archive_export_audited" not in seen_paths
