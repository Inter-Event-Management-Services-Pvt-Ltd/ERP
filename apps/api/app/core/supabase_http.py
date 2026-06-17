import logging
from contextvars import ContextVar, Token
from time import perf_counter

import httpx
from fastapi import Request

from app.core.config import Settings

SUPABASE_LOGGER_NAME = "iems.api.supabase"
_request_id_var: ContextVar[str | None] = ContextVar("iems_request_id", default=None)


def set_current_request_id(request_id: str) -> Token[str | None]:
    return _request_id_var.set(request_id)


def reset_current_request_id(token: Token[str | None]) -> None:
    _request_id_var.reset(token)


def create_supabase_http_client(settings: Settings) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=settings.supabase_request_timeout_seconds,
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
    )


def get_supabase_http_client(request: Request, settings: Settings) -> httpx.AsyncClient:
    client = getattr(request.app.state, "supabase_http_client", None)
    if isinstance(client, httpx.AsyncClient):
        return client

    client = create_supabase_http_client(settings)
    request.app.state.supabase_http_client = client
    return client


async def request_supabase(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    params: dict[str, str] | None = None,
    json_body: dict[str, object] | None = None,
    content: bytes | None = None,
    request_id: str | None = None,
) -> httpx.Response:
    started_at = perf_counter()
    logger = logging.getLogger(SUPABASE_LOGGER_NAME)
    effective_request_id = request_id or _request_id_var.get()
    try:
        response = await client.request(
            method,
            url,
            headers=headers,
            params=params,
            json=json_body,
            content=content,
        )
    except Exception:
        logger.exception(
            "supabase_request_failed",
            extra=_supabase_log_extra(
                method=method,
                url=url,
                status_code=0,
                started_at=started_at,
                request_id=effective_request_id,
                params=params,
                has_body=json_body is not None or content is not None,
            ),
        )
        raise

    logger.info(
        "supabase_request_completed",
        extra=_supabase_log_extra(
            method=method,
            url=url,
            status_code=response.status_code,
            started_at=started_at,
            request_id=effective_request_id,
            params=params,
            has_body=json_body is not None or content is not None,
        ),
    )
    return response


def _supabase_log_extra(
    *,
    method: str,
    url: str,
    status_code: int,
    started_at: float,
    request_id: str | None,
    params: dict[str, str] | None,
    has_body: bool,
) -> dict[str, object]:
    parsed_url = httpx.URL(url)
    return {
        "request_id": request_id,
        "method": method,
        "path": parsed_url.path,
        "supabase_host": parsed_url.host,
        "status_code": status_code,
        "duration_ms": round((perf_counter() - started_at) * 1000, 2),
        "query_keys": sorted(params) if params else None,
        "has_body": has_body,
    }
