from datetime import date, datetime
from typing import Any
from uuid import UUID

import httpx
from pydantic import ValidationError

from app.core.audit import AuditContext
from app.schemas.admin import (
    AuditEventExplorerResponse,
    DepartmentAssignmentCreate,
    DepartmentAssignmentResponse,
    EmployeeAdminCreate,
    EmployeeAdminResponse,
    EmployeeAdminUpdate,
    FolderTemplateCreate,
    FolderTemplateItemCreate,
    FolderTemplateItemResponse,
    FolderTemplateItemUpdate,
    FolderTemplateResponse,
    FolderTemplateUpdate,
    PolicyCreate,
    PolicyResponse,
    PolicyUpdate,
    RoleAssignmentCreate,
    RoleAssignmentResponse,
    RoleResponse,
)
from app.schemas.clients_projects import ReferenceSummary
from app.schemas.current_user import CurrentUser

DEPARTMENT_SELECT = "id,code,name"
ROLE_SELECT = "id,code,name,description"
EMPLOYEE_ADMIN_SELECT = (
    "id,employee_code,full_name,official_email,phone,designation,employment_status,"
    "joined_on,left_on,created_at,updated_at,"
    "department_assignments:employee_department_assignments("
    "id,employee_id,valid_from,valid_to,assigned_by,department:departments(id,code,name)"
    "),"
    "account:user_accounts(id,is_active,is_super_user,"
    "role_assignments:user_role_assignments("
    "assigned_at,expires_at,role:roles(id,code,name,description)"
    "))"
)
POLICY_SELECT = (
    "id,name,action_code,effect,priority,conditions,is_active,created_by,created_at,updated_at"
)
FOLDER_TEMPLATE_SELECT = (
    "id,name,project_type_id,is_active,created_by,created_at,"
    "items:folder_template_items(id,template_id,parent_item_id,name,sort_order)"
)
AUDIT_EXPLORER_SELECT = (
    "id,action_code,resource_type,resource_id,actor_employee_id,request_id,"
    "old_values,new_values,metadata,created_at,"
    "actor:employees!audit_events_actor_employee_id_fkey(id,employee_code,full_name)"
)


