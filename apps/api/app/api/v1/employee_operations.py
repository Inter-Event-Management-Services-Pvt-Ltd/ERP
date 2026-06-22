from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.dependencies import (
    get_current_user,
    get_employee_operations_service,
    require_permission,
)
from app.core.audit import audit_context_from_request
from app.schemas.clients_projects import ReferenceSummary
from app.schemas.current_user import CurrentUser
from app.schemas.employee_operations import (
    CalendarEventCreate,
    CalendarEventResponse,
    CalendarEventUpdate,
    LeaveRequestCreate,
    LeaveRequestResponse,
    LeaveReviewCreate,
    TaskAssigneesCreate,
    TaskCommentCreate,
    TaskCommentResponse,
    TaskCreate,
    TaskDocumentLinkCreate,
    TaskResponse,
    TaskUpdate,
)
from app.services.employee_operations import EmployeeOperationsError, EmployeeOperationsService

router = APIRouter(prefix="/v1", tags=["employee operations"])

AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
LeaveReviewUser = Annotated[CurrentUser, Depends(require_permission("leave.review"))]
TaskManageUser = Annotated[CurrentUser, Depends(require_permission("task.manage"))]
EmployeeOperationsServiceDep = Annotated[
    EmployeeOperationsService,
    Depends(get_employee_operations_service),
]


@router.get("/leave-types", response_model=list[ReferenceSummary])
async def list_leave_types(
    current_user: AuthenticatedUser,
    service: EmployeeOperationsServiceDep,
) -> list[ReferenceSummary]:
    try:
        return await service.list_leave_types(current_user=current_user)
    except EmployeeOperationsError as exc:
        raise _http_error(exc) from exc


