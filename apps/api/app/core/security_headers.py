from collections.abc import Awaitable, Callable

from fastapi import Request, Response

from app.core.config import Settings

RequestHandler = Callable[[Request], Awaitable[Response]]

API_CONTENT_SECURITY_POLICY = (
    "default-src 'none'; "
    "frame-ancestors 'none'; "
    "base-uri 'none'; "
    "form-action 'none'"
)


def security_headers_middleware(
    settings: Settings,
) -> Callable[[Request, RequestHandler], Awaitable[Response]]:
    async def middleware(request: Request, call_next: RequestHandler) -> Response:
        response = await call_next(request)

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "0")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), payment=()",
        )
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        if _should_add_api_csp(request, settings):
            response.headers.setdefault("Content-Security-Policy", API_CONTENT_SECURITY_POLICY)
        if _is_https_request(request) and settings.app_env.lower() not in {
            "development",
            "local",
            "test",
        }:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")

        return response

    return middleware


def _should_add_api_csp(request: Request, settings: Settings) -> bool:
    if not settings.expose_api_docs:
        return True
    return request.url.path not in {"/docs", "/redoc", "/openapi.json"}


def _is_https_request(request: Request) -> bool:
    return request.url.scheme == "https" or request.headers.get("X-Forwarded-Proto") == "https"
