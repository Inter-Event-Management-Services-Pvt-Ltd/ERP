from typing import Any
from uuid import UUID

import httpx
from pydantic import ValidationError

from app.core.audit import AuditContext
from app.schemas.approvals import (
    ApprovalRequestCreate,
    ApprovalRequestResponse,
)
from app.schemas.clients_projects import ReferenceSummary
from app.schemas.current_user import CurrentUser

REFERENCE_SELECT = "id,code,name"
PROJECT_MEMBER_SELECT = "project_id,employee_id,access_level,removed_at"
APPROVAL_SELECT = (
    "id,approval_type_id,project_id,document_version_id,archive_export_id,leave_request_id,"
    "requested_by,assigned_to,status,requested_at,completed_at,"
    "approval_type:approval_types(id,code,name),"
    "requested_by_employee:employees!approval_requests_requested_by_fkey"
    "(id,employee_code,full_name),"
    "assigned_to_employee:employees!approval_requests_assigned_to_fkey"
    "(id,employee_code,full_name),"
    "actions:approval_actions("
    "id,approval_request_id,action,performed_by,comment,created_at,"
    "performed_by_employee:employees!approval_actions_performed_by_fkey"
    "(id,employee_code,full_name)"
    ")"
)


class ApprovalsError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class ApprovalsService:
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

    async def list_approval_types(self, *, current_user: CurrentUser) -> list[ReferenceSummary]:
        _ensure_active_user(current_user)
        rows = await self._get_rows(
            "/rest/v1/approval_types",
            params={
                "select": REFERENCE_SELECT,
                "is_active": "eq.true",
                "order": "name.asc",
            },
        )
        return [_reference_from_row(row) for row in rows]

    async def list_approvals(
        self,
        *,
        current_user: CurrentUser,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[ApprovalRequestResponse]:
        _ensure_active_user(current_user)
        params = _list_params(limit=limit, offset=offset)
        if status is not None:
            params["status"] = f"eq.{status}"
        if not _has_permission(current_user, "approval.view_all"):
            params["or"] = (
                f"(requested_by.eq.{current_user.employee.id},"
                f"assigned_to.eq.{current_user.employee.id})"
            )
        rows = await self._get_rows("/rest/v1/approval_requests", params=params)
        return [_approval_from_row(row) for row in rows]

    async def create_approval(
        self,
        *,
        payload: ApprovalRequestCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ApprovalRequestResponse:
        _ensure_active_user(current_user)
        await self._authorize_create(payload=payload, current_user=current_user)
        row = await self._rpc(
            "create_approval_request_audited",
            {
                "p_approval_type_id": str(payload.approval_type_id),
                "p_project_id": _uuid_or_none(payload.project_id),
                "p_document_version_id": _uuid_or_none(payload.document_version_id),
                "p_archive_export_id": _uuid_or_none(payload.archive_export_id),
                "p_leave_request_id": _uuid_or_none(payload.leave_request_id),
                "p_requested_by": str(current_user.employee.id),
                "p_assigned_to": _uuid_or_none(payload.assigned_to),
                "p_comment": payload.comment,
                **_actor_context_payload(current_user, context),
            },
        )
        return _approval_from_row(row)

    async def get_approval(
        self,
        *,
        approval_id: UUID,
        current_user: CurrentUser,
    ) -> ApprovalRequestResponse:
        _ensure_active_user(current_user)
        params = _list_params(limit=1, offset=0)
        params["id"] = f"eq.{approval_id}"
        if not _has_permission(current_user, "approval.view_all"):
            params["or"] = (
                f"(requested_by.eq.{current_user.employee.id},"
                f"assigned_to.eq.{current_user.employee.id})"
            )
        rows = await self._get_rows("/rest/v1/approval_requests", params=params)
        if not rows:
            raise ApprovalsError(404, "NOT_FOUND", "Approval request not found")
        return _approval_from_row(rows[0])

    async def approve_approval(
        self,
        *,
        approval_id: UUID,
        comment: str | None,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ApprovalRequestResponse:
        return await self._review_approval(
            approval_id=approval_id,
            action="APPROVED",
            comment=comment,
            current_user=current_user,
            context=context,
        )

    async def reject_approval(
        self,
        *,
        approval_id: UUID,
        comment: str | None,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ApprovalRequestResponse:
        return await self._review_approval(
            approval_id=approval_id,
            action="REJECTED",
            comment=comment,
            current_user=current_user,
            context=context,
        )

    async def request_revision(
        self,
        *,
        approval_id: UUID,
        comment: str,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ApprovalRequestResponse:
        return await self._review_approval(
            approval_id=approval_id,
            action="REVISION_REQUESTED",
            comment=comment,
            current_user=current_user,
            context=context,
        )

    async def _review_approval(
        self,
        *,
        approval_id: UUID,
        action: str,
        comment: str | None,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ApprovalRequestResponse:
        _ensure_active_user(current_user)
        _require_permission(current_user, "approval.approve")
        row = await self._rpc(
            "review_approval_request_audited",
            {
                "p_approval_request_id": str(approval_id),
                "p_action": action,
                "p_comment": comment,
                **_actor_context_payload(current_user, context),
            },
        )
        return _approval_from_row(row)

    async def _authorize_create(
        self,
        *,
        payload: ApprovalRequestCreate,
        current_user: CurrentUser,
    ) -> None:
        if current_user.account.is_super_user:
            return
        if payload.project_id is not None:
            _require_permission(current_user, "project.manage")
            await self._require_project_access(
                project_id=payload.project_id,
                current_user=current_user,
                allowed_levels={"MANAGE"},
                message="Project approval request access denied",
            )
            return
        if payload.document_version_id is not None:
            _require_permission(current_user, "document.upload")
            project_id = await self._project_id_for_document_version(payload.document_version_id)
            await self._require_project_access(
                project_id=project_id,
                current_user=current_user,
                allowed_levels={"CONTRIBUTE", "MANAGE"},
                message="Document approval request access denied",
            )
            return
        if payload.archive_export_id is not None:
            _require_permission(current_user, "archive.export")
            project_id = await self._project_id_for_archive_export(payload.archive_export_id)
            await self._require_project_access(
                project_id=project_id,
                current_user=current_user,
                allowed_levels={"MANAGE"},
                message="Archive approval request access denied",
            )
            return
        if payload.leave_request_id is not None:
            employee_id = await self._employee_id_for_leave_request(payload.leave_request_id)
            if employee_id != current_user.employee.id:
                _require_permission(current_user, "leave.review")

    async def _project_id_for_document_version(self, version_id: UUID) -> UUID:
        rows = await self._get_rows(
            "/rest/v1/document_versions",
            params={
                "select": "id,document:documents(project_id)",
                "id": f"eq.{version_id}",
                "limit": "1",
            },
        )
        if not rows:
            raise ApprovalsError(404, "NOT_FOUND", "Document version not found")
        document = rows[0].get("document")
        if not isinstance(document, dict) or document.get("project_id") is None:
            raise ApprovalsError(
                503,
                "DATA_SERVICE_INVALID_RESPONSE",
                "Document version data service returned invalid data",
            )
        return UUID(str(document["project_id"]))

    async def _project_id_for_archive_export(self, archive_export_id: UUID) -> UUID:
        rows = await self._get_rows(
            "/rest/v1/archive_exports",
            params={"select": "project_id", "id": f"eq.{archive_export_id}", "limit": "1"},
        )
        if not rows:
            raise ApprovalsError(404, "NOT_FOUND", "Archive export not found")
        return UUID(str(rows[0]["project_id"]))

    async def _employee_id_for_leave_request(self, leave_request_id: UUID) -> UUID:
        rows = await self._get_rows(
            "/rest/v1/leave_requests",
            params={"select": "employee_id", "id": f"eq.{leave_request_id}", "limit": "1"},
        )
        if not rows:
            raise ApprovalsError(404, "NOT_FOUND", "Leave request not found")
        return UUID(str(rows[0]["employee_id"]))

    async def _require_project_access(
        self,
        *,
        project_id: UUID,
        current_user: CurrentUser,
        allowed_levels: set[str],
        message: str,
    ) -> None:
        if current_user.account.is_super_user:
            return
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
        if not rows or str(rows[0].get("access_level")) not in allowed_levels:
            raise ApprovalsError(403, "ABAC_DENIED", message)

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


def _ensure_active_user(current_user: CurrentUser) -> None:
    if not current_user.account.is_active:
        raise ApprovalsError(403, "PERMISSION_DENIED", "Permission denied")


def _require_permission(current_user: CurrentUser, permission_code: str) -> None:
    if not _has_permission(current_user, permission_code):
        raise ApprovalsError(403, "PERMISSION_DENIED", "Permission denied")


def _has_permission(current_user: CurrentUser, permission_code: str) -> bool:
    return current_user.account.is_super_user or permission_code in current_user.permissions


def _list_params(*, limit: int, offset: int) -> dict[str, str]:
    return {
        "select": APPROVAL_SELECT,
        "order": "requested_at.desc",
        "limit": str(limit),
        "offset": str(offset),
    }


def _actor_context_payload(current_user: CurrentUser, context: AuditContext) -> dict[str, object]:
    return {
        "p_actor_user_account_id": str(current_user.auth_user_id),
        "p_actor_employee_id": str(current_user.employee.id),
        "p_request_id": _uuid_or_none(context.request_id),
        "p_ip_address": context.ip_address,
        "p_user_agent": context.user_agent,
    }


def _reference_from_row(row: dict[str, Any]) -> ReferenceSummary:
    try:
        return ReferenceSummary.model_validate(row)
    except ValidationError as exc:
        raise ApprovalsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Reference data service returned invalid data",
        ) from exc


def _approval_from_row(row: dict[str, Any]) -> ApprovalRequestResponse:
    normalized = dict(row)
    actions = normalized.get("actions")
    if not isinstance(actions, list):
        normalized["actions"] = []
    try:
        return ApprovalRequestResponse.model_validate(normalized)
    except ValidationError as exc:
        raise ApprovalsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Approval data service returned invalid data",
        ) from exc


def _json_list(response: httpx.Response) -> list[dict[str, Any]]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise ApprovalsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid JSON",
        ) from exc
    if not isinstance(payload, list):
        raise ApprovalsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid payload",
        )
    for item in payload:
        if not isinstance(item, dict):
            raise ApprovalsError(
                503,
                "DATA_SERVICE_INVALID_RESPONSE",
                "Data service returned invalid payload",
            )
    return payload


def _json_object(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise ApprovalsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid JSON",
        ) from exc
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        return payload[0]
    raise ApprovalsError(
        503,
        "DATA_SERVICE_INVALID_RESPONSE",
        "Data service returned invalid payload",
    )


def _raise_supabase_error(response: httpx.Response) -> None:
    payload = _error_payload(response)
    pg_code = _optional_str(payload.get("code"))
    message = _optional_str(payload.get("message")) or "Supabase data service request failed"

    if message in {
        "IEMS_APPROVAL_REQUEST_NOT_FOUND",
        "IEMS_DOCUMENT_VERSION_NOT_FOUND",
        "IEMS_ARCHIVE_EXPORT_NOT_FOUND",
        "IEMS_LEAVE_REQUEST_NOT_FOUND",
    }:
        raise ApprovalsError(404, "NOT_FOUND", "Resource not found")
    if message in {
        "IEMS_APPROVAL_NOT_PENDING",
        "IEMS_APPROVAL_REVIEW_ACTION_INVALID",
        "IEMS_APPROVAL_REVISION_COMMENT_REQUIRED",
    }:
        raise ApprovalsError(422, "INVALID_STATE", "Approval request is not in a valid state")
    if pg_code == "23505":
        raise ApprovalsError(409, "RESOURCE_CONFLICT", "Resource already exists")
    if pg_code == "23503":
        raise ApprovalsError(422, "INVALID_REFERENCE", "Referenced resource is invalid")
    if pg_code == "23514":
        raise ApprovalsError(422, "INVALID_STATE", "Resource violates a constraint")
    if response.status_code == 404:
        raise ApprovalsError(404, "NOT_FOUND", "Resource not found")

    raise ApprovalsError(503, "DATA_SERVICE_ERROR", message)


def _error_payload(response: httpx.Response) -> dict[str, object]:
    try:
        payload = response.json()
    except ValueError:
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _uuid_or_none(value: UUID | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_str(value: object) -> str | None:
    if isinstance(value, str):
        return value
    return None
