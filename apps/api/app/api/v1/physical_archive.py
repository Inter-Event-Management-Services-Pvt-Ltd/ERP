from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.dependencies import (
    get_current_user,
    get_physical_archive_service,
    require_any_permission,
    require_permission,
)
from app.core.audit import audit_context_from_request
from app.schemas.current_user import CurrentUser
from app.schemas.physical_archive import (
    ArchiveLocationContentsResponse,
    ArchiveLocationCreate,
    ArchiveLocationResponse,
    ArchiveRoomCreate,
    ArchiveRoomResponse,
    PhysicalFileCheckoutCreate,
    PhysicalFileCreate,
    PhysicalFileLabelResponse,
    PhysicalFileMoveCreate,
    PhysicalFileResponse,
    PhysicalFileReturnCreate,
    PhysicalFileVerificationCreate,
)
from app.services.physical_archive import PhysicalArchiveError, PhysicalArchiveService

router = APIRouter(prefix="/v1", tags=["physical archive"])

AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
ArchiveReadUser = Annotated[
    CurrentUser,
    Depends(require_any_permission({"archive.view", "archive.manage"})),
]
ArchiveManageUser = Annotated[CurrentUser, Depends(require_permission("archive.manage"))]
PhysicalCheckoutUser = Annotated[
    CurrentUser,
    Depends(require_permission("physical_file.checkout")),
]
PhysicalArchiveServiceDep = Annotated[
    PhysicalArchiveService,
    Depends(get_physical_archive_service),
]


