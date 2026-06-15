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
PROJECT_ID = UUID("44444444-4444-4444-8444-444444444444")
FOLDER_ID = UUID("55555555-5555-4555-8555-555555555555")
DOCUMENT_ID = UUID("66666666-6666-4666-8666-666666666666")
LEAVE_TYPE_ID = UUID("77777777-7777-4777-8777-777777777777")
LEAVE_REQUEST_ID = UUID("88888888-8888-4888-8888-888888888888")
TASK_ID = UUID("99999999-9999-4999-8999-999999999999")
TASK_STATUS_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
COMPLETED_STATUS_ID = UUID("abababab-abab-4bab-8bab-abababababab")
PRIORITY_LEVEL_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
CALENDAR_EVENT_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
COMMENT_ID = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
REQUEST_ID = UUID("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")

CREATED_AT = datetime(2026, 6, 15, 9, 0, tzinfo=UTC)
DUE_AT = datetime(2026, 6, 20, 12, 0, tzinfo=UTC)
EVENT_STARTS_AT = datetime(2026, 6, 18, 10, 0, tzinfo=UTC)
EVENT_ENDS_AT = datetime(2026, 6, 18, 11, 0, tzinfo=UTC)


class RecordingEmployeeOperationsService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object, CurrentUser, AuditContext | None]] = []

    async def list_leave_types(self, *, current_user: CurrentUser) -> list[object]:
        self.calls.append(("list_leave_types", None, current_user, None))
        return [_reference_summary(LEAVE_TYPE_ID, "CASUAL", "Casual Leave")]

    async def list_task_statuses(self, *, current_user: CurrentUser) -> list[object]:
        self.calls.append(("list_task_statuses", None, current_user, None))
        return [_reference_summary(TASK_STATUS_ID, "TODO", "To Do")]

    async def create_leave_request(
        self,
        *,
        payload: object,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> object:
        self.calls.append(("create_leave_request", payload, current_user, context))
        return _leave_response(status="PENDING")

    async def list_my_leave_requests(
        self,
        *,
        current_user: CurrentUser,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[object]:
        self.calls.append(
            ("list_my_leave_requests", (status, limit, offset), current_user, None)
        )
        return [_leave_response(status="PENDING")]

    async def list_pending_leave_requests(
        self,
        *,
        current_user: CurrentUser,
        limit: int,
        offset: int,
    ) -> list[object]:
        self.calls.append(("list_pending_leave_requests", (limit, offset), current_user, None))
        return [_leave_response(status="PENDING")]

    async def approve_leave_request(
        self,
        *,
        request_id: UUID,
        review_comment: str | None,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> object:
        self.calls.append(
            (
                "approve_leave_request",
                (request_id, review_comment),
                current_user,
                context,
            )
        )
        return _leave_response(status="APPROVED", reviewed_by=EMPLOYEE_ID)

    async def reject_leave_request(
        self,
        *,
        request_id: UUID,
        review_comment: str | None,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> object:
        self.calls.append(
            ("reject_leave_request", (request_id, review_comment), current_user, context)
        )
        return _leave_response(status="REJECTED", reviewed_by=EMPLOYEE_ID)

    async def cancel_leave_request(
        self,
        *,
        request_id: UUID,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> object:
        self.calls.append(("cancel_leave_request", request_id, current_user, context))
        return _leave_response(status="CANCELLED")

    async def list_tasks(
        self,
        *,
        current_user: CurrentUser,
        project_id: UUID | None,
        assigned_to_me: bool,
        status_code: str | None,
        limit: int,
        offset: int,
    ) -> list[object]:
        self.calls.append(
            (
                "list_tasks",
                (project_id, assigned_to_me, status_code, limit, offset),
                current_user,
                None,
            )
        )
        return [_task_response()]

    async def create_task(
        self,
        *,
        payload: object,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> object:
        self.calls.append(("create_task", payload, current_user, context))
        return _task_response()

    async def get_task(self, *, task_id: UUID, current_user: CurrentUser) -> object:
        self.calls.append(("get_task", task_id, current_user, None))
        return _task_response()

    async def update_task(
        self,
        *,
        task_id: UUID,
        payload: object,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> object:
        self.calls.append(("update_task", (task_id, payload), current_user, context))
        return _task_response(completed_at=CREATED_AT)

    async def add_task_assignees(
        self,
        *,
        task_id: UUID,
        employee_ids: list[UUID],
        current_user: CurrentUser,
        context: AuditContext,
    ) -> object:
        self.calls.append(("add_task_assignees", (task_id, employee_ids), current_user, context))
        return _task_response(assignee_ids=employee_ids)

    async def add_task_comment(
        self,
        *,
        task_id: UUID,
        comment_text: str,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> object:
        self.calls.append(("add_task_comment", (task_id, comment_text), current_user, context))
        return _task_comment_response(comment_text=comment_text)

    async def link_task_document(
        self,
        *,
        task_id: UUID,
        document_id: UUID,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> object:
        self.calls.append(("link_task_document", (task_id, document_id), current_user, context))
        return _task_response(document_ids=[DOCUMENT_ID])

    async def list_calendar_events(
        self,
        *,
        current_user: CurrentUser,
        from_date: date | None,
        to_date: date | None,
        project_id: UUID | None,
    ) -> list[object]:
        self.calls.append(
            ("list_calendar_events", (from_date, to_date, project_id), current_user, None)
        )
        return [_calendar_event_response()]

    async def create_calendar_event(
        self,
        *,
        payload: object,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> object:
        self.calls.append(("create_calendar_event", payload, current_user, context))
        return _calendar_event_response()

    async def update_calendar_event(
        self,
        *,
        event_id: UUID,
        payload: object,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> object:
        self.calls.append(("update_calendar_event", (event_id, payload), current_user, context))
        return _calendar_event_response(title="Updated kickoff")


def _reference_summary(id_value: UUID, code: str, name: str) -> object:
    from app.schemas.clients_projects import ReferenceSummary

    return ReferenceSummary(id=id_value, code=code, name=name)


def _employee_summary(employee_id: UUID = EMPLOYEE_ID) -> object:
    from app.schemas.clients_projects import EmployeeSummary

    return EmployeeSummary(id=employee_id, employee_code="IEMS-001", full_name="Example Employee")


def _leave_response(*, status: str, reviewed_by: UUID | None = None) -> object:
    from app.schemas.employee_operations import LeaveRequestResponse

    return LeaveRequestResponse(
        id=LEAVE_REQUEST_ID,
        employee_id=EMPLOYEE_ID,
        employee=_employee_summary(),
        leave_type_id=LEAVE_TYPE_ID,
        leave_type=_reference_summary(LEAVE_TYPE_ID, "CASUAL", "Casual Leave"),
        start_date=date(2026, 6, 20),
        end_date=date(2026, 6, 21),
        reason="Family commitment",
        status=status,
        requested_at=CREATED_AT,
        reviewed_by=reviewed_by,
        reviewed_at=CREATED_AT if reviewed_by else None,
        review_comment="Approved",
    )


def _task_response(
    *,
    assignee_ids: list[UUID] | None = None,
    document_ids: list[UUID] | None = None,
    completed_at: datetime | None = None,
) -> object:
    from app.schemas.employee_operations import TaskResponse

    ids = assignee_ids or [EMPLOYEE_ID, OTHER_EMPLOYEE_ID]
    return TaskResponse(
        id=TASK_ID,
        project_id=PROJECT_ID,
        project=None,
        related_folder_id=FOLDER_ID,
        title="Prepare production checklist",
        description="Coordinate production readiness",
        task_status_id=COMPLETED_STATUS_ID if completed_at else TASK_STATUS_ID,
        task_status=_reference_summary(
            COMPLETED_STATUS_ID if completed_at else TASK_STATUS_ID,
            "COMPLETED" if completed_at else "TODO",
            "Completed" if completed_at else "To Do",
        ),
        priority_level_id=PRIORITY_LEVEL_ID,
        priority_level=_reference_summary(PRIORITY_LEVEL_ID, "HIGH", "High"),
        created_by=EMPLOYEE_ID,
        due_at=DUE_AT,
        completed_at=completed_at,
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
        assignees=[_employee_summary(employee_id) for employee_id in ids],
        document_ids=document_ids or [],
    )


def _task_comment_response(*, comment_text: str) -> object:
    from app.schemas.employee_operations import TaskCommentResponse

    return TaskCommentResponse(
        id=COMMENT_ID,
        task_id=TASK_ID,
        employee_id=EMPLOYEE_ID,
        employee=_employee_summary(),
        comment_text=comment_text,
        created_at=CREATED_AT,
        edited_at=None,
    )


def _calendar_event_response(*, title: str = "Project kickoff") -> object:
    from app.schemas.employee_operations import CalendarEventResponse

    return CalendarEventResponse(
        id=CALENDAR_EVENT_ID,
        event_type="MEETING",
        title=title,
        description="Kickoff meeting",
        starts_at=EVENT_STARTS_AT,
        ends_at=EVENT_ENDS_AT,
        location="Conference Room",
        project_id=PROJECT_ID,
        related_task_id=None,
        created_by=EMPLOYEE_ID,
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
        source="CALENDAR_EVENT",
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
    service: RecordingEmployeeOperationsService | None = None,
) -> RecordingEmployeeOperationsService:
    from app.api.dependencies import get_employee_operations_service

    installed_service = service or RecordingEmployeeOperationsService()

    async def override_current_user() -> CurrentUser:
        return current_user

    async def override_employee_operations_service() -> RecordingEmployeeOperationsService:
        return installed_service

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_employee_operations_service] = (
        override_employee_operations_service
    )
    return installed_service


def test_create_leave_request_returns_pending_request() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                "/v1/leave-requests",
                json={
                    "leave_type_id": str(LEAVE_TYPE_ID),
                    "start_date": "2026-06-20",
                    "end_date": "2026-06-21",
                    "reason": "Family commitment",
                },
                headers={"Authorization": "Bearer test-token", "X-Request-ID": str(REQUEST_ID)},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["status"] == "PENDING"
    assert service.calls[0][0] == "create_leave_request"
    assert service.calls[0][3] == AuditContext(
        request_id=REQUEST_ID,
        ip_address="127.0.0.1",
        user_agent="python-httpx/0.28.1",
    )


def test_approve_leave_request_requires_leave_review_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                f"/v1/leave-requests/{LEAVE_REQUEST_ID}/approve",
                json={"review_comment": "Approved"},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert service.calls == []


def test_approve_leave_request_records_review() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["leave.review"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                f"/v1/leave-requests/{LEAVE_REQUEST_ID}/approve",
                json={"review_comment": "Approved"},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"
    assert service.calls[0][0] == "approve_leave_request"
    assert service.calls[0][1] == (LEAVE_REQUEST_ID, "Approved")


def test_cancel_leave_request_is_available_to_request_owner() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                f"/v1/leave-requests/{LEAVE_REQUEST_ID}/cancel",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"
    assert service.calls[0][0] == "cancel_leave_request"


def test_create_task_requires_task_manage_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                "/v1/tasks",
                json={
                    "project_id": str(PROJECT_ID),
                    "related_folder_id": str(FOLDER_ID),
                    "title": "Prepare production checklist",
                    "priority_level_id": str(PRIORITY_LEVEL_ID),
                    "assignee_ids": [str(EMPLOYEE_ID), str(OTHER_EMPLOYEE_ID)],
                },
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert service.calls == []


def test_create_task_accepts_assignees_and_document_links() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["task.manage"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                "/v1/tasks",
                json={
                    "project_id": str(PROJECT_ID),
                    "related_folder_id": str(FOLDER_ID),
                    "title": "Prepare production checklist",
                    "description": "Coordinate production readiness",
                    "priority_level_id": str(PRIORITY_LEVEL_ID),
                    "due_at": DUE_AT.isoformat(),
                    "assignee_ids": [str(EMPLOYEE_ID), str(OTHER_EMPLOYEE_ID)],
                    "document_ids": [str(DOCUMENT_ID)],
                },
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["assignees"][1]["id"] == str(OTHER_EMPLOYEE_ID)
    assert service.calls[0][0] == "create_task"


def test_patch_task_can_mark_task_complete() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["task.manage"]))
    try:
        response = asyncio.run(
            _request(
                "PATCH",
                f"/v1/tasks/{TASK_ID}",
                json={"task_status_id": str(COMPLETED_STATUS_ID)},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["completed_at"] == CREATED_AT.isoformat().replace("+00:00", "Z")
    assert service.calls[0][0] == "update_task"


def test_add_task_comment_uses_visible_task_authorization_in_service() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                f"/v1/tasks/{TASK_ID}/comments",
                json={"comment_text": "Confirmed with vendor."},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["comment_text"] == "Confirmed with vendor."
    assert service.calls[0][0] == "add_task_comment"


def test_list_calendar_events_passes_date_and_project_filters() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                f"/v1/calendar/events?from_date=2026-06-01&to_date=2026-06-30&project_id={PROJECT_ID}",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["source"] == "CALENDAR_EVENT"
    assert service.calls[0][1] == (date(2026, 6, 1), date(2026, 6, 30), PROJECT_ID)


def test_create_calendar_event_requires_task_manage_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                "/v1/calendar/events",
                json={
                    "event_type": "MEETING",
                    "title": "Project kickoff",
                    "starts_at": EVENT_STARTS_AT.isoformat(),
                    "ends_at": EVENT_ENDS_AT.isoformat(),
                    "project_id": str(PROJECT_ID),
                },
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert service.calls == []


def test_create_calendar_event_records_project_link() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["task.manage"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                "/v1/calendar/events",
                json={
                    "event_type": "MEETING",
                    "title": "Project kickoff",
                    "starts_at": EVENT_STARTS_AT.isoformat(),
                    "ends_at": EVENT_ENDS_AT.isoformat(),
                    "location": "Conference Room",
                    "project_id": str(PROJECT_ID),
                    "attendee_ids": [str(EMPLOYEE_ID), str(OTHER_EMPLOYEE_ID)],
                },
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["project_id"] == str(PROJECT_ID)
    assert service.calls[0][0] == "create_calendar_event"
