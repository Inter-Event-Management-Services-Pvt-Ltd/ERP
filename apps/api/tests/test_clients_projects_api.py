import asyncio
from datetime import UTC, date, datetime
from uuid import UUID

from httpx import ASGITransport, AsyncClient, Response

from app.api.dependencies import get_clients_projects_service, get_current_user
from app.core.audit import AuditContext
from app.main import app
from app.schemas.clients_projects import (
    ClientCreate,
    ClientResponse,
    ClientUpdate,
    EmployeeSummary,
    FolderTreeNode,
    ProjectCreate,
    ProjectMemberCreate,
    ProjectMemberDetailResponse,
    ProjectMemberResponse,
    ProjectMemberUpdate,
    ProjectResponse,
    ProjectSummaryClient,
    ProjectUpdate,
    ReferenceSummary,
)
from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount

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

CREATED_AT = datetime(2026, 6, 5, 9, 0, tzinfo=UTC)
UPDATED_AT = datetime(2026, 6, 5, 9, 30, tzinfo=UTC)


class RecordingClientsProjectsService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object, CurrentUser, AuditContext | None]] = []

    async def list_clients(
        self,
        *,
        current_user: CurrentUser,
        include_inactive: bool = False,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ClientResponse]:
        self.calls.append(
            ("list_clients", (include_inactive, search, limit, offset), current_user, None)
        )
        return [_client_response()]

    async def create_client(
        self,
        *,
        payload: ClientCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ClientResponse:
        self.calls.append(("create_client", payload, current_user, context))
        return _client_response()

    async def get_client(
        self,
        *,
        client_id: UUID,
        current_user: CurrentUser,
    ) -> ClientResponse:
        self.calls.append(("get_client", client_id, current_user, None))
        return _client_response()

    async def update_client(
        self,
        *,
        client_id: UUID,
        payload: ClientUpdate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ClientResponse:
        self.calls.append(("update_client", (client_id, payload), current_user, context))
        return _client_response()

    async def delete_client(
        self,
        *,
        client_id: UUID,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> None:
        self.calls.append(("delete_client", client_id, current_user, context))

    async def list_projects(
        self,
        *,
        current_user: CurrentUser,
        client_id: UUID | None = None,
        include_archived: bool = False,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ProjectResponse]:
        self.calls.append(
            (
                "list_projects",
                (client_id, include_archived, search, limit, offset),
                current_user,
                None,
            )
        )
        return [_project_response()]

    async def list_project_types(
        self,
        *,
        current_user: CurrentUser,
    ) -> list[ReferenceSummary]:
        self.calls.append(("list_project_types", None, current_user, None))
        return [_reference_summary(PROJECT_TYPE_ID, "CONFERENCE", "Conference")]

    async def list_project_statuses(
        self,
        *,
        current_user: CurrentUser,
    ) -> list[ReferenceSummary]:
        self.calls.append(("list_project_statuses", None, current_user, None))
        return [_reference_summary(PROJECT_STATUS_ID, "PLANNING", "Planning")]

    async def list_priority_levels(
        self,
        *,
        current_user: CurrentUser,
    ) -> list[ReferenceSummary]:
        self.calls.append(("list_priority_levels", None, current_user, None))
        return [_reference_summary(PRIORITY_LEVEL_ID, "NORMAL", "Normal")]

    async def create_project(
        self,
        *,
        payload: ProjectCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ProjectResponse:
        self.calls.append(("create_project", payload, current_user, context))
        return _project_response()

    async def get_project(
        self,
        *,
        project_id: UUID,
        current_user: CurrentUser,
    ) -> ProjectResponse:
        self.calls.append(("get_project", project_id, current_user, None))
        return _project_response()

    async def update_project(
        self,
        *,
        project_id: UUID,
        payload: ProjectUpdate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ProjectResponse:
        self.calls.append(("update_project", (project_id, payload), current_user, context))
        return _project_response()

    async def delete_project(
        self,
        *,
        project_id: UUID,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> None:
        self.calls.append(("delete_project", project_id, current_user, context))

    async def add_project_member(
        self,
        *,
        project_id: UUID,
        payload: ProjectMemberCreate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ProjectMemberResponse:
        self.calls.append(("add_project_member", (project_id, payload), current_user, context))
        return ProjectMemberResponse(
            project_id=project_id,
            employee_id=payload.employee_id,
            access_level=payload.access_level,
            assigned_by=current_user.employee.id,
            assigned_at=CREATED_AT,
            removed_at=None,
        )

    async def list_project_members(
        self,
        *,
        project_id: UUID,
        current_user: CurrentUser,
    ) -> list[ProjectMemberDetailResponse]:
        self.calls.append(("list_project_members", project_id, current_user, None))
        return [
            ProjectMemberDetailResponse(
                project_id=project_id,
                employee_id=EMPLOYEE_ID,
                employee=EmployeeSummary(
                    id=EMPLOYEE_ID,
                    employee_code="IEMS-001",
                    full_name="Example Employee",
                ),
                access_level="MANAGE",
                assigned_by=EMPLOYEE_ID,
                assigned_at=CREATED_AT,
                removed_at=None,
            )
        ]

    async def update_project_member(
        self,
        *,
        project_id: UUID,
        employee_id: UUID,
        payload: ProjectMemberUpdate,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> ProjectMemberResponse:
        self.calls.append(
            ("update_project_member", (project_id, employee_id, payload), current_user, context)
        )
        return ProjectMemberResponse(
            project_id=project_id,
            employee_id=employee_id,
            access_level=payload.access_level,
            assigned_by=current_user.employee.id,
            assigned_at=CREATED_AT,
            removed_at=None,
        )

    async def remove_project_member(
        self,
        *,
        project_id: UUID,
        employee_id: UUID,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> None:
        self.calls.append(
            ("remove_project_member", (project_id, employee_id), current_user, context)
        )

    async def get_folder_tree(
        self,
        *,
        project_id: UUID,
        current_user: CurrentUser,
    ) -> FolderTreeNode:
        self.calls.append(("get_folder_tree", project_id, current_user, None))
        return FolderTreeNode(
            id=ROOT_FOLDER_ID,
            project_id=project_id,
            parent_folder_id=None,
            name="IEMS-2026-001",
            sort_order=0,
            children=[
                FolderTreeNode(
                    id=CHILD_FOLDER_ID,
                    project_id=project_id,
                    parent_folder_id=ROOT_FOLDER_ID,
                    name="01 Client Brief",
                    sort_order=10,
                    children=[],
                )
            ],
        )


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


def _client_response() -> ClientResponse:
    return ClientResponse(
        id=CLIENT_ID,
        client_code="ACME",
        legal_name="Acme Events Private Limited",
        display_name="Acme Events",
        is_active=True,
        notes="Preferred Delhi NCR client",
        created_at=CREATED_AT,
        updated_at=UPDATED_AT,
    )


def _reference_summary(reference_id: UUID, code: str, name: str) -> ReferenceSummary:
    return ReferenceSummary(id=reference_id, code=code, name=name)


def _project_response() -> ProjectResponse:
    return ProjectResponse(
        id=PROJECT_ID,
        project_code="IEMS-2026-001",
        client_id=CLIENT_ID,
        client=ProjectSummaryClient(
            id=CLIENT_ID,
            client_code="ACME",
            display_name="Acme Events",
        ),
        project_type_id=PROJECT_TYPE_ID,
        project_type=ReferenceSummary(
            id=PROJECT_TYPE_ID,
            code="CONFERENCE",
            name="Conference",
        ),
        project_status_id=PROJECT_STATUS_ID,
        project_status=ReferenceSummary(
            id=PROJECT_STATUS_ID,
            code="PLANNING",
            name="Planning",
        ),
        priority_level_id=PRIORITY_LEVEL_ID,
        priority_level=ReferenceSummary(
            id=PRIORITY_LEVEL_ID,
            code="NORMAL",
            name="Normal",
        ),
        name="Annual Leadership Conference",
        event_date=date(2026, 8, 12),
        venue="New Delhi",
        description="Annual client conference",
        project_manager_id=EMPLOYEE_ID,
        created_by=EMPLOYEE_ID,
        created_at=CREATED_AT,
        updated_at=UPDATED_AT,
        archived_at=None,
        deleted_at=None,
        root_folder_id=ROOT_FOLDER_ID,
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
    service: RecordingClientsProjectsService | None = None,
) -> RecordingClientsProjectsService:
    installed_service = service or RecordingClientsProjectsService()

    async def override_current_user() -> CurrentUser:
        return current_user

    async def override_clients_projects_service() -> RecordingClientsProjectsService:
        return installed_service

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_clients_projects_service] = override_clients_projects_service
    return installed_service


def test_create_client_requires_project_manage_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.view"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                "/v1/clients",
                json={
                    "client_code": "ACME",
                    "legal_name": "Acme Events Private Limited",
                    "display_name": "Acme Events",
                },
                headers={
                    "Authorization": "Bearer test-token",
                    "X-Request-ID": "phase2-client-deny",
                },
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert service.calls == []


def test_create_client_returns_created_client_and_passes_audit_context() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.manage"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                "/v1/clients",
                json={
                    "client_code": "ACME",
                    "legal_name": "Acme Events Private Limited",
                    "display_name": "Acme Events",
                    "notes": "Preferred Delhi NCR client",
                },
                headers={"Authorization": "Bearer test-token", "X-Request-ID": str(ROOT_FOLDER_ID)},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["client_code"] == "ACME"
    assert service.calls[0][0] == "create_client"
    assert isinstance(service.calls[0][1], ClientCreate)
    assert service.calls[0][2].employee.id == EMPLOYEE_ID
    assert service.calls[0][3] == AuditContext(
        request_id=ROOT_FOLDER_ID,
        ip_address="127.0.0.1",
        user_agent="python-httpx/0.28.1",
    )


def test_list_clients_accepts_project_view_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.view"]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/clients?limit=25&offset=5&search=acme",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(CLIENT_ID)
    assert service.calls[0][0] == "list_clients"
    assert service.calls[0][1] == (False, "acme", 25, 5)


def test_get_client_returns_client_detail() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.view"]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                f"/v1/clients/{CLIENT_ID}",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(CLIENT_ID)
    assert service.calls[0][0] == "get_client"


def test_update_client_requires_project_manage_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.view"]))
    try:
        response = asyncio.run(
            _request(
                "PATCH",
                f"/v1/clients/{CLIENT_ID}",
                json={"display_name": "Acme"},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert service.calls == []


def test_update_client_returns_updated_client() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.manage"]))
    try:
        response = asyncio.run(
            _request(
                "PATCH",
                f"/v1/clients/{CLIENT_ID}",
                json={"display_name": "Acme"},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(CLIENT_ID)
    assert service.calls[0][0] == "update_client"


def test_delete_client_requires_project_manage_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.view"]))
    try:
        response = asyncio.run(
            _request(
                "DELETE",
                f"/v1/clients/{CLIENT_ID}",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert service.calls == []


def test_delete_client_deactivates_and_returns_no_content() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.manage"]))
    try:
        response = asyncio.run(
            _request(
                "DELETE",
                f"/v1/clients/{CLIENT_ID}",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert response.content == b""
    assert service.calls[0][0] == "delete_client"


def test_list_projects_accepts_project_view_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.view"]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                f"/v1/projects?client_id={CLIENT_ID}&limit=10&offset=2",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(PROJECT_ID)
    assert service.calls[0][0] == "list_projects"


def test_project_reference_lookups_accept_project_view_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.view"]))
    try:
        project_types = asyncio.run(
            _request(
                "GET",
                "/v1/project-types",
                headers={"Authorization": "Bearer test-token"},
            )
        )
        project_statuses = asyncio.run(
            _request(
                "GET",
                "/v1/project-statuses",
                headers={"Authorization": "Bearer test-token"},
            )
        )
        priority_levels = asyncio.run(
            _request(
                "GET",
                "/v1/priority-levels",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert project_types.status_code == 200
    assert project_types.json() == [
        {"id": str(PROJECT_TYPE_ID), "code": "CONFERENCE", "name": "Conference"}
    ]
    assert project_statuses.status_code == 200
    assert project_statuses.json()[0]["id"] == str(PROJECT_STATUS_ID)
    assert priority_levels.status_code == 200
    assert priority_levels.json()[0]["id"] == str(PRIORITY_LEVEL_ID)
    assert [call[0] for call in service.calls] == [
        "list_project_types",
        "list_project_statuses",
        "list_priority_levels",
    ]


def test_project_reference_lookups_require_project_read_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/project-types",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert service.calls == []


def test_create_project_applies_folder_template_and_returns_root_folder() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.manage"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                "/v1/projects",
                json={
                    "project_code": "IEMS-2026-001",
                    "client_id": str(CLIENT_ID),
                    "project_type_id": str(PROJECT_TYPE_ID),
                    "project_status_id": str(PROJECT_STATUS_ID),
                    "priority_level_id": str(PRIORITY_LEVEL_ID),
                    "name": "Annual Leadership Conference",
                    "event_date": "2026-08-12",
                    "venue": "New Delhi",
                    "description": "Annual client conference",
                    "project_manager_id": str(EMPLOYEE_ID),
                },
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["id"] == str(PROJECT_ID)
    assert response.json()["root_folder_id"] == str(ROOT_FOLDER_ID)
    assert service.calls[0][0] == "create_project"
    assert isinstance(service.calls[0][1], ProjectCreate)


def test_create_project_validation_error_returns_field_details() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.manage"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                "/v1/projects",
                json={
                    "project_code": "IEMS-2026-001",
                    "client_id": "not-a-uuid",
                    "project_type_id": str(PROJECT_TYPE_ID),
                    "project_status_id": str(PROJECT_STATUS_ID),
                    "priority_level_id": str(PRIORITY_LEVEL_ID),
                    "name": "Annual Leadership Conference",
                    "event_date": "2026-08-12",
                    "venue": "New Delhi",
                },
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "VALIDATION_ERROR"
    assert any(
        field["field"] == "body.client_id" and field["type"] == "uuid_parsing"
        for field in payload["error"]["fields"]
    )
    assert service.calls == []


def test_get_project_returns_project_detail() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.view"]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                f"/v1/projects/{PROJECT_ID}",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(PROJECT_ID)
    assert service.calls[0][0] == "get_project"


def test_update_project_returns_updated_project() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.manage"]))
    try:
        response = asyncio.run(
            _request(
                "PATCH",
                f"/v1/projects/{PROJECT_ID}",
                json={"name": "Updated Conference"},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["id"] == str(PROJECT_ID)
    assert service.calls[0][0] == "update_project"


def test_delete_project_requires_project_manage_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.view"]))
    try:
        response = asyncio.run(
            _request(
                "DELETE",
                f"/v1/projects/{PROJECT_ID}",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert service.calls == []


def test_delete_project_soft_deletes_and_returns_no_content() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.manage"]))
    try:
        response = asyncio.run(
            _request(
                "DELETE",
                f"/v1/projects/{PROJECT_ID}",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert response.content == b""
    assert service.calls[0][0] == "delete_project"


def test_add_project_member_requires_project_manage_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.view"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                f"/v1/projects/{PROJECT_ID}/members",
                json={"employee_id": str(OTHER_EMPLOYEE_ID), "access_level": "VIEW"},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert service.calls == []


def test_list_project_members_returns_active_member_details() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.view"]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                f"/v1/projects/{PROJECT_ID}/members",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {
            "project_id": str(PROJECT_ID),
            "employee_id": str(EMPLOYEE_ID),
            "employee": {
                "id": str(EMPLOYEE_ID),
                "employee_code": "IEMS-001",
                "full_name": "Example Employee",
            },
            "access_level": "MANAGE",
            "assigned_by": str(EMPLOYEE_ID),
            "assigned_at": CREATED_AT.isoformat().replace("+00:00", "Z"),
            "removed_at": None,
        }
    ]
    assert service.calls[0][0] == "list_project_members"


def test_update_project_member_requires_project_manage_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.view"]))
    try:
        response = asyncio.run(
            _request(
                "PATCH",
                f"/v1/projects/{PROJECT_ID}/members/{OTHER_EMPLOYEE_ID}",
                json={"access_level": "CONTRIBUTE"},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert service.calls == []


def test_update_project_member_changes_access_level() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.manage"]))
    try:
        response = asyncio.run(
            _request(
                "PATCH",
                f"/v1/projects/{PROJECT_ID}/members/{OTHER_EMPLOYEE_ID}",
                json={"access_level": "CONTRIBUTE"},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["access_level"] == "CONTRIBUTE"
    assert service.calls[0][0] == "update_project_member"
    assert isinstance(service.calls[0][1][2], ProjectMemberUpdate)


def test_remove_project_member_returns_no_content() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.manage"]))
    try:
        response = asyncio.run(
            _request(
                "DELETE",
                f"/v1/projects/{PROJECT_ID}/members/{OTHER_EMPLOYEE_ID}",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert response.content == b""
    assert service.calls[0][0] == "remove_project_member"


def test_folder_tree_requires_project_view_permission_and_returns_hierarchy() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.view"]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                f"/v1/projects/{PROJECT_ID}/folders/tree",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(ROOT_FOLDER_ID)
    assert payload["children"][0]["name"] == "01 Client Brief"
    assert service.calls[0][0] == "get_folder_tree"
