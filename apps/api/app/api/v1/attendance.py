from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.dependencies import (
    get_attendance_service,
    get_current_user,
    require_permission,
)
from app.core.audit import audit_context_from_request
from app.schemas.attendance import (
    AttendanceCheckInCreate,
    AttendanceCheckOutCreate,
    AttendanceCorrectionUpdate,
    AttendanceSessionResponse,
    DirectorAttendanceSummaryResponse,
)
from app.schemas.current_user import CurrentUser
from app.services.attendance import AttendanceError, AttendanceService

router = APIRouter(prefix="/v1", tags=["attendance"])

AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
AttendanceViewAllUser = Annotated[CurrentUser, Depends(require_permission("attendance.view_all"))]
AttendanceCorrectUser = Annotated[CurrentUser, Depends(require_permission("attendance.correct"))]
AttendanceServiceDep = Annotated[AttendanceService, Depends(get_attendance_service)]


@router.post(
    "/attendance/check-in",
    response_model=AttendanceSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def check_in(
    payload: AttendanceCheckInCreate,
    request: Request,
    current_user: AuthenticatedUser,
    service: AttendanceServiceDep,
) -> AttendanceSessionResponse:
    try:
        return await service.check_in(
            remarks=payload.remarks,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except AttendanceError as exc:
        raise _http_error(exc) from exc


@router.post("/attendance/check-out", response_model=AttendanceSessionResponse)
async def check_out(
    payload: AttendanceCheckOutCreate,
    request: Request,
    current_user: AuthenticatedUser,
    service: AttendanceServiceDep,
) -> AttendanceSessionResponse:
    try:
        return await service.check_out(
            remarks=payload.remarks,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except AttendanceError as exc:
        raise _http_error(exc) from exc


@router.get("/attendance/me", response_model=list[AttendanceSessionResponse])
async def list_my_attendance(
    current_user: AuthenticatedUser,
    service: AttendanceServiceDep,
    from_date: date | None = None,
    to_date: date | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AttendanceSessionResponse]:
    try:
        return await service.list_my_attendance(
            current_user=current_user,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
        )
    except AttendanceError as exc:
        raise _http_error(exc) from exc


@router.get("/attendance/team", response_model=list[AttendanceSessionResponse])
async def list_team_attendance(
    current_user: AttendanceViewAllUser,
    service: AttendanceServiceDep,
    employee_id: UUID | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AttendanceSessionResponse]:
    try:
        return await service.list_team_attendance(
            current_user=current_user,
            employee_id=employee_id,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset,
        )
    except AttendanceError as exc:
        raise _http_error(exc) from exc


@router.patch("/attendance/sessions/{session_id}", response_model=AttendanceSessionResponse)
async def correct_attendance_session(
    session_id: UUID,
    payload: AttendanceCorrectionUpdate,
    request: Request,
    current_user: AttendanceCorrectUser,
    service: AttendanceServiceDep,
) -> AttendanceSessionResponse:
    try:
        return await service.correct_session(
            session_id=session_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except AttendanceError as exc:
        raise _http_error(exc) from exc


@router.get("/director/attendance", response_model=list[DirectorAttendanceSummaryResponse])
async def list_director_attendance(
    current_user: AttendanceViewAllUser,
    service: AttendanceServiceDep,
) -> list[DirectorAttendanceSummaryResponse]:
    try:
        return await service.list_director_attendance(current_user=current_user)
    except AttendanceError as exc:
        raise _http_error(exc) from exc


def _http_error(exc: AttendanceError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "code": exc.code,
            "message": exc.message,
        },
    )
