import asyncio
from datetime import date, datetime
from uuid import UUID

from httpx import ASGITransport, AsyncClient, Response

from app.api.dependencies import get_admin_service, get_current_user
from app.main import app
from app.schemas.admin import (
    AuditEventExplorerResponse,
    DepartmentAssignmentCreate,
    DepartmentAssignmentResponse,
    EmployeeAdminCreate,
    EmployeeAdminResponse,
    EmployeeAdminUpdate,
    FolderTemplateCreate,
    FolderTemplateResponse,
    PolicyCreate,
    PolicyResponse,
    PolicyUpdate,
    RoleAssignmentCreate,
    RoleAssignmentResponse,
    RoleResponse,
)
from app.schemas.clients_projects import ReferenceSummary
from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount

AUTH_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
OTHER_EMPLOYEE_ID = UUID("33333333-3333-4333-8333-333333333333")
ROLE_ID = UUID("44444444-4444-4444-8444-444444444444")
DEPARTMENT_ID = UUID("55555555-5555-4555-8555-555555555555")
POLICY_ID = UUID("66666666-6666-4666-8666-666666666666")
TEMPLATE_ID = UUID("77777777-7777-4777-8777-777777777777")
AUDIT_EVENT_ID = UUID("88888888-8888-4888-8888-888888888888")
CREATED_AT = datetime(2026, 6, 16, 9, 0, 0)


