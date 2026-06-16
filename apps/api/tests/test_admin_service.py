import asyncio
import json
from datetime import date
from uuid import UUID

import httpx
import pytest
from httpx import Response

from app.core.audit import AuditContext
from app.schemas.admin import (
    DepartmentAssignmentCreate,
    EmployeeAdminCreate,
    FolderTemplateCreate,
    FolderTemplateItemCreate,
    PolicyCreate,
    PolicyUpdate,
    RoleAssignmentCreate,
)
from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount
from app.services.admin import AdminError, AdminService

AUTH_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
OTHER_EMPLOYEE_ID = UUID("33333333-3333-4333-8333-333333333333")
ROLE_ID = UUID("44444444-4444-4444-8444-444444444444")
DEPARTMENT_ID = UUID("55555555-5555-4555-8555-555555555555")
POLICY_ID = UUID("66666666-6666-4666-8666-666666666666")
TEMPLATE_ID = UUID("77777777-7777-4777-8777-777777777777")
TEMPLATE_ITEM_ID = UUID("88888888-8888-4888-8888-888888888888")
REQUEST_ID = UUID("99999999-9999-4999-8999-999999999999")
CREATED_AT = "2026-06-16T09:00:00+00:00"


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
            official_email="admin@iemsnewdelhi.com",
            designation="Admin",
            employment_status="ACTIVE",
        ),
        roles=["SUPER_USER"] if is_super_user else ["ADMIN"],
        permissions=permissions or [],
    )


def _employee_row(employee_id: UUID = OTHER_EMPLOYEE_ID) -> dict[str, object]:
    return {
        "id": str(employee_id),
        "employee_code": "IEMS-OPS-010",
        "full_name": "New Employee",
        "official_email": "new.employee@iemsnewdelhi.com",
        "phone": "+91-99999-00000",
        "designation": "Coordinator",
        "employment_status": "ACTIVE",
        "joined_on": "2026-06-01",
        "left_on": None,
        "created_at": CREATED_AT,
        "updated_at": CREATED_AT,
        "current_department": None,
        "roles": [],
        "account": None,
    }


def _role_row(code: str = "MANAGER") -> dict[str, object]:
    return {
        "id": str(ROLE_ID),
        "code": code,
        "name": code.title(),
        "description": None,
    }


def _role_assignment_row(code: str = "MANAGER") -> dict[str, object]:
    return {
        "employee_id": str(OTHER_EMPLOYEE_ID),
        "user_account_id": str(UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")),
        "role": _role_row(code),
        "assigned_at": CREATED_AT,
        "expires_at": None,
    }


def _department_assignment_row() -> dict[str, object]:
    return {
        "id": str(UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")),
        "employee_id": str(OTHER_EMPLOYEE_ID),
        "department": {
            "id": str(DEPARTMENT_ID),
            "code": "OPS",
            "name": "Operations",
        },
        "valid_from": "2026-06-16",
        "valid_to": None,
        "assigned_by": str(EMPLOYEE_ID),
    }


def _policy_row() -> dict[str, object]:
    return {
        "id": str(POLICY_ID),
        "name": "Project managers can upload",
        "action_code": "document.upload",
        "effect": "ALLOW",
        "priority": 100,
        "conditions": {"role": "MANAGER"},
        "is_active": True,
        "created_by": str(AUTH_USER_ID),
        "created_at": CREATED_AT,
        "updated_at": CREATED_AT,
    }


def _template_row() -> dict[str, object]:
    return {
        "id": str(TEMPLATE_ID),
        "name": "Standard Event Project",
        "project_type_id": None,
        "is_active": True,
        "created_by": str(EMPLOYEE_ID),
        "created_at": CREATED_AT,
        "items": [
            {
                "id": str(TEMPLATE_ITEM_ID),
                "template_id": str(TEMPLATE_ID),
                "parent_item_id": None,
                "name": "01 Client Brief",
                "sort_order": 10,
            }
        ],
    }


def test_service_creates_employee_through_audited_rpc() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/rpc/create_employee_audited":
            return Response(200, json=_employee_row())
        return Response(500, json={"message": "unexpected request"})

    service = AdminService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.create_employee(
            payload=EmployeeAdminCreate(
                employee_code="IEMS-OPS-010",
                full_name="New Employee",
                official_email="new.employee@iemsnewdelhi.com",
                phone="+91-99999-00000",
                designation="Coordinator",
                employment_status="ACTIVE",
                joined_on=date(2026, 6, 1),
            ),
            current_user=_current_user(permissions=["employee.manage"]),
            context=AuditContext(request_id=REQUEST_ID),
            override_reason=None,
        )
    )

    assert result.id == OTHER_EMPLOYEE_ID
    request = seen_requests[0]
    assert request.url.path == "/rest/v1/rpc/create_employee_audited"
    payload = json.loads(request.content)
    assert payload["p_employee_code"] == "IEMS-OPS-010"
    assert payload["p_official_email"] == "new.employee@iemsnewdelhi.com"
    assert payload["p_actor_employee_id"] == str(EMPLOYEE_ID)
    assert payload["p_request_id"] == str(REQUEST_ID)


def test_service_requires_employee_manage_for_employee_create() -> None:
    service = AdminService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(lambda _request: Response(500)),
    )

    with pytest.raises(AdminError) as exc_info:
        asyncio.run(
            service.create_employee(
                payload=EmployeeAdminCreate(
                    employee_code="IEMS-OPS-010",
                    full_name="New Employee",
                    official_email="new.employee@iemsnewdelhi.com",
                    employment_status="ACTIVE",
                ),
                current_user=_current_user(permissions=["employee.view"]),
                context=AuditContext(),
                override_reason=None,
            )
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "PERMISSION_DENIED"


def test_service_requires_override_reason_when_super_user_bypasses_admin_permission() -> None:
    service = AdminService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(lambda _request: Response(500)),
    )

    with pytest.raises(AdminError) as exc_info:
        asyncio.run(
            service.create_policy(
                payload=PolicyCreate(
                    name="Sensitive bypass policy",
                    action_code="document.download",
                    effect="ALLOW",
                    priority=50,
                    conditions={"scope": "all"},
                    is_active=True,
                ),
                current_user=_current_user(is_super_user=True),
                context=AuditContext(),
                override_reason=None,
            )
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "SUPER_USER_OVERRIDE_REASON_REQUIRED"


def test_service_blocks_self_super_user_role_assignment() -> None:
    def handler(request: httpx.Request) -> Response:
        if request.url.path == "/rest/v1/roles":
            return Response(200, json=[_role_row("SUPER_USER")])
        return Response(500)

    service = AdminService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AdminError) as exc_info:
        asyncio.run(
            service.assign_employee_role(
                employee_id=EMPLOYEE_ID,
                payload=RoleAssignmentCreate(role_id=ROLE_ID),
                current_user=_current_user(permissions=["role.manage"]),
                context=AuditContext(),
                override_reason="Need emergency access for audit",
            )
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "SELF_ELEVATION_DENIED"


def test_service_assigns_employee_role_through_audited_rpc() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/roles":
            return Response(200, json=[_role_row("MANAGER")])
        if request.url.path == "/rest/v1/rpc/assign_employee_role_audited":
            return Response(200, json=_role_assignment_row("MANAGER"))
        return Response(500)

    service = AdminService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.assign_employee_role(
            employee_id=OTHER_EMPLOYEE_ID,
            payload=RoleAssignmentCreate(role_id=ROLE_ID),
            current_user=_current_user(permissions=["role.manage"]),
            context=AuditContext(request_id=REQUEST_ID),
            override_reason=None,
        )
    )

    assert result.role.code == "MANAGER"
    rpc_request = seen_requests[1]
    assert rpc_request.url.path == "/rest/v1/rpc/assign_employee_role_audited"
    payload = json.loads(rpc_request.content)
    assert payload["p_employee_id"] == str(OTHER_EMPLOYEE_ID)
    assert payload["p_role_id"] == str(ROLE_ID)


