from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user
from app.schemas.current_user import CurrentUser

router = APIRouter(prefix="/v1", tags=["current user"])

@router.get("/me", response_model=CurrentUser)
async def read_current_user(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    return current_user
