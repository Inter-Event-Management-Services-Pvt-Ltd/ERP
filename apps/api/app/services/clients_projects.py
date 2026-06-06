from typing import Any
from uuid import UUID

import httpx
from pydantic import ValidationError

from app.core.audit import AuditContext
from app.schemas.clients_projects import (
    ClientCreate,
    ClientResponse,
    ClientUpdate,
    FolderTreeNode,
    ProjectCreate,
    ProjectMemberCreate,
    ProjectMemberDetailResponse,
    ProjectMemberResponse,
    ProjectMemberUpdate,
    ProjectResponse,
    ProjectUpdate,
    ReferenceSummary,
)
from app.schemas.current_user import CurrentUser

PROJECT_SELECT = (
    "id,project_code,client_id,project_type_id,project_status_id,priority_level_id,"
    "name,event_date,venue,description,project_manager_id,created_by,created_at,updated_at,"
    "archived_at,deleted_at,"
    "client:clients(id,client_code,display_name),"
    "project_type:project_types(id,code,name),"
    "project_status:project_statuses(id,code,name),"
    "priority_level:priority_levels(id,code,name),"
    "project_manager:employees!projects_project_manager_id_fkey(id,employee_code,full_name)"
)
SCOPED_PROJECT_SELECT = f"{PROJECT_SELECT},project_members!inner(employee_id,removed_at)"
CLIENT_SELECT = "id,client_code,legal_name,display_name,is_active,notes,created_at,updated_at"
REFERENCE_SELECT = "id,code,name"
PROJECT_MEMBER_SELECT = (
    "project_id,employee_id,access_level,assigned_by,assigned_at,removed_at,"
    "employee:employees!project_members_employee_id_fkey(id,employee_code,full_name)"
)


