from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.me import router as me_router
from app.core.config import get_settings
from app.core.errors import http_exception_handler, validation_exception_handler
from app.core.request_id import request_id_middleware

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.middleware("http")(request_id_middleware)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.include_router(me_router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "iems-erp-api",
        "version": settings.app_version,
    }


@app.get("/ready", tags=["health"])
async def ready() -> dict[str, dict[str, str] | str]:
    return {
        "status": "ready",
        "checks": {
            "api": "ok",
        },
    }
