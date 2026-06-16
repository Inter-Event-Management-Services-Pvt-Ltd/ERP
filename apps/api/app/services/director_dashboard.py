from datetime import UTC, datetime
from typing import Any

import httpx
from pydantic import ValidationError

from app.schemas.current_user import CurrentUser
from app.schemas.director_dashboard import (
    DirectorApprovalSummaryResponse,
    DirectorArchiveMetrics,
    DirectorAttendanceMetrics,
    DirectorAuditEventResponse,
    DirectorOverdueTaskResponse,
    DirectorOverviewResponse,
    DirectorPhysicalFileSummaryResponse,
    DirectorProjectMetrics,
    DirectorProjectSummaryResponse,
)

ATTENDANCE_SELECT = (
    "employee_id,employee_code,full_name,first_check_in,last_check_out,total_minutes,"
    "attendance_state"
)
PROJECT_SELECT = (
    "id,project_code,name,event_date,archived_at,"
    "client:clients(display_name),"
    "project_status:project_statuses(code,name),"
    "priority_level:priority_levels(code,name),"
    "project_manager:employees!projects_project_manager_id_fkey(id,employee_code,full_name)"
)
APPROVAL_SELECT = (
    "id,approval_type,status,requested_at,requested_by_name,assigned_to_name,"
    "project_code,project_name"
)
OVERDUE_TASK_SELECT = "id,title,due_at,project_code,project_name,assignees"
PHYSICAL_FILE_SELECT = (
    "id,physical_file_code,project_code,project_name,client_name,status,archive_room,"
    "archive_location_code,checked_out_at,expected_return_at,checked_out_by"
)
AUDIT_EVENT_SELECT = (
    "id,action_code,resource_type,resource_id,actor_employee_id,request_id,created_at,"
    "actor:employees!audit_events_actor_employee_id_fkey(id,employee_code,full_name)"
)


