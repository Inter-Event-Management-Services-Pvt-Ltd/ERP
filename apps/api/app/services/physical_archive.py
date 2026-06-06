from datetime import date, datetime
from typing import Any
from uuid import UUID

import httpx
from pydantic import ValidationError

from app.core.audit import AuditContext
from app.schemas.current_user import CurrentUser
from app.schemas.physical_archive import (
    ArchiveLocationContentsResponse,
    ArchiveLocationCreate,
    ArchiveLocationResponse,
    ArchiveRoomCreate,
    ArchiveRoomResponse,
    PhysicalFileCheckoutCreate,
    PhysicalFileCreate,
    PhysicalFileLabelResponse,
    PhysicalFileMoveCreate,
    PhysicalFileResponse,
    PhysicalFileReturnCreate,
    PhysicalFileVerificationCreate,
)

ROOM_SELECT = "id,code,name,description,is_active"
LOCATION_SELECT = (
    "id,archive_room_id,parent_location_id,location_type,code,label,qr_token,is_active"
)
PHYSICAL_FILE_SELECT = (
    "id,physical_file_code,project_id,archive_location_id,volume_number,status,qr_token,"
    "archived_on,archived_by,last_verified_at,next_verification_at,notes,created_at,updated_at,"
    "project:projects(id,project_code,name),"
    "archive_location:archive_locations!physical_files_archive_location_id_fkey("
    "id,archive_room_id,location_type,code,label,qr_token,archive_room:archive_rooms(id,code,name)"
    "),"
    "open_checkout:physical_file_checkouts("
    "id,checked_out_by,checked_out_at,purpose,expected_return_at,returned_at"
    ")"
)
PROJECT_MEMBER_SELECT = "project_id,employee_id,access_level,removed_at"


