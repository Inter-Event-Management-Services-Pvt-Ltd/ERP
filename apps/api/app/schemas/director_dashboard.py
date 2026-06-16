from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.clients_projects import EmployeeSummary


class DirectorAttendanceMetrics(BaseModel):
    active_employee_count: int = Field(ge=0)
    checked_in_count: int = Field(ge=0)
    checked_out_count: int = Field(ge=0)
    absent_or_not_checked_in_count: int = Field(ge=0)
    total_minutes_today: int = Field(ge=0)


class DirectorProjectMetrics(BaseModel):
    active_count: int = Field(ge=0)
    planning_count: int = Field(ge=0)
    completed_count: int = Field(ge=0)
    archived_count: int = Field(ge=0)


class DirectorArchiveMetrics(BaseModel):
    checked_out_count: int = Field(ge=0)
    overdue_return_count: int = Field(ge=0)
    verification_due_count: int = Field(ge=0)
    missing_count: int = Field(ge=0)


class DirectorProjectSummaryResponse(BaseModel):
    id: UUID
    project_code: str
    name: str
    client_name: str | None
    project_status: str | None
    priority_level: str | None
    event_date: date | None
    project_manager_name: str | None
    archived_at: datetime | None


class DirectorApprovalSummaryResponse(BaseModel):
    id: UUID
    approval_type: str
    status: str
    requested_at: datetime
    requested_by_name: str
    assigned_to_name: str | None
    project_code: str | None
    project_name: str | None


class DirectorOverdueTaskResponse(BaseModel):
    id: UUID
    title: str
    due_at: datetime
    project_code: str | None
    project_name: str | None
    assignees: str | None


class DirectorPhysicalFileSummaryResponse(BaseModel):
    id: UUID
    physical_file_code: str
    project_code: str
    project_name: str
    client_name: str
    status: str
    archive_room: str
    archive_location_code: str
    checked_out_at: datetime | None
    expected_return_at: datetime | None
    checked_out_by: str | None
    is_return_overdue: bool


class DirectorUpcomingEventResponse(BaseModel):
    id: UUID
    title: str
    event_type: str
    starts_at: datetime
    ends_at: datetime | None
    project_code: str | None
    project_name: str | None
    location: str | None


class DirectorMissingRequiredDocumentResponse(BaseModel):
    project_id: UUID
    project_code: str
    project_name: str
    document_type_id: UUID
    document_type_code: str
    document_type_name: str


class DirectorVerificationReminderResponse(BaseModel):
    id: UUID
    physical_file_code: str
    project_code: str
    project_name: str
    archive_room: str
    archive_location_code: str
    last_verified_at: datetime | None
    next_verification_at: datetime


class DirectorAuditEventResponse(BaseModel):
    id: UUID
    action_code: str
    resource_type: str
    resource_id: UUID | None
    actor_employee_id: UUID | None
    actor: EmployeeSummary | None = None
    request_id: UUID | None
    created_at: datetime


class DirectorOverviewResponse(BaseModel):
    generated_at: datetime
    attendance: DirectorAttendanceMetrics
    projects: DirectorProjectMetrics
    pending_approval_count: int = Field(ge=0)
    overdue_task_count: int = Field(ge=0)
    physical_archive: DirectorArchiveMetrics
    recent_audit_events: list[DirectorAuditEventResponse] = Field(default_factory=list)
