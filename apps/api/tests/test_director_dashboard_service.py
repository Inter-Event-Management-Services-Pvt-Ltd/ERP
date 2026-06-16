import asyncio
import json
from uuid import UUID

import httpx
import pytest
from httpx import Response

from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount

AUTH_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
PROJECT_ID = UUID("33333333-3333-4333-8333-333333333333")
APPROVAL_ID = UUID("44444444-4444-4444-8444-444444444444")
TASK_ID = UUID("55555555-5555-4555-8555-555555555555")
PHYSICAL_FILE_ID = UUID("66666666-6666-4666-8666-666666666666")
AUDIT_EVENT_ID = UUID("77777777-7777-4777-8777-777777777777")
REQUEST_ID = UUID("88888888-8888-4888-8888-888888888888")
CALENDAR_EVENT_ID = UUID("99999999-9999-4999-8999-999999999999")
DOCUMENT_TYPE_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
CREATED_AT = "2026-06-16T09:00:00+00:00"


def _current_user(
    *,
    roles: list[str] | None = None,
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
            official_email="director@iemsnewdelhi.com",
            designation="Director",
            employment_status="ACTIVE",
        ),
        roles=roles or ["DIRECTOR"],
        permissions=permissions or [
            "project.view",
            "archive.view",
            "approval.view_all",
            "attendance.view_all",
            "audit.view",
        ],
    )


def _attendance_row(state: str) -> dict[str, object]:
    return {
        "employee_id": str(EMPLOYEE_ID),
        "employee_code": "IEMS-001",
        "full_name": "Example Employee",
        "first_check_in": CREATED_AT if state != "ABSENT_OR_NOT_CHECKED_IN" else None,
        "last_check_out": CREATED_AT if state == "CHECKED_OUT" else None,
        "total_minutes": 510 if state == "CHECKED_OUT" else 0,
        "attendance_state": state,
    }


def _project_row(status_code: str = "ACTIVE") -> dict[str, object]:
    return {
        "id": str(PROJECT_ID),
        "project_code": "IEMS-2026-001",
        "name": "Annual Leadership Conference",
        "event_date": "2026-08-12",
        "archived_at": None,
        "client": {"display_name": "Acme Events"},
        "project_status": {"code": status_code, "name": status_code.title()},
        "priority_level": {"code": "HIGH", "name": "High"},
        "project_manager": {
            "id": str(EMPLOYEE_ID),
            "employee_code": "IEMS-001",
            "full_name": "Aarav Mehta",
        },
    }


def _approval_row(status: str = "PENDING") -> dict[str, object]:
    return {
        "id": str(APPROVAL_ID),
        "approval_type": "DOCUMENT_APPROVAL",
        "status": status,
        "requested_at": CREATED_AT,
        "requested_by_name": "Nisha Rao",
        "assigned_to_name": "IEMS Director",
        "project_code": "IEMS-2026-001",
        "project_name": "Annual Leadership Conference",
    }


def _overdue_task_row() -> dict[str, object]:
    return {
        "id": str(TASK_ID),
        "title": "Close vendor reconciliation",
        "due_at": CREATED_AT,
        "project_code": "IEMS-2026-001",
        "project_name": "Annual Leadership Conference",
        "assignees": "Nisha Rao",
    }


def _physical_file_row() -> dict[str, object]:
    return {
        "id": str(PHYSICAL_FILE_ID),
        "physical_file_code": "PF-001",
        "project_code": "IEMS-2026-001",
        "project_name": "Annual Leadership Conference",
        "client_name": "Acme Events",
        "status": "CHECKED_OUT",
        "archive_room": "Main Archive",
        "archive_location_code": "R1-S1-C1-B1-F1",
        "checked_out_at": CREATED_AT,
        "expected_return_at": "2026-06-15T09:00:00+00:00",
        "checked_out_by": "Nisha Rao",
    }


def _verification_due_row() -> dict[str, object]:
    return {
        **_physical_file_row(),
        "next_verification_at": "2026-06-15T09:00:00+00:00",
        "last_verified_at": "2026-03-15T09:00:00+00:00",
    }


def _upcoming_event_row() -> dict[str, object]:
    return {
        "id": str(CALENDAR_EVENT_ID),
        "title": "Client walkthrough",
        "event_type": "SITE_VISIT",
        "starts_at": "2026-06-20T09:00:00+00:00",
        "ends_at": "2026-06-20T10:00:00+00:00",
        "project_code": "IEMS-2026-001",
        "project_name": "Annual Leadership Conference",
        "location": "India Habitat Centre",
    }


def _missing_required_document_row() -> dict[str, object]:
    return {
        "project_id": str(PROJECT_ID),
        "project_code": "IEMS-2026-001",
        "project_name": "Annual Leadership Conference",
        "document_type_id": str(DOCUMENT_TYPE_ID),
        "document_type_code": "FINAL_INVOICE",
        "document_type_name": "Final Invoice",
    }


