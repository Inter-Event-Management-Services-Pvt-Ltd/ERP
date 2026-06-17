from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from uuid import UUID

import httpx
from pydantic import ValidationError

from app.core.audit import AuditContext
from app.core.supabase_http import request_supabase
from app.schemas.clients_projects import ReferenceSummary
from app.schemas.current_user import CurrentUser
from app.schemas.employee_operations import (
    CalendarEventCreate,
    CalendarEventResponse,
    CalendarEventSource,
    CalendarEventType,
    CalendarEventUpdate,
    LeaveRequestCreate,
    LeaveRequestResponse,
    TaskCommentResponse,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)

REFERENCE_SELECT = "id,code,name"
PROJECT_MEMBER_SELECT = "project_id,employee_id,access_level,removed_at"
LEAVE_SELECT = (
    "id,employee_id,leave_type_id,start_date,end_date,reason,status,requested_at,"
    "reviewed_by,reviewed_at,review_comment,"
    "employee:employees!leave_requests_employee_id_fkey(id,employee_code,full_name),"
    "leave_type:leave_types(id,code,name)"
)
TASK_SELECT = (
    "id,project_id,related_folder_id,title,description,task_status_id,priority_level_id,"
    "created_by,due_at,completed_at,created_at,updated_at,"
    "project:projects(id,project_code,name),"
    "task_status:task_statuses(id,code,name),"
    "priority_level:priority_levels(id,code,name),"
    "assignees:task_assignees(employee:employees!task_assignees_employee_id_fkey"
    "(id,employee_code,full_name)),"
    "documents:task_document_links(document_id)"
)
TASK_COMMENT_SELECT = (
    "id,task_id,employee_id,comment_text,created_at,edited_at,"
    "employee:employees!task_comments_employee_id_fkey(id,employee_code,full_name)"
)
CALENDAR_EVENT_SELECT = (
    "id,project_id,related_task_id,event_type,title,description,starts_at,ends_at,location,"
    "created_by,created_at,updated_at"
)
PHYSICAL_FILE_CHECKOUT_SELECT = (
    "id,physical_file_id,checked_out_by,expected_return_at,returned_at,"
    "physical_file:physical_files(id,physical_file_code,project_id)"
)


