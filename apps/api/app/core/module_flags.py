from collections.abc import Awaitable, Callable
from re import Pattern, compile
from uuid import uuid4

from fastapi import Request, Response

from app.core.config import Settings, get_settings
from app.core.errors import error_response

RequestHandler = Callable[[Request], Awaitable[Response]]


MODULE_DISABLED_MESSAGE = "This module is not enabled for this rollout."


MODULE_PATH_RULES: tuple[tuple[str, tuple[str, ...], tuple[Pattern[str], ...]], ...] = (
    (
        "physical_archive",
        ("GET", "POST", "PATCH"),
        (
            compile(r"^/v1/archive/(rooms|locations)(/.*)?$"),
            compile(r"^/v1/physical-files(/.*)?$"),
            compile(r"^/v1/projects/[^/]+/physical-files(/.*)?$"),
        ),
    ),
    (
        "archive_exports",
        ("GET", "POST"),
        (
            compile(r"^/v1/projects/[^/]+/exports$"),
            compile(r"^/v1/exports(/.*)?$"),
        ),
    ),
    (
        "documents",
        ("GET", "POST", "PATCH", "DELETE"),
        (
            compile(r"^/v1/projects/[^/]+/folders(/.*)?$"),
            compile(r"^/v1/folders(/.*)?$"),
            compile(r"^/v1/documents(/.*)?$"),
            compile(r"^/v1/document-versions(/.*)?$"),
            compile(r"^/v1/confidentiality-levels$"),
            compile(r"^/v1/document-types$"),
        ),
    ),
    (
        "attendance",
        ("GET", "POST", "PATCH"),
        (
            compile(r"^/v1/attendance(/.*)?$"),
            compile(r"^/v1/director/attendance$"),
        ),
    ),
    (
        "leave",
        ("GET", "POST"),
        (
            compile(r"^/v1/leave-types$"),
            compile(r"^/v1/leave-requests(/.*)?$"),
        ),
    ),
    (
        "tasks",
        ("GET", "POST", "PATCH"),
        (
            compile(r"^/v1/task-statuses$"),
            compile(r"^/v1/tasks(/.*)?$"),
        ),
    ),
    (
        "calendar",
        ("GET", "POST", "PATCH"),
        (compile(r"^/v1/calendar(/.*)?$"),),
    ),
    (
        "approvals",
        ("GET", "POST"),
        (
            compile(r"^/v1/approval-types$"),
            compile(r"^/v1/approvals(/.*)?$"),
        ),
    ),
    (
        "director_dashboard",
        ("GET",),
        (compile(r"^/v1/director(/.*)?$"),),
    ),
    (
        "admin",
        ("GET", "POST", "PATCH", "DELETE"),
        (
            compile(r"^/v1/departments$"),
            compile(r"^/v1/roles$"),
            compile(r"^/v1/policies(/.*)?$"),
            compile(r"^/v1/audit-events$"),
            compile(r"^/v1/folder-templates(/.*)?$"),
            compile(r"^/v1/folder-template-items(/.*)?$"),
            compile(r"^/v1/employees/[^/]+(/.*)?$"),
        ),
    ),
    (
        "admin",
        ("POST",),
        (compile(r"^/v1/employees$"),),
    ),
    (
        "projects",
        ("GET", "POST", "PATCH", "DELETE"),
        (
            compile(r"^/v1/clients(/.*)?$"),
            compile(r"^/v1/projects(/.*)?$"),
            compile(r"^/v1/project-types$"),
            compile(r"^/v1/project-statuses$"),
            compile(r"^/v1/priority-levels$"),
        ),
    ),
)


async def module_gate_middleware(request: Request, call_next: RequestHandler) -> Response:
    module_name = module_for_request(request.method, request.url.path)
    if module_name is None:
        return await call_next(request)

    settings = _settings_for_request(request)
    if settings.module_flags[module_name]:
        return await call_next(request)

    request_id = _request_id(request)
    return error_response(
        status_code=403,
        code="MODULE_DISABLED",
        message=MODULE_DISABLED_MESSAGE,
        request_id=request_id,
    )


def module_for_request(method: str, path: str) -> str | None:
    if path == "/v1/modules":
        return None

    normalized_method = method.upper()
    for module_name, methods, patterns in MODULE_PATH_RULES:
        if normalized_method not in methods:
            continue
        if any(pattern.match(path) for pattern in patterns):
            return module_name
    return None


def _settings_for_request(request: Request) -> Settings:
    settings = getattr(request.app.state, "settings", None)
    if isinstance(settings, Settings):
        return settings
    return get_settings()


def _request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")
    if request_id is None:
        request_id = str(uuid4())
        request.state.request_id = request_id
    return str(request_id)
