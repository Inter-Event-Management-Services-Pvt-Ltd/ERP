import asyncio
import json
from datetime import UTC, date, datetime
from uuid import UUID

import httpx
import pytest
from httpx import Response

from app.core.audit import AuditContext
from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount

AUTH_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
OTHER_EMPLOYEE_ID = UUID("33333333-3333-4333-8333-333333333333")
SESSION_ID = UUID("44444444-4444-4444-8444-444444444444")
REQUEST_ID = UUID("55555555-5555-4555-8555-555555555555")

CHECKED_IN_AT = "2026-06-13T09:00:00+00:00"
CHECKED_OUT_AT = "2026-06-13T17:30:00+00:00"


def _current_user(
    *,
    permissions: list[str] | None = None,
    is_super_user: bool = False,
) -> CurrentUser:
    return CurrentUser(
        auth_user_id=AUTH_USER_ID,
        account=UserAccount(is_active=True, is_super_user=is_super_user),
        employee=EmployeeProfile(
            id=EMPLOYEE_ID,
            employee_code="IEMS-001",
            full_name="Example Employee",
            official_email="employee@iemsnewdelhi.com",
            designation="Coordinator",
            employment_status="ACTIVE",
        ),
        roles=["EMPLOYEE"],
        permissions=permissions or [],
    )


def _attendance_row(
    *,
    employee_id: UUID = EMPLOYEE_ID,
    checked_out_at: str | None = None,
    correction_reason: str | None = None,
) -> dict[str, object]:
    return {
        "id": str(SESSION_ID),
        "employee_id": str(employee_id),
        "employee": {
            "id": str(employee_id),
            "employee_code": "IEMS-001",
            "full_name": "Example Employee",
        },
        "checked_in_at": CHECKED_IN_AT,
        "checked_out_at": checked_out_at,
        "source": "WEB",
        "remarks": "Front desk",
        "created_by": str(EMPLOYEE_ID),
        "corrected_by": str(EMPLOYEE_ID) if correction_reason else None,
        "correction_reason": correction_reason,
        "created_at": CHECKED_IN_AT,
        "updated_at": checked_out_at or CHECKED_IN_AT,
    }


def _director_attendance_row() -> dict[str, object]:
    return {
        "employee_id": str(EMPLOYEE_ID),
        "employee_code": "IEMS-001",
        "full_name": "Example Employee",
        "first_check_in": CHECKED_IN_AT,
        "last_check_out": CHECKED_OUT_AT,
        "total_minutes": 510,
        "attendance_state": "CHECKED_OUT",
    }


def test_service_check_in_calls_audited_rpc_for_current_employee() -> None:
    from app.services.attendance import AttendanceService

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/rpc/check_in_attendance_audited":
            return Response(200, json=_attendance_row())
        return Response(500)

    service = AttendanceService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.check_in(
            remarks="Front desk",
            current_user=_current_user(),
            context=AuditContext(request_id=REQUEST_ID),
        )
    )

    assert result.employee_id == EMPLOYEE_ID
    assert result.checked_out_at is None
    request = seen_requests[0]
    assert request.url.path == "/rest/v1/rpc/check_in_attendance_audited"
    assert json.loads(request.content) == {
        "p_employee_id": str(EMPLOYEE_ID),
        "p_remarks": "Front desk",
        "p_actor_user_account_id": str(AUTH_USER_ID),
        "p_actor_employee_id": str(EMPLOYEE_ID),
        "p_request_id": str(REQUEST_ID),
        "p_ip_address": None,
        "p_user_agent": None,
    }


def test_service_maps_duplicate_open_session_to_conflict() -> None:
    from app.services.attendance import AttendanceError, AttendanceService

    def handler(request: httpx.Request) -> Response:
        if request.url.path == "/rest/v1/rpc/check_in_attendance_audited":
            return Response(
                400,
                json={"code": "P0001", "message": "IEMS_ATTENDANCE_SESSION_ALREADY_OPEN"},
            )
        return Response(500)

    service = AttendanceService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AttendanceError) as exc_info:
        asyncio.run(
            service.check_in(
                remarks=None,
                current_user=_current_user(),
                context=AuditContext(request_id=REQUEST_ID),
            )
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "RESOURCE_CONFLICT"


def test_service_check_out_calls_audited_rpc_for_current_employee() -> None:
    from app.services.attendance import AttendanceService

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/rpc/check_out_attendance_audited":
            return Response(200, json=_attendance_row(checked_out_at=CHECKED_OUT_AT))
        return Response(500)

    service = AttendanceService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.check_out(
            remarks="Leaving office",
            current_user=_current_user(),
            context=AuditContext(request_id=REQUEST_ID),
        )
    )

    assert result.checked_out_at == datetime(2026, 6, 13, 17, 30, tzinfo=UTC)
    request = seen_requests[0]
    assert request.url.path == "/rest/v1/rpc/check_out_attendance_audited"
    assert json.loads(request.content)["p_remarks"] == "Leaving office"


