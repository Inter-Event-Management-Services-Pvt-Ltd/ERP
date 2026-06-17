import asyncio
from datetime import UTC, date, datetime
from uuid import UUID

from httpx import ASGITransport, AsyncClient, Response

from app.api.dependencies import get_audit_writer, get_current_user
from app.core.audit import AuditContext, AuditEvent
from app.main import app
from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount

AUTH_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
PROJECT_ID = UUID("33333333-3333-4333-8333-333333333333")
APPROVAL_ID = UUID("44444444-4444-4444-8444-444444444444")
TASK_ID = UUID("55555555-5555-4555-8555-555555555555")
PHYSICAL_FILE_ID = UUID("66666666-6666-4666-8666-666666666666")
AUDIT_EVENT_ID = UUID("77777777-7777-4777-8777-777777777777")
REQUEST_ID = UUID("88888888-8888-4888-8888-888888888888")
CALENDAR_EVENT_ID = UUID("99999999-9999-4999-8999-999999999999")
DOCUMENT_TYPE_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
CREATED_AT = datetime(2026, 6, 16, 9, 0, tzinfo=UTC)


class RecordingDirectorDashboardService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object, CurrentUser]] = []

    async def get_overview(self, *, current_user: CurrentUser) -> object:
        self.calls.append(("get_overview", None, current_user))
        return _overview_response()

    async def list_projects(
        self,
        *,
        current_user: CurrentUser,
        limit: int,
        offset: int,
    ) -> list[object]:
        self.calls.append(("list_projects", (limit, offset), current_user))
        return [_project_response()]

    async def list_approvals(
        self,
        *,
        current_user: CurrentUser,
        status: str | None,
        limit: int,
        offset: int,
    ) -> list[object]:
        self.calls.append(("list_approvals", (status, limit, offset), current_user))
        return [_approval_response()]

    async def list_overdue_tasks(
        self,
        *,
        current_user: CurrentUser,
        limit: int,
        offset: int,
    ) -> list[object]:
        self.calls.append(("list_overdue_tasks", (limit, offset), current_user))
        return [_overdue_task_response()]

    async def list_physical_files(
        self,
        *,
        current_user: CurrentUser,
        limit: int,
        offset: int,
    ) -> list[object]:
        self.calls.append(("list_physical_files", (limit, offset), current_user))
        return [_physical_file_response()]

    async def list_upcoming_events(
        self,
        *,
        current_user: CurrentUser,
        limit: int,
        offset: int,
    ) -> list[object]:
        self.calls.append(("list_upcoming_events", (limit, offset), current_user))
        return [_upcoming_event_response()]

    async def list_missing_required_documents(
        self,
        *,
        current_user: CurrentUser,
        limit: int,
        offset: int,
    ) -> list[object]:
        self.calls.append(("list_missing_required_documents", (limit, offset), current_user))
        return [_missing_required_document_response()]

    async def list_verification_reminders(
        self,
        *,
        current_user: CurrentUser,
        limit: int,
        offset: int,
    ) -> list[object]:
        self.calls.append(("list_verification_reminders", (limit, offset), current_user))
        return [_verification_reminder_response()]

    async def list_audit_events(
        self,
        *,
        current_user: CurrentUser,
        limit: int,
        offset: int,
        action_code: str | None,
        resource_type: str | None,
    ) -> list[object]:
        self.calls.append(
            ("list_audit_events", (limit, offset, action_code, resource_type), current_user)
        )
        return [_audit_event_response()]


class RecordingAuditWriter:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    async def write_event(self, event: AuditEvent) -> UUID:
        self.events.append(event)
        return AUDIT_EVENT_ID


def _overview_response() -> object:
    from app.schemas.director_dashboard import (
        DirectorArchiveMetrics,
        DirectorAttendanceMetrics,
        DirectorOverviewResponse,
        DirectorProjectMetrics,
    )

    return DirectorOverviewResponse(
        generated_at=CREATED_AT,
        attendance=DirectorAttendanceMetrics(
            active_employee_count=3,
            checked_in_count=1,
            checked_out_count=1,
            absent_or_not_checked_in_count=1,
            total_minutes_today=510,
        ),
        projects=DirectorProjectMetrics(
            active_count=2,
            planning_count=1,
            completed_count=0,
            archived_count=0,
        ),
        pending_approval_count=1,
        overdue_task_count=1,
        physical_archive=DirectorArchiveMetrics(
            checked_out_count=1,
            overdue_return_count=1,
            verification_due_count=1,
            missing_count=0,
        ),
        recent_audit_events=[_audit_event_response()],
    )


