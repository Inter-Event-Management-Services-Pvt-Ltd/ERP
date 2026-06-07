import asyncio
import json
from datetime import date
from uuid import UUID

import httpx
import pytest
from httpx import Response

from app.core.audit import AuditContext
from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount
from app.schemas.physical_archive import (
    PhysicalFileCheckoutCreate,
    PhysicalFileMoveCreate,
)
from app.services.physical_archive import PhysicalArchiveError, PhysicalArchiveService

AUTH_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
PROJECT_ID = UUID("33333333-3333-4333-8333-333333333333")
ROOM_ID = UUID("44444444-4444-4444-8444-444444444444")
LOCATION_ID = UUID("55555555-5555-4555-8555-555555555555")
OTHER_LOCATION_ID = UUID("66666666-6666-4666-8666-666666666666")
PHYSICAL_FILE_ID = UUID("77777777-7777-4777-8777-777777777777")
REQUEST_ID = UUID("88888888-8888-4888-8888-888888888888")
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
            designation="Archive Manager",
            employment_status="ACTIVE",
        ),
        roles=["ADMIN"],
        permissions=permissions,
    )


def _membership_row() -> dict[str, object]:
    return {
        "project_id": str(PROJECT_ID),
        "employee_id": str(EMPLOYEE_ID),
        "access_level": "MANAGE",
        "removed_at": None,
    }


def _physical_file_row(*, status: str = "AVAILABLE") -> dict[str, object]:
    return {
        "id": str(PHYSICAL_FILE_ID),
        "physical_file_code": "PF-001",
        "project_id": str(PROJECT_ID),
        "project": {
            "id": str(PROJECT_ID),
            "project_code": "IEMS-2026-001",
            "name": "Demo Project",
        },
        "archive_location_id": str(LOCATION_ID),
        "archive_location": {
            "id": str(LOCATION_ID),
            "archive_room_id": "99999999-9999-4999-8999-999999999999",
            "location_type": "FILE_SLOT",
            "code": "SLOT-001",
            "label": "Slot 001",
            "qr_token": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        },
        "archive_room": {
            "id": "99999999-9999-4999-8999-999999999999",
            "code": "R1",
            "name": "Room 1",
        },
        "volume_number": 1,
        "status": status,
        "qr_token": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        "archived_on": date(2026, 6, 6).isoformat(),
        "archived_by": str(EMPLOYEE_ID),
        "last_verified_at": None,
        "next_verification_at": None,
        "notes": None,
        "created_at": CREATED_AT,
        "updated_at": CREATED_AT,
        "open_checkout": None,
    }


def test_checkout_physical_file_calls_audited_rpc() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/physical_files":
            return Response(200, json=[_physical_file_row()])
        if request.url.path == "/rest/v1/project_members":
            return Response(200, json=[_membership_row()])
        if request.url.path == "/rest/v1/rpc/checkout_physical_file_audited":
            return Response(200, json=_physical_file_row(status="CHECKED_OUT"))
        return Response(500)

    service = PhysicalArchiveService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.checkout_physical_file(
            physical_file_id=PHYSICAL_FILE_ID,
            payload=PhysicalFileCheckoutCreate(purpose="Audit review"),
            current_user=_current_user(permissions=["physical_file.checkout"]),
            context=AuditContext(request_id=REQUEST_ID),
        )
    )

    assert result.status == "CHECKED_OUT"
    body = json.loads(seen_requests[2].content)
    assert body["p_physical_file_id"] == str(PHYSICAL_FILE_ID)
    assert body["p_purpose"] == "Audit review"


def test_list_locations_fetches_active_locations_for_room() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/archive_locations":
            return Response(
                200,
                json=[
                    {
                        "id": str(LOCATION_ID),
                        "archive_room_id": str(ROOM_ID),
                        "parent_location_id": None,
                        "location_type": "RACK",
                        "code": "R1",
                        "label": "Rack 1",
                        "qr_token": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                        "is_active": True,
                    }
                ],
            )
        return Response(500)

    service = PhysicalArchiveService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.list_locations(
            room_id=ROOM_ID,
            current_user=_current_user(permissions=["archive.view"]),
        )
    )

    assert result[0].archive_room_id == ROOM_ID
    assert result[0].code == "R1"
    assert seen_requests[0].url.params["archive_room_id"] == f"eq.{ROOM_ID}"
    assert seen_requests[0].url.params["is_active"] == "eq.true"
    assert seen_requests[0].url.params["order"] == "location_type.asc,code.asc"


def test_physical_file_checked_out_state_maps_to_conflict() -> None:
    def handler(request: httpx.Request) -> Response:
        if request.url.path == "/rest/v1/rpc/move_physical_file_audited":
            return Response(
                400,
                json={"code": "P0001", "message": "IEMS_PHYSICAL_FILE_CHECKED_OUT"},
            )
        return Response(500)

    service = PhysicalArchiveService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(PhysicalArchiveError) as exc_info:
        asyncio.run(
            service.move_physical_file(
                physical_file_id=PHYSICAL_FILE_ID,
                payload=PhysicalFileMoveCreate(to_location_id=OTHER_LOCATION_ID),
                current_user=_current_user(permissions=["archive.manage"]),
                context=AuditContext(request_id=REQUEST_ID),
            )
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "INVALID_PHYSICAL_FILE_STATE"
