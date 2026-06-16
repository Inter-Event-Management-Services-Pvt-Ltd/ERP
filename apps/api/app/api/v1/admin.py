from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status

from app.api.dependencies import get_admin_service, get_current_user, require_permission
from app.core.audit import audit_context_from_request
from app.schemas.admin import (
    AuditEventExplorerResponse,
    DepartmentAssignmentCreate,
    DepartmentAssignmentResponse,
    EmployeeAdminCreate,
    EmployeeAdminResponse,
    EmployeeAdminUpdate,
    FolderTemplateCreate,
    FolderTemplateItemCreate,
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
from app.services.admin import AdminError, AdminService

router = APIRouter(prefix="/v1", tags=["admin"])

AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
EmployeeViewUser = Annotated[CurrentUser, Depends(require_permission("employee.view"))]
EmployeeManageUser = Annotated[CurrentUser, Depends(require_permission("employee.manage"))]
RoleManageUser = Annotated[CurrentUser, Depends(require_permission("role.manage"))]
PolicyManageUser = Annotated[CurrentUser, Depends(require_permission("policy.manage"))]
AuditViewUser = Annotated[CurrentUser, Depends(require_permission("audit.view"))]
FolderTemplateManageUser = Annotated[
    CurrentUser,
    Depends(require_permission("folder_template.manage")),
]
AdminServiceDep = Annotated[AdminService, Depends(get_admin_service)]
OverrideReasonHeader = Annotated[
    str | None,
    Header(alias="X-IEMS-Override-Reason"),
]


@router.get("/departments", response_model=list[ReferenceSummary])
async def list_departments(
    current_user: EmployeeViewUser,
    service: AdminServiceDep,
) -> list[ReferenceSummary]:
    try:
        return await service.list_departments(current_user=current_user)
    except AdminError as exc:
        raise _http_error(exc) from exc


@router.get("/roles", response_model=list[RoleResponse])
async def list_roles(
    current_user: EmployeeViewUser,
    service: AdminServiceDep,
) -> list[RoleResponse]:
    try:
        return await service.list_roles(current_user=current_user)
    except AdminError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/employees",
    response_model=EmployeeAdminResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_employee(
    payload: EmployeeAdminCreate,
    request: Request,
    current_user: EmployeeManageUser,
    service: AdminServiceDep,
    override_reason: OverrideReasonHeader = None,
) -> EmployeeAdminResponse:
    try:
        return await service.create_employee(
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
            override_reason=override_reason,
        )
    except AdminError as exc:
        raise _http_error(exc) from exc


@router.get("/employees/{employee_id}", response_model=EmployeeAdminResponse)
async def get_employee(
    employee_id: UUID,
    current_user: EmployeeViewUser,
    service: AdminServiceDep,
) -> EmployeeAdminResponse:
    try:
        return await service.get_employee(employee_id=employee_id, current_user=current_user)
    except AdminError as exc:
        raise _http_error(exc) from exc


@router.patch("/employees/{employee_id}", response_model=EmployeeAdminResponse)
async def update_employee(
    employee_id: UUID,
    payload: EmployeeAdminUpdate,
    request: Request,
    current_user: EmployeeManageUser,
    service: AdminServiceDep,
    override_reason: OverrideReasonHeader = None,
) -> EmployeeAdminResponse:
    try:
        return await service.update_employee(
            employee_id=employee_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
            override_reason=override_reason,
        )
    except AdminError as exc:
        raise _http_error(exc) from exc


@router.post("/employees/{employee_id}/roles", response_model=RoleAssignmentResponse)
async def assign_employee_role(
    employee_id: UUID,
    payload: RoleAssignmentCreate,
    request: Request,
    current_user: RoleManageUser,
    service: AdminServiceDep,
    override_reason: OverrideReasonHeader = None,
) -> RoleAssignmentResponse:
    try:
        return await service.assign_employee_role(
            employee_id=employee_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
            override_reason=override_reason,
        )
    except AdminError as exc:
        raise _http_error(exc) from exc


@router.delete("/employees/{employee_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_employee_role(
    employee_id: UUID,
    role_id: UUID,
    request: Request,
    current_user: RoleManageUser,
    service: AdminServiceDep,
    override_reason: OverrideReasonHeader = None,
) -> Response:
    try:
        await service.remove_employee_role(
            employee_id=employee_id,
            role_id=role_id,
            current_user=current_user,
            context=audit_context_from_request(request),
            override_reason=override_reason,
        )
    except AdminError as exc:
        raise _http_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/employees/{employee_id}/department-assignments",
    response_model=DepartmentAssignmentResponse,
)
async def assign_employee_department(
    employee_id: UUID,
    payload: DepartmentAssignmentCreate,
    request: Request,
    current_user: EmployeeManageUser,
    service: AdminServiceDep,
    override_reason: OverrideReasonHeader = None,
) -> DepartmentAssignmentResponse:
    try:
        return await service.assign_employee_department(
            employee_id=employee_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
            override_reason=override_reason,
        )
    except AdminError as exc:
        raise _http_error(exc) from exc