class DirectorDashboardError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class DirectorDashboardService:
    def __init__(
        self,
        *,
        supabase_url: str,
        service_role_key: str,
        timeout_seconds: float = 5.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._supabase_url = supabase_url.rstrip("/")
        self._service_role_key = service_role_key
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    async def get_overview(self, *, current_user: CurrentUser) -> DirectorOverviewResponse:
        _ensure_director_access(current_user)
        attendance_rows = await self._list_attendance_rows()
        projects = await self.list_projects(current_user=current_user, limit=500, offset=0)
        approvals = await self.list_approvals(
            current_user=current_user,
            status="PENDING",
            limit=100,
            offset=0,
        )
        overdue_tasks = await self.list_overdue_tasks(
            current_user=current_user,
            limit=100,
            offset=0,
        )
        physical_files = await self.list_physical_files(
            current_user=current_user,
            limit=500,
            offset=0,
        )
        audit_events = await self.list_audit_events(
            current_user=current_user,
            limit=10,
            offset=0,
            action_code=None,
            resource_type=None,
        )
        return DirectorOverviewResponse(
            generated_at=datetime.now(UTC),
            attendance=_attendance_metrics(attendance_rows),
            projects=_project_metrics(projects),
            pending_approval_count=len(approvals),
            overdue_task_count=len(overdue_tasks),
            physical_archive=_archive_metrics(physical_files),
            recent_audit_events=audit_events,
        )

    async def list_projects(
        self,
        *,
        current_user: CurrentUser,
        limit: int,
        offset: int,
    ) -> list[DirectorProjectSummaryResponse]:
        _ensure_director_access(current_user)
        rows = await self._get_rows(
            "/rest/v1/projects",
            params={
                "select": PROJECT_SELECT,
                "deleted_at": "is.null",
                "order": "updated_at.desc",
                "limit": str(limit),
                "offset": str(offset),
            },
        )
        return [_project_from_row(row) for row in rows]

    async def list_approvals(
        self,
        *,
        current_user: CurrentUser,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[DirectorApprovalSummaryResponse]:
        _ensure_director_access(current_user)
        params = {
            "select": APPROVAL_SELECT,
            "order": "requested_at.asc",
            "limit": str(limit),
            "offset": str(offset),
        }
        if status is not None:
            params["status"] = f"eq.{status}"
        rows = await self._get_rows("/rest/v1/director_pending_approvals_v", params=params)
        return [_approval_from_row(row) for row in rows]

    async def list_overdue_tasks(
        self,
        *,
        current_user: CurrentUser,
        limit: int,
        offset: int,
    ) -> list[DirectorOverdueTaskResponse]:
        _ensure_director_access(current_user)
        rows = await self._get_rows(
            "/rest/v1/director_overdue_tasks_v",
            params={
                "select": OVERDUE_TASK_SELECT,
                "order": "due_at.asc",
                "limit": str(limit),
                "offset": str(offset),
            },
        )
        return [_overdue_task_from_row(row) for row in rows]

    async def list_physical_files(
        self,
        *,
        current_user: CurrentUser,
        limit: int,
        offset: int,
    ) -> list[DirectorPhysicalFileSummaryResponse]:
        _ensure_director_access(current_user)
        rows = await self._get_rows(
            "/rest/v1/director_physical_file_status_v",
            params={
                "select": PHYSICAL_FILE_SELECT,
                "order": "expected_return_at.asc.nullslast",
                "limit": str(limit),
                "offset": str(offset),
            },
        )
        return [_physical_file_from_row(row) for row in rows]

    async def list_audit_events(
        self,
        *,
        current_user: CurrentUser,
        limit: int,
        offset: int,
        action_code: str | None,
        resource_type: str | None,
    ) -> list[DirectorAuditEventResponse]:
        _ensure_director_access(current_user)
        params = {
            "select": AUDIT_EVENT_SELECT,
            "order": "created_at.desc",
            "limit": str(limit),
            "offset": str(offset),
        }
        if action_code is not None:
            params["action_code"] = f"eq.{action_code}"
        if resource_type is not None:
            params["resource_type"] = f"eq.{resource_type}"
        rows = await self._get_rows("/rest/v1/audit_events", params=params)
        return [_audit_event_from_row(row) for row in rows]

    async def _list_attendance_rows(self) -> list[dict[str, Any]]:
        return await self._get_rows(
            "/rest/v1/director_attendance_today_v",
            params={"select": ATTENDANCE_SELECT, "order": "full_name.asc"},
        )

    async def _get_rows(self, path: str, *, params: dict[str, str]) -> list[dict[str, Any]]:
        response = await self._request("GET", path, params=params)
        return _json_list(response)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        async with httpx.AsyncClient(
            timeout=self._timeout_seconds,
            transport=self._transport,
        ) as client:
            response = await client.request(
                method,
                f"{self._supabase_url}{path}",
                headers=self._supabase_headers(),
                params=params,
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


def _ensure_director_access(current_user: CurrentUser) -> None:
    if current_user.account.is_super_user:
        return
    if "DIRECTOR" in current_user.roles:
        return
    raise DirectorDashboardError(403, "PERMISSION_DENIED", "Permission denied")


def _attendance_metrics(rows: list[dict[str, Any]]) -> DirectorAttendanceMetrics:
    checked_in_count = 0
    checked_out_count = 0
    absent_count = 0
    total_minutes = 0
    for row in rows:
        state = str(row.get("attendance_state") or "")
        if state == "CHECKED_IN":
            checked_in_count += 1
        elif state == "CHECKED_OUT":
            checked_out_count += 1
        elif state == "ABSENT_OR_NOT_CHECKED_IN":
            absent_count += 1
        total_minutes += _int_or_zero(row.get("total_minutes"))
    return DirectorAttendanceMetrics(
        active_employee_count=len(rows),
        checked_in_count=checked_in_count,
        checked_out_count=checked_out_count,
        absent_or_not_checked_in_count=absent_count,
        total_minutes_today=total_minutes,
    )


def _project_metrics(projects: list[DirectorProjectSummaryResponse]) -> DirectorProjectMetrics:
    return DirectorProjectMetrics(
        active_count=sum(1 for project in projects if project.project_status == "ACTIVE"),
        planning_count=sum(1 for project in projects if project.project_status == "PLANNING"),
        completed_count=sum(1 for project in projects if project.project_status == "COMPLETED"),
        archived_count=sum(
            1
            for project in projects
            if project.project_status == "ARCHIVED" or project.archived_at is not None
        ),
    )


def _archive_metrics(
    physical_files: list[DirectorPhysicalFileSummaryResponse],
) -> DirectorArchiveMetrics:
    return DirectorArchiveMetrics(
        checked_out_count=sum(1 for item in physical_files if item.status == "CHECKED_OUT"),
        overdue_return_count=sum(1 for item in physical_files if item.is_return_overdue),
        verification_due_count=0,
        missing_count=sum(1 for item in physical_files if item.status == "MISSING"),
    )


def _project_from_row(row: dict[str, Any]) -> DirectorProjectSummaryResponse:
    normalized = {
        "id": row.get("id"),
        "project_code": row.get("project_code"),
        "name": row.get("name"),
        "client_name": _nested_str(row, "client", "display_name"),
        "project_status": _nested_str(row, "project_status", "code"),
        "priority_level": _nested_str(row, "priority_level", "code"),
        "event_date": row.get("event_date"),
        "project_manager_name": _nested_str(row, "project_manager", "full_name"),
        "archived_at": row.get("archived_at"),
    }
    try:
        return DirectorProjectSummaryResponse.model_validate(normalized)
    except ValidationError as exc:
        raise DirectorDashboardError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Project dashboard data service returned invalid data",
        ) from exc


def _approval_from_row(row: dict[str, Any]) -> DirectorApprovalSummaryResponse:
    try:
        return DirectorApprovalSummaryResponse.model_validate(row)
    except ValidationError as exc:
        raise DirectorDashboardError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Approval dashboard data service returned invalid data",
        ) from exc


def _overdue_task_from_row(row: dict[str, Any]) -> DirectorOverdueTaskResponse:
    try:
        return DirectorOverdueTaskResponse.model_validate(row)
    except ValidationError as exc:
        raise DirectorDashboardError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Overdue task dashboard data service returned invalid data",
        ) from exc


