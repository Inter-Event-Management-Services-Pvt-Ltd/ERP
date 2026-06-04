from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

import httpx
from fastapi import Request


class AuditWriteError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class AuditContext:
    request_id: UUID | None = None
    ip_address: str | None = None
    user_agent: str | None = None


@dataclass(frozen=True)
class AuditEvent:
    action_code: str
    resource_type: str
    actor_user_account_id: UUID | None = None
    actor_employee_id: UUID | None = None
    resource_id: UUID | None = None
    context: AuditContext = field(default_factory=AuditContext)
    old_values: dict[str, object] | None = None
    new_values: dict[str, object] | None = None
    metadata: dict[str, object] | None = None


class SupabaseAuditWriter:
    def __init__(
        self,
        *,
        supabase_url: str,
        service_role_key: str,
        timeout_seconds: float = 5.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._supabase_url = supabase_url.rstrip("/")
        self._service_role_key = service_role_key
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    async def write_event(self, event: AuditEvent) -> UUID:
        payload = _strip_none_values(
            {
                "actor_user_account_id": _uuid_or_none(event.actor_user_account_id),
                "actor_employee_id": _uuid_or_none(event.actor_employee_id),
                "action_code": event.action_code,
                "resource_type": event.resource_type,
                "resource_id": _uuid_or_none(event.resource_id),
                "request_id": _uuid_or_none(event.context.request_id),
                "old_values": event.old_values,
                "new_values": event.new_values,
                "metadata": event.metadata,
                "ip_address": event.context.ip_address,
                "user_agent": event.context.user_agent,
            }
        )
        response = await self._post(
            "/rest/v1/audit_events",
            json_body=payload,
            params={"select": "id"},
            prefer="return=representation",
        )
        payload_rows = _json_list(response, "audit event creation")
        if not payload_rows or not isinstance(payload_rows[0].get("id"), str):
            raise AuditWriteError("Audit event creation returned invalid payload")
        return UUID(payload_rows[0]["id"])

    async def record_super_user_override(
        self,
        *,
        user_account_id: UUID,
        actor_employee_id: UUID,
        action_code: str,
        resource_type: str,
        resource_id: UUID,
        reason: str,
        context: AuditContext,
        metadata: dict[str, object] | None = None,
    ) -> UUID:
        response = await self._post(
            "/rest/v1/rpc/record_super_user_override",
            json_body={
                "p_user_account_id": str(user_account_id),
                "p_actor_employee_id": str(actor_employee_id),
                "p_action_code": action_code,
                "p_resource_type": resource_type,
                "p_resource_id": str(resource_id),
                "p_reason": reason,
                "p_request_id": _uuid_or_none(context.request_id),
                "p_metadata": metadata or {},
                "p_ip_address": context.ip_address,
                "p_user_agent": context.user_agent,
            },
        )
        return _uuid_from_rpc_payload(response.json())

    async def _post(
        self,
        path: str,
        *,
        json_body: dict[str, Any],
        params: dict[str, str] | None = None,
        prefer: str | None = None,
    ) -> httpx.Response:
        headers = _supabase_headers(self._service_role_key)
        if prefer is not None:
            headers["Prefer"] = prefer
        async with httpx.AsyncClient(
            timeout=self._timeout_seconds,
            transport=self._transport,
        ) as client:
            response = await client.post(
                f"{self._supabase_url}{path}",
                headers=headers,
                params=params,
                json=json_body,
            )
        if response.status_code >= 300:
            raise AuditWriteError(f"Supabase audit write failed: {response.status_code}")
        return response


def audit_context_from_request(request: Request) -> AuditContext:
    raw_request_id = getattr(request.state, "request_id", None)
    request_id = _try_uuid(str(raw_request_id)) if raw_request_id is not None else None
    return AuditContext(
        request_id=request_id,
        ip_address=request.client.host if request.client is not None else None,
        user_agent=request.headers.get("user-agent"),
    )


def _supabase_headers(service_role_key: str) -> dict[str, str]:
    headers = {
        "apikey": service_role_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if not service_role_key.startswith("sb_secret_"):
        headers["Authorization"] = f"Bearer {service_role_key}"
    return headers


def _json_list(response: httpx.Response, operation: str) -> list[dict[str, Any]]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise AuditWriteError(f"{operation} returned invalid JSON") from exc
    if not isinstance(payload, list):
        raise AuditWriteError(f"{operation} returned invalid payload")
    for item in payload:
        if not isinstance(item, dict):
            raise AuditWriteError(f"{operation} returned invalid payload")
    return payload


def _uuid_from_rpc_payload(payload: object) -> UUID:
    if isinstance(payload, str):
        return UUID(payload)
    if isinstance(payload, dict):
        for value in payload.values():
            if isinstance(value, str):
                return UUID(value)
    if isinstance(payload, list) and payload:
        return _uuid_from_rpc_payload(payload[0])
    raise AuditWriteError("Super User override RPC returned invalid payload")


def _uuid_or_none(value: UUID | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _strip_none_values(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def _try_uuid(value: str) -> UUID | None:
    try:
        return UUID(value)
    except ValueError:
        return None