@router.get("/policies", response_model=list[PolicyResponse])
async def list_policies(
    current_user: PolicyManageUser,
    service: AdminServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[PolicyResponse]:
    try:
        return await service.list_policies(
            current_user=current_user,
            limit=limit,
            offset=offset,
        )
    except AdminError as exc:
        raise _http_error(exc) from exc


@router.post("/policies", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    payload: PolicyCreate,
    request: Request,
    current_user: PolicyManageUser,
    service: AdminServiceDep,
    override_reason: OverrideReasonHeader = None,
) -> PolicyResponse:
    try:
        return await service.create_policy(
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
            override_reason=override_reason,
        )
    except AdminError as exc:
        raise _http_error(exc) from exc


@router.patch("/policies/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: UUID,
    payload: PolicyUpdate,
    request: Request,
    current_user: PolicyManageUser,
    service: AdminServiceDep,
    override_reason: OverrideReasonHeader = None,
) -> PolicyResponse:
    try:
        return await service.update_policy(
            policy_id=policy_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
            override_reason=override_reason,
        )
    except AdminError as exc:
        raise _http_error(exc) from exc


@router.get("/audit-events", response_model=list[AuditEventExplorerResponse])
async def list_audit_events(
    request: Request,
    current_user: AuditViewUser,
    service: AdminServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    action_code: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    resource_type: Annotated[str | None, Query(min_length=1, max_length=60)] = None,
    resource_id: UUID | None = None,
    actor_employee_id: UUID | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> list[AuditEventExplorerResponse]:
    try:
        return await service.list_audit_events(
            current_user=current_user,
            limit=limit,
            offset=offset,
            action_code=action_code,
            resource_type=resource_type,
            resource_id=resource_id,
            actor_employee_id=actor_employee_id,
            created_from=created_from,
            created_to=created_to,
            context=audit_context_from_request(request),
        )
    except AdminError as exc:
        raise _http_error(exc) from exc


@router.get("/folder-templates", response_model=list[FolderTemplateResponse])
async def list_folder_templates(
    current_user: AuthenticatedUser,
    service: AdminServiceDep,
    include_inactive: bool = False,
) -> list[FolderTemplateResponse]:
    try:
        return await service.list_folder_templates(
            current_user=current_user,
            include_inactive=include_inactive,
        )
    except AdminError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/folder-templates",
    response_model=FolderTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_folder_template(
    payload: FolderTemplateCreate,
    request: Request,
    current_user: FolderTemplateManageUser,
    service: AdminServiceDep,
    override_reason: OverrideReasonHeader = None,
) -> FolderTemplateResponse:
    try:
        return await service.create_folder_template(
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
            override_reason=override_reason,
        )
    except AdminError as exc:
        raise _http_error(exc) from exc


@router.get("/folder-templates/{template_id}", response_model=FolderTemplateResponse)
async def get_folder_template(
    template_id: UUID,
    current_user: AuthenticatedUser,
    service: AdminServiceDep,
) -> FolderTemplateResponse:
    try:
        return await service.get_folder_template(
            template_id=template_id,
            current_user=current_user,
        )
    except AdminError as exc:
        raise _http_error(exc) from exc


@router.patch("/folder-templates/{template_id}", response_model=FolderTemplateResponse)
async def update_folder_template(
    template_id: UUID,
    payload: FolderTemplateUpdate,
    request: Request,
    current_user: FolderTemplateManageUser,
    service: AdminServiceDep,
    override_reason: OverrideReasonHeader = None,
) -> FolderTemplateResponse:
    try:
        return await service.update_folder_template(
            template_id=template_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
            override_reason=override_reason,
        )
    except AdminError as exc:
        raise _http_error(exc) from exc


@router.post("/folder-templates/{template_id}/items", response_model=FolderTemplateResponse)
async def create_folder_template_item(
    template_id: UUID,
    payload: FolderTemplateItemCreate,
    request: Request,
    current_user: FolderTemplateManageUser,
    service: AdminServiceDep,
    override_reason: OverrideReasonHeader = None,
) -> FolderTemplateResponse:
    try:
        return await service.create_folder_template_item(
            template_id=template_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
            override_reason=override_reason,
        )
    except AdminError as exc:
        raise _http_error(exc) from exc


@router.patch("/folder-template-items/{item_id}", response_model=FolderTemplateResponse)
async def update_folder_template_item(
    item_id: UUID,
    payload: FolderTemplateItemUpdate,
    request: Request,
    current_user: FolderTemplateManageUser,
    service: AdminServiceDep,
    override_reason: OverrideReasonHeader = None,
) -> FolderTemplateResponse:
    try:
        return await service.update_folder_template_item(
            item_id=item_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
            override_reason=override_reason,
        )
    except AdminError as exc:
        raise _http_error(exc) from exc


def _http_error(exc: AdminError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "code": exc.code,
            "message": exc.message,
        },
    )
