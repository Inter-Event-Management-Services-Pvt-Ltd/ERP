from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.dependencies import (
    get_audit_writer,
    get_current_user,
    get_director_dashboard_service,
)
from app.core.audit import (
    AuditEvent,
    AuditWriteError,
    SupabaseAuditWriter,
    audit_context_from_request,
)
from app.schemas.current_user import CurrentUser
from app.schemas.director_dashboard import (
    DirectorApprovalSummaryResponse,
    DirectorAuditEventResponse,
    DirectorOverdueTaskResponse,
    DirectorOverviewResponse,
    DirectorPhysicalFileSummaryResponse,
    DirectorProjectSummaryResponse,
)
from app.services.director_dashboard import DirectorDashboardError, DirectorDashboardService

router = APIRouter(prefix="/v1/director", tags=["director dashboard"])

AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
DirectorDashboardServiceDep = Annotated[
    DirectorDashboardService,
    Depends(get_director_dashboard_service),
]
AuditWriterDep = Annotated[SupabaseAuditWriter, Depends(get_audit_writer)]


@router.get("/overview", response_model=DirectorOverviewResponse)
async def get_director_overview(
    request: Request,
    current_user: AuthenticatedUser,
    service: DirectorDashboardServiceDep,
    audit_writer: AuditWriterDep,
) -> DirectorOverviewResponse:
    _ensure_director_route_access(current_user)
    try:
        overview = await service.get_overview(current_user=current_user)
        await _record_sensitive_access(
            action_code="director.overview_viewed",
            resource_type="director_dashboard",
            request=request,
            current_user=current_user,
            audit_writer=audit_writer,
        )
        return overview
    except DirectorDashboardError as exc:
        raise _http_error(exc) from exc


@router.get("/projects", response_model=list[DirectorProjectSummaryResponse])
async def list_director_projects(
    current_user: AuthenticatedUser,
    service: DirectorDashboardServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DirectorProjectSummaryResponse]:
    _ensure_director_route_access(current_user)
    try:
        return await service.list_projects(
            current_user=current_user,
            limit=limit,
            offset=offset,
        )
    except DirectorDashboardError as exc:
        raise _http_error(exc) from exc


@router.get("/approvals", response_model=list[DirectorApprovalSummaryResponse])
async def list_director_approvals(
    current_user: AuthenticatedUser,
    service: DirectorDashboardServiceDep,
    status: Annotated[str | None, Query(min_length=1, max_length=30)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DirectorApprovalSummaryResponse]:
    _ensure_director_route_access(current_user)
    try:
        return await service.list_approvals(
            current_user=current_user,
            status=status,
            limit=limit,
            offset=offset,
        )
    except DirectorDashboardError as exc:
        raise _http_error(exc) from exc


@router.get("/overdue-tasks", response_model=list[DirectorOverdueTaskResponse])
async def list_director_overdue_tasks(
    current_user: AuthenticatedUser,
    service: DirectorDashboardServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DirectorOverdueTaskResponse]:
    _ensure_director_route_access(current_user)
    try:
        return await service.list_overdue_tasks(
            current_user=current_user,
            limit=limit,
            offset=offset,
        )
    except DirectorDashboardError as exc:
        raise _http_error(exc) from exc


@router.get("/physical-files", response_model=list[DirectorPhysicalFileSummaryResponse])
async def list_director_physical_files(
    current_user: AuthenticatedUser,
    service: DirectorDashboardServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DirectorPhysicalFileSummaryResponse]:
    _ensure_director_route_access(current_user)
    try:
        return await service.list_physical_files(
            current_user=current_user,
            limit=limit,
            offset=offset,
        )
    except DirectorDashboardError as exc:
        raise _http_error(exc) from exc


@router.get("/audit-events", response_model=list[DirectorAuditEventResponse])
async def list_director_audit_events(
    request: Request,
    current_user: AuthenticatedUser,
    service: DirectorDashboardServiceDep,
    audit_writer: AuditWriterDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    action_code: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
    resource_type: Annotated[str | None, Query(min_length=1, max_length=60)] = None,
) -> list[DirectorAuditEventResponse]:
    _ensure_director_route_access(current_user)
    try:
        events = await service.list_audit_events(
            current_user=current_user,
            limit=limit,
            offset=offset,
            action_code=action_code,
            resource_type=resource_type,
        )
        await _record_sensitive_access(
            action_code="director.audit_events_viewed",
            resource_type="audit_events",
            request=request,
            current_user=current_user,
            audit_writer=audit_writer,
        )
        return events
    except DirectorDashboardError as exc:
        raise _http_error(exc) from exc


async def _record_sensitive_access(
    *,
    action_code: str,
    resource_type: str,
    request: Request,
    current_user: CurrentUser,
    audit_writer: SupabaseAuditWriter,
) -> None:
    try:
        await audit_writer.write_event(
            AuditEvent(
                action_code=action_code,
                resource_type=resource_type,
                actor_user_account_id=current_user.auth_user_id,
                actor_employee_id=current_user.employee.id,
                context=audit_context_from_request(request),
                metadata={"endpoint": str(request.url.path)},
            )
        )
    except AuditWriteError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "AUDIT_WRITE_FAILED",
                "message": exc.message,
            },
        ) from exc


def _ensure_director_route_access(current_user: CurrentUser) -> None:
    if current_user.account.is_super_user or "DIRECTOR" in current_user.roles:
        return
    raise HTTPException(
        status_code=403,
        detail={
            "code": "PERMISSION_DENIED",
            "message": "Permission denied",
        },
    )


def _http_error(exc: DirectorDashboardError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "code": exc.code,
            "message": exc.message,
        },
    )
