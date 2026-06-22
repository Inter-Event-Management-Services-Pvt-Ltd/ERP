from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class RouteSpec:
    label: str
    path: str


def route_specs() -> list[RouteSpec]:
    return [
        RouteSpec("me", "/v1/me"),
        RouteSpec("projects", "/v1/projects"),
        RouteSpec("archive_rooms", "/v1/archive/rooms"),
        RouteSpec("tasks", "/v1/tasks"),
        RouteSpec("approvals", "/v1/approvals"),
        RouteSpec("director_overview", "/v1/director/overview"),
        RouteSpec("audit_events", "/v1/audit-events"),
    ]


async def main() -> int:
    base_url = os.environ.get("IEMS_API_BASE_URL", "http://localhost:8000").rstrip("/")
    token = os.environ.get("IEMS_ACCESS_TOKEN")
    if not token:
        raise SystemExit("Set IEMS_ACCESS_TOKEN before running the performance probe.")

    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=20.0) as client:
        for spec in route_specs():
            started = time.perf_counter()
            response = await client.get(f"{base_url}{spec.path}", headers=headers)
            duration_ms = (time.perf_counter() - started) * 1000
            print(
                f"{spec.label} {response.status_code} "
                f"{duration_ms:.2f}ms request_id={response.headers.get('X-Request-ID')}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
