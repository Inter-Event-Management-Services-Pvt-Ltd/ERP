import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID

from httpx import ASGITransport, AsyncClient, Response

from app.api.dependencies import get_current_user
from app.main import app
from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount

AUTH_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
OTHER_EMPLOYEE_ID = UUID("33333333-3333-4333-8333-333333333333")
NOTIFICATION_ID = UUID("44444444-4444-4444-8444-444444444444")
CREATED_AT = datetime(2026, 6, 20, 9, 0, tzinfo=UTC)
READ_AT = datetime(2026, 6, 20, 9, 5, tzinfo=UTC)


class SupabaseRecorder:
    def __init__(self, responses: list[Response]) -> None:
        self.responses = responses
        self.calls: list[dict[str, object]] = []

    async def request(
        self,
        client: object,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, str] | None = None,
        json_body: dict[str, object] | None = None,
    ) -> Response:
        self.calls.append(
            {
                "client": client,
                "method": method,
                "url": url,
                "headers": headers,
                "params": params or {},
                "json_body": json_body,
            }
        )
        return self.responses.pop(0)


def test_list_my_notifications_returns_current_employee_rows(monkeypatch) -> None:
    recorder = _install_overrides(
        monkeypatch,
        [
            Response(
                200,
                json=[
                    _notification_row(read_at=None),
                    _notification_row(
                        notification_id=UUID("55555555-5555-4555-8555-555555555555"),
                        notification_type="TASK",
                        title="Task updated",
                        read_at=READ_AT,
                    ),
                ],
            )
        ],
    )
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/me/notifications",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(NOTIFICATION_ID)
    assert response.json()[0]["employee_id"] == str(EMPLOYEE_ID)
    assert response.json()[0]["read_at"] is None
    assert response.json()[1]["read_at"] == READ_AT.isoformat().replace("+00:00", "Z")
    assert recorder.calls[0]["method"] == "GET"
    assert recorder.calls[0]["url"] == "http://supabase.test/rest/v1/notifications"
    assert recorder.calls[0]["params"] == {
        "select": "*",
        "employee_id": f"eq.{EMPLOYEE_ID}",
        "order": "created_at.desc",
        "limit": "50",
        "offset": "0",
    }


def test_list_my_notifications_passes_limit_and_offset_to_supabase(monkeypatch) -> None:
    recorder = _install_overrides(monkeypatch, [Response(200, json=[])])
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/me/notifications?limit=10&offset=25",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert recorder.calls[0]["params"]["limit"] == "10"
    assert recorder.calls[0]["params"]["offset"] == "25"


def test_mark_notification_read_returns_updated_notification(monkeypatch) -> None:
    recorder = _install_overrides(
        monkeypatch,
        [Response(200, json=[_notification_row(read_at=READ_AT)])],
    )
    try:
        response = asyncio.run(
            _request(
                "PATCH",
                f"/v1/me/notifications/{NOTIFICATION_ID}/read",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(NOTIFICATION_ID)
    assert response.json()["read_at"] == READ_AT.isoformat().replace("+00:00", "Z")
    assert recorder.calls[0]["method"] == "PATCH"
    assert recorder.calls[0]["params"] == {
        "select": "*",
        "id": f"eq.{NOTIFICATION_ID}",
        "employee_id": f"eq.{EMPLOYEE_ID}",
    }
    assert recorder.calls[0]["headers"]["Prefer"] == "return=representation"
    assert isinstance(recorder.calls[0]["json_body"], dict)
    assert isinstance(recorder.calls[0]["json_body"]["read_at"], str)


def test_mark_another_employee_notification_returns_not_found(monkeypatch) -> None:
    _install_overrides(monkeypatch, [Response(200, json=[])])
    try:
        response = asyncio.run(
            _request(
                "PATCH",
                f"/v1/me/notifications/{NOTIFICATION_ID}/read",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert response.json()["error"]["message"] == "Notification not found"


def test_mark_missing_notification_returns_not_found(monkeypatch) -> None:
    _install_overrides(monkeypatch, [Response(404, json={"message": "No rows"})])
    try:
        response = asyncio.run(
            _request(
                "PATCH",
                f"/v1/me/notifications/{NOTIFICATION_ID}/read",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert response.json()["error"]["message"] == "Notification not found"


async def _request(
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.request(method, path, headers=headers)


def _install_overrides(monkeypatch, responses: list[Response]) -> SupabaseRecorder:
    from app.api.v1 import me as me_module

    recorder = SupabaseRecorder(responses)
    settings = SimpleNamespace(
        supabase_url="http://supabase.test",
        supabase_service_role_key="legacy-service-role-key",
    )

    async def override_current_user() -> CurrentUser:
        return _current_user()

    app.dependency_overrides[get_current_user] = override_current_user
    monkeypatch.setattr(me_module, "get_settings", lambda: settings, raising=False)
    monkeypatch.setattr(
        me_module,
        "get_supabase_http_client",
        lambda _request, _settings: object(),
        raising=False,
    )
    monkeypatch.setattr(me_module, "request_supabase", recorder.request, raising=False)
    return recorder


def _current_user() -> CurrentUser:
    return CurrentUser(
        auth_user_id=AUTH_USER_ID,
        account=UserAccount(is_active=True, is_super_user=False),
        employee=EmployeeProfile(
            id=EMPLOYEE_ID,
            employee_code="IEMS-001",
            full_name="Example Employee",
            official_email="employee@iemsnewdelhi.com",
            designation="Coordinator",
            employment_status="ACTIVE",
        ),
        roles=["EMPLOYEE"],
        permissions=[],
    )


def _notification_row(
    *,
    notification_id: UUID = NOTIFICATION_ID,
    employee_id: UUID = EMPLOYEE_ID,
    notification_type: str = "APPROVAL",
    title: str = "Approval requested",
    read_at: datetime | None,
) -> dict[str, str | None]:
    return {
        "id": str(notification_id),
        "employee_id": str(employee_id),
        "notification_type": notification_type,
        "title": title,
        "message": "Please review the approval request.",
        "resource_type": "approval_request",
        "resource_id": str(OTHER_EMPLOYEE_ID),
        "read_at": read_at.isoformat() if read_at is not None else None,
        "created_at": CREATED_AT.isoformat(),
    }