class RecordingAdminService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object, CurrentUser, str | None]] = []

    async def list_departments(self, *, current_user: CurrentUser) -> list[ReferenceSummary]:
        self.calls.append(("list_departments", None, current_user, None))
        return [ReferenceSummary(id=DEPARTMENT_ID, code="OPS", name="Operations")]

    async def list_roles(self, *, current_user: CurrentUser) -> list[RoleResponse]:
        self.calls.append(("list_roles", None, current_user, None))
        return [RoleResponse(id=ROLE_ID, code="MANAGER", name="Manager", description=None)]

    async def get_employee(
        self,
        *,
        employee_id: UUID,
        current_user: CurrentUser,
    ) -> EmployeeAdminResponse:
        self.calls.append(("get_employee", employee_id, current_user, None))
        return _employee_response(employee_id)

    async def create_employee(
        self,
        *,
        payload: EmployeeAdminCreate,
        current_user: CurrentUser,
        context: object,
        override_reason: str | None,
    ) -> EmployeeAdminResponse:
        self.calls.append(("create_employee", payload, current_user, override_reason))
        return _employee_response(OTHER_EMPLOYEE_ID)

    async def update_employee(
        self,
        *,
        employee_id: UUID,
        payload: EmployeeAdminUpdate,
        current_user: CurrentUser,
        context: object,
        override_reason: str | None,
    ) -> EmployeeAdminResponse:
        self.calls.append(
            ("update_employee", (employee_id, payload), current_user, override_reason)
        )
        return _employee_response(employee_id, designation=payload.designation)

    async def assign_employee_role(
        self,
        *,
        employee_id: UUID,
        payload: RoleAssignmentCreate,
        current_user: CurrentUser,
        context: object,
        override_reason: str | None,
    ) -> RoleAssignmentResponse:
        self.calls.append(
            ("assign_employee_role", (employee_id, payload), current_user, override_reason)
        )
        return RoleAssignmentResponse(
            employee_id=employee_id,
            user_account_id=AUTH_USER_ID,
            role=RoleResponse(id=payload.role_id, code="MANAGER", name="Manager", description=None),
            assigned_at=CREATED_AT,
            expires_at=payload.expires_at,
        )

    async def remove_employee_role(
        self,
        *,
        employee_id: UUID,
        role_id: UUID,
        current_user: CurrentUser,
        context: object,
        override_reason: str | None,
    ) -> None:
        self.calls.append(
            ("remove_employee_role", (employee_id, role_id), current_user, override_reason)
        )

    async def assign_employee_department(
        self,
        *,
        employee_id: UUID,
        payload: DepartmentAssignmentCreate,
        current_user: CurrentUser,
        context: object,
        override_reason: str | None,
    ) -> DepartmentAssignmentResponse:
        self.calls.append(
            ("assign_employee_department", (employee_id, payload), current_user, override_reason)
        )
        return DepartmentAssignmentResponse(
            id=UUID("99999999-9999-4999-8999-999999999999"),
            employee_id=employee_id,
            department=ReferenceSummary(id=payload.department_id, code="OPS", name="Operations"),
            valid_from=payload.valid_from,
            valid_to=None,
            assigned_by=EMPLOYEE_ID,
        )

    async def list_policies(
        self,
        *,
        current_user: CurrentUser,
        limit: int,
        offset: int,
    ) -> list[PolicyResponse]:
        self.calls.append(("list_policies", (limit, offset), current_user, None))
        return [_policy_response()]

    async def create_policy(
        self,
        *,
        payload: PolicyCreate,
        current_user: CurrentUser,
        context: object,
        override_reason: str | None,
    ) -> PolicyResponse:
        self.calls.append(("create_policy", payload, current_user, override_reason))
        return _policy_response(name=payload.name)

    async def update_policy(
        self,
        *,
        policy_id: UUID,
        payload: PolicyUpdate,
        current_user: CurrentUser,
        context: object,
        override_reason: str | None,
    ) -> PolicyResponse:
        self.calls.append(("update_policy", (policy_id, payload), current_user, override_reason))
        return _policy_response(policy_id=policy_id, priority=payload.priority or 100)

    async def list_audit_events(
        self,
        *,
        current_user: CurrentUser,
        limit: int,
        offset: int,
        action_code: str | None,
        resource_type: str | None,
        resource_id: UUID | None,
        actor_employee_id: UUID | None,
        created_from: datetime | None,
        created_to: datetime | None,
        context: object,
    ) -> list[AuditEventExplorerResponse]:
        self.calls.append(
            (
                "list_audit_events",
                (
                    limit,
                    offset,
                    action_code,
                    resource_type,
                    resource_id,
                    actor_employee_id,
                    created_from,
                    created_to,
                ),
                current_user,
                None,
            )
        )
        return [_audit_event_response()]

    async def list_folder_templates(
        self,
        *,
        current_user: CurrentUser,
        include_inactive: bool,
    ) -> list[FolderTemplateResponse]:
        self.calls.append(("list_folder_templates", include_inactive, current_user, None))
        return [_folder_template_response()]

    async def create_folder_template(
        self,
        *,
        payload: FolderTemplateCreate,
        current_user: CurrentUser,
        context: object,
        override_reason: str | None,
    ) -> FolderTemplateResponse:
        self.calls.append(("create_folder_template", payload, current_user, override_reason))
        return _folder_template_response(name=payload.name)


def _current_user(*, permissions: list[str], is_super_user: bool = False) -> CurrentUser:
    return CurrentUser(
        auth_user_id=AUTH_USER_ID,
        account=UserAccount(is_active=True, is_super_user=is_super_user),
        employee=EmployeeProfile(
            id=EMPLOYEE_ID,
            employee_code="IEMS-001",
            full_name="Example Employee",
            official_email="admin@iemsnewdelhi.com",
            designation="Admin",
            employment_status="ACTIVE",
        ),
        roles=["SUPER_USER"] if is_super_user else ["ADMIN"],
        permissions=permissions,
    )


def _employee_response(
    employee_id: UUID,
    *,
    designation: str | None = "Coordinator",
) -> EmployeeAdminResponse:
    return EmployeeAdminResponse(
        id=employee_id,
        employee_code="IEMS-OPS-010",
        full_name="New Employee",
        official_email="new.employee@iemsnewdelhi.com",
        phone="+91-99999-00000",
        designation=designation,
        employment_status="ACTIVE",
        joined_on=date(2026, 6, 1),
        left_on=None,
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
        current_department=None,
        roles=[],
        account=None,
    )


