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
PROJECT_ID = UUID("44444444-4444-4444-8444-444444444444")
FOLDER_ID = UUID("55555555-5555-4555-8555-555555555555")
DOCUMENT_ID = UUID("66666666-6666-4666-8666-666666666666")
LEAVE_TYPE_ID = UUID("77777777-7777-4777-8777-777777777777")
LEAVE_REQUEST_ID = UUID("88888888-8888-4888-8888-888888888888")
TASK_ID = UUID("99999999-9999-4999-8999-999999999999")
TASK_STATUS_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
PRIORITY_LEVEL_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
CALENDAR_EVENT_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
CHECKOUT_ID = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
PHYSICAL_FILE_ID = UUID("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")
REQUEST_ID = UUID("ffffffff-ffff-4fff-8fff-ffffffffffff")

CREATED_AT = "2026-06-15T09:00:00+00:00"
DUE_AT = "2026-06-20T12:00:00+00:00"
EVENT_STARTS_AT = "2026-06-18T10:00:00+00:00"
EVENT_ENDS_AT = "2026-06-18T11:00:00+00:00"


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


def _employee_row(employee_id: UUID = EMPLOYEE_ID) -> dict[str, object]:
    return {
        "id": str(employee_id),
        "employee_code": "IEMS-001",
        "full_name": "Example Employee",
    }


def _reference_row(id_value: UUID, code: str, name: str) -> dict[str, object]:
    return {"id": str(id_value), "code": code, "name": name}


def _leave_row(*, status: str = "PENDING") -> dict[str, object]:
    return {
        "id": str(LEAVE_REQUEST_ID),
        "employee_id": str(EMPLOYEE_ID),
        "employee": _employee_row(),
        "leave_type_id": str(LEAVE_TYPE_ID),
        "leave_type": _reference_row(LEAVE_TYPE_ID, "CASUAL", "Casual Leave"),
        "start_date": "2026-06-20",
        "end_date": "2026-06-21",
        "reason": "Family commitment",
        "status": status,
        "requested_at": CREATED_AT,
        "reviewed_by": str(OTHER_EMPLOYEE_ID) if status in {"APPROVED", "REJECTED"} else None,
        "reviewed_at": CREATED_AT if status in {"APPROVED", "REJECTED"} else None,
        "review_comment": "Approved" if status == "APPROVED" else None,
    }


def _task_row(*, due_at: str | None = DUE_AT) -> dict[str, object]:
    return {
        "id": str(TASK_ID),
        "project_id": str(PROJECT_ID),
        "project": {
            "id": str(PROJECT_ID),
            "project_code": "IEMS-2026-DEMO-001",
            "name": "Demo Project",
        },
        "related_folder_id": str(FOLDER_ID),
        "title": "Prepare production checklist",
        "description": "Coordinate production readiness",
        "task_status_id": str(TASK_STATUS_ID),
        "task_status": _reference_row(TASK_STATUS_ID, "TODO", "To Do"),
        "priority_level_id": str(PRIORITY_LEVEL_ID),
        "priority_level": _reference_row(PRIORITY_LEVEL_ID, "HIGH", "High"),
        "created_by": str(EMPLOYEE_ID),
        "due_at": due_at,
        "completed_at": None,
        "created_at": CREATED_AT,
        "updated_at": CREATED_AT,
        "assignees": [
            {"employee": _employee_row()},
            {"employee": _employee_row(OTHER_EMPLOYEE_ID)},
        ],
        "documents": [{"document_id": str(DOCUMENT_ID)}],
    }


def _calendar_event_row() -> dict[str, object]:
    return {
        "id": str(CALENDAR_EVENT_ID),
        "project_id": str(PROJECT_ID),
        "related_task_id": None,
        "event_type": "MEETING",
        "title": "Project kickoff",
        "description": "Kickoff meeting",
        "starts_at": EVENT_STARTS_AT,
        "ends_at": EVENT_ENDS_AT,
        "location": "Conference Room",
        "created_by": str(EMPLOYEE_ID),
        "created_at": CREATED_AT,
        "updated_at": CREATED_AT,
    }


def _checkout_row() -> dict[str, object]:
    return {
        "id": str(CHECKOUT_ID),
        "physical_file_id": str(PHYSICAL_FILE_ID),
        "checked_out_by": str(EMPLOYEE_ID),
        "expected_return_at": "2026-06-22T17:00:00+00:00",
        "returned_at": None,
        "physical_file": {
            "id": str(PHYSICAL_FILE_ID),
            "physical_file_code": "PF-001",
            "project_id": str(PROJECT_ID),
        },
    }


