import asyncio

import pytest
from httpx import ASGITransport, AsyncClient, Response

from app.core.config import Settings
from app.core.module_flags import module_for_request
from app.core.rate_limit import InMemoryRateLimitStore, RateLimiter
from app.main import app


@pytest.fixture(autouse=True)
def reset_app_settings() -> None:
    settings = Settings()
    app.state.settings = settings
    app.state.rate_limiter = RateLimiter(settings=settings, store=InMemoryRateLimitStore())


async def _get(path: str, headers: dict[str, str] | None = None) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path, headers=headers)


def get(path: str, headers: dict[str, str] | None = None) -> Response:
    return asyncio.run(_get(path, headers=headers))


def test_settings_expose_module_flags_with_enabled_defaults() -> None:
    settings = Settings()

    assert settings.module_flags == {
        "projects": True,
        "documents": True,
        "archive_exports": True,
        "physical_archive": True,
        "attendance": True,
        "leave": True,
        "tasks": True,
        "calendar": True,
        "approvals": True,
        "director_dashboard": True,
        "admin": True,
    }


def test_modules_endpoint_returns_current_flags_without_auth() -> None:
    settings = Settings.model_validate(
        {
            "MODULE_ATTENDANCE_ENABLED": False,
            "MODULE_LEAVE_ENABLED": False,
        }
    )
    app.state.settings = settings
    app.state.rate_limiter = RateLimiter(settings=settings, store=InMemoryRateLimitStore())

    response = get("/v1/modules")

    assert response.status_code == 200
    modules = {module["code"]: module["enabled"] for module in response.json()}
    assert modules["attendance"] is False
    assert modules["leave"] is False
    assert modules["documents"] is True


def test_disabled_module_returns_stable_error_before_auth_resolution() -> None:
    settings = Settings.model_validate({"MODULE_ATTENDANCE_ENABLED": False})
    app.state.settings = settings
    app.state.rate_limiter = RateLimiter(settings=settings, store=InMemoryRateLimitStore())

    response = get("/v1/attendance/me", headers={"X-Request-ID": "module-disabled-test"})

    assert response.status_code == 403
    assert response.headers["X-Request-ID"] == "module-disabled-test"
    assert response.json() == {
        "error": {
            "code": "MODULE_DISABLED",
            "message": "This module is not enabled for this rollout.",
            "request_id": "module-disabled-test",
        }
    }


def test_enabled_module_still_uses_normal_auth_gate() -> None:
    response = get("/v1/attendance/me", headers={"X-Request-ID": "module-enabled-test"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_module_path_mapping_covers_split_employee_operations_routes() -> None:
    assert module_for_request("GET", "/v1/leave-requests/me") == "leave"
    assert module_for_request("POST", "/v1/tasks") == "tasks"
    assert module_for_request("PATCH", "/v1/calendar/events/event-id") == "calendar"
    assert module_for_request("GET", "/v1/modules") is None