def _physical_file_from_row(row: dict[str, Any]) -> DirectorPhysicalFileSummaryResponse:
    normalized = dict(row)
    normalized["is_return_overdue"] = _is_return_overdue(row)
    try:
        return DirectorPhysicalFileSummaryResponse.model_validate(normalized)
    except ValidationError as exc:
        raise DirectorDashboardError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Physical archive dashboard data service returned invalid data",
        ) from exc


def _audit_event_from_row(row: dict[str, Any]) -> DirectorAuditEventResponse:
    try:
        return DirectorAuditEventResponse.model_validate(row)
    except ValidationError as exc:
        raise DirectorDashboardError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Audit dashboard data service returned invalid data",
        ) from exc


def _is_return_overdue(row: dict[str, Any]) -> bool:
    expected_return_at = _parse_datetime(row.get("expected_return_at"))
    return expected_return_at is not None and expected_return_at < datetime.now(UTC)


def _nested_str(row: dict[str, Any], object_key: str, value_key: str) -> str | None:
    nested = row.get(object_key)
    value = nested.get(value_key) if isinstance(nested, dict) else None
    if isinstance(value, str):
        return value
    return None


def _json_list(response: httpx.Response) -> list[dict[str, Any]]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise DirectorDashboardError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid JSON",
        ) from exc
    if not isinstance(payload, list):
        raise DirectorDashboardError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid payload",
        )
    for item in payload:
        if not isinstance(item, dict):
            raise DirectorDashboardError(
                503,
                "DATA_SERVICE_INVALID_RESPONSE",
                "Data service returned invalid payload",
            )
    return payload


def _raise_supabase_error(response: httpx.Response) -> None:
    payload = _error_payload(response)
    message = _optional_str(payload.get("message")) or "Supabase data service request failed"
    if response.status_code == 404:
        raise DirectorDashboardError(404, "NOT_FOUND", "Resource not found")
    raise DirectorDashboardError(503, "DATA_SERVICE_ERROR", message)


def _error_payload(response: httpx.Response) -> dict[str, object]:
    try:
        payload = response.json()
    except ValueError:
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _optional_str(value: object) -> str | None:
    if isinstance(value, str):
        return value
    return None


def _int_or_zero(value: object) -> int:
    if isinstance(value, int):
        return value
    return 0


def _parse_datetime(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return None
