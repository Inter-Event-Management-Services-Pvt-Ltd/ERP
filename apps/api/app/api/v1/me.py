from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_current_user
from app.core.abac import ABACResource, ABACService
from app.core.rbac import AuthorizationError
from app.schemas.current_user import CurrentUser, CurrentUserPermissions

router = APIRouter(prefix="/v1", tags=["current user"])

@router.get("/me", response_model=CurrentUser)
async def read_current_user(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    return current_user


@router.get("/me/permissions", response_model=CurrentUserPermissions)
async def read_current_user_permissions(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
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
