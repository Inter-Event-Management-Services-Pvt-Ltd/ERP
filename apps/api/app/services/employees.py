from typing import Any

import httpx
from pydantic import ValidationError

from app.core.supabase_http import request_supabase
from app.schemas.current_user import CurrentUser
from app.schemas.employees import EmployeeDirectoryResponse

EMPLOYEE_DIRECTORY_SELECT = (
    "id,employee_code,full_name,official_email,designation,employment_status"
)
ASSIGNABLE_EMPLOYEE_STATUSES = {"ACTIVE", "ON_LEAVE"}


class EmployeesError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class EmployeesService:
    def __init__(
        self,
        *,
        supabase_url: str,
        service_role_key: str,
        timeout_seconds: float = 5.0,
        transport: httpx.AsyncBaseTransport | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._supabase_url = supabase_url.rstrip("/")
        self._service_role_key = service_role_key
        self._timeout_seconds = timeout_seconds
        self._transport = transport
        self._http_client = http_client

    async def list_employees(
        self,
        *,
        current_user: CurrentUser,
        status: str = "ACTIVE",
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EmployeeDirectoryResponse]:
        self._require_employee_lookup_access(current_user=current_user, status=status)
        params = {
            "select": EMPLOYEE_DIRECTORY_SELECT,
            "employment_status": f"eq.{status}",
            "order": "full_name.asc,employee_code.asc",
            "limit": str(limit),
            "offset": str(offset),
        }
        if search is not None:
            term = _postgrest_pattern(search)
            params["or"] = (
                f"(employee_code.ilike.{term},full_name.ilike.{term},"
                f"official_email.ilike.{term},designation.ilike.{term})"
            )

        rows = await self._get_rows("/rest/v1/employees", params=params)
        return [_employee_from_row(row) for row in rows]

    def _require_employee_lookup_access(self, *, current_user: CurrentUser, status: str) -> None:
        if _has_employee_view(current_user):
            return
        if _has_project_manage(current_user) and status in ASSIGNABLE_EMPLOYEE_STATUSES:
            return
        raise EmployeesError(403, "PERMISSION_DENIED", "Permission denied")

    async def _get_rows(self, path: str, *, params: dict[str, str]) -> list[dict[str, Any]]:
        response = await self._request("GET", path, params=params)
        return _json_list(response)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        url = f"{self._supabase_url}{path}"
        if self._http_client is not None:
            response = await request_supabase(
                self._http_client,
                method,
                url,
                headers=self._supabase_headers(),
                params=params,
            )
        else:
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds,
                transport=self._transport,
            ) as client:
                response = await request_supabase(
                    client,
                    method,
                    url,
                    headers=self._supabase_headers(),
                    params=params,
                )
        if response.status_code >= 300:
            _raise_supabase_error(response)
        return response

    def _supabase_headers(self) -> dict[str, str]:
        headers = {
            "apikey": self._service_role_key,
            "Accept": "application/json",
        }
        if not self._service_role_key.startswith("sb_secret_"):
            headers["Authorization"] = f"Bearer {self._service_role_key}"
        return headers


def _employee_from_row(row: dict[str, Any]) -> EmployeeDirectoryResponse:
    try:
        return EmployeeDirectoryResponse.model_validate(row)
    except ValidationError as exc:
        raise EmployeesError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Employee data service returned invalid data",
        ) from exc


def _json_list(response: httpx.Response) -> list[dict[str, Any]]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise EmployeesError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid JSON",
        ) from exc
    if not isinstance(payload, list):
        raise EmployeesError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid payload",
        )
    for item in payload:
        if not isinstance(item, dict):
            raise EmployeesError(
                503,
                "DATA_SERVICE_INVALID_RESPONSE",
                "Data service returned invalid payload",
            )
    return payload


def _raise_supabase_error(response: httpx.Response) -> None:
    if response.status_code == 404:
        raise EmployeesError(404, "NOT_FOUND", "Resource not found")
    raise EmployeesError(503, "DATA_SERVICE_ERROR", "Employee data service request failed")


def _has_employee_view(current_user: CurrentUser) -> bool:
    return current_user.account.is_super_user or "employee.view" in current_user.permissions


def _has_project_manage(current_user: CurrentUser) -> bool:
    return current_user.account.is_super_user or "project.manage" in current_user.permissions


def _postgrest_pattern(raw_value: str) -> str:
    cleaned = (
        raw_value.strip()
        .replace("*", "")
        .replace(",", " ")
        .replace("(", " ")
        .replace(")", " ")
    )
    return f"*{cleaned}*"