def _audit_event_row() -> dict[str, object]:
    return {
        "id": str(AUDIT_EVENT_ID),
        "action_code": "document.downloaded",
        "resource_type": "document_version",
        "resource_id": str(PROJECT_ID),
        "actor_employee_id": str(EMPLOYEE_ID),
        "actor": {
            "id": str(EMPLOYEE_ID),
            "employee_code": "IEMS-001",
            "full_name": "Example Employee",
        },
        "request_id": str(REQUEST_ID),
        "created_at": CREATED_AT,
    }


def test_service_denies_director_dashboard_to_non_director_non_super_user() -> None:
    from app.services.director_dashboard import DirectorDashboardError, DirectorDashboardService

    service = DirectorDashboardService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(lambda request: Response(500)),
    )

    with pytest.raises(DirectorDashboardError) as exc_info:
        asyncio.run(
            service.get_overview(
                current_user=_current_user(
                    roles=["ADMIN"],
                    permissions=["audit.view", "approval.view_all"],
                ),
            )
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "PERMISSION_DENIED"


def test_service_lists_pending_approvals_from_director_view() -> None:
    from app.services.director_dashboard import DirectorDashboardService

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/director_pending_approvals_v":
            return Response(200, json=[_approval_row()])
        return Response(500)

    service = DirectorDashboardService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    rows = asyncio.run(
        service.list_approvals(
            current_user=_current_user(),
            status="PENDING",
            limit=10,
            offset=5,
        )
    )

    assert rows[0].id == APPROVAL_ID
    assert rows[0].approval_type == "DOCUMENT_APPROVAL"
    params = seen_requests[0].url.params
    assert seen_requests[0].url.path == "/rest/v1/director_pending_approvals_v"
    assert params["status"] == "eq.PENDING"
    assert params["limit"] == "10"
    assert params["offset"] == "5"


def test_service_lists_audit_events_without_sensitive_value_payloads() -> None:
    from app.services.director_dashboard import DirectorDashboardService

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/audit_events":
            return Response(200, json=[_audit_event_row()])
        return Response(500)

    service = DirectorDashboardService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    rows = asyncio.run(
        service.list_audit_events(
            current_user=_current_user(),
            limit=25,
            offset=0,
            action_code="document.downloaded",
            resource_type="document_version",
        )
    )

    assert rows[0].id == AUDIT_EVENT_ID
    assert rows[0].actor is not None
    params = seen_requests[0].url.params
    assert "old_values" not in params["select"]
    assert "new_values" not in params["select"]
    assert "metadata" not in params["select"]
    assert params["action_code"] == "eq.document.downloaded"
    assert params["resource_type"] == "eq.document_version"


def test_service_get_overview_aggregates_existing_director_views() -> None:
    from app.services.director_dashboard import DirectorDashboardService

    seen_paths: list[str] = []

    def handler(request: httpx.Request) -> Response:
        seen_paths.append(request.url.path)
        if request.url.path == "/rest/v1/director_attendance_today_v":
            return Response(
                200,
                json=[
                    _attendance_row("CHECKED_IN"),
                    _attendance_row("CHECKED_OUT"),
                    _attendance_row("ABSENT_OR_NOT_CHECKED_IN"),
                ],
            )
        if request.url.path == "/rest/v1/projects":
            return Response(200, json=[_project_row("ACTIVE"), _project_row("PLANNING")])
        if request.url.path == "/rest/v1/director_pending_approvals_v":
            return Response(200, json=[_approval_row()])
        if request.url.path == "/rest/v1/director_overdue_tasks_v":
            return Response(200, json=[_overdue_task_row()])
        if request.url.path == "/rest/v1/director_physical_file_status_v":
            return Response(200, json=[_physical_file_row()])
        if request.url.path == "/rest/v1/director_archive_verification_due_v":
            return Response(200, json=[_verification_due_row()])
        if request.url.path == "/rest/v1/audit_events":
            return Response(200, json=[_audit_event_row()])
        return Response(500)

    service = DirectorDashboardService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(service.get_overview(current_user=_current_user()))

    assert result.attendance.active_employee_count == 3
    assert result.attendance.checked_in_count == 1
    assert result.attendance.checked_out_count == 1
    assert result.projects.active_count == 1
    assert result.projects.planning_count == 1
    assert result.pending_approval_count == 1
    assert result.overdue_task_count == 1
    assert result.physical_archive.checked_out_count == 1
    assert result.physical_archive.overdue_return_count == 1
    assert result.physical_archive.verification_due_count == 1
    assert result.recent_audit_events[0].action_code == "document.downloaded"
    assert seen_paths == [
        "/rest/v1/director_attendance_today_v",
        "/rest/v1/projects",
        "/rest/v1/director_pending_approvals_v",
        "/rest/v1/director_overdue_tasks_v",
        "/rest/v1/director_physical_file_status_v",
        "/rest/v1/director_archive_verification_due_v",
        "/rest/v1/audit_events",
    ]


def test_service_lists_upcoming_events_from_director_view() -> None:
    from app.services.director_dashboard import DirectorDashboardService

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/director_upcoming_events_v":
            return Response(200, json=[_upcoming_event_row()])
        return Response(500)

    service = DirectorDashboardService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    rows = asyncio.run(
        service.list_upcoming_events(current_user=_current_user(), limit=10, offset=0)
    )

    assert rows[0].id == CALENDAR_EVENT_ID
    assert rows[0].project_code == "IEMS-2026-001"
    assert seen_requests[0].url.params["order"] == "starts_at.asc"


def test_service_lists_missing_required_documents_from_director_view() -> None:
    from app.services.director_dashboard import DirectorDashboardService

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/director_missing_required_documents_v":
            return Response(200, json=[_missing_required_document_row()])
        return Response(500)

    service = DirectorDashboardService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    rows = asyncio.run(
        service.list_missing_required_documents(
            current_user=_current_user(),
            limit=10,
            offset=0,
        )
    )

    assert rows[0].document_type_code == "FINAL_INVOICE"
    assert seen_requests[0].url.path == "/rest/v1/director_missing_required_documents_v"


def test_service_lists_archive_verification_reminders_from_director_view() -> None:
    from app.services.director_dashboard import DirectorDashboardService

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/director_archive_verification_due_v":
            return Response(200, json=[_verification_due_row()])
        return Response(500)

    service = DirectorDashboardService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    rows = asyncio.run(
        service.list_verification_reminders(current_user=_current_user(), limit=10, offset=0)
    )

    assert rows[0].physical_file_code == "PF-001"
    assert rows[0].next_verification_at is not None
    assert seen_requests[0].url.params["order"] == "next_verification_at.asc"


def test_service_maps_supabase_errors_to_data_service_error() -> None:
    from app.services.director_dashboard import DirectorDashboardError, DirectorDashboardService

    def handler(request: httpx.Request) -> Response:
        return Response(500, json={"message": "database unavailable"})

    service = DirectorDashboardService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(DirectorDashboardError) as exc_info:
        asyncio.run(
            service.list_projects(current_user=_current_user(), limit=10, offset=0)
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.code == "DATA_SERVICE_ERROR"
    assert exc_info.value.message == "database unavailable"


def test_service_uses_secret_key_without_bearer_authorization_header() -> None:
    from app.services.director_dashboard import DirectorDashboardService

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/director_overdue_tasks_v":
            return Response(200, json=[_overdue_task_row()])
        return Response(500)

    service = DirectorDashboardService(
        supabase_url="http://localhost:54321",
        service_role_key="sb" "_secret_test_secret_key_value_123456",
        transport=httpx.MockTransport(handler),
    )

    rows = asyncio.run(
        service.list_overdue_tasks(
            current_user=_current_user(is_super_user=True),
            limit=10,
            offset=0,
        )
    )

    assert rows[0].id == TASK_ID
    assert seen_requests[0].headers["apikey"] == "sb_secret_test_secret_key_value_123456"
    assert "authorization" not in seen_requests[0].headers


def test_physical_file_rows_compute_overdue_return_state() -> None:
    from app.services.director_dashboard import DirectorDashboardService

    def handler(request: httpx.Request) -> Response:
        if request.url.path == "/rest/v1/director_physical_file_status_v":
            return Response(200, json=[_physical_file_row()])
        return Response(500)

    service = DirectorDashboardService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    rows = asyncio.run(
        service.list_physical_files(current_user=_current_user(), limit=10, offset=0)
    )

    assert rows[0].is_return_overdue is True


def test_service_sends_json_content_type_for_get_requests() -> None:
    from app.services.director_dashboard import DirectorDashboardService

    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        return Response(200, json=[])

    service = DirectorDashboardService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    asyncio.run(service.list_overdue_tasks(current_user=_current_user(), limit=10, offset=0))

    assert seen_requests[0].headers["content-type"] == "application/json"


def test_audit_event_response_rejects_unexpected_sensitive_fields() -> None:
    from app.schemas.director_dashboard import DirectorAuditEventResponse

    payload = {
        **_audit_event_row(),
        "old_values": {"secret": "before"},
        "new_values": {"secret": "after"},
        "metadata": {"secret": "details"},
    }

    serialized = json.loads(DirectorAuditEventResponse.model_validate(payload).model_dump_json())

    assert "old_values" not in serialized
    assert "new_values" not in serialized
    assert "metadata" not in serialized
