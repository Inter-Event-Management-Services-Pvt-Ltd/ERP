from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)

from app.api.dependencies import (
    get_documents_archive_service,
    require_any_permission,
    require_permission,
)
from app.core.audit import audit_context_from_request
from app.schemas.clients_projects import ReferenceSummary
from app.schemas.current_user import CurrentUser
from app.schemas.documents_archive import (
    ArchiveExportCreate,
    ArchiveExportResponse,
    DocumentResponse,
    FolderCreate,
    FolderResponse,
    FolderUpdate,
    SignedUrlResponse,
)
from app.services.documents_archive import DocumentsArchiveError, DocumentsArchiveService

router = APIRouter(prefix="/v1", tags=["documents and archive exports"])

DocumentReadUser = Annotated[
    CurrentUser,
    Depends(require_any_permission({"document.view", "document.download", "document.upload"})),
]
DocumentUploadUser = Annotated[CurrentUser, Depends(require_permission("document.upload"))]
DocumentDownloadUser = Annotated[CurrentUser, Depends(require_permission("document.download"))]
ArchiveExportUser = Annotated[CurrentUser, Depends(require_permission("archive.export"))]
ArchiveReadUser = Annotated[
    CurrentUser,
    Depends(require_any_permission({"archive.export", "archive.view"})),
]
DocumentsArchiveServiceDep = Annotated[
    DocumentsArchiveService,
    Depends(get_documents_archive_service),
]