class EmployeeOperationsError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class EmployeeOperationsService:
    def __init__(
        self,
        *,
        supabase_url: str,
        service_role_key: str,
        timeout_seconds: float = 5.0,
        transport: httpx.AsyncBaseTransport | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._supabase_url = supabase_url.rstrip("/")
        self._service_role_key = service_role_key
        self._timeout_seconds = timeout_seconds
        self._transport = transport
        self._http_client = http_client

    async def list_leave_types(self, *, current_user: CurrentUser) -> list[ReferenceSummary]:
        _ensure_active_user(current_user)
        rows = await self._get_rows(
            "/rest/v1/leave_types",
            params={"select": REFERENCE_SELECT, "order": "name.asc"},
        )
        return [_reference_from_row(row) for row in rows]

    async def list_task_statuses(self, *, current_user: CurrentUser) -> list[ReferenceSummary]:
        _ensure_active_user(current_user)
        rows = await self._get_rows(
            "/rest/v1/task_statuses",
            params={"select": REFERENCE_SELECT, "order": "name.asc"},
        )
        return [_reference_from_row(row) for row in rows]

    async def create_leave_request(
        self,
        *,
        payload: LeaveRequestCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> LeaveRequestResponse:
        _ensure_active_user(current_user)
        row = await self._rpc(
            "create_leave_request_audited",
            {
                "p_employee_id": str(current_user.employee.id),
                "p_leave_type_id": str(payload.leave_type_id),
                "p_start_date": payload.start_date.isoformat(),
                "p_end_date": payload.end_date.isoformat(),
                "p_reason": payload.reason,
                **_actor_context_payload(current_user, context),
            },
        )
        return _leave_from_row(row)

    async def list_my_leave_requests(
        self,
        *,
        current_user: CurrentUser,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[LeaveRequestResponse]:
        _ensure_active_user(current_user)
        params = _list_params(
            select=LEAVE_SELECT,
            order="requested_at.desc",
            limit=limit,
            offset=offset,
        )
        params["employee_id"] = f"eq.{current_user.employee.id}"
        if status is not None:
            params["status"] = f"eq.{status}"
        rows = await self._get_rows("/rest/v1/leave_requests", params=params)
        return [_leave_from_row(row) for row in rows]

    async def list_pending_leave_requests(
        self,
        *,
        current_user: CurrentUser,
        limit: int,
        offset: int,
    ) -> list[LeaveRequestResponse]:
        self._require_permission(current_user, "leave.review")
        params = _list_params(
            select=LEAVE_SELECT,
            order="requested_at.asc",
            limit=limit,
            offset=offset,
        )
        params["status"] = "eq.PENDING"
        rows = await self._get_rows("/rest/v1/leave_requests", params=params)
        return [_leave_from_row(row) for row in rows]

    async def approve_leave_request(
        self,
        *,
        request_id: UUID,
        review_comment: str | None,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> LeaveRequestResponse:
        self._require_permission(current_user, "leave.review")
        return await self._review_leave_request(
            request_id=request_id,
            status="APPROVED",
            review_comment=review_comment,
            current_user=current_user,
            context=context,
        )

    async def reject_leave_request(
        self,
        *,
        request_id: UUID,
        review_comment: str | None,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> LeaveRequestResponse:
        self._require_permission(current_user, "leave.review")
        return await self._review_leave_request(
            request_id=request_id,
            status="REJECTED",
            review_comment=review_comment,
            current_user=current_user,
            context=context,
        )

    async def cancel_leave_request(
        self,
        *,
        request_id: UUID,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> LeaveRequestResponse:
        _ensure_active_user(current_user)
        row = await self._rpc(
            "cancel_leave_request_audited",
            {
                "p_leave_request_id": str(request_id),
                **_actor_context_payload(current_user, context),
            },
        )
        return _leave_from_row(row)

    async def list_tasks(
        self,
        *,
        current_user: CurrentUser,
        project_id: UUID | None,
        assigned_to_me: bool,
        status_code: str | None,
        limit: int,
        offset: int,
    ) -> list[TaskResponse]:
        _ensure_active_user(current_user)
        params = _list_params(
            select=TASK_SELECT,
            order="due_at.asc.nullslast",
            limit=limit,
            offset=offset,
        )
        if status_code is not None:
            task_status_id = await self._task_status_id_for_code(status_code)
            params["task_status_id"] = f"eq.{task_status_id}"

        if project_id is not None:
            params["project_id"] = f"eq.{project_id}"

        if self._has_permission(current_user, "task.manage"):
            rows = await self._get_rows("/rest/v1/tasks", params=params)
            return [_task_from_row(row) for row in rows]

        if project_id is not None and not assigned_to_me:
            if await self._has_project_access(
                project_id=project_id,
                current_user=current_user,
                allowed_levels=None,
            ):
                rows = await self._get_rows("/rest/v1/tasks", params=params)
                return [_task_from_row(row) for row in rows]

        if assigned_to_me:
            task_ids = await self._assigned_task_ids(current_user)
            if not task_ids:
                return []
            params["id"] = _in_filter(task_ids)
            rows = await self._get_rows("/rest/v1/tasks", params=params)
            return [_task_from_row(row) for row in rows]

        visible_task_ids = await self._assigned_task_ids(current_user)
        project_ids = await self._accessible_project_ids(current_user)
        if project_id is not None and project_id not in project_ids:
            project_ids = []
        elif project_id is not None:
            project_ids = [project_id]

        visible_filters: list[str] = []
        if visible_task_ids:
            visible_filters.append(f"id.in.({_csv_uuids(visible_task_ids)})")
        if project_ids:
            visible_filters.append(f"project_id.in.({_csv_uuids(project_ids)})")
        if not visible_filters:
            return []
        params["or"] = f"({','.join(visible_filters)})"
        rows = await self._get_rows("/rest/v1/tasks", params=params)
        return [_task_from_row(row) for row in rows]

    async def create_task(
        self,
        *,
        payload: TaskCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> TaskResponse:
        self._require_permission(current_user, "task.manage")
        if payload.project_id is not None:
            await self._require_project_access(
                project_id=payload.project_id,
                current_user=current_user,
                allowed_levels={"MANAGE"},
            )
        row = await self._rpc(
            "create_task_audited",
            {
                "p_project_id": _uuid_or_none(payload.project_id),
                "p_related_folder_id": _uuid_or_none(payload.related_folder_id),
                "p_title": payload.title,
                "p_description": payload.description,
                "p_task_status_id": _uuid_or_none(payload.task_status_id),
                "p_priority_level_id": str(payload.priority_level_id),
                "p_due_at": _datetime_or_none(payload.due_at),
                "p_assignee_ids": [str(value) for value in payload.assignee_ids],
                "p_document_ids": [str(value) for value in payload.document_ids],
                **_actor_context_payload(current_user, context),
            },
        )
        return _task_from_row(row)

    async def get_task(self, *, task_id: UUID, current_user: CurrentUser) -> TaskResponse:
        row = await self._get_task_row(task_id)
        await self._require_task_visible(row=row, current_user=current_user)
        return _task_from_row(row)

    async def update_task(
        self,
        *,
        task_id: UUID,
        payload: TaskUpdate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> TaskResponse:
        self._require_permission(current_user, "task.manage")
        row = await self._get_task_row(task_id)
        await self._require_task_manage(row=row, current_user=current_user)
        if payload.project_id is not None:
            await self._require_project_access(
                project_id=payload.project_id,
                current_user=current_user,
                allowed_levels={"MANAGE"},
            )
        result = await self._rpc(
            "update_task_audited",
            {
                "p_task_id": str(task_id),
                "p_patch": _task_update_patch(payload),
                **_actor_context_payload(current_user, context),
            },
        )
        return _task_from_row(result)

    async def add_task_assignees(
        self,
        *,
        task_id: UUID,
        employee_ids: list[UUID],
        current_user: CurrentUser,
        context: AuditContext,
    ) -> TaskResponse:
        self._require_permission(current_user, "task.manage")
        row = await self._get_task_row(task_id)
        await self._require_task_manage(row=row, current_user=current_user)
        result = await self._rpc(
            "assign_task_assignees_audited",
            {
                "p_task_id": str(task_id),
                "p_employee_ids": [str(value) for value in employee_ids],
                **_actor_context_payload(current_user, context),
            },
        )
        return _task_from_row(result)

    async def add_task_comment(
        self,
        *,
        task_id: UUID,
        comment_text: str,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> TaskCommentResponse:
        row = await self._get_task_row(task_id)
        await self._require_task_visible(row=row, current_user=current_user)
        result = await self._rpc(
            "add_task_comment_audited",
            {
                "p_task_id": str(task_id),
                "p_comment_text": comment_text,
                **_actor_context_payload(current_user, context),
            },
        )
        return _task_comment_from_row(result)

    async def list_task_comments(
        self,
        *,
        task_id: UUID,
        current_user: CurrentUser,
        limit: int,
        offset: int,
    ) -> list[TaskCommentResponse]:
        row = await self._get_task_row(task_id)
        await self._require_task_visible(row=row, current_user=current_user)
        params = _list_params(
            select=TASK_COMMENT_SELECT,
            order="created_at.desc",
            limit=limit,
            offset=offset,
        )
        params["task_id"] = f"eq.{task_id}"
        rows = await self._get_rows("/rest/v1/task_comments", params=params)
        return [_task_comment_from_row(comment_row) for comment_row in rows]

    async def link_task_document(
        self,
        *,
        task_id: UUID,
        document_id: UUID,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> TaskResponse:
        self._require_permission(current_user, "task.manage")
        row = await self._get_task_row(task_id)
        await self._require_task_manage(row=row, current_user=current_user)
        result = await self._rpc(
            "link_task_document_audited",
            {
                "p_task_id": str(task_id),
                "p_document_id": str(document_id),
                **_actor_context_payload(current_user, context),
            },
        )
        return _task_from_row(result)

    async def list_calendar_events(
        self,
        *,
        current_user: CurrentUser,
        from_date: date | None,
        to_date: date | None,
        project_id: UUID | None,
    ) -> list[CalendarEventResponse]:
        _ensure_active_user(current_user)
        if project_id is not None:
            await self._require_project_access(
                project_id=project_id,
                current_user=current_user,
                allowed_levels=None,
            )

        events = await self._list_stored_calendar_events(
            current_user=current_user,
            from_date=from_date,
            to_date=to_date,
            project_id=project_id,
        )
        task_deadlines = await self._list_task_deadline_events(
            current_user=current_user,
            from_date=from_date,
            to_date=to_date,
            project_id=project_id,
        )
        leave_events = await self._list_leave_calendar_events(
            current_user=current_user,
            from_date=from_date,
            to_date=to_date,
        )
        file_returns = await self._list_physical_return_events(
            current_user=current_user,
            from_date=from_date,
            to_date=to_date,
            project_id=project_id,
        )
        return [*events, *task_deadlines, *leave_events, *file_returns]

    async def create_calendar_event(
        self,
        *,
        payload: CalendarEventCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> CalendarEventResponse:
        self._require_permission(current_user, "task.manage")
        if payload.project_id is not None:
            await self._require_project_access(
                project_id=payload.project_id,
                current_user=current_user,
                allowed_levels={"MANAGE"},
            )
        result = await self._rpc(
            "create_calendar_event_audited",
            {
                "p_project_id": _uuid_or_none(payload.project_id),
                "p_related_task_id": _uuid_or_none(payload.related_task_id),
                "p_event_type": payload.event_type.value,
                "p_title": payload.title,
                "p_description": payload.description,
                "p_starts_at": payload.starts_at.isoformat(),
                "p_ends_at": _datetime_or_none(payload.ends_at),
                "p_location": payload.location,
                "p_attendee_ids": [str(value) for value in payload.attendee_ids],
                **_actor_context_payload(current_user, context),
            },
        )
        return _calendar_event_from_row(result)

    async def update_calendar_event(
        self,
        *,
        event_id: UUID,
        payload: CalendarEventUpdate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> CalendarEventResponse:
        self._require_permission(current_user, "task.manage")
        event = await self._get_calendar_event_row(event_id)
        event_project_id = _optional_uuid(event.get("project_id"))
        if event_project_id is not None:
            await self._require_project_access(
                project_id=event_project_id,
                current_user=current_user,
                allowed_levels={"MANAGE"},
            )
        result = await self._rpc(
            "update_calendar_event_audited",
            {
                "p_event_id": str(event_id),
                "p_patch": payload.model_dump(mode="json", exclude_unset=True),
                **_actor_context_payload(current_user, context),
            },
        )
        return _calendar_event_from_row(result)

    async def _review_leave_request(
        self,
        *,
        request_id: UUID,
        status: str,
        review_comment: str | None,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> LeaveRequestResponse:
        row = await self._rpc(
            "review_leave_request_audited",
            {
                "p_leave_request_id": str(request_id),
                "p_status": status,
                "p_review_comment": review_comment,
                **_actor_context_payload(current_user, context),
            },
        )
        return _leave_from_row(row)

    async def _get_task_row(self, task_id: UUID) -> dict[str, Any]:
        rows = await self._get_rows(
            "/rest/v1/tasks",
            params={"select": TASK_SELECT, "id": f"eq.{task_id}", "limit": "1"},
        )
        if not rows:
            raise EmployeeOperationsError(404, "NOT_FOUND", "Task not found")
        return rows[0]

    async def _get_calendar_event_row(self, event_id: UUID) -> dict[str, Any]:
        rows = await self._get_rows(
            "/rest/v1/calendar_events",
            params={"select": CALENDAR_EVENT_SELECT, "id": f"eq.{event_id}", "limit": "1"},
        )
        if not rows:
            raise EmployeeOperationsError(404, "NOT_FOUND", "Calendar event not found")
        return rows[0]

    async def _require_task_visible(
        self,
        *,
        row: dict[str, Any],
        current_user: CurrentUser,
    ) -> None:
        if self._has_permission(current_user, "task.manage"):
            return
        if current_user.employee.id in _task_assignee_ids(row):
            return
        project_id = _optional_uuid(row.get("project_id"))
        if project_id is not None and await self._has_project_access(
            project_id=project_id,
            current_user=current_user,
            allowed_levels=None,
        ):
            return
        raise EmployeeOperationsError(403, "ABAC_DENIED", "Task access denied")

    async def _require_task_manage(self, *, row: dict[str, Any], current_user: CurrentUser) -> None:
        if current_user.account.is_super_user:
            return
        project_id = _optional_uuid(row.get("project_id"))
        if project_id is None:
            return
        await self._require_project_access(
            project_id=project_id,
            current_user=current_user,
            allowed_levels={"MANAGE"},
        )

    async def _list_stored_calendar_events(
        self,
        *,
        current_user: CurrentUser,
        from_date: date | None,
        to_date: date | None,
        project_id: UUID | None,
    ) -> list[CalendarEventResponse]:
        params = _calendar_params(
            select=CALENDAR_EVENT_SELECT,
            order="starts_at.asc",
            from_date=from_date,
            to_date=to_date,
        )
        if project_id is not None:
            params["project_id"] = f"eq.{project_id}"
        elif not self._has_permission(current_user, "task.manage"):
            project_ids = await self._accessible_project_ids(current_user)
            if project_ids:
                params["or"] = f"(project_id.is.null,project_id.in.({_csv_uuids(project_ids)}))"
            else:
                params["project_id"] = "is.null"
        rows = await self._get_rows("/rest/v1/calendar_events", params=params)
        return [_calendar_event_from_row(row) for row in rows]

    async def _list_task_deadline_events(
        self,
        *,
        current_user: CurrentUser,
        from_date: date | None,
        to_date: date | None,
        project_id: UUID | None,
    ) -> list[CalendarEventResponse]:
        rows = await self.list_tasks(
            current_user=current_user,
            project_id=project_id,
            assigned_to_me=False,
            status_code=None,
            limit=100,
            offset=0,
        )
        return [
            _task_deadline_event(task)
            for task in rows
            if task.due_at is not None and _datetime_in_date_range(task.due_at, from_date, to_date)
        ]

    async def _list_leave_calendar_events(
        self,
        *,
        current_user: CurrentUser,
        from_date: date | None,
        to_date: date | None,
    ) -> list[CalendarEventResponse]:
        params = _list_params(select=LEAVE_SELECT, order="start_date.asc", limit=100, offset=0)
        params["status"] = "eq.APPROVED"
        if not self._has_permission(current_user, "leave.review"):
            params["employee_id"] = f"eq.{current_user.employee.id}"
        if from_date is not None:
            params["end_date"] = f"gte.{from_date.isoformat()}"
        if to_date is not None:
            params["start_date"] = f"lte.{to_date.isoformat()}"
        rows = await self._get_rows("/rest/v1/leave_requests", params=params)
        return [_leave_calendar_event(_leave_from_row(row)) for row in rows]

    async def _list_physical_return_events(
        self,
        *,
        current_user: CurrentUser,
        from_date: date | None,
        to_date: date | None,
        project_id: UUID | None,
    ) -> list[CalendarEventResponse]:
        params = _calendar_params(
            select=PHYSICAL_FILE_CHECKOUT_SELECT,
            order="expected_return_at.asc",
            from_date=from_date,
            to_date=to_date,
            column="expected_return_at",
        )
        params["returned_at"] = "is.null"
        if not self._has_permission(current_user, "archive.view"):
            params["checked_out_by"] = f"eq.{current_user.employee.id}"
        rows = await self._get_rows("/rest/v1/physical_file_checkouts", params=params)
        events: list[CalendarEventResponse] = []
        for row in rows:
            event = _physical_return_event(row)
            if project_id is not None and event.project_id != project_id:
                continue
            if event.project_id is not None and not self._has_permission(
                current_user,
                "archive.view",
            ):
                if not await self._has_project_access(
                    project_id=event.project_id,
                    current_user=current_user,
                    allowed_levels=None,
                ):
                    continue
            events.append(event)
        return events

    async def _assigned_task_ids(self, current_user: CurrentUser) -> list[UUID]:
        rows = await self._get_rows(
            "/rest/v1/task_assignees",
            params={
                "select": "task_id",
                "employee_id": f"eq.{current_user.employee.id}",
                "limit": "1000",
            },
        )
        return [UUID(str(row["task_id"])) for row in rows]

    async def _accessible_project_ids(self, current_user: CurrentUser) -> list[UUID]:
        rows = await self._get_rows(
            "/rest/v1/project_members",
            params={
                "select": "project_id,access_level",
                "employee_id": f"eq.{current_user.employee.id}",
                "removed_at": "is.null",
                "limit": "1000",
            },
        )
        return [UUID(str(row["project_id"])) for row in rows]

    async def _task_status_id_for_code(self, status_code: str) -> UUID:
        rows = await self._get_rows(
            "/rest/v1/task_statuses",
            params={"select": "id", "code": f"eq.{status_code}", "limit": "1"},
        )
        if not rows:
            raise EmployeeOperationsError(422, "INVALID_REFERENCE", "Task status is invalid")
        return UUID(str(rows[0]["id"]))

    async def _require_project_access(
        self,
        *,
        project_id: UUID,
        current_user: CurrentUser,
        allowed_levels: set[str] | None,
    ) -> None:
        if current_user.account.is_super_user:
            return
        if not await self._has_project_access(
            project_id=project_id,
            current_user=current_user,
            allowed_levels=allowed_levels,
        ):
            raise EmployeeOperationsError(403, "ABAC_DENIED", "Project access denied")

    async def _has_project_access(
        self,
        *,
        project_id: UUID,
        current_user: CurrentUser,
        allowed_levels: set[str] | None,
    ) -> bool:
        if current_user.account.is_super_user:
            return True
        rows = await self._get_rows(
            "/rest/v1/project_members",
            params={
                "select": PROJECT_MEMBER_SELECT,
                "project_id": f"eq.{project_id}",
                "employee_id": f"eq.{current_user.employee.id}",
                "removed_at": "is.null",
                "limit": "1",
            },
        )
        if not rows:
            return False
        return allowed_levels is None or str(rows[0].get("access_level")) in allowed_levels

    def _has_permission(self, current_user: CurrentUser, permission_code: str) -> bool:
        return current_user.account.is_super_user or permission_code in current_user.permissions

    def _require_permission(self, current_user: CurrentUser, permission_code: str) -> None:
        if not self._has_permission(current_user, permission_code):
            raise EmployeeOperationsError(403, "PERMISSION_DENIED", "Permission denied")

    async def _get_rows(self, path: str, *, params: dict[str, str]) -> list[dict[str, Any]]:
        response = await self._request("GET", path, params=params)
        return _json_list(response)

    async def _rpc(self, function_name: str, payload: dict[str, object]) -> dict[str, Any]:
        response = await self._request(
            "POST",
            f"/rest/v1/rpc/{function_name}",
            json_body=payload,
        )
        return _json_object(response)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json_body: dict[str, object] | None = None,
    ) -> httpx.Response:
        url = f"{self._supabase_url}{path}"
        if self._http_client is not None:
            response = await request_supabase(
                self._http_client,
                method,
                url,
                headers=self._supabase_headers(),
                params=params,
                json_body=json_body,
            )
        else:
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds,
                transport=self._transport,
            ) as client:
                response = await request_supabase(
                    client,
                    method,
                    url,
                    headers=self._supabase_headers(),
                    params=params,
                    json_body=json_body,
                )
        if response.status_code >= 300:
            _raise_supabase_error(response)
        return response

    def _supabase_headers(self) -> dict[str, str]:
        headers = {
            "apikey": self._service_role_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if not self._service_role_key.startswith("sb_secret_"):
            headers["Authorization"] = f"Bearer {self._service_role_key}"
        return headers


def _ensure_active_user(current_user: CurrentUser) -> None:
    if not current_user.account.is_active:
        raise EmployeeOperationsError(403, "PERMISSION_DENIED", "Permission denied")


def _actor_context_payload(current_user: CurrentUser, context: AuditContext) -> dict[str, object]:
    return {
        "p_actor_user_account_id": str(current_user.auth_user_id),
        "p_actor_employee_id": str(current_user.employee.id),
        "p_request_id": _uuid_or_none(context.request_id),
        "p_ip_address": context.ip_address,
        "p_user_agent": context.user_agent,
    }


def _list_params(*, select: str, order: str, limit: int, offset: int) -> dict[str, str]:
    return {
        "select": select,
        "order": order,
        "limit": str(limit),
        "offset": str(offset),
    }


def _calendar_params(
    *,
    select: str,
    order: str,
    from_date: date | None,
    to_date: date | None,
    column: str = "starts_at",
) -> dict[str, str]:
    params = {"select": select, "order": order, "limit": "500"}
    lower = _start_of_day(from_date) if from_date is not None else None
    upper = _start_of_day(to_date + timedelta(days=1)) if to_date is not None else None
    if lower is not None:
        params[column] = f"gte.{lower}"
    if upper is not None:
        if column in params:
            params["and"] = f"({column}.gte.{lower},{column}.lt.{upper})"
            del params[column]
        else:
            params[column] = f"lt.{upper}"
    return params


def _task_update_patch(payload: TaskUpdate) -> dict[str, object]:
    return payload.model_dump(mode="json", exclude_unset=True)


def _reference_from_row(row: dict[str, Any]) -> ReferenceSummary:
    try:
        return ReferenceSummary.model_validate(row)
    except ValidationError as exc:
        raise EmployeeOperationsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Reference data service returned invalid data",
        ) from exc


def _leave_from_row(row: dict[str, Any]) -> LeaveRequestResponse:
    try:
        return LeaveRequestResponse.model_validate(row)
    except ValidationError as exc:
        raise EmployeeOperationsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Leave data service returned invalid data",
        ) from exc


def _task_from_row(row: dict[str, Any]) -> TaskResponse:
    normalized = dict(row)
    normalized["assignees"] = _task_assignees(row)
    normalized["document_ids"] = _task_document_ids(row)
    try:
        return TaskResponse.model_validate(normalized)
    except ValidationError as exc:
        raise EmployeeOperationsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Task data service returned invalid data",
        ) from exc


def _task_comment_from_row(row: dict[str, Any]) -> TaskCommentResponse:
    try:
        return TaskCommentResponse.model_validate(row)
    except ValidationError as exc:
        raise EmployeeOperationsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Task comment data service returned invalid data",
        ) from exc


def _calendar_event_from_row(
    row: dict[str, Any],
    *,
    source: str = "CALENDAR_EVENT",
) -> CalendarEventResponse:
    normalized = dict(row)
    normalized["source"] = source
    try:
        return CalendarEventResponse.model_validate(normalized)
    except ValidationError as exc:
        raise EmployeeOperationsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Calendar data service returned invalid data",
        ) from exc


def _task_deadline_event(task: TaskResponse) -> CalendarEventResponse:
    if task.due_at is None:
        raise EmployeeOperationsError(503, "DATA_SERVICE_INVALID_RESPONSE", "Task due_at missing")
    return CalendarEventResponse(
        id=task.id,
        event_type=CalendarEventType.DEADLINE,
        title=f"Task due: {task.title}",
        description=task.description,
        starts_at=task.due_at,
        ends_at=None,
        location=None,
        project_id=task.project_id,
        related_task_id=task.id,
        created_by=task.created_by,
        created_at=task.created_at,
        updated_at=task.updated_at,
        source=CalendarEventSource.TASK_DEADLINE,
    )


def _leave_calendar_event(leave: LeaveRequestResponse) -> CalendarEventResponse:
    employee_name = leave.employee.full_name if leave.employee is not None else "Employee"
    starts_at = datetime.combine(leave.start_date, time.min, tzinfo=UTC)
    ends_at = datetime.combine(leave.end_date + timedelta(days=1), time.min, tzinfo=UTC)
    return CalendarEventResponse(
        id=leave.id,
        event_type=CalendarEventType.LEAVE,
        title=f"Leave: {employee_name}",
        description=leave.reason,
        starts_at=starts_at,
        ends_at=ends_at,
        location=None,
        project_id=None,
        related_task_id=None,
        created_by=leave.employee_id,
        created_at=leave.requested_at,
        updated_at=leave.reviewed_at or leave.requested_at,
        source=CalendarEventSource.LEAVE,
    )


def _physical_return_event(row: dict[str, Any]) -> CalendarEventResponse:
    raw_physical_file = row.get("physical_file")
    physical_file: dict[str, Any] = raw_physical_file if isinstance(raw_physical_file, dict) else {}
    expected_return_at = _parse_datetime(row.get("expected_return_at"))
    if expected_return_at is None:
        raise EmployeeOperationsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Physical checkout expected_return_at missing",
        )
    physical_file_code = str(physical_file.get("physical_file_code") or "Physical file")
    return CalendarEventResponse(
        id=UUID(str(row["id"])),
        event_type=CalendarEventType.PHYSICAL_FILE_RETURN,
        title=f"Physical file return: {physical_file_code}",
        description=None,
        starts_at=expected_return_at,
        ends_at=None,
        location=None,
        project_id=_optional_uuid(physical_file.get("project_id")),
        related_task_id=None,
        created_by=_optional_uuid(row.get("checked_out_by")),
        created_at=None,
        updated_at=None,
        source=CalendarEventSource.PHYSICAL_FILE_RETURN,
    )


def _task_assignees(row: dict[str, Any]) -> list[dict[str, Any]]:
    assignees = row.get("assignees")
    if not isinstance(assignees, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in assignees:
        if not isinstance(item, dict):
            continue
        employee = item.get("employee")
        if isinstance(employee, dict):
            normalized.append(employee)
    return normalized


def _task_assignee_ids(row: dict[str, Any]) -> set[UUID]:
    return {UUID(str(employee["id"])) for employee in _task_assignees(row) if "id" in employee}


def _task_document_ids(row: dict[str, Any]) -> list[UUID]:
    documents = row.get("documents")
    if not isinstance(documents, list):
        return []
    ids: list[UUID] = []
    for item in documents:
        if isinstance(item, dict) and item.get("document_id") is not None:
            ids.append(UUID(str(item["document_id"])))
    return ids


def _json_list(response: httpx.Response) -> list[dict[str, Any]]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise EmployeeOperationsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid JSON",
        ) from exc
    if not isinstance(payload, list):
        raise EmployeeOperationsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid payload",
        )
    for item in payload:
        if not isinstance(item, dict):
            raise EmployeeOperationsError(
                503,
                "DATA_SERVICE_INVALID_RESPONSE",
                "Data service returned invalid payload",
            )
    return payload


def _json_object(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise EmployeeOperationsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid JSON",
        ) from exc
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        return payload[0]
    raise EmployeeOperationsError(
        503,
        "DATA_SERVICE_INVALID_RESPONSE",
        "Data service returned invalid payload",
    )


def _raise_supabase_error(response: httpx.Response) -> None:
    payload = _error_payload(response)
    pg_code = _optional_str(payload.get("code"))
    message = _optional_str(payload.get("message")) or "Supabase data service request failed"

    if message in {
        "IEMS_LEAVE_REQUEST_NOT_FOUND",
        "IEMS_TASK_NOT_FOUND",
        "IEMS_CALENDAR_EVENT_NOT_FOUND",
    }:
        raise EmployeeOperationsError(404, "NOT_FOUND", "Resource not found")
    if message in {"IEMS_LEAVE_REQUEST_NOT_PENDING", "IEMS_LEAVE_REQUEST_NOT_OWN"}:
        raise EmployeeOperationsError(422, "INVALID_STATE", "Resource is not in a valid state")
    if pg_code == "23505":
        raise EmployeeOperationsError(409, "RESOURCE_CONFLICT", "Resource already exists")
    if pg_code == "23503":
        raise EmployeeOperationsError(422, "INVALID_REFERENCE", "Referenced resource is invalid")
    if pg_code == "23514":
        raise EmployeeOperationsError(422, "INVALID_STATE", "Resource violates a constraint")
    if response.status_code == 404:
        raise EmployeeOperationsError(404, "NOT_FOUND", "Resource not found")

    raise EmployeeOperationsError(503, "DATA_SERVICE_ERROR", message)


def _error_payload(response: httpx.Response) -> dict[str, object]:
    try:
        payload = response.json()
    except ValueError:
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _start_of_day(value: date) -> str:
    return datetime.combine(value, time.min, tzinfo=UTC).isoformat()


def _datetime_in_date_range(value: datetime, from_date: date | None, to_date: date | None) -> bool:
    value_date = value.astimezone(UTC).date()
    if from_date is not None and value_date < from_date:
        return False
    if to_date is not None and value_date > to_date:
        return False
    return True


def _parse_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return None


def _datetime_or_none(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _uuid_or_none(value: UUID | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_uuid(value: object) -> UUID | None:
    if value is None:
        return None
    return UUID(str(value))


def _optional_str(value: object) -> str | None:
    if isinstance(value, str):
        return value
    return None


def _csv_uuids(values: list[UUID]) -> str:
    return ",".join(str(value) for value in values)


def _in_filter(values: list[UUID]) -> str:
    return f"in.({_csv_uuids(values)})"
