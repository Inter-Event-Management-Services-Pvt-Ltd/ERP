from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request

from app.core.audit import AuditWriteError, SupabaseAuditWriter, audit_context_from_request
from app.core.auth import AuthError, SupabaseJwtVerifier, parse_bearer_token
from app.core.config import get_settings
from app.core.current_user import CurrentUserError, SupabaseCurrentUserResolver
from app.core.rbac import AuthorizationError, RBACService
from app.core.supabase_http import get_supabase_http_client
from app.core.super_user import SuperUserOverrideService
from app.schemas.current_user import CurrentUser
from app.services.admin import AdminService
from app.services.approvals import ApprovalsService
from app.services.attendance import AttendanceService
from app.services.clients_projects import ClientsProjectsService
from app.services.director_dashboard import DirectorDashboardService
from app.services.documents_archive import DocumentsArchiveService
from app.services.employee_operations import EmployeeOperationsService
from app.services.employees import EmployeesService
from app.services.physical_archive import PhysicalArchiveService
from app.workers.archive_exports import enqueue_archive_export


async def get_current_user(
    request: Request,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> CurrentUser:
    try:
        token = parse_bearer_token(authorization)
        settings = get_settings()
        claims = SupabaseJwtVerifier.from_settings(settings).verify(token)
        if settings.supabase_url is None or settings.supabase_service_role_key is None:
            raise CurrentUserError(
                503,
                "AUTH_NOT_CONFIGURED",
                "Supabase employee resolver is not configured",
            )
        return await SupabaseCurrentUserResolver(
            supabase_url=settings.supabase_url,
            service_role_key=settings.supabase_service_role_key,
            timeout_seconds=settings.supabase_request_timeout_seconds,
            http_client=get_supabase_http_client(request, settings),
        ).resolve(claims)
    except (AuthError, CurrentUserError) as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc


def require_permission(permission_code: str) -> object:
    async def dependency(
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        try:
            RBACService().require_permission(current_user, permission_code)
            return current_user
        except AuthorizationError as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail={
                    "code": exc.code,
                    "message": exc.message,
                },
            ) from exc

    return dependency


def require_any_permission(permission_codes: set[str]) -> object:
    async def dependency(
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        rbac = RBACService()
        if any(
            rbac.has_permission(current_user, permission_code)
            for permission_code in permission_codes
        ):
            return current_user
        raise HTTPException(
            status_code=403,
            detail={
                "code": "PERMISSION_DENIED",
                "message": "Permission denied",
            },
        )

    return dependency


def get_clients_projects_service(request: Request) -> ClientsProjectsService:
    settings = get_settings()
    if settings.supabase_url is None or settings.supabase_service_role_key is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATA_SERVICE_NOT_CONFIGURED",
                "message": "Supabase data service is not configured",
            },
        )
    return ClientsProjectsService(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        timeout_seconds=settings.supabase_request_timeout_seconds,
        http_client=get_supabase_http_client(request, settings),
    )


def get_admin_service(request: Request) -> AdminService:
    settings = get_settings()
    if settings.supabase_url is None or settings.supabase_service_role_key is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATA_SERVICE_NOT_CONFIGURED",
                "message": "Supabase data service is not configured",
            },
        )
    return AdminService(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        timeout_seconds=settings.supabase_request_timeout_seconds,
        http_client=get_supabase_http_client(request, settings),
    )


def get_approvals_service(request: Request) -> ApprovalsService:
    settings = get_settings()
    if settings.supabase_url is None or settings.supabase_service_role_key is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATA_SERVICE_NOT_CONFIGURED",
                "message": "Supabase data service is not configured",
            },
        )
    return ApprovalsService(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        timeout_seconds=settings.supabase_request_timeout_seconds,
        http_client=get_supabase_http_client(request, settings),
    )


def get_employees_service(request: Request) -> EmployeesService:
    settings = get_settings()
    if settings.supabase_url is None or settings.supabase_service_role_key is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATA_SERVICE_NOT_CONFIGURED",
                "message": "Supabase data service is not configured",
            },
        )
    return EmployeesService(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        timeout_seconds=settings.supabase_request_timeout_seconds,
        http_client=get_supabase_http_client(request, settings),
    )