def test_create_leave_request_calls_audited_rpc_for_current_employee() -> None:
    from app.schemas.employee_operations import LeaveRequestCreate
    from app.services.employee_operations import EmployeeOperationsService

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/rpc/create_leave_request_audited":
            return Response(200, json=_leave_row())
        return Response(500)

    service = EmployeeOperationsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.create_leave_request(
            payload=LeaveRequestCreate(
                leave_type_id=LEAVE_TYPE_ID,
                start_date=date(2026, 6, 20),
                end_date=date(2026, 6, 21),
                reason="Family commitment",
            ),
            current_user=_current_user(),
            context=AuditContext(request_id=REQUEST_ID),
        )
    )

    assert result.status == "PENDING"
    assert seen_requests[0].url.path == "/rest/v1/rpc/create_leave_request_audited"
    assert json.loads(seen_requests[0].content) == {
        "p_employee_id": str(EMPLOYEE_ID),
        "p_leave_type_id": str(LEAVE_TYPE_ID),
        "p_start_date": "2026-06-20",
        "p_end_date": "2026-06-21",
        "p_reason": "Family commitment",
        "p_actor_user_account_id": str(AUTH_USER_ID),
        "p_actor_employee_id": str(EMPLOYEE_ID),
        "p_request_id": str(REQUEST_ID),
        "p_ip_address": None,
        "p_user_agent": None,
    }


def test_review_leave_request_maps_non_pending_state() -> None:
    from app.services.employee_operations import EmployeeOperationsError, EmployeeOperationsService

    def handler(request: httpx.Request) -> Response:
        if request.url.path == "/rest/v1/rpc/review_leave_request_audited":
            return Response(
                400,
                json={"code": "P0001", "message": "IEMS_LEAVE_REQUEST_NOT_PENDING"},
            )
        return Response(500)

    service = EmployeeOperationsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(EmployeeOperationsError) as exc_info:
        asyncio.run(
            service.approve_leave_request(
                request_id=LEAVE_REQUEST_ID,
                review_comment="Approved",
                current_user=_current_user(permissions=["leave.review"]),
                context=AuditContext(request_id=REQUEST_ID),
            )
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "INVALID_STATE"


def test_create_task_requires_project_manage_access_before_rpc() -> None:
    from app.schemas.employee_operations import TaskCreate
    from app.services.employee_operations import EmployeeOperationsService

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/project_members":
            return Response(200, json=[{"project_id": str(PROJECT_ID), "access_level": "MANAGE"}])
        if request.url.path == "/rest/v1/rpc/create_task_audited":
            return Response(200, json=_task_row())
        return Response(500)

    service = EmployeeOperationsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.create_task(
            payload=TaskCreate(
                project_id=PROJECT_ID,
                related_folder_id=FOLDER_ID,
                title="Prepare production checklist",
                description="Coordinate production readiness",
                priority_level_id=PRIORITY_LEVEL_ID,
                due_at=datetime(2026, 6, 20, 12, 0, tzinfo=UTC),
                assignee_ids=[EMPLOYEE_ID, OTHER_EMPLOYEE_ID],
                document_ids=[DOCUMENT_ID],
            ),
            current_user=_current_user(permissions=["task.manage"]),
            context=AuditContext(request_id=REQUEST_ID),
        )
    )

    assert result.id == TASK_ID
    assert seen_requests[0].url.path == "/rest/v1/project_members"
    assert seen_requests[1].url.path == "/rest/v1/rpc/create_task_audited"
    payload = json.loads(seen_requests[1].content)
    assert payload["p_project_id"] == str(PROJECT_ID)
    assert payload["p_assignee_ids"] == [str(EMPLOYEE_ID), str(OTHER_EMPLOYEE_ID)]
    assert payload["p_document_ids"] == [str(DOCUMENT_ID)]


def test_calendar_feed_includes_stored_events_deadlines_leave_and_file_returns() -> None:
    from app.services.employee_operations import EmployeeOperationsService

    def handler(request: httpx.Request) -> Response:
        if request.url.path == "/rest/v1/project_members":
            return Response(200, json=[{"project_id": str(PROJECT_ID), "access_level": "VIEW"}])
        if request.url.path == "/rest/v1/calendar_events":
            return Response(200, json=[_calendar_event_row()])
        if request.url.path == "/rest/v1/tasks":
            return Response(200, json=[_task_row()])
        if request.url.path == "/rest/v1/leave_requests":
            return Response(200, json=[_leave_row(status="APPROVED")])
        if request.url.path == "/rest/v1/physical_file_checkouts":
            return Response(200, json=[_checkout_row()])
        return Response(500)

    service = EmployeeOperationsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.list_calendar_events(
            current_user=_current_user(permissions=[]),
            from_date=date(2026, 6, 1),
            to_date=date(2026, 6, 30),
            project_id=PROJECT_ID,
        )
    )

    assert [event.source for event in result] == [
        "CALENDAR_EVENT",
        "TASK_DEADLINE",
        "LEAVE",
        "PHYSICAL_FILE_RETURN",
    ]
    assert result[1].related_task_id == TASK_ID
    assert result[3].event_type == "PHYSICAL_FILE_RETURN"