class AdminError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class AdminService:
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

    async def list_departments(self, *, current_user: CurrentUser) -> list[ReferenceSummary]:
        _require_any_explicit_or_super_user(
            current_user,
            {"employee.view", "employee.manage", "role.manage"},
        )
        rows = await self._get_rows(
            "/rest/v1/departments",
            params={"select": DEPARTMENT_SELECT, "order": "name.asc"},
        )
        return [_reference_from_row(row) for row in rows]

    async def list_roles(self, *, current_user: CurrentUser) -> list[RoleResponse]:
        _require_any_explicit_or_super_user(
            current_user,
            {"employee.view", "employee.manage", "role.manage"},
        )
        rows = await self._get_rows(
            "/rest/v1/roles",
            params={"select": ROLE_SELECT, "order": "name.asc"},
        )
        return [_role_from_row(row) for row in rows]

    async def get_employee(
        self,
        *,
        employee_id: UUID,
        current_user: CurrentUser,
    ) -> EmployeeAdminResponse:
        _require_any_explicit_or_super_user(
            current_user,
            {"employee.view", "employee.manage", "role.manage"},
        )
        row = await self._get_one(
            "/rest/v1/employees",
            params={"select": EMPLOYEE_ADMIN_SELECT, "id": f"eq.{employee_id}", "limit": "1"},
            not_found_message="Employee not found",
        )
        return _employee_from_row(row)

    async def create_employee(
        self,
        *,
        payload: EmployeeAdminCreate,
        current_user: CurrentUser,
        context: AuditContext,
        override_reason: str | None,
    ) -> EmployeeAdminResponse:
        override_reason = _require_permission_or_super_user_override(
            current_user=current_user,
            permission_code="employee.manage",
            override_reason=override_reason,
        )
        row = await self._rpc(
            "create_employee_audited",
            {
                "p_employee_code": payload.employee_code,
                "p_full_name": payload.full_name,
                "p_official_email": payload.official_email,
                "p_phone": payload.phone,
                "p_designation": payload.designation,
                "p_employment_status": payload.employment_status,
                "p_joined_on": _date_or_none(payload.joined_on),
                **_actor_context_payload(current_user, context, override_reason),
            },
        )
        return _employee_from_row(row)

    async def update_employee(
        self,
        *,
        employee_id: UUID,
        payload: EmployeeAdminUpdate,
        current_user: CurrentUser,
        context: AuditContext,
        override_reason: str | None,
    ) -> EmployeeAdminResponse:
        override_reason = _require_permission_or_super_user_override(
            current_user=current_user,
            permission_code="employee.manage",
            override_reason=override_reason,
        )
        patch = payload.model_dump(mode="json", exclude_unset=True)
        if not patch:
            raise AdminError(422, "VALIDATION_ERROR", "At least one field must be provided")
        row = await self._rpc(
            "update_employee_audited",
            {
                "p_employee_id": str(employee_id),
                "p_patch": patch,
                **_actor_context_payload(current_user, context, override_reason),
            },
        )
        return _employee_from_row(row)

    async def assign_employee_role(
        self,
        *,
        employee_id: UUID,
        payload: RoleAssignmentCreate,
        current_user: CurrentUser,
        context: AuditContext,
        override_reason: str | None,
    ) -> RoleAssignmentResponse:
        override_reason = _require_permission_or_super_user_override(
            current_user=current_user,
            permission_code="role.manage",
            override_reason=override_reason,
        )
        role = await self._get_role(payload.role_id)
        if role.code == "SUPER_USER":
            if employee_id == current_user.employee.id:
                raise AdminError(
                    403,
                    "SELF_ELEVATION_DENIED",
                    "Admins cannot elevate their own Super User access",
                )
            if not current_user.account.is_super_user:
                raise AdminError(403, "SUPER_USER_REQUIRED", "Super User access required")
            override_reason = _require_meaningful_override_reason(override_reason)

        row = await self._rpc(
            "assign_employee_role_audited",
            {
                "p_employee_id": str(employee_id),
                "p_role_id": str(payload.role_id),
                "p_expires_at": _datetime_or_none(payload.expires_at),
                **_actor_context_payload(current_user, context, override_reason),
            },
        )
        return _role_assignment_from_row(row)

    async def remove_employee_role(
        self,
        *,
        employee_id: UUID,
        role_id: UUID,
        current_user: CurrentUser,
        context: AuditContext,
        override_reason: str | None,
    ) -> None:
        override_reason = _require_permission_or_super_user_override(
            current_user=current_user,
            permission_code="role.manage",
            override_reason=override_reason,
        )
        role = await self._get_role(role_id)
        if role.code == "SUPER_USER":
            if employee_id == current_user.employee.id:
                raise AdminError(
                    403,
                    "SELF_SUPER_USER_CHANGE_DENIED",
                    "Admins cannot change their own Super User access",
                )
            if not current_user.account.is_super_user:
                raise AdminError(403, "SUPER_USER_REQUIRED", "Super User access required")
            override_reason = _require_meaningful_override_reason(override_reason)

        await self._rpc(
            "remove_employee_role_audited",
            {
                "p_employee_id": str(employee_id),
                "p_role_id": str(role_id),
                **_actor_context_payload(current_user, context, override_reason),
            },
        )

    async def assign_employee_department(
        self,
        *,
        employee_id: UUID,
        payload: DepartmentAssignmentCreate,
        current_user: CurrentUser,
        context: AuditContext,
        override_reason: str | None,
    ) -> DepartmentAssignmentResponse:
        override_reason = _require_permission_or_super_user_override(
            current_user=current_user,
            permission_code="employee.manage",
            override_reason=override_reason,
        )
        row = await self._rpc(
            "assign_employee_department_audited",
            {
                "p_employee_id": str(employee_id),
                "p_department_id": str(payload.department_id),
                "p_valid_from": payload.valid_from.isoformat(),
                **_actor_context_payload(current_user, context, override_reason),
            },
        )
        return _department_assignment_from_row(row)

    async def list_policies(
        self,
        *,
        current_user: CurrentUser,
        limit: int,
        offset: int,
    ) -> list[PolicyResponse]:
        _require_any_explicit_or_super_user(current_user, {"policy.manage"})
        rows = await self._get_rows(
            "/rest/v1/policies",
            params={
                "select": POLICY_SELECT,
                "order": "priority.asc,name.asc",
                "limit": str(limit),
                "offset": str(offset),
            },
        )
        return [_policy_from_row(row) for row in rows]

    async def create_policy(
        self,
        *,
        payload: PolicyCreate,
        current_user: CurrentUser,
        context: AuditContext,
        override_reason: str | None,
    ) -> PolicyResponse:
        override_reason = _require_permission_or_super_user_override(
            current_user=current_user,
            permission_code="policy.manage",
            override_reason=override_reason,
        )
        row = await self._rpc(
            "create_policy_audited",
            {
                "p_name": payload.name,
                "p_action_code": payload.action_code,
                "p_effect": payload.effect,
                "p_priority": payload.priority,
                "p_conditions": payload.conditions,
                "p_is_active": payload.is_active,
                **_actor_context_payload(current_user, context, override_reason),
            },
        )
        return _policy_from_row(row)

    async def update_policy(
        self,
        *,
        policy_id: UUID,
        payload: PolicyUpdate,
        current_user: CurrentUser,
        context: AuditContext,
        override_reason: str | None,
    ) -> PolicyResponse:
        override_reason = _require_permission_or_super_user_override(
            current_user=current_user,
            permission_code="policy.manage",
            override_reason=override_reason,
        )
        patch = payload.model_dump(mode="json", exclude_unset=True)
        if not patch:
            raise AdminError(422, "VALIDATION_ERROR", "At least one field must be provided")
        row = await self._rpc(
            "update_policy_audited",
            {
                "p_policy_id": str(policy_id),
                "p_patch": patch,
                **_actor_context_payload(current_user, context, override_reason),
            },
        )
        return _policy_from_row(row)

    async def list_audit_events(
        self,
        *,
        current_user: CurrentUser,
        limit: int,
        offset: int,
        action_code: str | None,
        resource_type: str | None,
        resource_id: UUID | None,
        actor_employee_id: UUID | None,
        created_from: datetime | None,
        created_to: datetime | None,
        context: AuditContext,
    ) -> list[AuditEventExplorerResponse]:
        _require_any_explicit_or_super_user(current_user, {"audit.view"})
        params = {
            "select": AUDIT_EXPLORER_SELECT,
            "order": "created_at.desc",
            "limit": str(limit),
            "offset": str(offset),
        }
        if action_code is not None:
            params["action_code"] = f"eq.{action_code}"
        if resource_type is not None:
            params["resource_type"] = f"eq.{resource_type}"
        if resource_id is not None:
            params["resource_id"] = f"eq.{resource_id}"
        if actor_employee_id is not None:
            params["actor_employee_id"] = f"eq.{actor_employee_id}"
        if created_from is not None and created_to is not None:
            params["and"] = (
                f"(created_at.gte.{created_from.isoformat()},"
                f"created_at.lte.{created_to.isoformat()})"
            )
        elif created_from is not None:
            params["created_at"] = f"gte.{created_from.isoformat()}"
        elif created_to is not None:
            params["created_at"] = f"lte.{created_to.isoformat()}"

        rows = await self._get_rows("/rest/v1/audit_events", params=params)
        await self._write_audit_explorer_access(current_user=current_user, context=context)
        return [_audit_event_from_row(row) for row in rows]

    async def list_folder_templates(
        self,
        *,
        current_user: CurrentUser,
        include_inactive: bool,
    ) -> list[FolderTemplateResponse]:
        _ensure_active_user(current_user)
        params = {"select": FOLDER_TEMPLATE_SELECT, "order": "name.asc"}
        if not include_inactive:
            params["is_active"] = "eq.true"
        rows = await self._get_rows("/rest/v1/folder_templates", params=params)
        return [_folder_template_from_row(row) for row in rows]

    async def get_folder_template(
        self,
        *,
        template_id: UUID,
        current_user: CurrentUser,
    ) -> FolderTemplateResponse:
        _ensure_active_user(current_user)
        row = await self._get_one(
            "/rest/v1/folder_templates",
            params={
                "select": FOLDER_TEMPLATE_SELECT,
                "id": f"eq.{template_id}",
                "limit": "1",
            },
            not_found_message="Folder template not found",
        )
        return _folder_template_from_row(row)

    async def create_folder_template(
        self,
        *,
        payload: FolderTemplateCreate,
        current_user: CurrentUser,
        context: AuditContext,
        override_reason: str | None,
    ) -> FolderTemplateResponse:
        override_reason = _require_permission_or_super_user_override(
            current_user=current_user,
            permission_code="folder_template.manage",
            override_reason=override_reason,
        )
        row = await self._rpc(
            "create_folder_template_audited",
            {
                "p_name": payload.name,
                "p_project_type_id": _uuid_or_none(payload.project_type_id),
                **_actor_context_payload(current_user, context, override_reason),
            },
        )
        return _folder_template_from_row(row)

    async def update_folder_template(
        self,
        *,
        template_id: UUID,
        payload: FolderTemplateUpdate,
        current_user: CurrentUser,
        context: AuditContext,
        override_reason: str | None,
    ) -> FolderTemplateResponse:
        override_reason = _require_permission_or_super_user_override(
            current_user=current_user,
            permission_code="folder_template.manage",
            override_reason=override_reason,
        )
        patch = payload.model_dump(mode="json", exclude_unset=True)
        if not patch:
            raise AdminError(422, "VALIDATION_ERROR", "At least one field must be provided")
        row = await self._rpc(
            "update_folder_template_audited",
            {
                "p_template_id": str(template_id),
                "p_patch": patch,
                **_actor_context_payload(current_user, context, override_reason),
            },
        )
        return _folder_template_from_row(row)

    async def create_folder_template_item(
        self,
        *,
        template_id: UUID,
        payload: FolderTemplateItemCreate,
        current_user: CurrentUser,
        context: AuditContext,
        override_reason: str | None,
    ) -> FolderTemplateResponse:
        override_reason = _require_permission_or_super_user_override(
            current_user=current_user,
            permission_code="folder_template.manage",
            override_reason=override_reason,
        )
        row = await self._rpc(
            "create_folder_template_item_audited",
            {
                "p_template_id": str(template_id),
                "p_parent_item_id": _uuid_or_none(payload.parent_item_id),
                "p_name": payload.name,
                "p_sort_order": payload.sort_order,
                **_actor_context_payload(current_user, context, override_reason),
            },
        )
        return _folder_template_from_row(row)

    async def update_folder_template_item(
        self,
        *,
        item_id: UUID,
        payload: FolderTemplateItemUpdate,
        current_user: CurrentUser,
        context: AuditContext,
        override_reason: str | None,
    ) -> FolderTemplateResponse:
        override_reason = _require_permission_or_super_user_override(
            current_user=current_user,
            permission_code="folder_template.manage",
            override_reason=override_reason,
        )
        patch = payload.model_dump(mode="json", exclude_unset=True)
        if not patch:
            raise AdminError(422, "VALIDATION_ERROR", "At least one field must be provided")
        row = await self._rpc(
            "update_folder_template_item_audited",
            {
                "p_item_id": str(item_id),
                "p_patch": patch,
                **_actor_context_payload(current_user, context, override_reason),
            },
        )
        return _folder_template_from_row(row)

    async def _get_role(self, role_id: UUID) -> RoleResponse:
        row = await self._get_one(
            "/rest/v1/roles",
            params={"select": ROLE_SELECT, "id": f"eq.{role_id}", "limit": "1"},
            not_found_message="Role not found",
        )
        return _role_from_row(row)

    async def _write_audit_explorer_access(
        self,
        *,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> None:
        await self._post(
            "/rest/v1/audit_events",
            json_body={
                "actor_user_account_id": str(current_user.auth_user_id),
                "actor_employee_id": str(current_user.employee.id),
                "action_code": "audit.explorer_viewed",
                "resource_type": "audit_events",
                "request_id": _uuid_or_none(context.request_id),
                "ip_address": context.ip_address,
                "user_agent": context.user_agent,
            },
        )

    async def _get_one(
        self,
        path: str,
        *,
        params: dict[str, str],
        not_found_message: str,
    ) -> dict[str, Any]:
        rows = await self._get_rows(path, params=params)
        if not rows:
            raise AdminError(404, "NOT_FOUND", not_found_message)
        return rows[0]

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

    async def _post(self, path: str, *, json_body: dict[str, object]) -> None:
        await self._request("POST", path, json_body=json_body)

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
        raise AdminError(403, "PERMISSION_DENIED", "Permission denied")


def _require_any_explicit_or_super_user(
    current_user: CurrentUser,
    permission_codes: set[str],
) -> None:
    _ensure_active_user(current_user)
    if current_user.account.is_super_user:
        return
    if any(permission in current_user.permissions for permission in permission_codes):
        return
    raise AdminError(403, "PERMISSION_DENIED", "Permission denied")


def _require_permission_or_super_user_override(
    *,
    current_user: CurrentUser,
    permission_code: str,
    override_reason: str | None,
) -> str | None:
    _ensure_active_user(current_user)
    if permission_code in current_user.permissions:
        return None
    if not current_user.account.is_super_user:
        raise AdminError(403, "PERMISSION_DENIED", "Permission denied")
    return _require_meaningful_override_reason(override_reason)


def _require_meaningful_override_reason(reason: str | None) -> str:
    if reason is None or len(reason.strip()) < 8:
        raise AdminError(
            403,
            "SUPER_USER_OVERRIDE_REASON_REQUIRED",
            "A meaningful Super User override reason is required",
        )
    return reason.strip()


def _actor_context_payload(
    current_user: CurrentUser,
    context: AuditContext,
    override_reason: str | None,
) -> dict[str, object]:
    return {
        "p_actor_user_account_id": str(current_user.auth_user_id),
        "p_actor_employee_id": str(current_user.employee.id),
        "p_request_id": _uuid_or_none(context.request_id),
        "p_ip_address": context.ip_address,
        "p_user_agent": context.user_agent,
        "p_override_reason": override_reason,
    }


def _employee_from_row(row: dict[str, Any]) -> EmployeeAdminResponse:
    normalized = dict(row)
    normalized["current_department"] = _current_department(row)
    normalized["account"] = _account(row)
    normalized["roles"] = _role_assignments(row)
    try:
        return EmployeeAdminResponse.model_validate(normalized)
    except ValidationError as exc:
        raise AdminError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Employee admin data service returned invalid data",
        ) from exc


