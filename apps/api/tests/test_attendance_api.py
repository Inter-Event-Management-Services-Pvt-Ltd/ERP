import asyncio
from datetime import UTC, date, datetime
from uuid import UUID

from httpx import ASGITransport, AsyncClient, Response

from app.api.dependencies import get_current_user
from app.core.audit import AuditContext
from app.main import app
from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount

AUTH_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
OTHER_EMPLOYEE_ID = UUID("33333333-3333-4333-8333-333333333333")
SESSION_ID = UUID("44444444-4444-4444-8444-444444444444")
REQUEST_ID = UUID("55555555-5555-4555-8555-555555555555")

CHECKED_IN_AT = datetime(2026, 6, 13, 9, 0, tzinfo=UTC)
CHECKED_OUT_AT = datetime(2026, 6, 13, 17, 30, tzinfo=UTC)


class RecordingAttendanceService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object, CurrentUser, AuditContext | None]] = []

    async def check_in(
        self,
        *,
        remarks: str | None,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> object:
        self.calls.append(("check_in", remarks, current_user, context))
        return _attendance_response(checked_out_at=None)

    async def check_out(
        self,
        *,
        remarks: str | None,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> object:
        self.calls.append(("check_out", remarks, current_user, context))
        return _attendance_response(checked_out_at=CHECKED_OUT_AT)

    async def list_my_attendance(
        self,
        *,
        current_user: CurrentUser,
        from_date: date | None,
        to_date: date | None,
        limit: int,
        offset: int,
    ) -> list[object]:
        self.calls.append(
            ("list_my_attendance", (from_date, to_date, limit, offset), current_user, None)
        )
        return [_attendance_response(checked_out_at=CHECKED_OUT_AT)]

    async def list_team_attendance(
        self,
        *,
        current_user: CurrentUser,
        employee_id: UUID | None,
        from_date: date | None,
        to_date: date | None,
        limit: int,
        offset: int,
    ) -> list[object]:
        self.calls.append(
            (
                "list_team_attendance",
                (employee_id, from_date, to_date, limit, offset),
                current_user,
                None,
            )
        )
        return [_attendance_response(employee_id=OTHER_EMPLOYEE_ID, checked_out_at=None)]

    async def list_director_attendance(self, *, current_user: CurrentUser) -> list[object]:
        self.calls.append(("list_director_attendance", None, current_user, None))
        return [_director_attendance_response()]

    async def correct_session(
        self,
        *,
        session_id: UUID,
        payload: object,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> object:
        self.calls.append(("correct_session", (session_id, payload), current_user, context))
        return _attendance_response(checked_out_at=CHECKED_OUT_AT, correction_reason="Missed scan")


def _attendance_response(
    *,
    employee_id: UUID = EMPLOYEE_ID,
    checked_out_at: datetime | None,
    correction_reason: str | None = None,
) -> object:
    from app.schemas.attendance import AttendanceEmployeeSummary, AttendanceSessionResponse

    return AttendanceSessionResponse(
        id=SESSION_ID,
        employee_id=employee_id,
        employee=AttendanceEmployeeSummary(
            id=employee_id,
            employee_code="IEMS-001",
            full_name="Example Employee",
        ),
        checked_in_at=CHECKED_IN_AT,
        checked_out_at=checked_out_at,
        source="WEB",
        remarks="Front desk",
        created_by=EMPLOYEE_ID,
        corrected_by=EMPLOYEE_ID if correction_reason else None,
        correction_reason=correction_reason,
        created_at=CHECKED_IN_AT,
        updated_at=CHECKED_OUT_AT if checked_out_at else CHECKED_IN_AT,
        total_minutes=510 if checked_out_at else None,
    )


def _director_attendance_response() -> object:
    from app.schemas.attendance import DirectorAttendanceSummaryResponse

    return DirectorAttendanceSummaryResponse(
        employee_id=EMPLOYEE_ID,
        employee_code="IEMS-001",
        full_name="Example Employee",
        first_check_in=CHECKED_IN_AT,
        last_check_out=CHECKED_OUT_AT,
        total_minutes=510,
        attendance_state="CHECKED_OUT",
    )


def _current_user(*, permissions: list[str], is_super_user: bool = False) -> CurrentUser:
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
        permissions=permissions,
    )


async def _request(
    method: str,
    path: str,
    *,
    json: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.request(method, path, json=json, headers=headers)


def _install_overrides(
    *,
    current_user: CurrentUser,
    service: RecordingAttendanceService | None = None,
) -> RecordingAttendanceService:
    from app.api.dependencies import get_attendance_service

    installed_service = service or RecordingAttendanceService()

    async def override_current_user() -> CurrentUser:
        return current_user

    async def override_attendance_service() -> RecordingAttendanceService:
        return installed_service

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_attendance_service] = override_attendance_service
    return installed_service


def test_check_in_returns_open_session_for_current_employee() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                "/v1/attendance/check-in",
                json={"remarks": "Front desk"},
                headers={"Authorization": "Bearer test-token", "X-Request-ID": str(REQUEST_ID)},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["employee_id"] == str(EMPLOYEE_ID)
    assert response.json()["checked_out_at"] is None
    assert service.calls[0][0] == "check_in"
    assert service.calls[0][1] == "Front desk"
    assert service.calls[0][3] == AuditContext(
        request_id=REQUEST_ID,
        ip_address="127.0.0.1",
        user_agent="python-httpx/0.28.1",
    )


def test_check_out_returns_closed_session_for_current_employee() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                "/v1/attendance/check-out",
                json={"remarks": "Leaving office"},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["checked_out_at"] == CHECKED_OUT_AT.isoformat().replace("+00:00", "Z")
    assert response.json()["total_minutes"] == 510
    assert service.calls[0][0] == "check_out"


def test_my_attendance_does_not_require_attendance_view_all() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/attendance/me?from_date=2026-06-01&to_date=2026-06-30&limit=10&offset=5",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(SESSION_ID)
    assert service.calls[0][0] == "list_my_attendance"
    assert service.calls[0][1] == (date(2026, 6, 1), date(2026, 6, 30), 10, 5)


def test_team_attendance_requires_attendance_view_all() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/attendance/team",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert service.calls == []


def test_team_attendance_returns_employee_scoped_rows_for_privileged_user() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["attendance.view_all"]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                f"/v1/attendance/team?employee_id={OTHER_EMPLOYEE_ID}",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["employee_id"] == str(OTHER_EMPLOYEE_ID)
    assert service.calls[0][0] == "list_team_attendance"
    assert service.calls[0][1][0] == OTHER_EMPLOYEE_ID


def test_director_attendance_requires_attendance_view_all() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/director/attendance",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert service.calls == []


def test_director_attendance_returns_today_summary_for_privileged_user() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["attendance.view_all"]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/director/attendance",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["attendance_state"] == "CHECKED_OUT"
    assert service.calls[0][0] == "list_director_attendance"


def test_correct_attendance_requires_attendance_correct_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "PATCH",
                f"/v1/attendance/sessions/{SESSION_ID}",
                json={
                    "checked_in_at": CHECKED_IN_AT.isoformat(),
                    "correction_reason": "Missed scan",
                },
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert service.calls == []


def test_correct_attendance_requires_reason() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["attendance.correct"]))
    try:
        response = asyncio.run(
            _request(
                "PATCH",
                f"/v1/attendance/sessions/{SESSION_ID}",
                json={"remarks": "Adjusted"},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert service.calls == []


def test_correct_attendance_returns_corrected_session() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["attendance.correct"]))
    try:
        response = asyncio.run(
            _request(
                "PATCH",
                f"/v1/attendance/sessions/{SESSION_ID}",
                json={
                    "checked_out_at": CHECKED_OUT_AT.isoformat(),
                    "remarks": "Adjusted by admin",
                    "correction_reason": "Missed scan",
                },
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["correction_reason"] == "Missed scan"
    assert service.calls[0][0] == "correct_session"
