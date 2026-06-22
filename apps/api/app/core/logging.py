import json
import logging
import sys
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from time import perf_counter

from fastapi import Request, Response

RequestHandler = Callable[[Request], Awaitable[Response]]

ACCESS_LOGGER_NAME = "iems.api.access"


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in (
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "client_ip",
            "supabase_host",
            "query_keys",
            "has_body",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, separators=(",", ":"))


def configure_logging(log_level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(_log_level(log_level))

    logging.getLogger("httpx").setLevel(logging.NOTSET)
    logging.getLogger("httpcore").setLevel(logging.NOTSET)


async def structured_access_log_middleware(
    request: Request,
    call_next: RequestHandler,
) -> Response:
    started_at = perf_counter()
    logger = logging.getLogger(ACCESS_LOGGER_NAME)
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request_failed",
            extra=_request_log_extra(request, 500, started_at),
        )
        raise

    logger.info(
        "request_completed",
        extra=_request_log_extra(request, response.status_code, started_at),
    )
    return response


def _request_log_extra(
    request: Request,
    status_code: int,
    started_at: float,
) -> dict[str, object]:
    request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")
    return {
        "request_id": str(request_id) if request_id is not None else None,
        "method": request.method,
        "path": request.url.path,
        "status_code": status_code,
        "duration_ms": round((perf_counter() - started_at) * 1000, 2),
        "client_ip": request.client.host if request.client is not None else None,
    }


def _log_level(raw_level: str) -> int:
    level = logging.getLevelName(raw_level.upper())
    if isinstance(level, int):
        return level
    return logging.INFO
