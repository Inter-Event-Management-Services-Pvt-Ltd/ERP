from typing import Annotated

from fastapi import Depends, Header, HTTPException

from app.core.auth import AuthError, SupabaseJwtVerifier, parse_bearer_token
from app.core.config import get_settings
from app.core.current_user import CurrentUserError, SupabaseCurrentUserResolver
from app.core.rbac import AuthorizationError, RBACService
from app.schemas.current_user import CurrentUser


async def get_current_user(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> CurrentUser:
    try:
        token = parse_bearer_token(authorization)
        settings = get_settings()
        claims = SupabaseJwtVerifier.from_settings(settings).verify(token)
        return await SupabaseCurrentUserResolver.from_settings(settings).resolve(claims)
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