def _project_response() -> object:
    from app.schemas.director_dashboard import DirectorProjectSummaryResponse

    return DirectorProjectSummaryResponse(
        id=PROJECT_ID,
        project_code="IEMS-2026-001",
        name="Annual Leadership Conference",
        client_name="Acme Events",
        project_status="ACTIVE",
        priority_level="HIGH",
        event_date=date(2026, 8, 12),
        project_manager_name="Aarav Mehta",
        archived_at=None,
    )


def _approval_response() -> object:
    from app.schemas.director_dashboard import DirectorApprovalSummaryResponse

    return DirectorApprovalSummaryResponse(
        id=APPROVAL_ID,
        approval_type="DOCUMENT_APPROVAL",
        status="PENDING",
        requested_at=CREATED_AT,
        requested_by_name="Nisha Rao",
        assigned_to_name="IEMS Director",
        project_code="IEMS-2026-001",
        project_name="Annual Leadership Conference",
    )


def _overdue_task_response() -> object:
    from app.schemas.director_dashboard import DirectorOverdueTaskResponse

    return DirectorOverdueTaskResponse(
        id=TASK_ID,
        title="Close vendor reconciliation",
        due_at=CREATED_AT,
        project_code="IEMS-2026-001",
        project_name="Annual Leadership Conference",
        assignees="Nisha Rao",
    )


def _physical_file_response() -> object:
    from app.schemas.director_dashboard import DirectorPhysicalFileSummaryResponse

    return DirectorPhysicalFileSummaryResponse(
        id=PHYSICAL_FILE_ID,
        physical_file_code="PF-001",
        project_code="IEMS-2026-001",
        project_name="Annual Leadership Conference",
        client_name="Acme Events",
        status="CHECKED_OUT",
        archive_room="Main Archive",
        archive_location_code="R1-S1-C1-B1-F1",
        checked_out_at=CREATED_AT,
        expected_return_at=CREATED_AT,
        checked_out_by="Nisha Rao",
        is_return_overdue=True,
    )


def _upcoming_event_response() -> object:
    from app.schemas.director_dashboard import DirectorUpcomingEventResponse

    return DirectorUpcomingEventResponse(
        id=CALENDAR_EVENT_ID,
        title="Client walkthrough",
        event_type="SITE_VISIT",
        starts_at=CREATED_AT,
        ends_at=CREATED_AT,
        project_code="IEMS-2026-001",
        project_name="Annual Leadership Conference",
        location="India Habitat Centre",
    )


def _missing_required_document_response() -> object:
    from app.schemas.director_dashboard import DirectorMissingRequiredDocumentResponse

    return DirectorMissingRequiredDocumentResponse(
        project_id=PROJECT_ID,
        project_code="IEMS-2026-001",
        project_name="Annual Leadership Conference",
        document_type_id=DOCUMENT_TYPE_ID,
        document_type_code="FINAL_INVOICE",
        document_type_name="Final Invoice",
    )


def _verification_reminder_response() -> object:
    from app.schemas.director_dashboard import DirectorVerificationReminderResponse

    return DirectorVerificationReminderResponse(
        id=PHYSICAL_FILE_ID,
        physical_file_code="PF-001",
        project_code="IEMS-2026-001",
        project_name="Annual Leadership Conference",
        archive_room="Main Archive",
        archive_location_code="R1-S1-C1-B1-F1",
        last_verified_at=CREATED_AT,
        next_verification_at=CREATED_AT,
    )


def _audit_event_response() -> object:
    from app.schemas.clients_projects import EmployeeSummary
    from app.schemas.director_dashboard import DirectorAuditEventResponse

    return DirectorAuditEventResponse(
        id=AUDIT_EVENT_ID,
        action_code="document.downloaded",
        resource_type="document_version",
        resource_id=PROJECT_ID,
        actor_employee_id=EMPLOYEE_ID,
        actor=EmployeeSummary(
            id=EMPLOYEE_ID,
            employee_code="IEMS-001",
            full_name="Example Employee",
        ),
        request_id=REQUEST_ID,
        created_at=CREATED_AT,
    )


def _current_user(
    *,
    roles: list[str],
    permissions: list[str],
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
            designation="Director",
            employment_status="ACTIVE",
        ),
        roles=roles,
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
    service: RecordingDirectorDashboardService | None = None,
    audit_writer: RecordingAuditWriter | None = None,
) -> tuple[RecordingDirectorDashboardService, RecordingAuditWriter]:
    from app.api.dependencies import get_director_dashboard_service

    installed_service = service or RecordingDirectorDashboardService()
    installed_audit_writer = audit_writer or RecordingAuditWriter()

    async def override_current_user() -> CurrentUser:
        return current_user

    async def override_director_dashboard_service() -> RecordingDirectorDashboardService:
        return installed_service

    async def override_audit_writer() -> RecordingAuditWriter:
        return installed_audit_writer

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_director_dashboard_service] = override_director_dashboard_service
    app.dependency_overrides[get_audit_writer] = override_audit_writer
    return installed_service, installed_audit_writer