@router.post(
    "/projects/{project_id}/folders",
    response_model=FolderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_folder(
    project_id: UUID,
    payload: FolderCreate,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_permission("project.manage"))],
    service: DocumentsArchiveServiceDep,
) -> FolderResponse:
    try:
        return await service.create_folder(
            project_id=project_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except DocumentsArchiveError as exc:
        raise _http_error(exc) from exc


@router.patch("/folders/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: UUID,
    payload: FolderUpdate,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_permission("project.manage"))],
    service: DocumentsArchiveServiceDep,
) -> FolderResponse:
    try:
        return await service.update_folder(
            folder_id=folder_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except DocumentsArchiveError as exc:
        raise _http_error(exc) from exc


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(require_permission("project.manage"))],
    service: DocumentsArchiveServiceDep,
) -> Response:
    try:
        await service.delete_folder(
            folder_id=folder_id,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except DocumentsArchiveError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/folders/{folder_id}/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    folder_id: UUID,
    request: Request,
    current_user: DocumentUploadUser,
    service: DocumentsArchiveServiceDep,
    file: Annotated[UploadFile, File()],
    confidentiality_level_id: Annotated[UUID, Form()],
    document_type_id: Annotated[UUID | None, Form()] = None,
    display_name: Annotated[str | None, Form(max_length=255)] = None,
    change_note: Annotated[str | None, Form()] = None,
) -> DocumentResponse:
    try:
        content = await file.read()
        return await service.upload_document(
            folder_id=folder_id,
            filename=file.filename or "",
            mime_type=file.content_type or "application/octet-stream",
            content=content,
            display_name=display_name,
            document_type_id=document_type_id,
            confidentiality_level_id=confidentiality_level_id,
            change_note=change_note,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except DocumentsArchiveError as exc:
        raise _http_error(exc) from exc


@router.get("/documents/search", response_model=list[DocumentResponse])
async def search_documents(
    current_user: DocumentReadUser,
    service: DocumentsArchiveServiceDep,
    project_id: UUID | None = None,
    folder_id: UUID | None = None,
    search: Annotated[str | None, Query(min_length=1, max_length=150)] = None,
    q: Annotated[str | None, Query(min_length=1, max_length=150)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DocumentResponse]:
    try:
        return await service.search_documents(
            current_user=current_user,
            project_id=project_id,
            folder_id=folder_id,
            search=search or q,
            limit=limit,
            offset=offset,
        )
    except DocumentsArchiveError as exc:
        raise _http_error(exc) from exc


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    current_user: DocumentReadUser,
    service: DocumentsArchiveServiceDep,
) -> DocumentResponse:
    try:
        return await service.get_document(document_id=document_id, current_user=current_user)
    except DocumentsArchiveError as exc:
        raise _http_error(exc) from exc


@router.post("/documents/{document_id}/versions", response_model=DocumentResponse)
async def create_document_version(
    document_id: UUID,
    request: Request,
    current_user: DocumentUploadUser,
    service: DocumentsArchiveServiceDep,
    file: Annotated[UploadFile, File()],
    change_note: Annotated[str | None, Form()] = None,
) -> DocumentResponse:
    try:
        content = await file.read()
        return await service.create_document_version(
            document_id=document_id,
            filename=file.filename or "",
            mime_type=file.content_type or "application/octet-stream",
            content=content,
            change_note=change_note,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except DocumentsArchiveError as exc:
        raise _http_error(exc) from exc


@router.get("/document-versions/{version_id}/download-url", response_model=SignedUrlResponse)
async def get_document_version_download_url(
    version_id: UUID,
    request: Request,
    current_user: DocumentDownloadUser,
    service: DocumentsArchiveServiceDep,
) -> SignedUrlResponse:
    try:
        return await service.get_document_version_download_url(
            version_id=version_id,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except DocumentsArchiveError as exc:
        raise _http_error(exc) from exc


@router.get("/confidentiality-levels", response_model=list[ReferenceSummary])
async def list_confidentiality_levels(
    current_user: DocumentReadUser,
    service: DocumentsArchiveServiceDep,
) -> list[ReferenceSummary]:
    try:
        return await service.list_confidentiality_levels(current_user=current_user)
    except DocumentsArchiveError as exc:
        raise _http_error(exc) from exc


@router.get("/document-types", response_model=list[ReferenceSummary])
async def list_document_types(
    current_user: DocumentReadUser,
    service: DocumentsArchiveServiceDep,
) -> list[ReferenceSummary]:
    try:
        return await service.list_document_types(current_user=current_user)
    except DocumentsArchiveError as exc:
        raise _http_error(exc) from exc


@router.post(
    "/projects/{project_id}/exports",
    response_model=ArchiveExportResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_archive_export(
    project_id: UUID,
    payload: ArchiveExportCreate,
    request: Request,
    current_user: ArchiveExportUser,
    service: DocumentsArchiveServiceDep,
) -> ArchiveExportResponse:
    try:
        return await service.create_archive_export(
            project_id=project_id,
            payload=payload,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except DocumentsArchiveError as exc:
        raise _http_error(exc) from exc


@router.get("/projects/{project_id}/exports", response_model=list[ArchiveExportResponse])
async def list_archive_exports(
    project_id: UUID,
    current_user: ArchiveReadUser,
    service: DocumentsArchiveServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ArchiveExportResponse]:
    try:
        return await service.list_archive_exports(
            project_id=project_id,
            current_user=current_user,
            limit=limit,
            offset=offset,
        )
    except DocumentsArchiveError as exc:
        raise _http_error(exc) from exc


@router.get("/exports/{export_id}", response_model=ArchiveExportResponse)
async def get_archive_export(
    export_id: UUID,
    current_user: ArchiveReadUser,
    service: DocumentsArchiveServiceDep,
) -> ArchiveExportResponse:
    try:
        return await service.get_archive_export(export_id=export_id, current_user=current_user)
    except DocumentsArchiveError as exc:
        raise _http_error(exc) from exc


@router.get("/exports/{export_id}/download-url", response_model=SignedUrlResponse)
async def get_archive_export_download_url(
    export_id: UUID,
    current_user: ArchiveReadUser,
    service: DocumentsArchiveServiceDep,
) -> SignedUrlResponse:
    try:
        return await service.get_archive_export_download_url(
            export_id=export_id,
            current_user=current_user,
        )
    except DocumentsArchiveError as exc:
        raise _http_error(exc) from exc


@router.post("/exports/{export_id}/cancel", response_model=ArchiveExportResponse)
async def cancel_archive_export(
    export_id: UUID,
    request: Request,
    current_user: ArchiveExportUser,
    service: DocumentsArchiveServiceDep,
) -> ArchiveExportResponse:
    try:
        return await service.cancel_archive_export(
            export_id=export_id,
            current_user=current_user,
            context=audit_context_from_request(request),
        )
    except DocumentsArchiveError as exc:
        raise _http_error(exc) from exc


def _http_error(exc: DocumentsArchiveError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={
            "code": exc.code,
            "message": exc.message,
        },
    )
