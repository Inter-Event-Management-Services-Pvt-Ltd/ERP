import asyncio
import json
from uuid import UUID

import httpx
import pytest
from httpx import Response

from app.core.audit import AuditContext
from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount

AUTH_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
OTHER_EMPLOYEE_ID = UUID("33333333-3333-4333-8333-333333333333")
PROJECT_ID = UUID("44444444-4444-4444-8444-444444444444")
APPROVAL_TYPE_ID = UUID("55555555-5555-4555-8555-555555555555")
APPROVAL_ID = UUID("66666666-6666-4666-8666-666666666666")
ACTION_ID = UUID("77777777-7777-4777-8777-777777777777")
REQUEST_ID = UUID("88888888-8888-4888-8888-888888888888")
CREATED_AT = "2026-06-16T10:00:00+00:00"


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
        roles=["SUPER_USER"] if is_super_user else ["EMPLOYEE"],
        permissions=permissions or [],
    )


def _approval_type_row() -> dict[str, object]:
    return {
        "id": str(APPROVAL_TYPE_ID),
        "code": "PROJECT_CLOSURE",
        "name": "Project Closure",
    }


def _employee_row(employee_id: UUID = EMPLOYEE_ID) -> dict[str, object]:
    return {
        "id": str(employee_id),
        "employee_code": "IEMS-001" if employee_id == EMPLOYEE_ID else "IEMS-002",
        "full_name": "Example Employee" if employee_id == EMPLOYEE_ID else "Approver User",
    }


def _membership_row(access_level: str = "MANAGE") -> dict[str, object]:
    return {
        "project_id": str(PROJECT_ID),
        "employee_id": str(EMPLOYEE_ID),
        "access_level": access_level,
        "removed_at": None,
    }


def _approval_row(status: str = "PENDING", action: str = "SUBMITTED") -> dict[str, object]:
    return {
        "id": str(APPROVAL_ID),
        "approval_type_id": str(APPROVAL_TYPE_ID),
        "approval_type": _approval_type_row(),
        "project_id": str(PROJECT_ID),
        "document_version_id": None,
        "archive_export_id": None,
        "leave_request_id": None,
        "requested_by": str(EMPLOYEE_ID),
        "requested_by_employee": _employee_row(),
        "assigned_to": str(OTHER_EMPLOYEE_ID),
        "assigned_to_employee": _employee_row(OTHER_EMPLOYEE_ID),
        "status": status,
        "requested_at": CREATED_AT,
        "completed_at": CREATED_AT if status != "PENDING" else None,
        "actions": [
            {
                "id": str(ACTION_ID),
                "approval_request_id": str(APPROVAL_ID),
                "action": action,
                "performed_by": str(EMPLOYEE_ID),
                "performed_by_employee": _employee_row(),
                "comment": "Looks correct",
                "created_at": CREATED_AT,
            }
        ],
    }


def test_service_lists_approval_types() -> None:
    from app.services.approvals import ApprovalsService

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        return Response(200, json=[_approval_type_row()])

    service = ApprovalsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    rows = asyncio.run(service.list_approval_types(current_user=_current_user()))

    assert rows[0].code == "PROJECT_CLOSURE"
    assert seen_requests[0].url.path == "/rest/v1/approval_types"
    assert seen_requests[0].url.params["select"] == "id,code,name"
    assert seen_requests[0].url.params["is_active"] == "eq.true"


def test_service_scopes_approval_list_to_involved_user_without_view_all() -> None:
    from app.services.approvals import ApprovalsService

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        return Response(200, json=[_approval_row()])

    service = ApprovalsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    approvals = asyncio.run(
        service.list_approvals(
            current_user=_current_user(),
            status="PENDING",
            limit=25,
            offset=10,
        )
    )

    assert approvals[0].id == APPROVAL_ID
    params = seen_requests[0].url.params
    assert params["status"] == "eq.PENDING"
    assert params["or"] == f"(requested_by.eq.{EMPLOYEE_ID},assigned_to.eq.{EMPLOYEE_ID})"
    assert params["limit"] == "25"
    assert params["offset"] == "10"


def test_service_lists_all_approvals_with_view_all_permission() -> None:
    from app.services.approvals import ApprovalsService

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        return Response(200, json=[_approval_row()])

    service = ApprovalsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    asyncio.run(
        service.list_approvals(
            current_user=_current_user(permissions=["approval.view_all"]),
            status=None,
            limit=50,
            offset=0,
        )
    )

    assert "or" not in seen_requests[0].url.params