def test_service_maps_missing_open_session_to_invalid_state() -> None:
    from app.services.attendance import AttendanceError, AttendanceService

    def handler(request: httpx.Request) -> Response:
        if request.url.path == "/rest/v1/rpc/check_out_attendance_audited":
            return Response(
                400,
                json={"code": "P0001", "message": "IEMS_ATTENDANCE_OPEN_SESSION_NOT_FOUND"},
            )
        return Response(500)

    service = AttendanceService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AttendanceError) as exc_info:
        asyncio.run(
            service.check_out(
                remarks=None,
                current_user=_current_user(),
                context=AuditContext(request_id=REQUEST_ID),
            )
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "INVALID_STATE"


def test_service_lists_own_attendance_with_date_filters() -> None:
    from app.services.attendance import AttendanceService

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/attendance_sessions":
            return Response(200, json=[_attendance_row(checked_out_at=CHECKED_OUT_AT)])
        return Response(500)

    service = AttendanceService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    rows = asyncio.run(
        service.list_my_attendance(
            current_user=_current_user(),
            from_date=date(2026, 6, 1),
            to_date=date(2026, 6, 30),
            limit=10,
            offset=5,
        )
    )

    assert rows[0].id == SESSION_ID
    params = seen_requests[0].url.params
    assert params["employee_id"] == f"eq.{EMPLOYEE_ID}"
    assert params["and"] == (
        "(checked_in_at.gte.2026-06-01T00:00:00+00:00,"
        "checked_in_at.lt.2026-07-01T00:00:00+00:00)"
    )
    assert params["limit"] == "10"
    assert params["offset"] == "5"


def test_service_lists_team_attendance_requires_permission() -> None:
    from app.services.attendance import AttendanceError, AttendanceService

    service = AttendanceService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(lambda request: Response(500)),
    )

    with pytest.raises(AttendanceError) as exc_info:
        asyncio.run(
            service.list_team_attendance(
                current_user=_current_user(),
                employee_id=None,
                from_date=None,
                to_date=None,
                limit=50,
                offset=0,
            )
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "PERMISSION_DENIED"


def test_service_lists_team_attendance_for_privileged_user() -> None:
    from app.services.attendance import AttendanceService

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/attendance_sessions":
            return Response(
                200,
                json=[_attendance_row(employee_id=OTHER_EMPLOYEE_ID, checked_out_at=None)],
            )
        return Response(500)

    service = AttendanceService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    rows = asyncio.run(
        service.list_team_attendance(
            current_user=_current_user(permissions=["attendance.view_all"]),
            employee_id=OTHER_EMPLOYEE_ID,
            from_date=None,
            to_date=None,
            limit=50,
            offset=0,
        )
    )

    assert rows[0].employee_id == OTHER_EMPLOYEE_ID
    assert seen_requests[0].url.params["employee_id"] == f"eq.{OTHER_EMPLOYEE_ID}"


def test_service_lists_director_attendance_requires_view_all() -> None:
    from app.services.attendance import AttendanceError, AttendanceService

    service = AttendanceService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(lambda request: Response(500)),
    )

    with pytest.raises(AttendanceError) as exc_info:
        asyncio.run(service.list_director_attendance(current_user=_current_user()))

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "PERMISSION_DENIED"


def test_service_lists_director_attendance_from_summary_view() -> None:
    from app.services.attendance import AttendanceService

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/director_attendance_today_v":
            return Response(200, json=[_director_attendance_row()])
        return Response(500)

    service = AttendanceService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    rows = asyncio.run(
        service.list_director_attendance(
            current_user=_current_user(permissions=["attendance.view_all"]),
        )
    )

    assert rows[0].employee_id == EMPLOYEE_ID
    assert rows[0].attendance_state == "CHECKED_OUT"
    assert seen_requests[0].url.path == "/rest/v1/director_attendance_today_v"


def test_service_correct_session_calls_audited_rpc() -> None:
    from app.schemas.attendance import AttendanceCorrectionUpdate
    from app.services.attendance import AttendanceService

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/rpc/correct_attendance_session_audited":
            return Response(
                200,
                json=_attendance_row(
                    checked_out_at=CHECKED_OUT_AT,
                    correction_reason="Missed scan",
                ),
            )
        return Response(500)

    service = AttendanceService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.correct_session(
            session_id=SESSION_ID,
            payload=AttendanceCorrectionUpdate(
                checked_out_at=datetime(2026, 6, 13, 17, 30, tzinfo=UTC),
                remarks="Adjusted by admin",
                correction_reason="Missed scan",
            ),
            current_user=_current_user(permissions=["attendance.correct"]),
            context=AuditContext(request_id=REQUEST_ID),
        )
    )

    assert result.correction_reason == "Missed scan"
    request = seen_requests[0]
    assert request.url.path == "/rest/v1/rpc/correct_attendance_session_audited"
    body = json.loads(request.content)
    assert body["p_session_id"] == str(SESSION_ID)
    assert body["p_patch"]["checked_out_at"] == CHECKED_OUT_AT
    assert body["p_patch"]["remarks"] == "Adjusted by admin"
    assert body["p_correction_reason"] == "Missed scan"
