from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.dependencies import (
    get_approvals_service,
    get_current_user,
    require_permission,
)
from app.core.audit import audit_context_from_request
from app.schemas.approvals import (
    ApprovalRequestCreate,
    ApprovalRequestResponse,
    ApprovalReviewCreate,
    ApprovalRevisionRequestCreate,
)
from app.schemas.clients_projects import ReferenceSummary
from app.schemas.current_user import CurrentUser
from app.services.approvals import ApprovalsError, ApprovalsService

router = APIRouter(prefix="/v1", tags=["approvals"])

AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
ApprovalReviewer = Annotated[CurrentUser, Depends(require_permission("approval.approve"))]
ApprovalsServiceDep = Annotated[ApprovalsService, Depends(get_approvals_service)]


@router.get("/approval-types", response_model=list[ReferenceSummary])
async def list_approval_types(
    current_user: AuthenticatedUser,
    service: ApprovalsServiceDep,
) -> list[ReferenceSummary]:
    try:
        return await service.list_approval_types(current_user=current_user)
    except ApprovalsError as exc:
        raise _http_error(exc) from exc


@router.get("/approvals", response_model=list[ApprovalRequestResponse])
async def list_approvals(
    current_user: AuthenticatedUser,
    service: ApprovalsServiceDep,
    status: Annotated[str | None, Query(min_length=1, max_length=30)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ApprovalRequestResponse]:
    try:
        return await service.list_approvals(
            current_user=current_user,
            status=status,
            limit=limit,
            offset=offset,
        )
    except ApprovalsError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/approvals",
    response_model=ApprovalRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_approval(
    payload: ApprovalRequestCreate,
    request: Request,
    current_user: AuthenticatedUser,
    service: ApprovalsServiceDep,
) -> ApprovalRequestResponse:
    try:
        return await service.create_approval(
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except ApprovalsError as exc:
        raise _http_error(exc) from exc


@router.get("/approvals/{approval_id}", response_model=ApprovalRequestResponse)
async def get_approval(
    approval_id: UUID,
    current_user: AuthenticatedUser,
    service: ApprovalsServiceDep,
) -> ApprovalRequestResponse:
    try:
        return await service.get_approval(approval_id=approval_id, current_user=current_user)
    except ApprovalsError as exc:
        raise _http_error(exc) from exc


@router.post("/approvals/{approval_id}/approve", response_model=ApprovalRequestResponse)
async def approve_approval(
    approval_id: UUID,
    payload: ApprovalReviewCreate,
    request: Request,
    current_user: ApprovalReviewer,
    service: ApprovalsServiceDep,
) -> ApprovalRequestResponse:
    try:
        return await service.approve_approval(
            approval_id=approval_id,
            comment=payload.comment,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except ApprovalsError as exc:
        raise _http_error(exc) from exc


@router.post("/approvals/{approval_id}/reject", response_model=ApprovalRequestResponse)
async def reject_approval(
    approval_id: UUID,
    payload: ApprovalReviewCreate,
    request: Request,
    current_user: ApprovalReviewer,
    service: ApprovalsServiceDep,
) -> ApprovalRequestResponse:
    try:
        return await service.reject_approval(
            approval_id=approval_id,
            comment=payload.comment,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except ApprovalsError as exc:
        raise _http_error(exc) from exc


@router.post("/approvals/{approval_id}/request-revision", response_model=ApprovalRequestResponse)
async def request_approval_revision(
    approval_id: UUID,
    payload: ApprovalRevisionRequestCreate,
    request: Request,
    current_user: ApprovalReviewer,
    service: ApprovalsServiceDep,
) -> ApprovalRequestResponse:
    try:
        return await service.request_revision(
            approval_id=approval_id,
            comment=payload.comment,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except ApprovalsError as exc:
        raise _http_error(exc) from exc


def _http_error(exc: ApprovalsError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "code": exc.code,
            "message": exc.message,
        },
    )
