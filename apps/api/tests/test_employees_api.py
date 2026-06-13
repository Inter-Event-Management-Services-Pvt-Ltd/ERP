import asyncio
from uuid import UUID

from httpx import ASGITransport, AsyncClient, Response

from app.api.dependencies import get_current_user, get_employees_service
from app.main import app
from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount
from app.schemas.employees import EmployeeDirectoryResponse

AUTH_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
OTHER_EMPLOYEE_ID = UUID("33333333-3333-4333-8333-333333333333")


class RecordingEmployeesService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object, CurrentUser]] = []

    async def list_employees(
        self,
        *,
        current_user: CurrentUser,
        status: str = "ACTIVE",
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EmployeeDirectoryResponse]:
        self.calls.append(("list_employees", (status, search, limit, offset), current_user))
        return [
            EmployeeDirectoryResponse(
                id=OTHER_EMPLOYEE_ID,
                employee_code="IEMS-002",
                full_name="Assignment Target",
                official_email="target@iemsnewdelhi.com",
                designation="Coordinator",
                employment_status="ACTIVE",
            )
        ]


def _current_user(*, permissions: list[str], is_super_user: bool = False) -> CurrentUser:
    return CurrentUser(
        auth_user_id=AUTH_USER_ID,
        account=UserAccount(is_active=True, is_super_user=is_super_user),
        employee=EmployeeProfile(
            id=EMPLOYEE_ID,
            employee_code="IEMS-001",
            full_name="Example Employee",
            official_email="employee@iemsnewdelhi.com",
            designation="Coordinator",
            employment_status="ACTIVE",
        ),
        roles=["EMPLOYEE"],
        permissions=permissions,
    )


async def _request(
    method: str,
    path: str,
    *,
    headers: dict[str, str] | None = None,
) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.request(method, path, headers=headers)


def _install_overrides(
    *,
    current_user: CurrentUser,
    service: RecordingEmployeesService | None = None,
) -> RecordingEmployeesService:
    installed_service = service or RecordingEmployeesService()

    async def override_current_user() -> CurrentUser:
        return current_user

    async def override_employees_service() -> RecordingEmployeesService:
        return installed_service

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_employees_service] = override_employees_service
    return installed_service


def test_list_employees_accepts_project_manager_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.manage"]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/employees?status=ACTIVE&search=target&limit=10&offset=2",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(OTHER_EMPLOYEE_ID),
            "employee_code": "IEMS-002",
            "full_name": "Assignment Target",
            "official_email": "target@iemsnewdelhi.com",
            "designation": "Coordinator",
            "employment_status": "ACTIVE",
        }
    ]
    assert service.calls[0][0] == "list_employees"
    assert service.calls[0][1] == ("ACTIVE", "target", 10, 2)


def test_list_employees_accepts_employee_view_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["employee.view"]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/employees?status=ON_LEAVE",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert service.calls[0][1] == ("ON_LEAVE", None, 50, 0)


def test_list_employees_requires_directory_or_project_manage_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.view"]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/employees",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert service.calls == []