def test_service_create_project_approval_requires_manage_membership() -> None:
    from app.schemas.approvals import ApprovalRequestCreate
    from app.services.approvals import ApprovalsError, ApprovalsService

    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> Response:
        seen_paths.append(request.url.path)
        if request.url.path == "/rest/v1/project_members":
            return Response(200, json=[])
        return Response(500)

    service = ApprovalsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ApprovalsError) as exc_info:
        asyncio.run(
            service.create_approval(
                payload=ApprovalRequestCreate(
                    approval_type_id=APPROVAL_TYPE_ID,
                    project_id=PROJECT_ID,
                    assigned_to=OTHER_EMPLOYEE_ID,
                    comment="Please review project closure.",
                ),
                current_user=_current_user(permissions=["project.manage"]),
                context=AuditContext(request_id=REQUEST_ID),
            )
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "ABAC_DENIED"
    assert "/rest/v1/rpc/create_approval_request_audited" not in seen_paths


def test_service_create_project_approval_does_not_treat_approve_as_target_access() -> None:
    from app.schemas.approvals import ApprovalRequestCreate
    from app.services.approvals import ApprovalsError, ApprovalsService

    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> Response:
        seen_paths.append(request.url.path)
        return Response(500)

    service = ApprovalsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ApprovalsError) as exc_info:
        asyncio.run(
            service.create_approval(
                payload=ApprovalRequestCreate(
                    approval_type_id=APPROVAL_TYPE_ID,
                    project_id=PROJECT_ID,
                    assigned_to=OTHER_EMPLOYEE_ID,
                    comment="Please review project closure.",
                ),
                current_user=_current_user(permissions=["approval.approve"]),
                context=AuditContext(request_id=REQUEST_ID),
            )
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "PERMISSION_DENIED"
    assert seen_paths == []


def test_service_creates_approval_through_audited_rpc() -> None:
    from app.schemas.approvals import ApprovalRequestCreate
    from app.services.approvals import ApprovalsService

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/project_members":
            return Response(200, json=[_membership_row()])
        if request.url.path == "/rest/v1/rpc/create_approval_request_audited":
            return Response(200, json=_approval_row())
        return Response(500)

    service = ApprovalsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    approval = asyncio.run(
        service.create_approval(
            payload=ApprovalRequestCreate(
                approval_type_id=APPROVAL_TYPE_ID,
                project_id=PROJECT_ID,
                assigned_to=OTHER_EMPLOYEE_ID,
                comment="Please review project closure.",
            ),
            current_user=_current_user(permissions=["project.manage"]),
            context=AuditContext(
                request_id=REQUEST_ID,
                ip_address="127.0.0.1",
                user_agent="pytest",
            ),
        )
    )

    assert approval.status == "PENDING"
    rpc_body = json.loads(seen_requests[1].content)
    assert rpc_body == {
        "p_approval_type_id": str(APPROVAL_TYPE_ID),
        "p_project_id": str(PROJECT_ID),
        "p_document_version_id": None,
        "p_archive_export_id": None,
        "p_leave_request_id": None,
        "p_requested_by": str(EMPLOYEE_ID),
        "p_assigned_to": str(OTHER_EMPLOYEE_ID),
        "p_comment": "Please review project closure.",
        "p_actor_user_account_id": str(AUTH_USER_ID),
        "p_actor_employee_id": str(EMPLOYEE_ID),
        "p_request_id": str(REQUEST_ID),
        "p_ip_address": "127.0.0.1",
        "p_user_agent": "pytest",
    }


def test_service_approves_request_through_audited_rpc() -> None:
    from app.services.approvals import ApprovalsService

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        return Response(200, json=_approval_row(status="APPROVED", action="APPROVED"))

    service = ApprovalsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.approve_approval(
            approval_id=APPROVAL_ID,
            comment="Approved",
            current_user=_current_user(permissions=["approval.approve"]),
            context=AuditContext(request_id=REQUEST_ID),
        )
    )

    assert result.status == "APPROVED"
    assert seen_requests[0].url.path == "/rest/v1/rpc/review_approval_request_audited"
    assert json.loads(seen_requests[0].content)["p_action"] == "APPROVED"


def test_service_maps_non_pending_review_to_invalid_state() -> None:
    from app.services.approvals import ApprovalsError, ApprovalsService

    def handler(request: httpx.Request) -> Response:
        return Response(400, json={"code": "P0001", "message": "IEMS_APPROVAL_NOT_PENDING"})

    service = ApprovalsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ApprovalsError) as exc_info:
        asyncio.run(
            service.reject_approval(
                approval_id=APPROVAL_ID,
                comment="Rejected",
                current_user=_current_user(permissions=["approval.approve"]),
                context=AuditContext(request_id=REQUEST_ID),
            )
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "INVALID_STATE"