def _policy_response(
    *,
    policy_id: UUID = POLICY_ID,
    name: str = "Project managers can upload",
    priority: int = 100,
) -> PolicyResponse:
    return PolicyResponse(
        id=policy_id,
        name=name,
        action_code="document.upload",
        effect="ALLOW",
        priority=priority,
        conditions={"role": "MANAGER"},
        is_active=True,
        created_by=AUTH_USER_ID,
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
    )


def _audit_event_response() -> AuditEventExplorerResponse:
    return AuditEventExplorerResponse(
        id=AUDIT_EVENT_ID,
        action_code="policy.changed",
        resource_type="policy",
        resource_id=POLICY_ID,
        actor_employee_id=EMPLOYEE_ID,
        actor=None,
        request_id=None,
        old_values={"priority": 100},
        new_values={"priority": 10},
        metadata={"source": "admin"},
        created_at=CREATED_AT,
    )


def _folder_template_response(
    *,
    name: str = "Standard Event Project",
) -> FolderTemplateResponse:
    return FolderTemplateResponse(
        id=TEMPLATE_ID,
        name=name,
        project_type_id=None,
        is_active=True,
        created_by=EMPLOYEE_ID,
        created_at=CREATED_AT,
        items=[],
    )


async def _request(
    method: str,
    path: str,
    *,
    json_body: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.request(method, path, json=json_body, headers=headers)


def _install_overrides(
    *,
    current_user: CurrentUser,
    service: RecordingAdminService | None = None,
) -> RecordingAdminService:
    installed_service = service or RecordingAdminService()

    async def override_current_user() -> CurrentUser:
        return current_user

    async def override_admin_service() -> RecordingAdminService:
        return installed_service

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_admin_service] = override_admin_service
    return installed_service


def test_create_employee_requires_employee_manage_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["employee.view"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                "/v1/employees",
                json_body={
                    "employee_code": "IEMS-OPS-010",
                    "full_name": "New Employee",
                    "official_email": "new.employee@iemsnewdelhi.com",
                    "employment_status": "ACTIVE",
                },
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert service.calls == []


def test_create_employee_passes_override_reason_to_service() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["employee.manage"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                "/v1/employees",
                json_body={
                    "employee_code": "IEMS-OPS-010",
                    "full_name": "New Employee",
                    "official_email": "new.employee@iemsnewdelhi.com",
                    "employment_status": "ACTIVE",
                },
                headers={
                    "Authorization": "Bearer test-token",
                    "X-IEMS-Override-Reason": "Emergency employee setup",
                },
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert service.calls[0][0] == "create_employee"
    assert service.calls[0][3] == "Emergency employee setup"


def test_assign_role_requires_role_manage_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["employee.manage"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                f"/v1/employees/{OTHER_EMPLOYEE_ID}/roles",
                json_body={"role_id": str(ROLE_ID)},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert service.calls == []


def test_delete_employee_role_returns_no_content() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["role.manage"]))
    try:
        response = asyncio.run(
            _request(
                "DELETE",
                f"/v1/employees/{OTHER_EMPLOYEE_ID}/roles/{ROLE_ID}",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert service.calls[0][0] == "remove_employee_role"


def test_policy_write_requires_policy_manage_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["audit.view"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                "/v1/policies",
                json_body={
                    "name": "Project managers can upload",
                    "action_code": "document.upload",
                    "effect": "ALLOW",
                    "priority": 100,
                    "conditions": {"role": "MANAGER"},
                    "is_active": True,
                },
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert service.calls == []


def test_audit_explorer_requires_audit_view_and_passes_filters() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["audit.view"]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                f"/v1/audit-events?action_code=policy.changed&resource_type=policy&resource_id={POLICY_ID}&limit=10&offset=2",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["old_values"] == {"priority": 100}
    assert payload[0]["metadata"] == {"source": "admin"}
    assert service.calls[0][0] == "list_audit_events"
    assert service.calls[0][1][0:5] == (
        10,
        2,
        "policy.changed",
        "policy",
        POLICY_ID,
    )


def test_folder_template_create_requires_folder_template_manage() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["policy.manage"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                "/v1/folder-templates",
                json_body={"name": "Standard Event Project", "project_type_id": None},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert service.calls == []
