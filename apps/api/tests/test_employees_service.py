import asyncio
from uuid import UUID

import httpx
import pytest
from httpx import Response

from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount
from app.services.employees import EmployeesError, EmployeesService

AUTH_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
OTHER_EMPLOYEE_ID = UUID("33333333-3333-4333-8333-333333333333")


def _current_user(
    *,
    permissions: list[str] | None = None,
    is_super_user: bool = False,
) -> CurrentUser:
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
        roles=["SUPER_USER"] if is_super_user else ["EMPLOYEE"],
        permissions=permissions or [],
    )


def _employee_row() -> dict[str, object]:
    return {
        "id": str(OTHER_EMPLOYEE_ID),
        "employee_code": "IEMS-002",
        "full_name": "Assignment Target",
        "official_email": "target@iemsnewdelhi.com",
        "designation": "Coordinator",
        "employment_status": "ACTIVE",
    }


def test_service_lists_active_employees_for_project_manager_assignment() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        return Response(200, json=[_employee_row()])

    service = EmployeesService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    employees = asyncio.run(
        service.list_employees(
            current_user=_current_user(permissions=["project.manage"]),
            search="target",
            limit=20,
            offset=5,
        )
    )

    assert employees[0].id == OTHER_EMPLOYEE_ID
    assert employees[0].official_email == "target@iemsnewdelhi.com"
    request = seen_requests[0]
    assert request.url.path == "/rest/v1/employees"
    assert request.url.params["select"] == (
        "id,employee_code,full_name,official_email,designation,employment_status"
    )
    assert request.url.params["employment_status"] == "eq.ACTIVE"
    assert request.url.params["limit"] == "20"
    assert request.url.params["offset"] == "5"
    assert "full_name.ilike.*target*" in request.url.params["or"]


def test_service_allows_employee_view_to_filter_on_leave_employees() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        return Response(200, json=[{**_employee_row(), "employment_status": "ON_LEAVE"}])

    service = EmployeesService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    employees = asyncio.run(
        service.list_employees(
            current_user=_current_user(permissions=["employee.view"]),
            status="ON_LEAVE",
        )
    )

    assert employees[0].employment_status == "ON_LEAVE"
    assert seen_requests[0].url.params["employment_status"] == "eq.ON_LEAVE"


def test_service_restricts_project_manager_directory_to_assignable_statuses() -> None:
    service = EmployeesService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(lambda _request: Response(500)),
    )

    with pytest.raises(EmployeesError) as exc_info:
        asyncio.run(
            service.list_employees(
                current_user=_current_user(permissions=["project.manage"]),
                status="INACTIVE",
            )
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "PERMISSION_DENIED"


def test_service_requires_directory_or_project_manage_permission() -> None:
    service = EmployeesService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(lambda _request: Response(500)),
    )

    with pytest.raises(EmployeesError) as exc_info:
        asyncio.run(
            service.list_employees(
                current_user=_current_user(permissions=["project.view"]),
            )
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "PERMISSION_DENIED"
