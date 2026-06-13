import asyncio
import json
from datetime import date
from uuid import UUID

import httpx
import pytest
from httpx import Response

from app.core.audit import AuditContext
from app.schemas.clients_projects import ClientCreate, ProjectCreate, ProjectMemberUpdate
from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount
from app.services.clients_projects import ClientsProjectsError, ClientsProjectsService

AUTH_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
OTHER_EMPLOYEE_ID = UUID("33333333-3333-4333-8333-333333333333")
CLIENT_ID = UUID("44444444-4444-4444-8444-444444444444")
PROJECT_ID = UUID("55555555-5555-4555-8555-555555555555")
PROJECT_TYPE_ID = UUID("66666666-6666-4666-8666-666666666666")
PROJECT_STATUS_ID = UUID("77777777-7777-4777-8777-777777777777")
PRIORITY_LEVEL_ID = UUID("88888888-8888-4888-8888-888888888888")
ROOT_FOLDER_ID = UUID("99999999-9999-4999-8999-999999999999")
CHILD_FOLDER_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
REQUEST_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")

CREATED_AT = "2026-06-05T09:00:00+00:00"
UPDATED_AT = "2026-06-05T09:30:00+00:00"


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


def _client_row() -> dict[str, object]:
    return {
        "id": str(CLIENT_ID),
        "client_code": "ACME",
        "legal_name": "Acme Events Private Limited",
        "display_name": "Acme Events",
        "is_active": True,
        "notes": "Preferred Delhi NCR client",
        "created_at": CREATED_AT,
        "updated_at": UPDATED_AT,
    }


def _project_row() -> dict[str, object]:
    return {
        "id": str(PROJECT_ID),
        "project_code": "IEMS-2026-001",
        "client_id": str(CLIENT_ID),
        "client": {
            "id": str(CLIENT_ID),
            "client_code": "ACME",
            "display_name": "Acme Events",
        },
        "project_type_id": str(PROJECT_TYPE_ID),
        "project_type": {
            "id": str(PROJECT_TYPE_ID),
            "code": "CONFERENCE",
            "name": "Conference",
        },
        "project_status_id": str(PROJECT_STATUS_ID),
        "project_status": {
            "id": str(PROJECT_STATUS_ID),
            "code": "PLANNING",
            "name": "Planning",
        },
        "priority_level_id": str(PRIORITY_LEVEL_ID),
        "priority_level": {
            "id": str(PRIORITY_LEVEL_ID),
            "code": "NORMAL",
            "name": "Normal",
        },
        "name": "Annual Leadership Conference",
        "event_date": "2026-08-12",
        "venue": "New Delhi",
        "description": "Annual client conference",
        "project_manager_id": str(EMPLOYEE_ID),
        "project_manager": {
            "id": str(EMPLOYEE_ID),
            "employee_code": "IEMS-001",
            "full_name": "Example Employee",
        },
        "created_by": str(EMPLOYEE_ID),
        "created_at": CREATED_AT,
        "updated_at": UPDATED_AT,
        "archived_at": None,
        "deleted_at": None,
        "root_folder_id": str(ROOT_FOLDER_ID),
    }


def _project_member_row() -> dict[str, object]:
    return {
        "project_id": str(PROJECT_ID),
        "employee_id": str(EMPLOYEE_ID),
        "employee": {
            "id": str(EMPLOYEE_ID),
            "employee_code": "IEMS-001",
            "full_name": "Example Employee",
        },
        "access_level": "MANAGE",
        "assigned_by": str(EMPLOYEE_ID),
        "assigned_at": CREATED_AT,
        "removed_at": None,
    }


def test_service_creates_client_through_audited_rpc() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        return Response(200, json=_client_row())

    service = ClientsProjectsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.create_client(
            payload=ClientCreate(
                client_code="ACME",
                legal_name="Acme Events Private Limited",
                display_name="Acme Events",
                notes="Preferred Delhi NCR client",
            ),
            current_user=_current_user(permissions=["project.manage"]),
            context=AuditContext(
                request_id=REQUEST_ID,
                ip_address="127.0.0.1",
                user_agent="pytest",
            ),
        )
    )

    assert result.id == CLIENT_ID
    request = seen_requests[0]
    assert str(request.url) == "http://localhost:54321/rest/v1/rpc/create_client_audited"
    assert request.headers["apikey"] == "legacy-service-role-key"
    assert request.headers["authorization"] == "Bearer legacy-service-role-key"
    assert json.loads(request.content) == {
        "p_client_code": "ACME",
        "p_legal_name": "Acme Events Private Limited",
        "p_display_name": "Acme Events",
        "p_notes": "Preferred Delhi NCR client",
        "p_actor_user_account_id": str(AUTH_USER_ID),
        "p_actor_employee_id": str(EMPLOYEE_ID),
        "p_request_id": str(REQUEST_ID),
        "p_ip_address": "127.0.0.1",
        "p_user_agent": "pytest",
    }