def _current_department(row: dict[str, Any]) -> dict[str, Any] | None:
    assignments = row.get("department_assignments")
    if not isinstance(assignments, list):
        return None
    for assignment in assignments:
        if not isinstance(assignment, dict) or assignment.get("valid_to") is not None:
            continue
        department = assignment.get("department")
        if isinstance(department, dict):
            return department
    return None


def _account(row: dict[str, Any]) -> dict[str, Any] | None:
    account = row.get("account")
    return account if isinstance(account, dict) else None


def _role_assignments(row: dict[str, Any]) -> list[dict[str, Any]]:
    account = _account(row)
    if account is None:
        return []
    assignments = account.get("role_assignments")
    if not isinstance(assignments, list):
        return []
    normalized: list[dict[str, Any]] = []
    for assignment in assignments:
        if not isinstance(assignment, dict):
            continue
        role = assignment.get("role")
        if not isinstance(role, dict):
            continue
        normalized.append(
            {
                "employee_id": row.get("id"),
                "user_account_id": account.get("id"),
                "role": role,
                "assigned_at": assignment.get("assigned_at"),
                "expires_at": assignment.get("expires_at"),
            }
        )
    return normalized


def _role_from_row(row: dict[str, Any]) -> RoleResponse:
    try:
        return RoleResponse.model_validate(row)
    except ValidationError as exc:
        raise AdminError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Role data service returned invalid data",
        ) from exc


