from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.clients_projects import EmployeeSummary, ReferenceSummary


class LeaveStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class TaskStatusCode(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class CalendarEventType(StrEnum):
    MEETING = "MEETING"
    SITE_VISIT = "SITE_VISIT"
    EVENT = "EVENT"
    DEADLINE = "DEADLINE"
    LEAVE = "LEAVE"
    ARCHIVE_VERIFICATION = "ARCHIVE_VERIFICATION"
    PHYSICAL_FILE_RETURN = "PHYSICAL_FILE_RETURN"
    REMINDER = "REMINDER"


class CalendarEventSource(StrEnum):
    CALENDAR_EVENT = "CALENDAR_EVENT"
    TASK_DEADLINE = "TASK_DEADLINE"
    LEAVE = "LEAVE"
    PHYSICAL_FILE_RETURN = "PHYSICAL_FILE_RETURN"


class TaskProjectSummary(BaseModel):
    id: UUID
    project_code: str
    name: str


class LeaveRequestCreate(BaseModel):
    leave_type_id: UUID
    start_date: date
    end_date: date
    reason: str = Field(min_length=3, max_length=2000)

    @model_validator(mode="after")
    def validate_dates(self) -> "LeaveRequestCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class LeaveReviewCreate(BaseModel):
    review_comment: str | None = Field(default=None, max_length=1000)


class LeaveRequestResponse(BaseModel):
    id: UUID
    employee_id: UUID
    employee: EmployeeSummary | None = None
    leave_type_id: UUID
    leave_type: ReferenceSummary | None = None
    start_date: date
    end_date: date
    reason: str
    status: LeaveStatus
    requested_at: datetime
    reviewed_by: UUID | None
    reviewed_at: datetime | None
    review_comment: str | None


class TaskCreate(BaseModel):
    project_id: UUID | None = None
    related_folder_id: UUID | None = None
    title: str = Field(min_length=1, max_length=250)
    description: str | None = None
    task_status_id: UUID | None = None
    priority_level_id: UUID
    due_at: datetime | None = None
    assignee_ids: list[UUID] = Field(default_factory=list)
    document_ids: list[UUID] = Field(default_factory=list)


class TaskUpdate(BaseModel):
    project_id: UUID | None = None
    related_folder_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=250)
    description: str | None = None
    task_status_id: UUID | None = None
    priority_level_id: UUID | None = None
    due_at: datetime | None = None


class TaskAssigneesCreate(BaseModel):
    employee_ids: list[UUID] = Field(min_length=1)


class TaskCommentCreate(BaseModel):
    comment_text: str = Field(min_length=1, max_length=4000)


class TaskDocumentLinkCreate(BaseModel):
    document_id: UUID


class TaskCommentResponse(BaseModel):
    id: UUID
    task_id: UUID
    employee_id: UUID
    employee: EmployeeSummary | None = None
    comment_text: str
    created_at: datetime
    edited_at: datetime | None


class TaskResponse(BaseModel):
    id: UUID
    project_id: UUID | None
    project: TaskProjectSummary | None = None
    related_folder_id: UUID | None
    title: str
    description: str | None
    task_status_id: UUID
    task_status: ReferenceSummary | None = None
    priority_level_id: UUID
    priority_level: ReferenceSummary | None = None
    created_by: UUID
    due_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    assignees: list[EmployeeSummary] = Field(default_factory=list)
    document_ids: list[UUID] = Field(default_factory=list)


class CalendarEventCreate(BaseModel):
    project_id: UUID | None = None
    related_task_id: UUID | None = None
    event_type: CalendarEventType
    title: str = Field(min_length=1, max_length=250)
    description: str | None = None
    starts_at: datetime
    ends_at: datetime | None = None
    location: str | None = Field(default=None, max_length=250)
    attendee_ids: list[UUID] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_times(self) -> "CalendarEventCreate":
        if self.ends_at is not None and self.ends_at < self.starts_at:
            raise ValueError("ends_at must be on or after starts_at")
        return self


class CalendarEventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=250)
    description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    location: str | None = Field(default=None, max_length=250)


class CalendarEventResponse(BaseModel):
    id: UUID
    event_type: CalendarEventType
    title: str
    description: str | None
    starts_at: datetime
    ends_at: datetime | None
    location: str | None
    project_id: UUID | None
    related_task_id: UUID | None
    created_by: UUID | None
    created_at: datetime | None
    updated_at: datetime | None
    source: CalendarEventSource = CalendarEventSource.CALENDAR_EVENT
