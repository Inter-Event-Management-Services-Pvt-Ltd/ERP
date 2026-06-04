import asyncio
import json
from uuid import UUID

import httpx
from httpx import Response

from app.core.audit import AuditContext, AuditEvent, SupabaseAuditWriter

AUDIT_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
AUTH_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
REQUEST_ID = UUID("33333333-3333-4333-8333-333333333333")
RESOURCE_ID = UUID("44444444-4444-4444-8444-444444444444")
OVERRIDE_ID = UUID("55555555-5555-4555-8555-555555555555")


def test_supabase_audit_writer_posts_audit_event() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        return Response(201, json=[{"id": str(AUDIT_ID)}])

    writer = SupabaseAuditWriter(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )
    event = AuditEvent(
        actor_user_account_id=AUTH_USER_ID,
        actor_employee_id=EMPLOYEE_ID,
        action_code="phase1.test",
        resource_type="phase1_resource",
        resource_id=RESOURCE_ID,
        context=AuditContext(
            request_id=REQUEST_ID,
            ip_address="127.0.0.1",
            user_agent="pytest",
        ),
        metadata={"source": "test"},
    )

    created_id = asyncio.run(writer.write_event(event))

    assert created_id == AUDIT_ID
    request = seen_requests[0]
    assert str(request.url) == "http://localhost:54321/rest/v1/audit_events?select=id"
    assert request.headers["apikey"] == "legacy-service-role-key"
    assert request.headers["authorization"] == "Bearer legacy-service-role-key"
    assert request.headers["prefer"] == "return=representation"
    body = json.loads(request.content)
    assert body["actor_user_account_id"] == str(AUTH_USER_ID)
    assert body["actor_employee_id"] == str(EMPLOYEE_ID)
    assert body["action_code"] == "phase1.test"
    assert body["resource_type"] == "phase1_resource"
    assert body["resource_id"] == str(RESOURCE_ID)
    assert body["request_id"] == str(REQUEST_ID)
    assert body["metadata"] == {"source": "test"}
    assert body["ip_address"] == "127.0.0.1"
    assert body["user_agent"] == "pytest"


def test_supabase_audit_writer_records_super_user_override_through_rpc() -> None:
    seen_requests: list[httpx.Request] = []
    service_key = "sb" "_secret_test_secret_key_value_123456"

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        return Response(200, json=str(OVERRIDE_ID))

    writer = SupabaseAuditWriter(
        supabase_url="http://localhost:54321",
        service_role_key=service_key,
        transport=httpx.MockTransport(handler),
    )

    created_id = asyncio.run(
        writer.record_super_user_override(
            user_account_id=AUTH_USER_ID,
            actor_employee_id=EMPLOYEE_ID,
            action_code="project.delete",
            resource_type="project",
            resource_id=RESOURCE_ID,
            reason="Phase 1 override test",
            context=AuditContext(
                request_id=REQUEST_ID,
                ip_address="127.0.0.1",
                user_agent="pytest",
            ),
            metadata={"phase": "1"},
        )
    )

    assert created_id == OVERRIDE_ID
    request = seen_requests[0]
    assert str(request.url) == "http://localhost:54321/rest/v1/rpc/record_super_user_override"
    assert request.headers["apikey"] == service_key
    assert "authorization" not in request.headers
    body = json.loads(request.content)
    assert body == {
        "p_user_account_id": str(AUTH_USER_ID),
        "p_actor_employee_id": str(EMPLOYEE_ID),
        "p_action_code": "project.delete",
        "p_resource_type": "project",
        "p_resource_id": str(RESOURCE_ID),
        "p_reason": "Phase 1 override test",
        "p_request_id": str(REQUEST_ID),
        "p_metadata": {"phase": "1"},
        "p_ip_address": "127.0.0.1",
        "p_user_agent": "pytest",
    }