def _role_assignment_from_row(row: dict[str, Any]) -> RoleAssignmentResponse:
    try:
        return RoleAssignmentResponse.model_validate(row)
    except ValidationError as exc:
        raise AdminError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Role assignment data service returned invalid data",
        ) from exc


def _department_assignment_from_row(row: dict[str, Any]) -> DepartmentAssignmentResponse:
    try:
        return DepartmentAssignmentResponse.model_validate(row)
    except ValidationError as exc:
        raise AdminError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Department assignment data service returned invalid data",
        ) from exc


def _policy_from_row(row: dict[str, Any]) -> PolicyResponse:
    try:
        return PolicyResponse.model_validate(row)
    except ValidationError as exc:
        raise AdminError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Policy data service returned invalid data",
        ) from exc


def _folder_template_from_row(row: dict[str, Any]) -> FolderTemplateResponse:
    normalized = dict(row)
    items = normalized.get("items")
    if not isinstance(items, list):
        normalized["items"] = []
    else:
        normalized["items"] = sorted(
            [item for item in items if isinstance(item, dict)],
            key=lambda item: (int(item.get("sort_order") or 0), str(item.get("name") or "")),
        )
    try:
        return FolderTemplateResponse.model_validate(normalized)
    except ValidationError as exc:
        raise AdminError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Folder template data service returned invalid data",
        ) from exc


