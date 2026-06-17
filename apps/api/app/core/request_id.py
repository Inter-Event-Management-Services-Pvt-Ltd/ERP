from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response

from app.core.supabase_http import reset_current_request_id, set_current_request_id

RequestHandler = Callable[[Request], Awaitable[Response]]


async def request_id_middleware(request: Request, call_next: RequestHandler) -> Response:
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    request_id_token = set_current_request_id(request_id)

    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        reset_current_request_id(request_id_token)
