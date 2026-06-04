from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import httpx
from pydantic import ValidationError

from app.core.auth import TokenClaims
from app.core.config import Settings
from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount


class CurrentUserError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class SupabaseCurrentUserResolver:
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

    @classmethod
    def from_settings(cls, settings: Settings) -> "SupabaseCurrentUserResolver":
        if settings.supabase_url is None or settings.supabase_service_role_key is None:
            raise CurrentUserError(
                503,
                "AUTH_NOT_CONFIGURED",
                "Supabase employee resolver is not configured",
            )

        return cls(
            supabase_url=settings.supabase_url,
            service_role_key=settings.supabase_service_role_key,
            timeout_seconds=settings.supabase_request_timeout_seconds,
        )

    async def resolve(self, claims: TokenClaims) -> CurrentUser:
        response = await self._fetch_user_account(claims.subject)
        account_rows = _json_list(response)
        if not account_rows:
            raise CurrentUserError(403, "ACCOUNT_NOT_APPROVED", "Account is not approved")

        account_row = _dict_value(account_rows[0])
        employee_row = _dict_value(account_row.get("employee"))

        if not _bool_value(account_row.get("is_active")):
            raise CurrentUserError(403, "ACCOUNT_DISABLED", "Account is disabled")

        employment_status = _str_value(employee_row.get("employment_status"))
        if employment_status in {"INACTIVE", "EXITED"}:
            raise CurrentUserError(403, "ACCOUNT_DISABLED", "Employee is disabled")

        official_email = _str_value(employee_row.get("official_email"))
        if official_email.lower() != claims.email.lower():
            raise CurrentUserError(
                403,
                "ACCOUNT_EMAIL_MISMATCH",
                "Token email does not match employee account",
            )

        try:
            return CurrentUser(
                auth_user_id=UUID(_str_value(account_row.get("id"))),
                account=UserAccount(
                    is_active=True,
                    is_super_user=_bool_value(account_row.get("is_super_user")),
                ),
                employee=EmployeeProfile(
                    id=UUID(_str_value(employee_row.get("id"))),
                    employee_code=_str_value(employee_row.get("employee_code")),
                    full_name=_str_value(employee_row.get("full_name")),
                    official_email=official_email,
                    designation=_optional_str_value(employee_row.get("designation")),
                    employment_status=employment_status,
                ),
                roles=_active_role_codes(account_row.get("role_assignments")),
                permissions=_active_permission_codes(account_row.get("role_assignments")),
            )
        except (ValidationError, ValueError) as exc:
            raise CurrentUserError(
                503,
                "AUTH_RESOLUTION_FAILED",
                "Current employee lookup returned invalid data",
            ) from exc

    async def _fetch_user_account(self, auth_user_id: UUID) -> httpx.Response:
        headers = self._supabase_headers()
        params = {
            "select": (
                "id,is_active,is_super_user,"
                "employee:employees("
                "id,employee_code,full_name,official_email,designation,employment_status"
                "),"
                "role_assignments:user_role_assignments("
                "expires_at,"
                "role:roles(code,role_permissions(permission:permissions(code)))"
                ")"
            ),
            "id": f"eq.{auth_user_id}",
            "limit": "1",
        }
        async with httpx.AsyncClient(
            timeout=self._timeout_seconds,
            transport=self._transport,
        ) as client:
            response = await client.get(
                f"{self._supabase_url}/rest/v1/user_accounts",
                headers=headers,
                params=params,
            )

        if response.status_code >= 400:
            raise CurrentUserError(
                503,
                "AUTH_RESOLUTION_FAILED",
                "Current employee lookup failed",
            )
        return response

    def _supabase_headers(self) -> dict[str, str]:
        headers = {
            "apikey": self._service_role_key,
            "Accept": "application/json",
        }
        if not self._service_role_key.startswith("sb_secret_"):
            headers["Authorization"] = f"Bearer {self._service_role_key}"
        return headers


def _json_list(response: httpx.Response) -> list[object]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise CurrentUserError(
            503,
            "AUTH_RESOLUTION_FAILED",
            "Current employee lookup returned invalid JSON",
        ) from exc

    if not isinstance(payload, list):
        raise CurrentUserError(
            503,
            "AUTH_RESOLUTION_FAILED",
            "Current employee lookup returned invalid JSON",
        )
    return payload


def _dict_value(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CurrentUserError(
            503,
            "AUTH_RESOLUTION_FAILED",
            "Current employee lookup returned invalid data",
        )
    return value


def _str_value(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise CurrentUserError(
            503,
            "AUTH_RESOLUTION_FAILED",
            "Current employee lookup returned invalid data",
        )
    return value


def _optional_str_value(value: object) -> str | None:
    if value is None:
        return None
    return _str_value(value)


def _bool_value(value: object) -> bool:
    if not isinstance(value, bool):
        raise CurrentUserError(
            503,
            "AUTH_RESOLUTION_FAILED",
            "Current employee lookup returned invalid data",
        )
    return value


def _active_role_codes(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    role_codes: list[str] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        expires_at = item.get("expires_at")
        if _role_assignment_expired(expires_at):
            continue
        role = item.get("role")
        if not isinstance(role, dict):
            continue
        code = role.get("code")
        if isinstance(code, str) and code and code not in role_codes:
            role_codes.append(code)
    return role_codes


def _active_permission_codes(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    permission_codes: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            continue
        expires_at = item.get("expires_at")
        if _role_assignment_expired(expires_at):
            continue
        role = item.get("role")
        if not isinstance(role, dict):
            continue
        role_permissions = role.get("role_permissions")
        if not isinstance(role_permissions, list):
            continue
        for role_permission in role_permissions:
            if not isinstance(role_permission, dict):
                continue
            permission = role_permission.get("permission")
            if not isinstance(permission, dict):
                continue
            code = permission.get("code")
            if isinstance(code, str) and code:
                permission_codes.add(code)
    return sorted(permission_codes)


def _role_assignment_expired(raw_expires_at: object) -> bool:
    if raw_expires_at is None:
        return False
    if not isinstance(raw_expires_at, str):
        return True

    try:
        expires_at = datetime.fromisoformat(raw_expires_at.replace("Z", "+00:00"))
    except ValueError:
        return True

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at <= datetime.now(tz=UTC)
