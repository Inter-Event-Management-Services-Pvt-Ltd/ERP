from fastapi import APIRouter, Request

from app.core.config import Settings, get_settings
from app.schemas.modules import ModuleStatusResponse

router = APIRouter(prefix="/v1", tags=["modules"])


@router.get("/modules", response_model=list[ModuleStatusResponse])
async def list_modules(request: Request) -> list[ModuleStatusResponse]:
    settings = getattr(request.app.state, "settings", None)
    if not isinstance(settings, Settings):
        settings = get_settings()
    return [
        ModuleStatusResponse(code=code, enabled=enabled)
        for code, enabled in settings.module_flags.items()
    ]
