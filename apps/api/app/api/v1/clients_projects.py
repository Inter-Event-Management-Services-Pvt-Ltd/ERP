from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from app.api.dependencies import (
    get_clients_projects_service,
    require_any_permission,
    require_permission,
)
from app.core.audit import audit_context_from_request
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
from app.services.clients_projects import ClientsProjectsError, ClientsProjectsService

router = APIRouter(prefix="/v1", tags=["clients and projects"])

ProjectReadUser = Annotated[
    CurrentUser,
    Depends(require_any_permission({"project.view", "project.manage"})),
]
ProjectManageUser = Annotated[CurrentUser, Depends(require_permission("project.manage"))]
ClientsProjectsServiceDep = Annotated[
    ClientsProjectsService,
    Depends(get_clients_projects_service),
]


@router.get("/clients", response_model=list[ClientResponse])
async def list_clients(
    current_user: ProjectReadUser,
    service: ClientsProjectsServiceDep,
    include_inactive: bool = False,
    search: Annotated[str | None, Query(min_length=1, max_length=150)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ClientResponse]:
    try:
        return await service.list_clients(
            current_user=current_user,
            include_inactive=include_inactive,
            search=search,
            limit=limit,
            offset=offset,
        )
    except ClientsProjectsError as exc:
        raise _http_error(exc) from exc


@router.post("/clients", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    payload: ClientCreate,
    request: Request,
    current_user: ProjectManageUser,
    service: ClientsProjectsServiceDep,
) -> ClientResponse:
    try:
        return await service.create_client(
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except ClientsProjectsError as exc:
        raise _http_error(exc) from exc


@router.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: UUID,
    current_user: ProjectReadUser,
    service: ClientsProjectsServiceDep,
) -> ClientResponse:
    try:
        return await service.get_client(client_id=client_id, current_user=current_user)
    except ClientsProjectsError as exc:
        raise _http_error(exc) from exc


@router.patch("/clients/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    payload: ClientUpdate,
    request: Request,
    current_user: ProjectManageUser,
    service: ClientsProjectsServiceDep,
) -> ClientResponse:
    try:
        return await service.update_client(
            client_id=client_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except ClientsProjectsError as exc:
        raise _http_error(exc) from exc


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: UUID,
    request: Request,
    current_user: ProjectManageUser,
    service: ClientsProjectsServiceDep,
) -> Response:
    try:
        await service.delete_client(
            client_id=client_id,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ClientsProjectsError as exc:
        raise _http_error(exc) from exc


@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    current_user: ProjectReadUser,
    service: ClientsProjectsServiceDep,
    client_id: UUID | None = None,
    include_archived: bool = False,
    search: Annotated[str | None, Query(min_length=1, max_length=150)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ProjectResponse]:
    try:
        return await service.list_projects(
            current_user=current_user,
            client_id=client_id,
            include_archived=include_archived,
            search=search,
            limit=limit,
            offset=offset,
        )
    except ClientsProjectsError as exc:
        raise _http_error(exc) from exc


@router.get("/project-types", response_model=list[ReferenceSummary])
async def list_project_types(
    current_user: ProjectReadUser,
    service: ClientsProjectsServiceDep,
) -> list[ReferenceSummary]:
    try:
        return await service.list_project_types(current_user=current_user)
    except ClientsProjectsError as exc:
        raise _http_error(exc) from exc


@router.get("/project-statuses", response_model=list[ReferenceSummary])
async def list_project_statuses(
    current_user: ProjectReadUser,
    service: ClientsProjectsServiceDep,
) -> list[ReferenceSummary]:
    try:
        return await service.list_project_statuses(current_user=current_user)
    except ClientsProjectsError as exc:
        raise _http_error(exc) from exc


@router.get("/priority-levels", response_model=list[ReferenceSummary])
async def list_priority_levels(
    current_user: ProjectReadUser,
    service: ClientsProjectsServiceDep,
) -> list[ReferenceSummary]:
    try:
        return await service.list_priority_levels(current_user=current_user)
    except ClientsProjectsError as exc:
        raise _http_error(exc) from exc


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    request: Request,
    current_user: ProjectManageUser,
    service: ClientsProjectsServiceDep,
) -> ProjectResponse:
    try:
        return await service.create_project(
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except ClientsProjectsError as exc:
        raise _http_error(exc) from exc


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: ProjectReadUser,
    service: ClientsProjectsServiceDep,
) -> ProjectResponse:
    try:
        return await service.get_project(project_id=project_id, current_user=current_user)
    except ClientsProjectsError as exc:
        raise _http_error(exc) from exc


@router.patch("/projects/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    request: Request,
    current_user: ProjectManageUser,
    service: ClientsProjectsServiceDep,
) -> ProjectResponse:
    try:
        return await service.update_project(
            project_id=project_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except ClientsProjectsError as exc:
        raise _http_error(exc) from exc


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    request: Request,
    current_user: ProjectManageUser,
    service: ClientsProjectsServiceDep,
) -> Response:
    try:
        await service.delete_project(
            project_id=project_id,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ClientsProjectsError as exc:
        raise _http_error(exc) from exc


@router.post("/projects/{project_id}/members", response_model=ProjectMemberResponse)
async def add_project_member(
    project_id: UUID,
    payload: ProjectMemberCreate,
    request: Request,
    current_user: ProjectManageUser,
    service: ClientsProjectsServiceDep,
) -> ProjectMemberResponse:
    try:
        return await service.add_project_member(
            project_id=project_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except ClientsProjectsError as exc:
        raise _http_error(exc) from exc


@router.get("/projects/{project_id}/members", response_model=list[ProjectMemberDetailResponse])
async def list_project_members(
    project_id: UUID,
    current_user: ProjectReadUser,
    service: ClientsProjectsServiceDep,
) -> list[ProjectMemberDetailResponse]:
    try:
        return await service.list_project_members(project_id=project_id, current_user=current_user)
    except ClientsProjectsError as exc:
        raise _http_error(exc) from exc


@router.patch("/projects/{project_id}/members/{employee_id}", response_model=ProjectMemberResponse)
async def update_project_member(
    project_id: UUID,
    employee_id: UUID,
    payload: ProjectMemberUpdate,
    request: Request,
    current_user: ProjectManageUser,
    service: ClientsProjectsServiceDep,
) -> ProjectMemberResponse:
    try:
        return await service.update_project_member(
            project_id=project_id,
            employee_id=employee_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except ClientsProjectsError as exc:
        raise _http_error(exc) from exc


@router.delete(
    "/projects/{project_id}/members/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_project_member(
    project_id: UUID,
    employee_id: UUID,
    request: Request,
    current_user: ProjectManageUser,
    service: ClientsProjectsServiceDep,
) -> Response:
    try:
        await service.remove_project_member(
            project_id=project_id,
            employee_id=employee_id,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ClientsProjectsError as exc:
        raise _http_error(exc) from exc


@router.get("/projects/{project_id}/folders/tree", response_model=FolderTreeNode)
async def get_project_folder_tree(
    project_id: UUID,
    current_user: ProjectReadUser,
    service: ClientsProjectsServiceDep,
) -> FolderTreeNode:
    try:
        return await service.get_folder_tree(project_id=project_id, current_user=current_user)
    except ClientsProjectsError as exc:
        raise _http_error(exc) from exc


def _http_error(exc: ClientsProjectsError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "code": exc.code,
            "message": exc.message,
        },
    )
