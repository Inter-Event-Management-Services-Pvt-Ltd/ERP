import asyncio
from datetime import UTC, date, datetime
from uuid import UUID

from httpx import ASGITransport, AsyncClient, Response

from app.api.dependencies import get_current_user, get_physical_archive_service
from app.core.audit import AuditContext
from app.main import app
from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount
from app.schemas.physical_archive import (
    ArchiveLocationResponse,
    ArchiveRoomCreate,
    ArchiveRoomResponse,
    PhysicalFileCheckoutCreate,
    PhysicalFileResponse,
)

AUTH_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
PROJECT_ID = UUID("33333333-3333-4333-8333-333333333333")
ROOM_ID = UUID("44444444-4444-4444-8444-444444444444")
LOCATION_ID = UUID("55555555-5555-4555-8555-555555555555")
PHYSICAL_FILE_ID = UUID("66666666-6666-4666-8666-666666666666")
QR_TOKEN = UUID("77777777-7777-4777-8777-777777777777")
CREATED_AT = datetime(2026, 6, 6, 8, 0, tzinfo=UTC)


class RecordingPhysicalArchiveService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object, CurrentUser, AuditContext | None]] = []

    async def create_room(
        self,
        *,
        payload: ArchiveRoomCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ArchiveRoomResponse:
        self.calls.append(("create_room", payload, current_user, context))
        return ArchiveRoomResponse(
            id=ROOM_ID,
            code=payload.code,
            name=payload.name,
            description=payload.description,
            is_active=True,
        )

    async def list_locations(
        self,
        *,
        current_user: CurrentUser,
        room_id: UUID,
        include_inactive: bool = False,
    ) -> list[ArchiveLocationResponse]:
        self.calls.append(("list_locations", (room_id, include_inactive), current_user, None))
        return [
            ArchiveLocationResponse(
                id=LOCATION_ID,
                archive_room_id=room_id,
                parent_location_id=None,
                location_type="RACK",
                code="R1",
                label="Rack 1",
                qr_token=UUID("77777777-7777-4777-8777-777777777777"),
                is_active=True,
            )
        ]

    async def checkout_physical_file(
        self,
        *,
        physical_file_id: UUID,
        payload: PhysicalFileCheckoutCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> PhysicalFileResponse:
        self.calls.append(("checkout", (physical_file_id, payload), current_user, context))
        return _physical_file_response(status="CHECKED_OUT")

    async def get_physical_file_by_qr_token(
        self,
        *,
        qr_token: UUID,
        current_user: CurrentUser,
    ) -> PhysicalFileResponse:
        self.calls.append(("get_by_qr", qr_token, current_user, None))
        return _physical_file_response()

    async def list_project_physical_files(
        self,
        *,
        project_id: UUID,
        current_user: CurrentUser,
    ) -> list[PhysicalFileResponse]:
        self.calls.append(("list_project_physical_files", project_id, current_user, None))
        return [_physical_file_response()]


def _current_user(*, permissions: list[str], is_super_user: bool = False) -> CurrentUser:
    return CurrentUser(
        auth_user_id=AUTH_USER_ID,
        account=UserAccount(is_active=True, is_super_user=is_super_user),
        employee=EmployeeProfile(
            id=EMPLOYEE_ID,
            employee_code="IEMS-001",
            full_name="Example Employee",
            official_email="employee@iemsnewdelhi.com",
            designation="Archive Manager",
            employment_status="ACTIVE",
        ),
        roles=["ADMIN"],
        permissions=permissions,
    )


def _physical_file_response(*, status: str = "AVAILABLE") -> PhysicalFileResponse:
    return PhysicalFileResponse(
        id=PHYSICAL_FILE_ID,
        physical_file_code="PF-001",
        project_id=PROJECT_ID,
        archive_location_id=LOCATION_ID,
        volume_number=1,
        status=status,
        qr_token=UUID("77777777-7777-4777-8777-777777777777"),
        archived_on=date(2026, 6, 6),
        archived_by=EMPLOYEE_ID,
        last_verified_at=None,
        next_verification_at=None,
        notes=None,
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
    )


async def _request(
    method: str,
    path: str,
    *,
    json: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.request(method, path, json=json, headers=headers)


def _install_overrides(
    *,
    current_user: CurrentUser,
    service: RecordingPhysicalArchiveService | None = None,
) -> RecordingPhysicalArchiveService:
    installed_service = service or RecordingPhysicalArchiveService()

    async def override_current_user() -> CurrentUser:
        return current_user

    async def override_physical_archive_service() -> RecordingPhysicalArchiveService:
        return installed_service

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_physical_archive_service] = override_physical_archive_service
    return installed_service


def test_create_archive_room_requires_archive_manage() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["archive.view"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                "/v1/archive/rooms",
                json={"code": "R1", "name": "Room 1"},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert service.calls == []


def test_create_archive_room_returns_created_room() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["archive.manage"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                "/v1/archive/rooms",
                json={"code": "R1", "name": "Room 1"},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["code"] == "R1"
    assert service.calls[0][0] == "create_room"


def test_list_archive_locations_requires_archive_read() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                f"/v1/archive/locations?room_id={ROOM_ID}",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert service.calls == []


def test_list_archive_locations_returns_room_locations() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["archive.view"]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                f"/v1/archive/locations?room_id={ROOM_ID}",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["archive_room_id"] == str(ROOM_ID)
    assert response.json()[0]["code"] == "R1"
    assert service.calls[0][0] == "list_locations"
    assert service.calls[0][1] == (ROOM_ID, False)


def test_get_physical_file_by_qr_requires_archive_read() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                f"/v1/physical-files/by-qr/{QR_TOKEN}",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert service.calls == []


def test_get_physical_file_by_qr_returns_physical_file() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["archive.view"]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                f"/v1/physical-files/by-qr/{QR_TOKEN}",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(PHYSICAL_FILE_ID)
    assert service.calls[0][0] == "get_by_qr"
    assert service.calls[0][1] == QR_TOKEN


def test_list_project_physical_files_allows_project_member_context() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                f"/v1/projects/{PROJECT_ID}/physical-files",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(PHYSICAL_FILE_ID)
    assert service.calls[0][0] == "list_project_physical_files"
    assert service.calls[0][1] == PROJECT_ID


def test_checkout_physical_file_requires_checkout_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["archive.view"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                f"/v1/physical-files/{PHYSICAL_FILE_ID}/checkout",
                json={"purpose": "Audit review"},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert service.calls == []


def test_checkout_physical_file_returns_checked_out_file() -> None:
    service = _install_overrides(
        current_user=_current_user(permissions=["physical_file.checkout"])
    )
    try:
        response = asyncio.run(
            _request(
                "POST",
                f"/v1/physical-files/{PHYSICAL_FILE_ID}/checkout",
                json={"purpose": "Audit review"},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "CHECKED_OUT"
    assert service.calls[0][0] == "checkout"