class PhysicalArchiveError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class PhysicalArchiveService:
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

    async def list_rooms(
        self,
        *,
        current_user: CurrentUser,
        include_inactive: bool = False,
    ) -> list[ArchiveRoomResponse]:
        self._require_archive_read(current_user)
        params = {"select": ROOM_SELECT, "order": "code.asc"}
        if not include_inactive:
            params["is_active"] = "eq.true"
        rows = await self._get_rows("/rest/v1/archive_rooms", params=params)
        return [_room_from_row(row) for row in rows]

    async def create_room(
        self,
        *,
        payload: ArchiveRoomCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ArchiveRoomResponse:
        self._require_archive_manage(current_user)
        row = await self._rpc(
            "create_archive_room_audited",
            {
                "p_code": payload.code,
                "p_name": payload.name,
                "p_description": payload.description,
                **_actor_context_payload(current_user, context),
            },
        )
        return _room_from_row(row)

    async def create_location(
        self,
        *,
        payload: ArchiveLocationCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ArchiveLocationResponse:
        self._require_archive_manage(current_user)
        row = await self._rpc(
            "create_archive_location_audited",
            {
                "p_archive_room_id": str(payload.archive_room_id),
                "p_parent_location_id": _uuid_or_none(payload.parent_location_id),
                "p_location_type": payload.location_type,
                "p_code": payload.code,
                "p_label": payload.label,
                **_actor_context_payload(current_user, context),
            },
        )
        return _location_from_row(row)

    async def get_location_contents(
        self,
        *,
        location_id: UUID,
        current_user: CurrentUser,
    ) -> ArchiveLocationContentsResponse:
        self._require_archive_read(current_user)
        location = await self._get_location_row(location_id)
        child_rows = await self._get_rows(
            "/rest/v1/archive_locations",
            params={
                "select": LOCATION_SELECT,
                "parent_location_id": f"eq.{location_id}",
                "is_active": "eq.true",
                "order": "location_type.asc,code.asc",
            },
        )
        file_rows = await self._get_rows(
            "/rest/v1/physical_files",
            params={
                "select": PHYSICAL_FILE_SELECT,
                "archive_location_id": f"eq.{location_id}",
                "order": "physical_file_code.asc",
            },
        )
        return ArchiveLocationContentsResponse(
            location=_location_from_row(location),
            child_locations=[_location_from_row(row) for row in child_rows],
            physical_files=[
                _physical_file_from_row(_normalize_physical_file_row(row)) for row in file_rows
            ],
        )

    async def create_physical_file(
        self,
        *,
        project_id: UUID,
        payload: PhysicalFileCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> PhysicalFileResponse:
        self._require_archive_manage(current_user)
        await self._require_project_manage_access(project_id=project_id, current_user=current_user)
        row = await self._rpc(
            "create_physical_file_audited",
            {
                "p_physical_file_code": payload.physical_file_code,
                "p_project_id": str(project_id),
                "p_archive_location_id": str(payload.archive_location_id),
                "p_volume_number": payload.volume_number,
                "p_archived_on": _date_or_none(payload.archived_on),
                "p_notes": payload.notes,
                **_actor_context_payload(current_user, context),
            },
        )
        return _physical_file_from_row(row)

    async def get_physical_file(
        self,
        *,
        physical_file_id: UUID,
        current_user: CurrentUser,
    ) -> PhysicalFileResponse:
        row = await self._get_physical_file_row(physical_file_id)
        if not (current_user.account.is_super_user or "archive.view" in current_user.permissions):
            await self._require_project_read_access(
                project_id=UUID(str(row["project_id"])),
                current_user=current_user,
            )
        return _physical_file_from_row(_normalize_physical_file_row(row))

    async def checkout_physical_file(
        self,
        *,
        physical_file_id: UUID,
        payload: PhysicalFileCheckoutCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> PhysicalFileResponse:
        self._require_permission(current_user, "physical_file.checkout")
        row = await self._get_physical_file_row(physical_file_id)
        if not (current_user.account.is_super_user or "archive.view" in current_user.permissions):
            await self._require_project_read_access(
                project_id=UUID(str(row["project_id"])),
                current_user=current_user,
            )
        result = await self._rpc(
            "checkout_physical_file_audited",
            {
                "p_physical_file_id": str(physical_file_id),
                "p_purpose": payload.purpose,
                "p_expected_return_at": _datetime_or_none(payload.expected_return_at),
                **_actor_context_payload(current_user, context),
            },
        )
        return _physical_file_from_row(result)

    async def return_physical_file(
        self,
        *,
        physical_file_id: UUID,
        payload: PhysicalFileReturnCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> PhysicalFileResponse:
        self._require_archive_manage(current_user)
        result = await self._rpc(
            "return_physical_file_audited",
            {
                "p_physical_file_id": str(physical_file_id),
                "p_returned_to_location_id": _uuid_or_none(payload.returned_to_location_id),
                "p_remarks": payload.remarks,
                **_actor_context_payload(current_user, context),
            },
        )
        return _physical_file_from_row(result)

    async def move_physical_file(
        self,
        *,
        physical_file_id: UUID,
        payload: PhysicalFileMoveCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> PhysicalFileResponse:
        self._require_archive_manage(current_user)
        result = await self._rpc(
            "move_physical_file_audited",
            {
                "p_physical_file_id": str(physical_file_id),
                "p_to_location_id": str(payload.to_location_id),
                "p_remarks": payload.remarks,
                **_actor_context_payload(current_user, context),
            },
        )
        return _physical_file_from_row(result)

    async def verify_physical_file(
        self,
        *,
        physical_file_id: UUID,
        payload: PhysicalFileVerificationCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> PhysicalFileResponse:
        self._require_archive_manage(current_user)
        result = await self._rpc(
            "verify_physical_file_audited",
            {
                "p_physical_file_id": str(physical_file_id),
                "p_location_correct": payload.location_correct,
                "p_label_readable": payload.label_readable,
                "p_physical_file_present": payload.physical_file_present,
                "p_digital_archive_present": payload.digital_archive_present,
                "p_documents_complete": payload.documents_complete,
                "p_remarks": payload.remarks,
                **_actor_context_payload(current_user, context),
            },
        )
        return _physical_file_from_row(result)

    async def get_physical_file_label(
        self,
        *,
        physical_file_id: UUID,
        current_user: CurrentUser,
    ) -> PhysicalFileLabelResponse:
        physical_file = await self.get_physical_file(
            physical_file_id=physical_file_id,
            current_user=current_user,
        )
        if physical_file.project is None or physical_file.archive_location is None:
            raise PhysicalArchiveError(
                503,
                "DATA_SERVICE_INVALID_RESPONSE",
                "Physical file label data is incomplete",
            )
        archive_room_name = (
            physical_file.archive_room.name if physical_file.archive_room is not None else ""
        )
        return PhysicalFileLabelResponse(
            physical_file_id=physical_file.id,
            physical_file_code=physical_file.physical_file_code,
            project_code=physical_file.project.project_code,
            project_name=physical_file.project.name,
            location_code=physical_file.archive_location.code,
            archive_room=archive_room_name,
            qr_token=physical_file.qr_token,
            label_text=(
                f"{physical_file.physical_file_code} | "
                f"{physical_file.project.project_code} | "
                f"{archive_room_name}/{physical_file.archive_location.code}"
            ),
        )

    async def _get_location_row(self, location_id: UUID) -> dict[str, Any]:
        rows = await self._get_rows(
            "/rest/v1/archive_locations",
            params={
                "select": LOCATION_SELECT,
                "id": f"eq.{location_id}",
                "limit": "1",
            },
        )
        if not rows:
            raise PhysicalArchiveError(404, "NOT_FOUND", "Archive location not found")
        return rows[0]

    async def _get_physical_file_row(self, physical_file_id: UUID) -> dict[str, Any]:
        rows = await self._get_rows(
            "/rest/v1/physical_files",
            params={
                "select": PHYSICAL_FILE_SELECT,
                "id": f"eq.{physical_file_id}",
                "limit": "1",
            },
        )
        if not rows:
            raise PhysicalArchiveError(404, "NOT_FOUND", "Physical file not found")
        return rows[0]

    async def _require_project_read_access(
        self,
        *,
        project_id: UUID,
        current_user: CurrentUser,
    ) -> None:
        if current_user.account.is_super_user:
            return
        rows = await self._get_rows(
            "/rest/v1/project_members",
            params={
                "select": PROJECT_MEMBER_SELECT,
                "project_id": f"eq.{project_id}",
                "employee_id": f"eq.{current_user.employee.id}",
                "removed_at": "is.null",
                "limit": "1",
            },
        )
        if not rows:
            raise PhysicalArchiveError(403, "ABAC_DENIED", "Project archive access denied")

    async def _require_project_manage_access(
        self,
        *,
        project_id: UUID,
        current_user: CurrentUser,
    ) -> None:
        if current_user.account.is_super_user:
            return
        rows = await self._get_rows(
            "/rest/v1/project_members",
            params={
                "select": PROJECT_MEMBER_SELECT,
                "project_id": f"eq.{project_id}",
                "employee_id": f"eq.{current_user.employee.id}",
                "access_level": "eq.MANAGE",
                "removed_at": "is.null",
                "limit": "1",
            },
        )
        if not rows:
            raise PhysicalArchiveError(403, "ABAC_DENIED", "Project archive manage access denied")

    def _require_archive_read(self, current_user: CurrentUser) -> None:
        if not (
            current_user.account.is_super_user
            or "archive.view" in current_user.permissions
            or "archive.manage" in current_user.permissions
        ):
            raise PhysicalArchiveError(403, "PERMISSION_DENIED", "Permission denied")

    def _require_archive_manage(self, current_user: CurrentUser) -> None:
        self._require_permission(current_user, "archive.manage")

    def _require_permission(self, current_user: CurrentUser, permission_code: str) -> None:
        if current_user.account.is_super_user:
            return
        if permission_code not in current_user.permissions:
            raise PhysicalArchiveError(403, "PERMISSION_DENIED", "Permission denied")

    async def _get_rows(self, path: str, *, params: dict[str, str]) -> list[dict[str, Any]]:
        response = await self._request("GET", path, params=params)
        return _json_list(response)

    async def _rpc(self, function_name: str, payload: dict[str, object]) -> dict[str, Any]:
        response = await self._request(
            "POST",
            f"/rest/v1/rpc/{function_name}",
            json_body=payload,
        )
        return _json_object(response)

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json_body: dict[str, object] | None = None,
    ) -> httpx.Response:
        async with httpx.AsyncClient(
            timeout=self._timeout_seconds,
            transport=self._transport,
        ) as client:
            response = await client.request(
                method,
                f"{self._supabase_url}{path}",
                headers=self._supabase_headers(),
                params=params,
                json=json_body,
            )
        if response.status_code >= 300:
            _raise_supabase_error(response)
        return response

    def _supabase_headers(self) -> dict[str, str]:
        headers = {
            "apikey": self._service_role_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if not self._service_role_key.startswith("sb_secret_"):
            headers["Authorization"] = f"Bearer {self._service_role_key}"
        return headers


def _actor_context_payload(current_user: CurrentUser, context: AuditContext) -> dict[str, object]:
    return {
        "p_actor_user_account_id": str(current_user.auth_user_id),
        "p_actor_employee_id": str(current_user.employee.id),
        "p_request_id": _uuid_or_none(context.request_id),
        "p_ip_address": context.ip_address,
        "p_user_agent": context.user_agent,
    }


def _room_from_row(row: dict[str, Any]) -> ArchiveRoomResponse:
    try:
        return ArchiveRoomResponse.model_validate(row)
    except ValidationError as exc:
        raise PhysicalArchiveError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Archive room data service returned invalid data",
        ) from exc


def _location_from_row(row: dict[str, Any]) -> ArchiveLocationResponse:
    try:
        return ArchiveLocationResponse.model_validate(row)
    except ValidationError as exc:
        raise PhysicalArchiveError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Archive location data service returned invalid data",
        ) from exc


def _physical_file_from_row(row: dict[str, Any]) -> PhysicalFileResponse:
    try:
        return PhysicalFileResponse.model_validate(row)
    except ValidationError as exc:
        raise PhysicalArchiveError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Physical file data service returned invalid data",
        ) from exc


def _normalize_physical_file_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    archive_location = normalized.get("archive_location")
    if isinstance(archive_location, dict) and "archive_room" in archive_location:
        normalized["archive_room"] = archive_location["archive_room"]
    open_checkout = normalized.get("open_checkout")
    if isinstance(open_checkout, list):
        active = [
            checkout
            for checkout in open_checkout
            if isinstance(checkout, dict) and checkout.get("returned_at") is None
        ]
        normalized["open_checkout"] = active[0] if active else None
    return normalized


def _json_list(response: httpx.Response) -> list[dict[str, Any]]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise PhysicalArchiveError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid JSON",
        ) from exc
    if not isinstance(payload, list):
        raise PhysicalArchiveError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid payload",
        )
    for item in payload:
        if not isinstance(item, dict):
            raise PhysicalArchiveError(
                503,
                "DATA_SERVICE_INVALID_RESPONSE",
                "Data service returned invalid payload",
            )
    return payload


def _json_object(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise PhysicalArchiveError(
            503,
            "DATA_SERVICE_INVALID_RESPONSE",
            "Data service returned invalid JSON",
        ) from exc
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list) and payload and isinstance(payload[0], dict):
        return payload[0]
    raise PhysicalArchiveError(
        503,
        "DATA_SERVICE_INVALID_RESPONSE",
        "Data service returned invalid payload",
    )


def _raise_supabase_error(response: httpx.Response) -> None:
    payload = _error_payload(response)
    pg_code = _optional_str(payload.get("code"))
    message = _optional_str(payload.get("message")) or "Supabase data service request failed"

    if message in {
        "IEMS_ARCHIVE_ROOM_NOT_FOUND",
        "IEMS_ARCHIVE_LOCATION_NOT_FOUND",
        "IEMS_PHYSICAL_FILE_NOT_FOUND",
        "IEMS_PHYSICAL_CHECKOUT_NOT_FOUND",
    }:
        raise PhysicalArchiveError(404, "NOT_FOUND", "Resource not found")
    if message == "IEMS_PHYSICAL_FILE_NOT_AVAILABLE":
        raise PhysicalArchiveError(
            409,
            "INVALID_PHYSICAL_FILE_STATE",
            "Physical file is not available for checkout",
        )
    if message == "IEMS_PHYSICAL_FILE_CHECKED_OUT":
        raise PhysicalArchiveError(
            409,
            "INVALID_PHYSICAL_FILE_STATE",
            "Physical file is checked out",
        )
    if message == "IEMS_INVALID_ARCHIVE_LOCATION_HIERARCHY":
        raise PhysicalArchiveError(422, "INVALID_STATE", "Archive location hierarchy is invalid")
    if pg_code == "23505":
        raise PhysicalArchiveError(409, "RESOURCE_CONFLICT", "Resource already exists")
    if pg_code == "23503":
        raise PhysicalArchiveError(422, "INVALID_REFERENCE", "Referenced resource is invalid")
    if pg_code == "23514":
        raise PhysicalArchiveError(422, "INVALID_STATE", "Resource violates a constraint")
    if response.status_code == 404:
        raise PhysicalArchiveError(404, "NOT_FOUND", "Resource not found")

    raise PhysicalArchiveError(503, "DATA_SERVICE_ERROR", message)


def _error_payload(response: httpx.Response) -> dict[str, object]:
    try:
        payload = response.json()
    except ValueError:
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _uuid_or_none(value: UUID | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _date_or_none(value: date | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _datetime_or_none(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _optional_str(value: object) -> str | None:
    if isinstance(value, str):
        return value
    return None
