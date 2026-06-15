from datetime import UTC, date, datetime, time, timedelta
from typing import Any
from uuid import UUID

import httpx
from pydantic import ValidationError

from app.core.audit import AuditContext
from app.schemas.attendance import (
    AttendanceCorrectionUpdate,
    AttendanceSessionResponse,
    DirectorAttendanceSummaryResponse,
)
from app.schemas.current_user import CurrentUser

ATTENDANCE_SELECT = (
    "id,employee_id,checked_in_at,checked_out_at,source,remarks,created_by,corrected_by,"
    "correction_reason,created_at,updated_at,"
    "employee:employees!attendance_sessions_employee_id_fkey(id,employee_code,full_name)"
)
DIRECTOR_ATTENDANCE_SELECT = (
    "employee_id,employee_code,full_name,first_check_in,last_check_out,total_minutes,"
    "attendance_state"
)


class AttendanceError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class AttendanceService:
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

    async def check_in(
        self,
        *,
        remarks: str | None,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> AttendanceSessionResponse:
        row = await self._rpc(
            "check_in_attendance_audited",
            {
                "p_employee_id": str(current_user.employee.id),
                "p_remarks": remarks,
                **_actor_context_payload(current_user, context),
            },
        )
        return _attendance_from_row(row)

    async def check_out(
        self,
        *,
        remarks: str | None,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> AttendanceSessionResponse:
        row = await self._rpc(
            "check_out_attendance_audited",
            {
                "p_employee_id": str(current_user.employee.id),
                "p_remarks": remarks,
                **_actor_context_payload(current_user, context),
            },
        )
        return _attendance_from_row(row)

    async def list_my_attendance(
        self,
        *,
        current_user: CurrentUser,
        from_date: date | None,
        to_date: date | None,
        limit: int,
        offset: int,
    ) -> list[AttendanceSessionResponse]:
        params = _attendance_list_params(
            limit=limit,
            offset=offset,
            from_date=from_date,
            to_date=to_date,
        )
        params["employee_id"] = f"eq.{current_user.employee.id}"
        rows = await self._get_rows("/rest/v1/attendance_sessions", params=params)
        return [_attendance_from_row(row) for row in rows]

    async def list_team_attendance(
        self,
        *,
        current_user: CurrentUser,
        employee_id: UUID | None,
        from_date: date | None,
        to_date: date | None,
        limit: int,
        offset: int,
    ) -> list[AttendanceSessionResponse]:
        self._require_permission(current_user, "attendance.view_all")
        params = _attendance_list_params(
            limit=limit,
            offset=offset,
            from_date=from_date,
            to_date=to_date,
        )
        if employee_id is not None:
            params["employee_id"] = f"eq.{employee_id}"
        rows = await self._get_rows("/rest/v1/attendance_sessions", params=params)
        return [_attendance_from_row(row) for row in rows]

    async def correct_session(
        self,
        *,
        session_id: UUID,
        payload: AttendanceCorrectionUpdate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> AttendanceSessionResponse:
        self._require_permission(current_user, "attendance.correct")
        row = await self._rpc(
            "correct_attendance_session_audited",
            {
                "p_session_id": str(session_id),
                "p_patch": _correction_patch(payload),
                "p_correction_reason": payload.correction_reason,
                **_actor_context_payload(current_user, context),
            },
        )
        return _attendance_from_row(row)

    async def list_director_attendance(
        self,
        *,
        current_user: CurrentUser,
    ) -> list[DirectorAttendanceSummaryResponse]:
        self._require_permission(current_user, "attendance.view_all")
        rows = await self._get_rows(
            "/rest/v1/director_attendance_today_v",
            params={
                "select": DIRECTOR_ATTENDANCE_SELECT,
                "order": "full_name.asc",
            },
        )
        return [_director_attendance_from_row(row) for row in rows]

    def _require_permission(self, current_user: CurrentUser, permission_code: str) -> None:
        if current_user.account.is_super_user:
            return
        if permission_code not in current_user.permissions:
            raise AttendanceError(403, "PERMISSION_DENIED", "Permission denied")

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
        async with httpx.AsyncClient(
            timeout=self._timeout_seconds,
            transport=self._transport,
        ) as client:
            response = await client.request(
                method,
                f"{self._supabase_url}{path}",
                headers=self._supabase_headers(),
                params=params,
                json=json_body,
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


def _attendance_list_params(
    *,
    limit: int,
    offset: int,
    from_date: date | None,
    to_date: date | None,
) -> dict[str, str]:
    params = {
        "select": ATTENDANCE_SELECT,
        "order": "checked_in_at.desc",
        "limit": str(limit),
        "offset": str(offset),
    }
    lower = _start_of_day(from_date) if from_date is not None else None
    upper = _start_of_day(to_date + timedelta(days=1)) if to_date is not None else None
    if lower is not None and upper is not None:
        params["and"] = f"(checked_in_at.gte.{lower},checked_in_at.lt.{upper})"
    elif lower is not None:
        params["checked_in_at"] = f"gte.{lower}"
    elif upper is not None:
        params["checked_in_at"] = f"lt.{upper}"
    return params


def _actor_context_payload(current_user: CurrentUser, context: AuditContext) -> dict[str, object]:
    return {
        "p_actor_user_account_id": str(current_user.auth_user_id),
        "p_actor_employee_id": str(current_user.employee.id),
        "p_request_id": _uuid_or_none(context.request_id),
        "p_ip_address": context.ip_address,
        "p_user_agent": context.user_agent,
    }


def _correction_patch(payload: AttendanceCorrectionUpdate) -> dict[str, object]:
    patch: dict[str, object] = {}
    if "checked_in_at" in payload.model_fields_set:
        patch["checked_in_at"] = _datetime_or_none(payload.checked_in_at)
    if "checked_out_at" in payload.model_fields_set:
        patch["checked_out_at"] = _datetime_or_none(payload.checked_out_at)
    if "remarks" in payload.model_fields_set:
        patch["remarks"] = payload.remarks
    return patch


def _attendance_from_row(row: dict[str, Any]) -> AttendanceSessionResponse:
    normalized = dict(row)
    normalized["total_minutes"] = _total_minutes(normalized)
    try:
        return AttendanceSessionResponse.model_validate(normalized)
    except ValidationError as exc:
        raise AttendanceError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Attendance data service returned invalid data",
        ) from exc


def _director_attendance_from_row(row: dict[str, Any]) -> DirectorAttendanceSummaryResponse:
    try:
        return DirectorAttendanceSummaryResponse.model_validate(row)
    except ValidationError as exc:
        raise AttendanceError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Director attendance data service returned invalid data",
        ) from exc


def _total_minutes(row: dict[str, Any]) -> int | None:
    checked_in_at = _parse_datetime(row.get("checked_in_at"))
    checked_out_at = _parse_datetime(row.get("checked_out_at"))
    if checked_in_at is None or checked_out_at is None:
        return None
    return int((checked_out_at - checked_in_at).total_seconds() // 60)


def _json_list(response: httpx.Response) -> list[dict[str, Any]]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise AttendanceError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid JSON",
        ) from exc
    if not isinstance(payload, list):
        raise AttendanceError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid payload",
        )
    for item in payload:
        if not isinstance(item, dict):
            raise AttendanceError(
                503,
                "DATA_SERVICE_INVALID_RESPONSE",
                "Data service returned invalid payload",
            )
    return payload


def _json_object(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise AttendanceError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid JSON",
        ) from exc
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        return payload[0]
    raise AttendanceError(
        503,
        "DATA_SERVICE_INVALID_RESPONSE",
        "Data service returned invalid payload",
    )


def _raise_supabase_error(response: httpx.Response) -> None:
    payload = _error_payload(response)
    pg_code = _optional_str(payload.get("code"))
    message = _optional_str(payload.get("message")) or "Supabase data service request failed"

    if message == "IEMS_ATTENDANCE_SESSION_ALREADY_OPEN":
        raise AttendanceError(
            409,
            "RESOURCE_CONFLICT",
            "Employee already has an open attendance session",
        )
    if message == "IEMS_ATTENDANCE_OPEN_SESSION_NOT_FOUND":
        raise AttendanceError(
            422,
            "INVALID_STATE",
            "Employee has no open attendance session",
        )
    if message == "IEMS_ATTENDANCE_SESSION_NOT_FOUND":
        raise AttendanceError(404, "NOT_FOUND", "Attendance session not found")
    if message == "IEMS_ATTENDANCE_CORRECTION_REASON_REQUIRED":
        raise AttendanceError(422, "VALIDATION_ERROR", "Correction reason is required")
    if pg_code == "23505":
        raise AttendanceError(409, "RESOURCE_CONFLICT", "Resource already exists")
    if pg_code == "23503":
        raise AttendanceError(422, "INVALID_REFERENCE", "Referenced resource is invalid")
    if pg_code == "23514":
        raise AttendanceError(422, "INVALID_STATE", "Resource violates a constraint")
    if response.status_code == 404:
        raise AttendanceError(404, "NOT_FOUND", "Resource not found")

    raise AttendanceError(503, "DATA_SERVICE_ERROR", message)


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


def _optional_str(value: object) -> str | None:
    if isinstance(value, str):
        return value
    return None
