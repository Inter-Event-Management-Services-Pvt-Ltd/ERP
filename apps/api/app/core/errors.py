from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette import status
from starlette.exceptions import HTTPException as StarletteHTTPException


def error_response(
    status_code: int,
    code: str,
    message: str,
    request_id: str,
    fields: list[dict[str, str]] | None = None,
) -> JSONResponse:
    error: dict[str, object] = {
        "code": code,
        "message": message,
        "request_id": request_id,
    }
    if fields:
        error["fields"] = fields

    return JSONResponse(
        status_code=status_code,
        content={"error": error},
        headers={"X-Request-ID": request_id},
    )


def _request_id(request: Request) -> str:
    return str(request.state.request_id)


def _detail_value(detail: Any, key: str, default: str) -> str:
    if isinstance(detail, dict):
        value = detail.get(key)
        if isinstance(value, str):
            return value
    return default


async def http_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, StarletteHTTPException):
        raise exc

    request_id = _request_id(request)
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        return error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message="Route not found",
            request_id=request_id,
        )

    return error_response(
        status_code=exc.status_code,
        code=_detail_value(exc.detail, "code", "HTTP_ERROR"),
        message=_detail_value(exc.detail, "message", "HTTP error"),
        request_id=request_id,
    )


async def validation_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    if not isinstance(exc, RequestValidationError):
        raise exc

    return error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        code="VALIDATION_ERROR",
        message="Request validation failed",
        request_id=_request_id(request),
        fields=_validation_fields(exc),
    )


def _validation_fields(exc: RequestValidationError) -> list[dict[str, str]]:
    fields: list[dict[str, str]] = []
    for error in exc.errors():
        loc = error.get("loc")
        message = error.get("msg")
        error_type = error.get("type")
        if not isinstance(loc, tuple) or not isinstance(message, str) or not isinstance(
            error_type,
            str,
        ):
            continue
        fields.append(
            {
                "field": ".".join(str(part) for part in loc),
                "message": message,
                "type": error_type,
            }
        )
    return fields
