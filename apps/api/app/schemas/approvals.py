from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.clients_projects import EmployeeSummary, ReferenceSummary


class ApprovalStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVISION_REQUESTED = "REVISION_REQUESTED"
    CANCELLED = "CANCELLED"


class ApprovalAction(StrEnum):
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVISION_REQUESTED = "REVISION_REQUESTED"
    CANCELLED = "CANCELLED"
    COMMENTED = "COMMENTED"


class ApprovalRequestCreate(BaseModel):
    approval_type_id: UUID
    project_id: UUID | None = None
    document_version_id: UUID | None = None
    archive_export_id: UUID | None = None
    leave_request_id: UUID | None = None
    assigned_to: UUID | None = None
    comment: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_single_target(self) -> "ApprovalRequestCreate":
        target_count = sum(
            target is not None
            for target in (
                self.project_id,
                self.document_version_id,
                self.archive_export_id,
                self.leave_request_id,
            )
        )
        if target_count != 1:
            raise ValueError("approval request must reference exactly one target")
        return self


class ApprovalReviewCreate(BaseModel):
    comment: str | None = Field(default=None, max_length=2000)


class ApprovalRevisionRequestCreate(BaseModel):
    comment: str = Field(min_length=1, max_length=2000)


class ApprovalActionResponse(BaseModel):
    id: UUID
    approval_request_id: UUID
    action: ApprovalAction
    performed_by: UUID
    performed_by_employee: EmployeeSummary | None = None
    comment: str | None
    created_at: datetime


class ApprovalRequestResponse(BaseModel):
    id: UUID
    approval_type_id: UUID
    approval_type: ReferenceSummary | None = None
    project_id: UUID | None
    document_version_id: UUID | None
    archive_export_id: UUID | None
    leave_request_id: UUID | None
    requested_by: UUID
    requested_by_employee: EmployeeSummary | None = None
    assigned_to: UUID | None
    assigned_to_employee: EmployeeSummary | None = None
    status: ApprovalStatus
    requested_at: datetime
    completed_at: datetime | None
    actions: list[ApprovalActionResponse] = Field(default_factory=list)
