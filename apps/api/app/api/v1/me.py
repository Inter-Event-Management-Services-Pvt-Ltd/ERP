from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, status

router = APIRouter(prefix="/v1", tags=["current user"])


@router.get("/me")
async def read_current_user(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> dict[str, str]:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_REQUIRED",
                "message": "Authentication required",
            },
        )

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "code": "AUTH_NOT_CONFIGURED",
            "message": "Supabase JWT verification is not configured yet",
        },
    )