class ClientsProjectsError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class ClientsProjectsService:
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

    async def list_clients(
        self,
        *,
        current_user: CurrentUser,
        include_inactive: bool = False,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ClientResponse]:
        self._require_project_read(current_user)
        params = {
            "select": CLIENT_SELECT,
            "order": "display_name.asc",
            "limit": str(limit),
            "offset": str(offset),
        }
        if not include_inactive:
            params["is_active"] = "eq.true"
        if search is not None:
            term = _postgrest_pattern(search)
            params["or"] = (
                f"(client_code.ilike.{term},legal_name.ilike.{term},display_name.ilike.{term})"
            )

        rows = await self._get_rows("/rest/v1/clients", params=params)
        return [_client_from_row(row) for row in rows]

    async def create_client(
        self,
        *,
        payload: ClientCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ClientResponse:
        self._require_project_manage(current_user)
        row = await self._rpc(
            "create_client_audited",
            {
                "p_client_code": payload.client_code,
                "p_legal_name": payload.legal_name,
                "p_display_name": payload.display_name,
                "p_notes": payload.notes,
                **_actor_context_payload(current_user, context),
            },
        )
        return _client_from_row(row)

    async def get_client(self, *, client_id: UUID, current_user: CurrentUser) -> ClientResponse:
        self._require_project_read(current_user)
        rows = await self._get_rows(
            "/rest/v1/clients",
            params={
                "select": CLIENT_SELECT,
                "id": f"eq.{client_id}",
                "limit": "1",
            },
        )
        if not rows:
            raise ClientsProjectsError(404, "NOT_FOUND", "Client not found")
        return _client_from_row(rows[0])

    async def update_client(
        self,
        *,
        client_id: UUID,
        payload: ClientUpdate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ClientResponse:
        self._require_project_manage(current_user)
        row = await self._rpc(
            "update_client_audited",
            {
                "p_client_id": str(client_id),
                "p_patch": payload.model_dump(mode="json", exclude_unset=True),
                **_actor_context_payload(current_user, context),
            },
        )
        return _client_from_row(row)

    async def delete_client(
        self,
        *,
        client_id: UUID,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> None:
        self._require_project_manage(current_user)
        await self._rpc(
            "deactivate_client_audited",
            {
                "p_client_id": str(client_id),
                **_actor_context_payload(current_user, context),
            },
        )

    async def list_projects(
        self,
        *,
        current_user: CurrentUser,
        client_id: UUID | None = None,
        include_archived: bool = False,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ProjectResponse]:
        self._require_project_read(current_user)
        scoped = not _has_project_manage(current_user)
        params = {
            "select": SCOPED_PROJECT_SELECT if scoped else PROJECT_SELECT,
            "deleted_at": "is.null",
            "order": "created_at.desc",
            "limit": str(limit),
            "offset": str(offset),
        }
        if scoped:
            params["project_members.employee_id"] = f"eq.{current_user.employee.id}"
            params["project_members.removed_at"] = "is.null"
        if client_id is not None:
            params["client_id"] = f"eq.{client_id}"
        if not include_archived:
            params["archived_at"] = "is.null"
        if search is not None:
            term = _postgrest_pattern(search)
            params["or"] = f"(project_code.ilike.{term},name.ilike.{term},venue.ilike.{term})"

        rows = await self._get_rows("/rest/v1/projects", params=params)
        return [_project_from_row(row) for row in rows]

    async def list_project_types(
        self,
        *,
        current_user: CurrentUser,
    ) -> list[ReferenceSummary]:
        self._require_project_read(current_user)
        rows = await self._get_rows(
            "/rest/v1/project_types",
            params={
                "select": REFERENCE_SELECT,
                "is_active": "eq.true",
                "order": "name.asc",
            },
        )
        return [_reference_from_row(row) for row in rows]

    async def list_project_statuses(
        self,
        *,
        current_user: CurrentUser,
    ) -> list[ReferenceSummary]:
        self._require_project_read(current_user)
        rows = await self._get_rows(
            "/rest/v1/project_statuses",
            params={
                "select": REFERENCE_SELECT,
                "order": "sort_order.asc,name.asc",
            },
        )
        return [_reference_from_row(row) for row in rows]

    async def list_priority_levels(
        self,
        *,
        current_user: CurrentUser,
    ) -> list[ReferenceSummary]:
        self._require_project_read(current_user)
        rows = await self._get_rows(
            "/rest/v1/priority_levels",
            params={
                "select": REFERENCE_SELECT,
                "order": "rank.asc,name.asc",
            },
        )
        return [_reference_from_row(row) for row in rows]

    async def create_project(
        self,
        *,
        payload: ProjectCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ProjectResponse:
        self._require_project_manage(current_user)
        row = await self._rpc(
            "create_project_with_folder_template",
            {
                "p_project_code": payload.project_code,
                "p_client_id": str(payload.client_id),
                "p_project_type_id": str(payload.project_type_id),
                "p_project_status_id": str(payload.project_status_id),
                "p_priority_level_id": str(payload.priority_level_id),
                "p_name": payload.name,
                "p_event_date": _iso_or_none(payload.event_date),
                "p_venue": payload.venue,
                "p_description": payload.description,
                "p_project_manager_id": _uuid_or_none(payload.project_manager_id),
                "p_created_by": str(current_user.employee.id),
                "p_folder_template_id": _uuid_or_none(payload.folder_template_id),
                **_actor_context_payload(current_user, context),
            },
        )
        return _project_from_row(row)

    async def get_project(self, *, project_id: UUID, current_user: CurrentUser) -> ProjectResponse:
        await self._require_project_read_access(project_id=project_id, current_user=current_user)
        rows = await self._get_rows(
            "/rest/v1/projects",
            params={
                "select": PROJECT_SELECT,
                "id": f"eq.{project_id}",
                "deleted_at": "is.null",
                "limit": "1",
            },
        )
        if not rows:
            raise ClientsProjectsError(404, "NOT_FOUND", "Project not found")
        return _project_from_row(rows[0])

    async def update_project(
        self,
        *,
        project_id: UUID,
        payload: ProjectUpdate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ProjectResponse:
        await self._require_project_manage_access(project_id=project_id, current_user=current_user)
        row = await self._rpc(
            "update_project_audited",
            {
                "p_project_id": str(project_id),
                "p_patch": payload.model_dump(mode="json", exclude_unset=True),
                **_actor_context_payload(current_user, context),
            },
        )
        return _project_from_row(row)

    async def delete_project(
        self,
        *,
        project_id: UUID,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> None:
        await self._require_project_manage_access(project_id=project_id, current_user=current_user)
        await self._rpc(
            "soft_delete_project_audited",
            {
                "p_project_id": str(project_id),
                **_actor_context_payload(current_user, context),
            },
        )

    async def add_project_member(
        self,
        *,
        project_id: UUID,
        payload: ProjectMemberCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ProjectMemberResponse:
        await self._require_project_manage_access(project_id=project_id, current_user=current_user)
        row = await self._rpc(
            "upsert_project_member_audited",
            {
                "p_project_id": str(project_id),
                "p_employee_id": str(payload.employee_id),
                "p_access_level": payload.access_level.value,
                **_actor_context_payload(current_user, context),
            },
        )
        return _project_member_from_row(row)

    async def list_project_members(
        self,
        *,
        project_id: UUID,
        current_user: CurrentUser,
    ) -> list[ProjectMemberDetailResponse]:
        await self._require_project_read_access(project_id=project_id, current_user=current_user)
        rows = await self._get_rows(
            "/rest/v1/project_members",
            params={
                "select": PROJECT_MEMBER_SELECT,
                "project_id": f"eq.{project_id}",
                "removed_at": "is.null",
                "order": "assigned_at.desc",
            },
        )
        return [_project_member_detail_from_row(row) for row in rows]

    async def update_project_member(
        self,
        *,
        project_id: UUID,
        employee_id: UUID,
        payload: ProjectMemberUpdate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ProjectMemberResponse:
        await self._require_project_manage_access(project_id=project_id, current_user=current_user)
        row = await self._rpc(
            "upsert_project_member_audited",
            {
                "p_project_id": str(project_id),
                "p_employee_id": str(employee_id),
                "p_access_level": payload.access_level.value,
                **_actor_context_payload(current_user, context),
            },
        )
        return _project_member_from_row(row)

    async def remove_project_member(
        self,
        *,
        project_id: UUID,
        employee_id: UUID,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> None:
        await self._require_project_manage_access(project_id=project_id, current_user=current_user)
        await self._rpc(
            "remove_project_member_audited",
            {
                "p_project_id": str(project_id),
                "p_employee_id": str(employee_id),
                **_actor_context_payload(current_user, context),
            },
        )

    async def get_folder_tree(
        self,
        *,
        project_id: UUID,
        current_user: CurrentUser,
    ) -> FolderTreeNode:
        await self._require_project_read_access(project_id=project_id, current_user=current_user)
        rows = await self._get_rows(
            "/rest/v1/folders",
            params={
                "select": "id,project_id,parent_folder_id,name,sort_order",
                "project_id": f"eq.{project_id}",
                "deleted_at": "is.null",
                "order": "sort_order.asc,name.asc",
            },
        )
        return _folder_tree_from_rows(rows)

    async def _require_project_read_access(
        self,
        *,
        project_id: UUID,
        current_user: CurrentUser,
    ) -> None:
        self._require_project_read(current_user)
        if _has_project_manage(current_user):
            return
        await self._require_active_project_membership(
            project_id=project_id,
            current_user=current_user,
        )

    async def _require_project_manage_access(
        self,
        *,
        project_id: UUID,
        current_user: CurrentUser,
    ) -> None:
        self._require_project_manage(current_user)
        if current_user.account.is_super_user:
            return
        rows = await self._get_rows(
            "/rest/v1/project_members",
            params={
                "select": "project_id,employee_id,access_level,removed_at",
                "project_id": f"eq.{project_id}",
                "employee_id": f"eq.{current_user.employee.id}",
                "access_level": "eq.MANAGE",
                "removed_at": "is.null",
                "limit": "1",
            },
        )
        if not rows:
            raise ClientsProjectsError(403, "ABAC_DENIED", "Project manage access denied")

    async def _require_active_project_membership(
        self,
        *,
        project_id: UUID,
        current_user: CurrentUser,
    ) -> None:
        rows = await self._get_rows(
            "/rest/v1/project_members",
            params={
                "select": "project_id,employee_id,removed_at",
                "project_id": f"eq.{project_id}",
                "employee_id": f"eq.{current_user.employee.id}",
                "removed_at": "is.null",
                "limit": "1",
            },
        )
        if not rows:
            raise ClientsProjectsError(404, "NOT_FOUND", "Project not found")

    def _require_project_read(self, current_user: CurrentUser) -> None:
        if not (_has_project_view(current_user) or _has_project_manage(current_user)):
            raise ClientsProjectsError(403, "PERMISSION_DENIED", "Permission denied")

    def _require_project_manage(self, current_user: CurrentUser) -> None:
        if not _has_project_manage(current_user):
            raise ClientsProjectsError(403, "PERMISSION_DENIED", "Permission denied")

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


def _actor_context_payload(current_user: CurrentUser, context: AuditContext) -> dict[str, object]:
    return {
        "p_actor_user_account_id": str(current_user.auth_user_id),
        "p_actor_employee_id": str(current_user.employee.id),
        "p_request_id": _uuid_or_none(context.request_id),
        "p_ip_address": context.ip_address,
        "p_user_agent": context.user_agent,
    }


def _client_from_row(row: dict[str, Any]) -> ClientResponse:
    try:
        return ClientResponse.model_validate(row)
    except ValidationError as exc:
        raise ClientsProjectsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Client data service returned invalid data",
        ) from exc


def _project_from_row(row: dict[str, Any]) -> ProjectResponse:
    try:
        return ProjectResponse.model_validate(row)
    except ValidationError as exc:
        raise ClientsProjectsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Project data service returned invalid data",
        ) from exc


def _reference_from_row(row: dict[str, Any]) -> ReferenceSummary:
    try:
        return ReferenceSummary.model_validate(row)
    except ValidationError as exc:
        raise ClientsProjectsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Reference data service returned invalid data",
        ) from exc


def _project_member_from_row(row: dict[str, Any]) -> ProjectMemberResponse:
    try:
        return ProjectMemberResponse.model_validate(row)
    except ValidationError as exc:
        raise ClientsProjectsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Project member data service returned invalid data",
        ) from exc


def _project_member_detail_from_row(row: dict[str, Any]) -> ProjectMemberDetailResponse:
    try:
        return ProjectMemberDetailResponse.model_validate(row)
    except ValidationError as exc:
        raise ClientsProjectsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Project member data service returned invalid data",
        ) from exc


def _folder_tree_from_rows(rows: list[dict[str, Any]]) -> FolderTreeNode:
    nodes: dict[UUID, FolderTreeNode] = {}
    for row in rows:
        try:
            node = FolderTreeNode.model_validate({**row, "children": []})
        except ValidationError as exc:
            raise ClientsProjectsError(
                503,
                "DATA_SERVICE_INVALID_RESPONSE",
                "Folder data service returned invalid data",
            ) from exc
        nodes[node.id] = node

    roots: list[FolderTreeNode] = []
    for node in nodes.values():
        if node.parent_folder_id is None:
            roots.append(node)
            continue
        parent = nodes.get(node.parent_folder_id)
        if parent is None:
            raise ClientsProjectsError(
                503,
                "FOLDER_TREE_INVALID",
                "Folder hierarchy references a missing parent",
            )
        parent.children.append(node)

    if not roots:
        raise ClientsProjectsError(404, "NOT_FOUND", "Folder tree not found")
    if len(roots) > 1:
        raise ClientsProjectsError(
            503,
            "FOLDER_TREE_INVALID",
            "Project has more than one root folder",
        )

    _sort_folder_tree(roots[0])
    return roots[0]


def _sort_folder_tree(node: FolderTreeNode) -> None:
    node.children.sort(key=lambda child: (child.sort_order, child.name.lower()))
    for child in node.children:
        _sort_folder_tree(child)


def _json_list(response: httpx.Response) -> list[dict[str, Any]]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise ClientsProjectsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid JSON",
        ) from exc
    if not isinstance(payload, list):
        raise ClientsProjectsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid payload",
        )
    for item in payload:
        if not isinstance(item, dict):
            raise ClientsProjectsError(
                503,
                "DATA_SERVICE_INVALID_RESPONSE",
                "Data service returned invalid payload",
            )
    return payload


def _json_object(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise ClientsProjectsError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid JSON",
        ) from exc
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        return payload[0]
    raise ClientsProjectsError(
        503,
        "DATA_SERVICE_INVALID_RESPONSE",
        "Data service returned invalid payload",
    )


def _raise_supabase_error(response: httpx.Response) -> None:
    payload = _error_payload(response)
    pg_code = _optional_str(payload.get("code"))
    message = _optional_str(payload.get("message")) or "Supabase data service request failed"

    if message == "IEMS_LAST_PROJECT_MANAGER":
        raise ClientsProjectsError(
            409,
            "INVALID_PROJECT_MEMBER_STATE",
            "Project must retain at least one active MANAGE member",
        )
    if message in {"IEMS_PROJECT_NOT_FOUND", "IEMS_CLIENT_NOT_FOUND"}:
        raise ClientsProjectsError(404, "NOT_FOUND", "Resource not found")
    if message == "IEMS_EMPLOYEE_NOT_ACTIVE":
        raise ClientsProjectsError(422, "INVALID_REFERENCE", "Employee is not active")
    if pg_code == "23505":
        raise ClientsProjectsError(409, "RESOURCE_CONFLICT", "Resource already exists")
    if pg_code == "23503":
        raise ClientsProjectsError(422, "INVALID_REFERENCE", "Referenced resource is invalid")
    if pg_code == "23514":
        raise ClientsProjectsError(422, "INVALID_STATE", "Resource violates a database constraint")
    if response.status_code == 404:
        raise ClientsProjectsError(404, "NOT_FOUND", "Resource not found")

    raise ClientsProjectsError(503, "DATA_SERVICE_ERROR", message)


def _error_payload(response: httpx.Response) -> dict[str, object]:
    try:
        payload = response.json()
    except ValueError:
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _has_project_view(current_user: CurrentUser) -> bool:
    return current_user.account.is_super_user or "project.view" in current_user.permissions


def _has_project_manage(current_user: CurrentUser) -> bool:
    return current_user.account.is_super_user or "project.manage" in current_user.permissions


def _postgrest_pattern(raw_value: str) -> str:
    cleaned = (
        raw_value.strip()
        .replace("*", "")
        .replace(",", " ")
        .replace("(", " ")
        .replace(")", " ")
    )
    return f"*{cleaned}*"


def _iso_or_none(value: object) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return str(value.isoformat())
    return str(value)


def _uuid_or_none(value: UUID | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_str(value: object) -> str | None:
    if isinstance(value, str):
        return value
    return None