def test_service_assigns_department_through_audited_rpc() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/rpc/assign_employee_department_audited":
            return Response(200, json=_department_assignment_row())
        return Response(500)

    service = AdminService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.assign_employee_department(
            employee_id=OTHER_EMPLOYEE_ID,
            payload=DepartmentAssignmentCreate(
                department_id=DEPARTMENT_ID,
                valid_from=date(2026, 6, 16),
            ),
            current_user=_current_user(permissions=["employee.manage"]),
            context=AuditContext(request_id=REQUEST_ID),
            override_reason=None,
        )
    )

    assert result.department.code == "OPS"
    assert seen_requests[0].url.path == "/rest/v1/rpc/assign_employee_department_audited"


def test_service_updates_policy_through_audited_rpc() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/rpc/update_policy_audited":
            return Response(200, json={**_policy_row(), "priority": 10})
        return Response(500)

    service = AdminService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.update_policy(
            policy_id=POLICY_ID,
            payload=PolicyUpdate(priority=10),
            current_user=_current_user(permissions=["policy.manage"]),
            context=AuditContext(request_id=REQUEST_ID),
            override_reason=None,
        )
    )

    assert result.priority == 10
    payload = json.loads(seen_requests[0].content)
    assert payload["p_policy_id"] == str(POLICY_ID)
    assert payload["p_patch"] == {"priority": 10}


def test_service_creates_folder_template_item_through_audited_rpc() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/rpc/create_folder_template_audited":
            return Response(200, json={**_template_row(), "items": []})
        if request.url.path == "/rest/v1/rpc/create_folder_template_item_audited":
            return Response(200, json=_template_row())
        return Response(500)

    service = AdminService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    template = asyncio.run(
        service.create_folder_template(
            payload=FolderTemplateCreate(name="Standard Event Project", project_type_id=None),
            current_user=_current_user(permissions=["folder_template.manage"]),
            context=AuditContext(request_id=REQUEST_ID),
            override_reason=None,
        )
    )
    result = asyncio.run(
        service.create_folder_template_item(
            template_id=template.id,
            payload=FolderTemplateItemCreate(
                parent_item_id=None,
                name="01 Client Brief",
                sort_order=10,
            ),
            current_user=_current_user(permissions=["folder_template.manage"]),
            context=AuditContext(request_id=REQUEST_ID),
            override_reason=None,
        )
    )

    assert result.items[0].name == "01 Client Brief"
    assert seen_requests[1].url.path == "/rest/v1/rpc/create_folder_template_item_audited"
