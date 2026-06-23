from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.admin import router as admin_router
from app.api.v1.approvals import router as approvals_router
from app.api.v1.attendance import router as attendance_router
from app.api.v1.clients_projects import router as clients_projects_router
from app.api.v1.director_dashboard import router as director_dashboard_router
from app.api.v1.documents_archive import router as documents_archive_router
from app.api.v1.employee_operations import router as employee_operations_router
from app.api.v1.employees import router as employees_router
from app.api.v1.me import router as me_router
from app.api.v1.physical_archive import router as physical_archive_router
from app.core.config import get_settings
from app.core.errors import http_exception_handler, validation_exception_handler
from app.core.logging import configure_logging, structured_access_log_middleware
from app.core.rate_limit import close_rate_limiter, create_rate_limiter, rate_limit_middleware
from app.core.request_id import request_id_middleware
from app.core.security_headers import security_headers_middleware
from app.core.supabase_http import create_supabase_http_client

settings = get_settings()
configure_logging(settings.log_level)

docs_url = "/docs" if settings.expose_api_docs else None
redoc_url = "/redoc" if settings.expose_api_docs else None
openapi_url = "/openapi.json" if settings.expose_api_docs else None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.settings = settings
    app.state.supabase_http_client = create_supabase_http_client(settings)
    app.state.rate_limiter = create_rate_limiter(settings)
    try:
        yield
    finally:
        await close_rate_limiter(app.state.rate_limiter)
        await app.state.supabase_http_client.aclose()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_allowed_origin_list),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.settings = settings
app.middleware("http")(request_id_middleware)
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(security_headers_middleware(settings))
app.middleware("http")(structured_access_log_middleware)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.include_router(admin_router)
app.include_router(approvals_router)
app.include_router(attendance_router)
app.include_router(clients_projects_router)
app.include_router(director_dashboard_router)
app.include_router(documents_archive_router)
app.include_router(employee_operations_router)
app.include_router(employees_router)
app.include_router(me_router)
app.include_router(physical_archive_router)


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