def _folder_template_item_from_row(row: dict[str, Any]) -> FolderTemplateItemResponse:
    try:
        return FolderTemplateItemResponse.model_validate(row)
    except ValidationError as exc:
        raise AdminError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Folder template item data service returned invalid data",
        ) from exc


def _reference_from_row(row: dict[str, Any]) -> ReferenceSummary:
    try:
        return ReferenceSummary.model_validate(row)
    except ValidationError as exc:
        raise AdminError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Reference data service returned invalid data",
        ) from exc


def _audit_event_from_row(row: dict[str, Any]) -> AuditEventExplorerResponse:
    try:
        return AuditEventExplorerResponse.model_validate(row)
    except ValidationError as exc:
        raise AdminError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Audit event data service returned invalid data",
        ) from exc


def _json_list(response: httpx.Response) -> list[dict[str, Any]]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise AdminError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid JSON",
        ) from exc
    if not isinstance(payload, list):
        raise AdminError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid payload",
        )
    for item in payload:
        if not isinstance(item, dict):
            raise AdminError(
                503,
                "DATA_SERVICE_INVALID_RESPONSE",
                "Data service returned invalid payload",
            )
    return payload


def _json_object(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise AdminError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid JSON",
        ) from exc
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        return payload[0]
    raise AdminError(503, "DATA_SERVICE_INVALID_RESPONSE", "Data service returned invalid payload")