def test_service_creates_project_through_template_rpc() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        return Response(200, json=_project_row())

    service = ClientsProjectsService(
        supabase_url="http://localhost:54321",
        service_role_key="sb" "_secret_test_secret_key_value_123456",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.create_project(
            payload=ProjectCreate(
                project_code="IEMS-2026-001",
                client_id=CLIENT_ID,
                project_type_id=PROJECT_TYPE_ID,
                project_status_id=PROJECT_STATUS_ID,
                priority_level_id=PRIORITY_LEVEL_ID,
                name="Annual Leadership Conference",
                event_date=date(2026, 8, 12),
                venue="New Delhi",
                description="Annual client conference",
                project_manager_id=EMPLOYEE_ID,
            ),
            current_user=_current_user(permissions=["project.manage"]),
            context=AuditContext(request_id=REQUEST_ID),
        )
    )

    assert result.root_folder_id == ROOT_FOLDER_ID
    request = seen_requests[0]
    assert str(request.url) == "http://localhost:54321/rest/v1/rpc/create_project_with_folder_template"
    assert "authorization" not in request.headers
    assert json.loads(request.content)["p_created_by"] == str(EMPLOYEE_ID)
    assert json.loads(request.content)["p_folder_template_id"] is None


def test_service_scopes_project_list_to_membership_without_project_manage() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        return Response(200, json=[_project_row()])

    service = ClientsProjectsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    projects = asyncio.run(
        service.list_projects(
            current_user=_current_user(permissions=["project.view"]),
            limit=25,
            offset=10,
        )
    )

    assert projects[0].id == PROJECT_ID
    params = seen_requests[0].url.params
    assert params["project_members.employee_id"] == f"eq.{EMPLOYEE_ID}"
    assert params["project_members.removed_at"] == "is.null"
    assert params["limit"] == "25"
    assert params["offset"] == "10"


def test_service_lists_project_reference_data() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        return Response(
            200,
            json=[
                {
                    "id": str(PROJECT_TYPE_ID),
                    "code": "CONFERENCE",
                    "name": "Conference",
                }
            ],
        )

    service = ClientsProjectsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    project_types = asyncio.run(
        service.list_project_types(current_user=_current_user(permissions=["project.view"]))
    )

    assert project_types[0].id == PROJECT_TYPE_ID
    assert seen_requests[0].url.path == "/rest/v1/project_types"
    assert seen_requests[0].url.params["select"] == "id,code,name"
    assert seen_requests[0].url.params["is_active"] == "eq.true"
    assert seen_requests[0].url.params["order"] == "name.asc"


def test_service_lists_project_members_with_employee_summary() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        return Response(200, json=[_project_member_row()])

    service = ClientsProjectsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    members = asyncio.run(
        service.list_project_members(
            project_id=PROJECT_ID,
            current_user=_current_user(permissions=["project.manage"]),
        )
    )

    assert members[0].employee is not None
    assert members[0].employee.full_name == "Example Employee"
    assert seen_requests[0].url.path == "/rest/v1/project_members"
    assert seen_requests[0].url.params["project_id"] == f"eq.{PROJECT_ID}"
    assert seen_requests[0].url.params["removed_at"] == "is.null"
    assert seen_requests[0].url.params["order"] == "assigned_at.desc"


def test_service_soft_deletes_project_through_audited_rpc() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/project_members":
            return Response(
                200,
                json=[
                    {
                        "project_id": str(PROJECT_ID),
                        "employee_id": str(EMPLOYEE_ID),
                        "access_level": "MANAGE",
                        "removed_at": None,
                    }
                ],
            )
        return Response(200, json=_project_row())

    service = ClientsProjectsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    asyncio.run(
        service.delete_project(
            project_id=PROJECT_ID,
            current_user=_current_user(permissions=["project.manage"]),
            context=AuditContext(request_id=REQUEST_ID),
        )
    )

    request = seen_requests[1]
    assert request.url.path == "/rest/v1/rpc/soft_delete_project_audited"
    assert json.loads(request.content) == {
        "p_project_id": str(PROJECT_ID),
        "p_actor_user_account_id": str(AUTH_USER_ID),
        "p_actor_employee_id": str(EMPLOYEE_ID),
        "p_request_id": str(REQUEST_ID),
        "p_ip_address": None,
        "p_user_agent": None,
    }