@router.get("/archive/rooms", response_model=list[ArchiveRoomResponse])
async def list_archive_rooms(
    current_user: ArchiveReadUser,
    service: PhysicalArchiveServiceDep,
    include_inactive: bool = False,
) -> list[ArchiveRoomResponse]:
    try:
        return await service.list_rooms(
            current_user=current_user,
            include_inactive=include_inactive,
        )
    except PhysicalArchiveError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/archive/rooms",
    response_model=ArchiveRoomResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_archive_room(
    payload: ArchiveRoomCreate,
    request: Request,
    current_user: ArchiveManageUser,
    service: PhysicalArchiveServiceDep,
) -> ArchiveRoomResponse:
    try:
        return await service.create_room(
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except PhysicalArchiveError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/archive/locations",
    response_model=ArchiveLocationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_archive_location(
    payload: ArchiveLocationCreate,
    request: Request,
    current_user: ArchiveManageUser,
    service: PhysicalArchiveServiceDep,
) -> ArchiveLocationResponse:
    try:
        return await service.create_location(
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except PhysicalArchiveError as exc:
        raise _http_error(exc) from exc


@router.get("/archive/locations", response_model=list[ArchiveLocationResponse])
async def list_archive_locations(
    current_user: ArchiveReadUser,
    service: PhysicalArchiveServiceDep,
    room_id: Annotated[UUID, Query()],
    include_inactive: bool = False,
) -> list[ArchiveLocationResponse]:
    try:
        return await service.list_locations(
            current_user=current_user,
            room_id=room_id,
            include_inactive=include_inactive,
        )
    except PhysicalArchiveError as exc:
        raise _http_error(exc) from exc


@router.get(
    "/archive/locations/{location_id}/contents",
    response_model=ArchiveLocationContentsResponse,
)
async def get_archive_location_contents(
    location_id: UUID,
    current_user: ArchiveReadUser,
    service: PhysicalArchiveServiceDep,
) -> ArchiveLocationContentsResponse:
    try:
        return await service.get_location_contents(
            location_id=location_id,
            current_user=current_user,
        )
    except PhysicalArchiveError as exc:
        raise _http_error(exc) from exc


@router.get("/projects/{project_id}/physical-files", response_model=list[PhysicalFileResponse])
async def list_project_physical_files(
    project_id: UUID,
    current_user: AuthenticatedUser,
    service: PhysicalArchiveServiceDep,
) -> list[PhysicalFileResponse]:
    try:
        return await service.list_project_physical_files(
            project_id=project_id,
            current_user=current_user,
        )
    except PhysicalArchiveError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/projects/{project_id}/physical-files",
    response_model=PhysicalFileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_physical_file(
    project_id: UUID,
    payload: PhysicalFileCreate,
    request: Request,
    current_user: ArchiveManageUser,
    service: PhysicalArchiveServiceDep,
) -> PhysicalFileResponse:
    try:
        return await service.create_physical_file(
            project_id=project_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except PhysicalArchiveError as exc:
        raise _http_error(exc) from exc


@router.get("/physical-files/{physical_file_id}", response_model=PhysicalFileResponse)
async def get_physical_file(
    physical_file_id: UUID,
    current_user: ArchiveReadUser,
    service: PhysicalArchiveServiceDep,
) -> PhysicalFileResponse:
    try:
        return await service.get_physical_file(
            physical_file_id=physical_file_id,
            current_user=current_user,
        )
    except PhysicalArchiveError as exc:
        raise _http_error(exc) from exc


@router.get("/physical-files/by-qr/{qr_token}", response_model=PhysicalFileResponse)
async def get_physical_file_by_qr_token(
    qr_token: UUID,
    current_user: ArchiveReadUser,
    service: PhysicalArchiveServiceDep,
) -> PhysicalFileResponse:
    try:
        return await service.get_physical_file_by_qr_token(
            qr_token=qr_token,
            current_user=current_user,
        )
    except PhysicalArchiveError as exc:
        raise _http_error(exc) from exc


@router.post("/physical-files/{physical_file_id}/checkout", response_model=PhysicalFileResponse)
async def checkout_physical_file(
    physical_file_id: UUID,
    payload: PhysicalFileCheckoutCreate,
    request: Request,
    current_user: PhysicalCheckoutUser,
    service: PhysicalArchiveServiceDep,
) -> PhysicalFileResponse:
    try:
        return await service.checkout_physical_file(
            physical_file_id=physical_file_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except PhysicalArchiveError as exc:
        raise _http_error(exc) from exc


@router.post("/physical-files/{physical_file_id}/return", response_model=PhysicalFileResponse)
async def return_physical_file(
    physical_file_id: UUID,
    payload: PhysicalFileReturnCreate,
    request: Request,
    current_user: ArchiveManageUser,
    service: PhysicalArchiveServiceDep,
) -> PhysicalFileResponse:
    try:
        return await service.return_physical_file(
            physical_file_id=physical_file_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except PhysicalArchiveError as exc:
        raise _http_error(exc) from exc


@router.post("/physical-files/{physical_file_id}/move", response_model=PhysicalFileResponse)
async def move_physical_file(
    physical_file_id: UUID,
    payload: PhysicalFileMoveCreate,
    request: Request,
    current_user: ArchiveManageUser,
    service: PhysicalArchiveServiceDep,
) -> PhysicalFileResponse:
    try:
        return await service.move_physical_file(
            physical_file_id=physical_file_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except PhysicalArchiveError as exc:
        raise _http_error(exc) from exc


@router.post("/physical-files/{physical_file_id}/verify", response_model=PhysicalFileResponse)
async def verify_physical_file(
    physical_file_id: UUID,
    payload: PhysicalFileVerificationCreate,
    request: Request,
    current_user: ArchiveManageUser,
    service: PhysicalArchiveServiceDep,
) -> PhysicalFileResponse:
    try:
        return await service.verify_physical_file(
            physical_file_id=physical_file_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except PhysicalArchiveError as exc:
        raise _http_error(exc) from exc


@router.get("/physical-files/{physical_file_id}/label", response_model=PhysicalFileLabelResponse)
async def get_physical_file_label(
    physical_file_id: UUID,
    current_user: ArchiveReadUser,
    service: PhysicalArchiveServiceDep,
) -> PhysicalFileLabelResponse:
    try:
        return await service.get_physical_file_label(
            physical_file_id=physical_file_id,
            current_user=current_user,
        )
    except PhysicalArchiveError as exc:
        raise _http_error(exc) from exc


def _http_error(exc: PhysicalArchiveError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "code": exc.code,
            "message": exc.message,
        },
    )