def _raise_supabase_error(response: httpx.Response) -> None:
    payload = _error_payload(response)
    pg_code = _optional_str(payload.get("code"))
    message = _optional_str(payload.get("message")) or "Supabase data service request failed"
    if response.status_code == 404:
        raise AdminError(404, "NOT_FOUND", "Resource not found")
    if pg_code == "23505":
        raise AdminError(409, "RESOURCE_CONFLICT", "Resource already exists")
    if pg_code == "23503":
        raise AdminError(422, "INVALID_REFERENCE", "Referenced resource is invalid")
    if pg_code == "23514":
        raise AdminError(422, "INVALID_STATE", "Resource violates a constraint")
    if message in {
        "IEMS_EMPLOYEE_NOT_FOUND",
        "IEMS_POLICY_NOT_FOUND",
        "IEMS_FOLDER_TEMPLATE_NOT_FOUND",
        "IEMS_FOLDER_TEMPLATE_ITEM_NOT_FOUND",
        "IEMS_ROLE_NOT_FOUND",
    }:
        raise AdminError(404, "NOT_FOUND", "Resource not found")
    if message == "IEMS_EMPLOYEE_ACCOUNT_NOT_FOUND":
        raise AdminError(422, "INVALID_STATE", "Employee does not have an approved user account")
    if message == "IEMS_FOLDER_TEMPLATE_ITEM_PARENT_INVALID":
        raise AdminError(422, "INVALID_REFERENCE", "Parent template item is invalid")
    if message == "IEMS_SUPER_USER_OVERRIDE_REASON_REQUIRED":
        raise AdminError(
            403,
            "SUPER_USER_OVERRIDE_REASON_REQUIRED",
            "A meaningful Super User override reason is required",
        )
    if message == "IEMS_SELF_SUPER_USER_CHANGE_DENIED":
        raise AdminError(
            403,
            "SELF_ELEVATION_DENIED",
            "Admins cannot change their own Super User access",
        )
    raise AdminError(503, "DATA_SERVICE_ERROR", message)


def _error_payload(response: httpx.Response) -> dict[str, object]:
    try:
        payload = response.json()
    except ValueError:
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _date_or_none(value: date | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


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
