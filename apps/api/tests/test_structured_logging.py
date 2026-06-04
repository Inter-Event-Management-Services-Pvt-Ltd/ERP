import asyncio
import json
import logging

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.logging import JsonLogFormatter, structured_access_log_middleware
from app.core.request_id import request_id_middleware


def test_json_log_formatter_emits_structured_record() -> None:
    record = logging.LogRecord(
        name="iems.api.access",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="request_completed",
        args=(),
        exc_info=None,
    )
    record.request_id = "phase1-request"
    record.method = "GET"
    record.path = "/health"
    record.status_code = 200

    payload = json.loads(JsonLogFormatter().format(record))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "iems.api.access"
    assert payload["message"] == "request_completed"
    assert payload["request_id"] == "phase1-request"
    assert payload["method"] == "GET"
    assert payload["path"] == "/health"
    assert payload["status_code"] == 200
    assert "authorization" not in payload


def test_structured_access_log_middleware_logs_request_id(caplog: pytest.LogCaptureFixture) -> None:
    app = FastAPI()
    app.middleware("http")(request_id_middleware)
    app.middleware("http")(structured_access_log_middleware)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    async def run_request() -> None:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/health", headers={"X-Request-ID": "phase1-log-id"})
            assert response.status_code == 200

    with caplog.at_level(logging.INFO, logger="iems.api.access"):
        asyncio.run(run_request())

    matching = [
        record
        for record in caplog.records
        if record.name == "iems.api.access" and record.getMessage() == "request_completed"
    ]
    assert len(matching) == 1
    assert matching[0].request_id == "phase1-log-id"
    assert matching[0].method == "GET"
    assert matching[0].path == "/health"
    assert matching[0].status_code == 200
