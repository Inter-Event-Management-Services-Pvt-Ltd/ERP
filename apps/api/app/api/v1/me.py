from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import ValidationError

from app.api.dependencies import get_current_user
from app.core.abac import ABACResource, ABACService
from app.core.config import get_settings
from app.core.rbac import AuthorizationError
from app.core.supabase_http import get_supabase_http_client, request_supabase
from app.schemas.current_user import (
    CurrentUser,
    CurrentUserPermissions,
    NotificationResponse,
)

router = APIRouter(prefix="/v1", tags=["current user"])
AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]

@router.get("/me", response_model=CurrentUser)
async def read_current_user(
    current_user: AuthenticatedUser,
) -> CurrentUser:
    return current_user


@router.get("/me/permissions", response_model=CurrentUserPermissions)
async def read_current_user_permissions(
    current_user: AuthenticatedUser,
) -> CurrentUserPermissions:
    try:
        ABACService().require_access(
            current_user,
            "employee.profile.view_self",
            ABACResource(
                resource_type="employee_profile",
                attributes={"employee_id": str(current_user.employee.id)},
            ),
        )
    except AuthorizationError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc

    return CurrentUserPermissions(
        roles=current_user.roles,
        permissions=current_user.permissions,
        is_super_user=current_user.account.is_super_user,
        super_user_requires_reason=True,
    )


@router.get("/me/notifications", response_model=list[NotificationResponse])
async def list_current_user_notifications(
    request: Request,
    current_user: AuthenticatedUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[NotificationResponse]:
    settings = get_settings()
    supabase_url, service_role_key, client = _supabase_request_config(request, settings)
    response = await request_supabase(
        client,
        "GET",
        f"{supabase_url}/rest/v1/notifications",
        headers=_supabase_headers(service_role_key),
        params={
            "select": "*",
            "employee_id": f"eq.{current_user.employee.id}",
            "order": "created_at.desc",
            "limit": str(limit),
            "offset": str(offset),
        },
    )
    if response.status_code >= 300:
        raise _data_service_error()
    return _notification_list(response)


@router.patch(
    "/me/notifications/{notification_id}/read",
    response_model=NotificationResponse,
)
async def mark_current_user_notification_read(
    notification_id: UUID,
    request: Request,
    current_user: AuthenticatedUser,
) -> NotificationResponse:
    settings = get_settings()
    supabase_url, service_role_key, client = _supabase_request_config(request, settings)
    headers = _supabase_headers(service_role_key)
    headers["Prefer"] = "return=representation"
    response = await request_supabase(
        client,
        "PATCH",
        f"{supabase_url}/rest/v1/notifications",
        headers=headers,
        params={
            "select": "*",
            "id": f"eq.{notification_id}",
            "employee_id": f"eq.{current_user.employee.id}",
        },
        json_body={"read_at": datetime.now(tz=UTC).isoformat()},
    )
    if response.status_code == 404:
        raise _notification_not_found()
    if response.status_code >= 300:
        raise _data_service_error()

    rows = _notification_list(response)
    if not rows:
        raise _notification_not_found()
    return rows[0]


def _supabase_request_config(
    request: Request,
    settings: Any,
) -> tuple[str, str, httpx.AsyncClient]:
    supabase_url = settings.supabase_url
    service_role_key = settings.supabase_service_role_key
    if supabase_url is None or service_role_key is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATA_SERVICE_NOT_CONFIGURED",
                "message": "Supabase data service is not configured",
            },
        )
    return supabase_url.rstrip("/"), service_role_key, get_supabase_http_client(request, settings)


def _supabase_headers(service_role_key: str) -> dict[str, str]:
    headers = {
        "apikey": service_role_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if not service_role_key.startswith("sb_secret_"):
        headers["Authorization"] = f"Bearer {service_role_key}"
    return headers


def _notification_list(response: httpx.Response) -> list[NotificationResponse]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise _invalid_data_response() from exc
    if not isinstance(payload, list):
        raise _invalid_data_response()

    notifications: list[NotificationResponse] = []
    for item in payload:
        if not isinstance(item, dict):
            raise _invalid_data_response()
        try:
            notifications.append(NotificationResponse.model_validate(item))
        except ValidationError as exc:
            raise _invalid_data_response() from exc
    return notifications


def _notification_not_found() -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={
            "code": "NOT_FOUND",
            "message": "Notification not found",
        },
    )


def _invalid_data_response() -> HTTPException:
    return HTTPException(
        status_code=503,
        detail={
            "code": "DATA_SERVICE_INVALID_RESPONSE",
            "message": "Notification data service returned invalid data",
        },
    )


def _data_service_error() -> HTTPException:
    return HTTPException(
        status_code=503,
        detail={
            "code": "DATA_SERVICE_ERROR",
            "message": "Notification data service request failed",
        },
    )
