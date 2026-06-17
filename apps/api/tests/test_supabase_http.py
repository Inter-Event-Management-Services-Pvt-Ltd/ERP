import asyncio
import logging
from types import SimpleNamespace

import httpx
import pytest
from starlette.requests import Request

from app.api import dependencies
from app.core.config import Settings
from app.core.supabase_http import reset_current_request_id, set_current_request_id
from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount
from app.services.clients_projects import ClientsProjectsService


def _request_with_supabase_client(client: httpx.AsyncClient) -> Request:
    app = SimpleNamespace(state=SimpleNamespace(supabase_http_client=client))
    return Request({"type": "http", "app": app})


def test_clients_projects_factory_reuses_request_scoped_supabase_http_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async_client = httpx.AsyncClient(transport=httpx.MockTransport(lambda _: httpx.Response(200)))
    request = _request_with_supabase_client(async_client)
    monkeypatch.setattr(
        dependencies,
        "get_settings",
        lambda: Settings(
            SUPABASE_URL="http://localhost:54321",
            SUPABASE_SERVICE_ROLE_KEY="legacy-service-role-key",
        ),
    )

    try:
        service = dependencies.get_clients_projects_service(request)
    finally:
        asyncio.run(async_client.aclose())

    assert service._http_client is async_client


def test_service_logs_supabase_request_timing(caplog: pytest.LogCaptureFixture) -> None:
    current_user = CurrentUser(
        auth_user_id="11111111-1111-4111-8111-111111111111",
        account=UserAccount(is_active=True, is_super_user=False),
        employee=EmployeeProfile(
            id="22222222-2222-4222-8222-222222222222",
            employee_code="IEMS-001",
            full_name="Example Employee",
            official_email="employee@iemsnewdelhi.com",
            designation="Coordinator",
            employment_status="ACTIVE",
        ),
        roles=["EMPLOYEE"],
        permissions=["project.view"],
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/rest/v1/clients"
        return httpx.Response(200, json=[])

    service = ClientsProjectsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    caplog.set_level(logging.INFO, logger="iems.api.supabase")
    request_id_token = set_current_request_id("perf-request-1")
    try:
        result = asyncio.run(service.list_clients(current_user=current_user))
    finally:
        reset_current_request_id(request_id_token)

    assert result == []
    record = next(
        record for record in caplog.records if record.message == "supabase_request_completed"
    )
    assert record.method == "GET"
    assert record.path == "/rest/v1/clients"
    assert record.request_id == "perf-request-1"
    assert record.status_code == 200
    assert isinstance(record.duration_ms, float)
    assert record.query_keys == ["is_active", "limit", "offset", "order", "select"]