@router.get("/task-statuses", response_model=list[ReferenceSummary])
async def list_task_statuses(
    current_user: AuthenticatedUser,
    service: EmployeeOperationsServiceDep,
) -> list[ReferenceSummary]:
    try:
        return await service.list_task_statuses(current_user=current_user)
    except EmployeeOperationsError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/leave-requests",
    response_model=LeaveRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_leave_request(
    payload: LeaveRequestCreate,
    request: Request,
    current_user: AuthenticatedUser,
    service: EmployeeOperationsServiceDep,
) -> LeaveRequestResponse:
    try:
        return await service.create_leave_request(
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except EmployeeOperationsError as exc:
        raise _http_error(exc) from exc


@router.get("/leave-requests/me", response_model=list[LeaveRequestResponse])
async def list_my_leave_requests(
    current_user: AuthenticatedUser,
    service: EmployeeOperationsServiceDep,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[LeaveRequestResponse]:
    try:
        return await service.list_my_leave_requests(
            current_user=current_user,
            status=status_filter,
            limit=limit,
            offset=offset,
        )
    except EmployeeOperationsError as exc:
        raise _http_error(exc) from exc


@router.get("/leave-requests/pending", response_model=list[LeaveRequestResponse])
async def list_pending_leave_requests(
    current_user: LeaveReviewUser,
    service: EmployeeOperationsServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[LeaveRequestResponse]:
    try:
        return await service.list_pending_leave_requests(
            current_user=current_user,
            limit=limit,
            offset=offset,
        )
    except EmployeeOperationsError as exc:
        raise _http_error(exc) from exc


@router.post("/leave-requests/{request_id}/approve", response_model=LeaveRequestResponse)
async def approve_leave_request(
    request_id: UUID,
    payload: LeaveReviewCreate,
    request: Request,
    current_user: LeaveReviewUser,
    service: EmployeeOperationsServiceDep,
) -> LeaveRequestResponse:
    try:
        return await service.approve_leave_request(
            request_id=request_id,
            review_comment=payload.review_comment,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except EmployeeOperationsError as exc:
        raise _http_error(exc) from exc


@router.post("/leave-requests/{request_id}/reject", response_model=LeaveRequestResponse)
async def reject_leave_request(
    request_id: UUID,
    payload: LeaveReviewCreate,
    request: Request,
    current_user: LeaveReviewUser,
    service: EmployeeOperationsServiceDep,
) -> LeaveRequestResponse:
    try:
        return await service.reject_leave_request(
            request_id=request_id,
            review_comment=payload.review_comment,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except EmployeeOperationsError as exc:
        raise _http_error(exc) from exc


@router.post("/leave-requests/{request_id}/cancel", response_model=LeaveRequestResponse)
async def cancel_leave_request(
    request_id: UUID,
    request: Request,
    current_user: AuthenticatedUser,
    service: EmployeeOperationsServiceDep,
) -> LeaveRequestResponse:
    try:
        return await service.cancel_leave_request(
            request_id=request_id,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except EmployeeOperationsError as exc:
        raise _http_error(exc) from exc


@router.get("/tasks", response_model=list[TaskResponse])
async def list_tasks(
    current_user: AuthenticatedUser,
    service: EmployeeOperationsServiceDep,
    project_id: UUID | None = None,
    assigned_to_me: bool = False,
    status_code: Annotated[str | None, Query(min_length=1, max_length=40)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TaskResponse]:
    try:
        return await service.list_tasks(
            current_user=current_user,
            project_id=project_id,
            assigned_to_me=assigned_to_me,
            status_code=status_code,
            limit=limit,
            offset=offset,
        )
    except EmployeeOperationsError as exc:
        raise _http_error(exc) from exc


@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    request: Request,
    current_user: TaskManageUser,
    service: EmployeeOperationsServiceDep,
) -> TaskResponse:
    try:
        return await service.create_task(
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except EmployeeOperationsError as exc:
        raise _http_error(exc) from exc


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user: AuthenticatedUser,
    service: EmployeeOperationsServiceDep,
) -> TaskResponse:
    try:
        return await service.get_task(task_id=task_id, current_user=current_user)
    except EmployeeOperationsError as exc:
        raise _http_error(exc) from exc


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    request: Request,
    current_user: TaskManageUser,
    service: EmployeeOperationsServiceDep,
) -> TaskResponse:
    try:
        return await service.update_task(
            task_id=task_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except EmployeeOperationsError as exc:
        raise _http_error(exc) from exc


@router.post("/tasks/{task_id}/assignees", response_model=TaskResponse)
async def add_task_assignees(
    task_id: UUID,
    payload: TaskAssigneesCreate,
    request: Request,
    current_user: TaskManageUser,
    service: EmployeeOperationsServiceDep,
) -> TaskResponse:
    try:
        return await service.add_task_assignees(
            task_id=task_id,
            employee_ids=payload.employee_ids,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except EmployeeOperationsError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/tasks/{task_id}/comments",
    response_model=TaskCommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_task_comment(
    task_id: UUID,
    payload: TaskCommentCreate,
    request: Request,
    current_user: AuthenticatedUser,
    service: EmployeeOperationsServiceDep,
) -> TaskCommentResponse:
    try:
        return await service.add_task_comment(
            task_id=task_id,
            comment_text=payload.comment_text,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except EmployeeOperationsError as exc:
        raise _http_error(exc) from exc


@router.get("/tasks/{task_id}/comments", response_model=list[TaskCommentResponse])
async def list_task_comments(
    task_id: UUID,
    current_user: AuthenticatedUser,
    service: EmployeeOperationsServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TaskCommentResponse]:
    try:
        return await service.list_task_comments(
            task_id=task_id,
            current_user=current_user,
            limit=limit,
            offset=offset,
        )
    except EmployeeOperationsError as exc:
        raise _http_error(exc) from exc


@router.post("/tasks/{task_id}/documents", response_model=TaskResponse)
async def link_task_document(
    task_id: UUID,
    payload: TaskDocumentLinkCreate,
    request: Request,
    current_user: TaskManageUser,
    service: EmployeeOperationsServiceDep,
) -> TaskResponse:
    try:
        return await service.link_task_document(
            task_id=task_id,
            document_id=payload.document_id,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except EmployeeOperationsError as exc:
        raise _http_error(exc) from exc


@router.get("/calendar/events", response_model=list[CalendarEventResponse])
async def list_calendar_events(
    current_user: AuthenticatedUser,
    service: EmployeeOperationsServiceDep,
    from_date: date | None = None,
    to_date: date | None = None,
    project_id: UUID | None = None,
) -> list[CalendarEventResponse]:
    try:
        return await service.list_calendar_events(
            current_user=current_user,
            from_date=from_date,
            to_date=to_date,
            project_id=project_id,
        )
    except EmployeeOperationsError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/calendar/events",
    response_model=CalendarEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_calendar_event(
    payload: CalendarEventCreate,
    request: Request,
    current_user: TaskManageUser,
    service: EmployeeOperationsServiceDep,
) -> CalendarEventResponse:
    try:
        return await service.create_calendar_event(
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except EmployeeOperationsError as exc:
        raise _http_error(exc) from exc


@router.patch("/calendar/events/{event_id}", response_model=CalendarEventResponse)
async def update_calendar_event(
    event_id: UUID,
    payload: CalendarEventUpdate,
    request: Request,
    current_user: TaskManageUser,
    service: EmployeeOperationsServiceDep,
) -> CalendarEventResponse:
    try:
        return await service.update_calendar_event(
            event_id=event_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except EmployeeOperationsError as exc:
        raise _http_error(exc) from exc


def _http_error(exc: EmployeeOperationsError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "code": exc.code,
            "message": exc.message,
        },
    )