def test_director_overview_requires_director_role_or_super_user() -> None:
    service, audit_writer = _install_overrides(
        current_user=_current_user(roles=["EMPLOYEE"], permissions=["audit.view"]),
    )
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/director/overview",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PERMISSION_DENIED"
    assert service.calls == []
    assert audit_writer.events == []


def test_director_overview_returns_metrics_and_logs_sensitive_access() -> None:
    service, audit_writer = _install_overrides(
        current_user=_current_user(roles=["DIRECTOR"], permissions=["audit.view"]),
    )
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/director/overview",
                headers={"Authorization": "Bearer test-token", "X-Request-ID": str(REQUEST_ID)},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["attendance"]["active_employee_count"] == 3
    assert response.json()["pending_approval_count"] == 1
    assert response.json()["recent_audit_events"][0]["action_code"] == "document.downloaded"
    assert service.calls[0][0] == "get_overview"
    assert audit_writer.events[0].action_code == "director.overview_viewed"
    assert audit_writer.events[0].context == AuditContext(
        request_id=REQUEST_ID,
        ip_address="127.0.0.1",
        user_agent="python-httpx/0.28.1",
    )


def test_director_projects_accepts_pagination() -> None:
    service, _audit_writer = _install_overrides(
        current_user=_current_user(roles=["DIRECTOR"], permissions=["project.view"]),
    )
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/director/projects?limit=10&offset=5",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["project_code"] == "IEMS-2026-001"
    assert service.calls[0][0] == "list_projects"
    assert service.calls[0][1] == (10, 5)


def test_director_approvals_passes_status_filter() -> None:
    service, _audit_writer = _install_overrides(
        current_user=_current_user(roles=["DIRECTOR"], permissions=["approval.view_all"]),
    )
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/director/approvals?status=PENDING",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["approval_type"] == "DOCUMENT_APPROVAL"
    assert service.calls[0][0] == "list_approvals"
    assert service.calls[0][1] == ("PENDING", 50, 0)


def test_director_overdue_tasks_returns_task_rows() -> None:
    service, _audit_writer = _install_overrides(
        current_user=_current_user(roles=["DIRECTOR"], permissions=["project.view"]),
    )
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/director/overdue-tasks",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(TASK_ID)
    assert service.calls[0][0] == "list_overdue_tasks"


def test_director_physical_files_returns_archive_rows() -> None:
    service, _audit_writer = _install_overrides(
        current_user=_current_user(roles=["DIRECTOR"], permissions=["archive.view"]),
    )
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/director/physical-files",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["is_return_overdue"] is True
    assert service.calls[0][0] == "list_physical_files"


def test_director_upcoming_events_returns_calendar_rows() -> None:
    service, _audit_writer = _install_overrides(
        current_user=_current_user(roles=["DIRECTOR"], permissions=["project.view"]),
    )
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/director/upcoming-events?limit=10&offset=2",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(CALENDAR_EVENT_ID)
    assert service.calls[0][0] == "list_upcoming_events"
    assert service.calls[0][1] == (10, 2)


def test_director_missing_required_documents_returns_gap_rows() -> None:
    service, _audit_writer = _install_overrides(
        current_user=_current_user(roles=["DIRECTOR"], permissions=["document.view"]),
    )
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/director/missing-required-documents",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["document_type_code"] == "FINAL_INVOICE"
    assert service.calls[0][0] == "list_missing_required_documents"


def test_director_verification_reminders_returns_due_rows() -> None:
    service, _audit_writer = _install_overrides(
        current_user=_current_user(roles=["DIRECTOR"], permissions=["archive.view"]),
    )
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/director/verification-reminders",
                headers={"Authorization": "Bearer test-token"},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["physical_file_code"] == "PF-001"
    assert service.calls[0][0] == "list_verification_reminders"


def test_director_audit_events_logs_sensitive_access() -> None:
    service, audit_writer = _install_overrides(
        current_user=_current_user(roles=["DIRECTOR"], permissions=["audit.view"]),
    )
    try:
        response = asyncio.run(
            _request(
                "GET",
                "/v1/director/audit-events?action_code=document.downloaded&resource_type=document_version",
                headers={"Authorization": "Bearer test-token", "X-Request-ID": str(REQUEST_ID)},
            )
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()[0]["id"] == str(AUDIT_EVENT_ID)
    assert service.calls[0][0] == "list_audit_events"
    assert service.calls[0][1] == (50, 0, "document.downloaded", "document_version")
    assert audit_writer.events[0].action_code == "director.audit_events_viewed"
