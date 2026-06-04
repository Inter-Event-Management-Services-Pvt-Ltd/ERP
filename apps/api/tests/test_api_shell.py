import asyncio

from httpx import ASGITransport, AsyncClient, Response

from app.main import app


async def _get(path: str, headers: dict[str, str] | None = None) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path, headers=headers)


def get(path: str, headers: dict[str, str] | None = None) -> Response:
    return asyncio.run(_get(path, headers=headers))


def test_health_endpoint_returns_service_status() -> None:
    response = get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "iems-erp-api",
        "version": "0.1.0",
    }


def test_readiness_endpoint_returns_api_check() -> None:
    response = get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {
            "api": "ok",
        },
    }


def test_protected_me_endpoint_requires_authorization() -> None:
    response = get("/v1/me", headers={"X-Request-ID": "phase1-test-request"})

    assert response.status_code == 401
    assert response.headers["X-Request-ID"] == "phase1-test-request"
    assert response.json() == {
        "error": {
            "code": "AUTH_REQUIRED",
            "message": "Authentication required",
            "request_id": "phase1-test-request",
        }
    }


def test_unknown_route_uses_stable_error_envelope() -> None:
    response = get("/missing", headers={"X-Request-ID": "phase1-missing-route"})

    assert response.status_code == 404
    assert response.headers["X-Request-ID"] == "phase1-missing-route"
    assert response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Route not found",
            "request_id": "phase1-missing-route",
        }
    }
