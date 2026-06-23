import asyncio

import pytest
from httpx import ASGITransport, AsyncClient, Response

from app.core.config import Settings
from app.core.rate_limit import InMemoryRateLimitStore, RateLimiter
from app.main import app


@pytest.fixture(autouse=True)
def reset_rate_limiter_state() -> None:
    install_test_rate_limiter()


async def _get(path: str, headers: dict[str, str] | None = None) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path, headers=headers)


async def _options(path: str, headers: dict[str, str] | None = None) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.options(path, headers=headers)


def get(path: str, headers: dict[str, str] | None = None) -> Response:
    return asyncio.run(_get(path, headers=headers))


def options(path: str, headers: dict[str, str] | None = None) -> Response:
    return asyncio.run(_options(path, headers=headers))


def install_test_rate_limiter(
    *,
    default_requests: int = 120,
    auth_requests: int = 30,
    trust_proxy_headers: bool = True,
) -> None:
    settings = Settings(
        RATE_LIMIT_DEFAULT_REQUESTS=default_requests,
        RATE_LIMIT_AUTH_REQUESTS=auth_requests,
        RATE_LIMIT_TRUST_PROXY_HEADERS=trust_proxy_headers,
    )
    app.state.settings = settings
    app.state.rate_limiter = RateLimiter(settings=settings, store=InMemoryRateLimitStore())


def test_rate_limiter_returns_stable_429_envelope() -> None:
    install_test_rate_limiter(auth_requests=1)

    first = get("/v1/me", headers={"X-Request-ID": "rl-one", "CF-Connecting-IP": "203.0.113.10"})
    second = get("/v1/me", headers={"X-Request-ID": "rl-two", "CF-Connecting-IP": "203.0.113.10"})

    assert first.status_code == 401
    assert first.headers["X-RateLimit-Policy"] == "auth"
    assert second.status_code == 429
    assert second.headers["X-Request-ID"] == "rl-two"
    assert second.headers["Retry-After"].isdigit()
    assert second.headers["X-RateLimit-Limit"] == "1"
    assert second.headers["X-RateLimit-Remaining"] == "0"
    assert second.headers["X-RateLimit-Policy"] == "auth"
    assert second.json() == {
        "error": {
            "code": "RATE_LIMIT_EXCEEDED",
            "message": "Too many requests. Please retry after the rate-limit window resets.",
            "request_id": "rl-two",
        }
    }


def test_rate_limiter_uses_forwarded_client_ip_when_trusted() -> None:
    install_test_rate_limiter(auth_requests=1)

    first = get("/v1/me", headers={"CF-Connecting-IP": "203.0.113.11"})
    second = get("/v1/me", headers={"CF-Connecting-IP": "203.0.113.12"})

    assert first.status_code == 401
    assert second.status_code == 401


def test_rate_limiter_exempts_health_and_options() -> None:
    install_test_rate_limiter(default_requests=1)

    assert get("/health").status_code == 200
    assert get("/health").status_code == 200

    response = options(
        "/v1/projects",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,x-request-id",
        },
    )

    assert response.status_code == 200
    assert "X-RateLimit-Limit" not in response.headers


def test_api_responses_include_security_headers() -> None:
    install_test_rate_limiter()

    response = get("/health", headers={"X-Forwarded-Proto": "https"})

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "0"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert response.headers["Permissions-Policy"] == (
        "camera=(), microphone=(), geolocation=(), payment=()"
    )
    assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert response.headers["Content-Security-Policy"] == (
        "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
    )
