import asyncio
from typing import Annotated
from uuid import UUID

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_audit_writer, get_current_user, require_super_user_override
from app.core.audit import AuditContext
from app.core.rbac import AuthorizationError
from app.core.super_user import SuperUserOverrideService
from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount

AUTH_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
REQUEST_ID = UUID("33333333-3333-4333-8333-333333333333")
RESOURCE_ID = UUID("44444444-4444-4444-8444-444444444444")
OVERRIDE_ID = UUID("55555555-5555-4555-8555-555555555555")


class RecordingOverrideWriter:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def record_super_user_override(
        self,
        *,
        user_account_id: UUID,
        actor_employee_id: UUID,
        action_code: str,
        resource_type: str,
        resource_id: UUID,
        reason: str,
        context: AuditContext,
        metadata: dict[str, object] | None = None,
    ) -> UUID:
        self.calls.append(
            {
                "user_account_id": user_account_id,
                "actor_employee_id": actor_employee_id,
                "action_code": action_code,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "reason": reason,
                "context": context,
                "metadata": metadata,
            }
        )
        return OVERRIDE_ID


def _current_user(*, is_super_user: bool) -> CurrentUser:
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
        roles=["SUPER_USER"] if is_super_user else ["EMPLOYEE"],
        permissions=[],
    )


def test_super_user_override_service_rejects_non_super_user() -> None:
    writer = RecordingOverrideWriter()

    with pytest.raises(AuthorizationError) as exc_info:
        asyncio.run(
            SuperUserOverrideService().record_override(
                current_user=_current_user(is_super_user=False),
                action_code="project.delete",
                resource_type="project",
                resource_id=RESOURCE_ID,
                reason="Valid business reason",
                context=AuditContext(request_id=REQUEST_ID),
                writer=writer,
            )
        )

    assert exc_info.value.code == "SUPER_USER_REQUIRED"
    assert writer.calls == []


def test_super_user_override_service_rejects_short_reason() -> None:
    writer = RecordingOverrideWriter()

    with pytest.raises(AuthorizationError) as exc_info:
        asyncio.run(
            SuperUserOverrideService().record_override(
                current_user=_current_user(is_super_user=True),
                action_code="project.delete",
                resource_type="project",
                resource_id=RESOURCE_ID,
                reason="short",
                context=AuditContext(request_id=REQUEST_ID),
                writer=writer,
            )
        )

    assert exc_info.value.code == "SUPER_USER_OVERRIDE_REASON_REQUIRED"
    assert writer.calls == []


def test_super_user_override_service_records_override_and_audit_context() -> None:
    writer = RecordingOverrideWriter()
    context = AuditContext(
        request_id=REQUEST_ID,
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    override_id = asyncio.run(
        SuperUserOverrideService().record_override(
            current_user=_current_user(is_super_user=True),
            action_code="project.delete",
            resource_type="project",
            resource_id=RESOURCE_ID,
            reason="Valid business reason",
            context=context,
            writer=writer,
            metadata={"phase": "1"},
        )
    )

    assert override_id == OVERRIDE_ID
    assert writer.calls == [
        {
            "user_account_id": AUTH_USER_ID,
            "actor_employee_id": EMPLOYEE_ID,
            "action_code": "project.delete",
            "resource_type": "project",
            "resource_id": RESOURCE_ID,
            "reason": "Valid business reason",
            "context": context,
            "metadata": {"phase": "1"},
        }
    ]


def test_super_user_override_dependency_records_header_reason() -> None:
    writer = RecordingOverrideWriter()
    app = FastAPI()

    async def override_current_user() -> CurrentUser:
        return _current_user(is_super_user=True)

    async def override_audit_writer() -> RecordingOverrideWriter:
        return writer

    @app.post("/projects/{project_id}/override")
    async def override_project(
        _override_id: Annotated[
            UUID,
            Depends(require_super_user_override("project.delete", "project", "project_id")),
        ],
    ) -> dict[str, str]:
        return {"status": "ok"}

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_audit_writer] = override_audit_writer

    async def run_request() -> tuple[int, dict[str, str]]:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                f"/projects/{RESOURCE_ID}/override",
                headers={
                    "X-IEMS-Override-Reason": "Valid dependency reason",
                    "X-Request-ID": str(REQUEST_ID),
                },
            )
            return response.status_code, response.json()

    status_code, payload = asyncio.run(run_request())

    assert status_code == 200
    assert payload == {"status": "ok"}
    assert writer.calls[0]["reason"] == "Valid dependency reason"
    assert writer.calls[0]["resource_id"] == RESOURCE_ID