def test_service_deactivates_client_through_audited_rpc() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        return Response(200, json={**_client_row(), "is_active": False})

    service = ClientsProjectsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    asyncio.run(
        service.delete_client(
            client_id=CLIENT_ID,
            current_user=_current_user(permissions=["project.manage"]),
            context=AuditContext(request_id=REQUEST_ID),
        )
    )

    request = seen_requests[0]
    assert request.url.path == "/rest/v1/rpc/deactivate_client_audited"
    assert json.loads(request.content) == {
        "p_client_id": str(CLIENT_ID),
        "p_actor_user_account_id": str(AUTH_USER_ID),
        "p_actor_employee_id": str(EMPLOYEE_ID),
        "p_request_id": str(REQUEST_ID),
        "p_ip_address": None,
        "p_user_agent": None,
    }


def test_service_rejects_project_member_list_without_membership() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        return Response(200, json=[])

    service = ClientsProjectsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ClientsProjectsError) as exc_info:
        asyncio.run(
            service.list_project_members(
                project_id=PROJECT_ID,
                current_user=_current_user(permissions=["project.view"]),
            )
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "NOT_FOUND"
    assert seen_requests[0].url.path == "/rest/v1/project_members"
    assert seen_requests[0].url.params["employee_id"] == f"eq.{EMPLOYEE_ID}"


def test_service_updates_project_member_access_level_through_audited_rpc() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/project_members":
            return Response(
                200,
                json=[
                    {
                        "project_id": str(PROJECT_ID),
                        "employee_id": str(EMPLOYEE_ID),
                        "access_level": "MANAGE",
                        "removed_at": None,
                    }
                ],
            )
        return Response(
            200,
            json={
                "project_id": str(PROJECT_ID),
                "employee_id": str(OTHER_EMPLOYEE_ID),
                "access_level": "CONTRIBUTE",
                "assigned_by": str(EMPLOYEE_ID),
                "assigned_at": CREATED_AT,
                "removed_at": None,
            },
        )

    service = ClientsProjectsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.update_project_member(
            project_id=PROJECT_ID,
            employee_id=OTHER_EMPLOYEE_ID,
            payload=ProjectMemberUpdate(access_level="CONTRIBUTE"),
            current_user=_current_user(permissions=["project.manage"]),
            context=AuditContext(request_id=REQUEST_ID),
        )
    )

    assert result.access_level == "CONTRIBUTE"
    request = seen_requests[1]
    assert request.url.path == "/rest/v1/rpc/upsert_project_member_audited"
    assert json.loads(request.content) == {
        "p_project_id": str(PROJECT_ID),
        "p_employee_id": str(OTHER_EMPLOYEE_ID),
        "p_access_level": "CONTRIBUTE",
        "p_actor_user_account_id": str(AUTH_USER_ID),
        "p_actor_employee_id": str(EMPLOYEE_ID),
        "p_request_id": str(REQUEST_ID),
        "p_ip_address": None,
        "p_user_agent": None,
    }


def test_service_builds_folder_tree_from_flat_rows() -> None:
    def handler(request: httpx.Request) -> Response:
        assert request.url.path == "/rest/v1/folders"
        return Response(
            200,
            json=[
                {
                    "id": str(CHILD_FOLDER_ID),
                    "project_id": str(PROJECT_ID),
                    "parent_folder_id": str(ROOT_FOLDER_ID),
                    "name": "01 Client Brief",
                    "sort_order": 10,
                },
                {
                    "id": str(ROOT_FOLDER_ID),
                    "project_id": str(PROJECT_ID),
                    "parent_folder_id": None,
                    "name": "IEMS-2026-001",
                    "sort_order": 0,
                },
            ],
        )

    service = ClientsProjectsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    tree = asyncio.run(
        service.get_folder_tree(
            project_id=PROJECT_ID,
            current_user=_current_user(permissions=["project.manage"]),
        )
    )

    assert tree.id == ROOT_FOLDER_ID
    assert tree.children[0].id == CHILD_FOLDER_ID


def test_service_maps_last_project_manager_removal_to_conflict() -> None:
    def handler(request: httpx.Request) -> Response:
        if request.url.path == "/rest/v1/rpc/remove_project_member_audited":
            return Response(
                400,
                json={
                    "code": "P0001",
                    "message": "IEMS_LAST_PROJECT_MANAGER",
                },
            )
        return Response(500)

    service = ClientsProjectsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(ClientsProjectsError) as exc_info:
        asyncio.run(
            service.remove_project_member(
                project_id=PROJECT_ID,
                employee_id=EMPLOYEE_ID,
                current_user=_current_user(permissions=["project.manage"], is_super_user=True),
                context=AuditContext(request_id=REQUEST_ID),
            )
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.code == "INVALID_PROJECT_MEMBER_STATE"