def get_documents_archive_service(request: Request) -> DocumentsArchiveService:
    settings = get_settings()
    if settings.supabase_url is None or settings.supabase_service_role_key is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATA_SERVICE_NOT_CONFIGURED",
                "message": "Supabase data service is not configured",
            },
        )
    return DocumentsArchiveService(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        timeout_seconds=settings.supabase_request_timeout_seconds,
        http_client=get_supabase_http_client(request, settings),
        signed_url_ttl_seconds=settings.signed_url_ttl_seconds,
        archive_export_ttl_hours=settings.archive_export_ttl_hours,
        max_upload_bytes=settings.max_upload_bytes,
        allowed_upload_mime_types=settings.allowed_upload_mime_type_set,
        project_documents_bucket=settings.project_documents_bucket,
        generated_archives_bucket=settings.generated_archives_bucket,
        enqueue_archive_export=enqueue_archive_export,
    )


def get_physical_archive_service(request: Request) -> PhysicalArchiveService:
    settings = get_settings()
    if settings.supabase_url is None or settings.supabase_service_role_key is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATA_SERVICE_NOT_CONFIGURED",
                "message": "Supabase data service is not configured",
            },
        )
    return PhysicalArchiveService(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        timeout_seconds=settings.supabase_request_timeout_seconds,
        http_client=get_supabase_http_client(request, settings),
    )


def get_attendance_service(request: Request) -> AttendanceService:
    settings = get_settings()
    if settings.supabase_url is None or settings.supabase_service_role_key is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATA_SERVICE_NOT_CONFIGURED",
                "message": "Supabase data service is not configured",
            },
        )
    return AttendanceService(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        timeout_seconds=settings.supabase_request_timeout_seconds,
        http_client=get_supabase_http_client(request, settings),
    )


def get_employee_operations_service(request: Request) -> EmployeeOperationsService:
    settings = get_settings()
    if settings.supabase_url is None or settings.supabase_service_role_key is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATA_SERVICE_NOT_CONFIGURED",
                "message": "Supabase data service is not configured",
            },
        )
    return EmployeeOperationsService(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        timeout_seconds=settings.supabase_request_timeout_seconds,
        http_client=get_supabase_http_client(request, settings),
    )


def get_director_dashboard_service(request: Request) -> DirectorDashboardService:
    settings = get_settings()
    if settings.supabase_url is None or settings.supabase_service_role_key is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATA_SERVICE_NOT_CONFIGURED",
                "message": "Supabase data service is not configured",
            },
        )
    return DirectorDashboardService(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        timeout_seconds=settings.supabase_request_timeout_seconds,
        http_client=get_supabase_http_client(request, settings),
    )


def get_audit_writer(request: Request) -> SupabaseAuditWriter:
    settings = get_settings()
    if settings.supabase_url is None or settings.supabase_service_role_key is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "AUDIT_NOT_CONFIGURED",
                "message": "Supabase audit writer is not configured",
            },
        )
    return SupabaseAuditWriter(
        supabase_url=settings.supabase_url,
        service_role_key=settings.supabase_service_role_key,
        timeout_seconds=settings.supabase_request_timeout_seconds,
        http_client=get_supabase_http_client(request, settings),
    )


def require_super_user_override(
    action_code: str,
    resource_type: str,
    resource_id_path_param: str,
) -> object:
    async def dependency(
        request: Request,
        current_user: Annotated[CurrentUser, Depends(get_current_user)],
        writer: Annotated[SupabaseAuditWriter, Depends(get_audit_writer)],
        override_reason: Annotated[
            str | None,
            Header(alias="X-IEMS-Override-Reason"),
        ] = None,
    ) -> UUID:
        resource_id = _resource_uuid_from_path(request, resource_id_path_param)
        try:
            return await SuperUserOverrideService().record_override(
                current_user=current_user,
                action_code=action_code,
                resource_type=resource_type,
                resource_id=resource_id,
                reason=override_reason,
                context=audit_context_from_request(request),
                writer=writer,
            )
        except AuthorizationError as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail={
                    "code": exc.code,
                    "message": exc.message,
                },
            ) from exc
        except AuditWriteError as exc:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "AUDIT_WRITE_FAILED",
                    "message": exc.message,
                },
            ) from exc

    return dependency


def _resource_uuid_from_path(request: Request, path_param: str) -> UUID:
    raw_value = request.path_params.get(path_param)
    if raw_value is None:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "ROUTE_CONFIGURATION_ERROR",
                "message": "Override resource path parameter is not configured",
            },
        )
    try:
        return UUID(str(raw_value))
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "Override resource id must be a UUID",
            },
        ) from exc
