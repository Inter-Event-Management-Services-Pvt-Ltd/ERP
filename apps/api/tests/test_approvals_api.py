import asyncio
from datetime import UTC, datetime
from uuid import UUID

from httpx import ASGITransport, AsyncClient, Response

from app.api.dependencies import get_current_user
from app.core.audit import AuditContext
from app.main import app
from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount

AUTH_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
OTHER_EMPLOYEE_ID = UUID("33333333-3333-4333-8333-333333333333")
PROJECT_ID = UUID("44444444-4444-4444-8444-444444444444")
APPROVAL_TYPE_ID = UUID("55555555-5555-4555-8555-555555555555")
APPROVAL_ID = UUID("66666666-6666-4666-8666-666666666666")
ACTION_ID = UUID("77777777-7777-4777-8777-777777777777")
REQUEST_ID = UUID("88888888-8888-4888-8888-888888888888")
CREATED_AT = datetime(2026, 6, 16, 10, 0, tzinfo=UTC)


class RecordingApprovalsService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object, CurrentUser, AuditContext | None]] = []

    async def list_approval_types(self, *, current_user: CurrentUser) -> list[object]:
        self.calls.append(("list_approval_types", None, current_user, None))
        return [_reference_summary()]

    async def list_approvals(
        self,
        *,
        current_user: CurrentUser,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[object]:
        self.calls.append(("list_approvals", (status, limit, offset), current_user, None))
        return [_approval_response()]

    async def create_approval(
        self,
        *,
        payload: object,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> object:
        self.calls.append(("create_approval", payload, current_user, context))
        return _approval_response()

    async def get_approval(self, *, approval_id: UUID, current_user: CurrentUser) -> object:
        self.calls.append(("get_approval", approval_id, current_user, None))
        return _approval_response()

    async def approve_approval(
        self,
        *,
        approval_id: UUID,
        comment: str | None,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> object:
        self.calls.append(("approve_approval", (approval_id, comment), current_user, context))
        return _approval_response(status="APPROVED", action="APPROVED")

    async def reject_approval(
        self,
        *,
        approval_id: UUID,
        comment: str | None,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> object:
        self.calls.append(("reject_approval", (approval_id, comment), current_user, context))
        return _approval_response(status="REJECTED", action="REJECTED")

    async def request_revision(
        self,
        *,
        approval_id: UUID,
        comment: str,
        current_user: CurrentUser,
        context: AuditContext,
    ) -> object:
        self.calls.append(("request_revision", (approval_id, comment), current_user, context))
        return _approval_response(status="REVISION_REQUESTED", action="REVISION_REQUESTED")


def _reference_summary() -> object:
    from app.schemas.clients_projects import ReferenceSummary

    return ReferenceSummary(
        id=APPROVAL_TYPE_ID,
        code="PROJECT_CLOSURE",
        name="Project Closure",
    )


def _employee_summary(employee_id: UUID = EMPLOYEE_ID) -> object:
    from app.schemas.clients_projects import EmployeeSummary

    return EmployeeSummary(
        id=employee_id,
        employee_code="IEMS-001",
        full_name="Example Employee",
    )


def _approval_response(
    *,
    status: str = "PENDING",
    action: str = "SUBMITTED",
) -> object:
    from app.schemas.approvals import ApprovalActionResponse, ApprovalRequestResponse

    return ApprovalRequestResponse(
        id=APPROVAL_ID,
        approval_type_id=APPROVAL_TYPE_ID,
        approval_type=_reference_summary(),
        project_id=PROJECT_ID,
        document_version_id=None,
        archive_export_id=None,
        leave_request_id=None,
        requested_by=EMPLOYEE_ID,
        requested_by_employee=_employee_summary(),
        assigned_to=OTHER_EMPLOYEE_ID,
        assigned_to_employee=_employee_summary(OTHER_EMPLOYEE_ID),
        status=status,
        requested_at=CREATED_AT,
        completed_at=CREATED_AT if status != "PENDING" else None,
        actions=[
            ApprovalActionResponse(
                id=ACTION_ID,
                approval_request_id=APPROVAL_ID,
                action=action,
                performed_by=EMPLOYEE_ID,
                performed_by_employee=_employee_summary(),
                comment="Looks correct",
                created_at=CREATED_AT,
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
        roles=["SUPER_USER"] if is_super_user else ["EMPLOYEE"],
        permissions=permissions,
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
    service: RecordingApprovalsService | None = None,
) -> RecordingApprovalsService:
    from app.api.dependencies import get_approvals_service

    installed_service = service or RecordingApprovalsService()

    async def override_current_user() -> CurrentUser:
        return current_user

    async def override_approvals_service() -> RecordingApprovalsService:
        return installed_service

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_approvals_service] = override_approvals_service
    return installed_service


def test_list_approval_types_returns_reference_rows() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/approval-types",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["code"] == "PROJECT_CLOSURE"
    assert service.calls[0][0] == "list_approval_types"


def test_list_approvals_passes_status_and_pagination() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/approvals?status=PENDING&limit=10&offset=5",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["actions"][0]["action"] == "SUBMITTED"
    assert service.calls[0][0] == "list_approvals"
    assert service.calls[0][1] == ("PENDING", 10, 5)


def test_create_approval_records_audit_context() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["project.manage"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                "/v1/approvals",
                json={
                    "approval_type_id": str(APPROVAL_TYPE_ID),
                    "project_id": str(PROJECT_ID),
                    "assigned_to": str(OTHER_EMPLOYEE_ID),
                    "comment": "Please review project closure.",
                },
                headers={"Authorization": "Bearer test-token", "X-Request-ID": str(REQUEST_ID)},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["status"] == "PENDING"
    assert service.calls[0][0] == "create_approval"
    assert service.calls[0][3] == AuditContext(
        request_id=REQUEST_ID,
        ip_address="127.0.0.1",
        user_agent="python-httpx/0.28.1",
    )


def test_get_approval_returns_comment_history() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "GET",
                f"/v1/approvals/{APPROVAL_ID}",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["actions"][0]["comment"] == "Looks correct"
    assert service.calls[0][0] == "get_approval"
    assert service.calls[0][1] == APPROVAL_ID


def test_approve_approval_requires_approval_permission() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                f"/v1/approvals/{APPROVAL_ID}/approve",
                json={"comment": "Approved"},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert service.calls == []


def test_approve_approval_returns_approved_request() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["approval.approve"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                f"/v1/approvals/{APPROVAL_ID}/approve",
                json={"comment": "Approved"},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"
    assert response.json()["actions"][0]["action"] == "APPROVED"
    assert service.calls[0][0] == "approve_approval"
    assert service.calls[0][1] == (APPROVAL_ID, "Approved")


def test_reject_approval_returns_rejected_request() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["approval.approve"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                f"/v1/approvals/{APPROVAL_ID}/reject",
                json={"comment": "Missing final invoice."},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"
    assert service.calls[0][0] == "reject_approval"


def test_request_revision_requires_meaningful_comment() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["approval.approve"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                f"/v1/approvals/{APPROVAL_ID}/request-revision",
                json={},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert service.calls == []


def test_request_revision_returns_revision_requested_request() -> None:
    service = _install_overrides(current_user=_current_user(permissions=["approval.approve"]))
    try:
        response = asyncio.run(
            _request(
                "POST",
                f"/v1/approvals/{APPROVAL_ID}/request-revision",
                json={"comment": "Upload the signed approval letter."},
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "REVISION_REQUESTED"
    assert service.calls[0][0] == "request_revision"
