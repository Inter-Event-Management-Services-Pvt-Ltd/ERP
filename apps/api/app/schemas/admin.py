from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.schemas.clients_projects import EmployeeSummary, ReferenceSummary
from app.schemas.employees import EmploymentStatus


class PolicyEffect(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"


class EmployeeAccountSummary(BaseModel):
    id: UUID
    is_active: bool
    is_super_user: bool


class RoleResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None


class RoleAssignmentCreate(BaseModel):
    role_id: UUID
    expires_at: datetime | None = None


class RoleAssignmentResponse(BaseModel):
    employee_id: UUID
    user_account_id: UUID
    role: RoleResponse
    assigned_at: datetime
    expires_at: datetime | None


class DepartmentAssignmentCreate(BaseModel):
    department_id: UUID
    valid_from: date


class DepartmentAssignmentResponse(BaseModel):
    id: UUID
    employee_id: UUID
    department: ReferenceSummary
    valid_from: date
    valid_to: date | None
    assigned_by: UUID | None


class EmployeeAdminCreate(BaseModel):
    employee_code: str = Field(min_length=1, max_length=30)
    full_name: str = Field(min_length=1, max_length=150)
    official_email: str = Field(min_length=3, max_length=320)
    phone: str | None = Field(default=None, max_length=30)
    designation: str | None = Field(default=None, max_length=120)
    employment_status: EmploymentStatus = "ACTIVE"
    joined_on: date | None = None


class EmployeeAdminUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    designation: str | None = Field(default=None, max_length=120)
    employment_status: EmploymentStatus | None = None
    joined_on: date | None = None
    left_on: date | None = None


class EmployeeAdminResponse(BaseModel):
    id: UUID
    employee_code: str
    full_name: str
    official_email: str
    phone: str | None
    designation: str | None
    employment_status: EmploymentStatus
    joined_on: date | None
    left_on: date | None
    created_at: datetime
    updated_at: datetime
    current_department: ReferenceSummary | None = None
    roles: list[RoleAssignmentResponse] = Field(default_factory=list)
    account: EmployeeAccountSummary | None = None


class PolicyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    action_code: str = Field(min_length=1, max_length=100)
    effect: PolicyEffect
    priority: int = Field(default=100, ge=0, le=10000)
    conditions: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class PolicyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    action_code: str | None = Field(default=None, min_length=1, max_length=100)
    effect: PolicyEffect | None = None
    priority: int | None = Field(default=None, ge=0, le=10000)
    conditions: dict[str, Any] | None = None
    is_active: bool | None = None


class PolicyResponse(BaseModel):
    id: UUID
    name: str
    action_code: str
    effect: PolicyEffect
    priority: int
    conditions: dict[str, Any]
    is_active: bool
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime


class FolderTemplateItemCreate(BaseModel):
    parent_item_id: UUID | None = None
    name: str = Field(min_length=1, max_length=200)
    sort_order: int = 0


class FolderTemplateItemUpdate(BaseModel):
    parent_item_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    sort_order: int | None = None


class FolderTemplateItemResponse(BaseModel):
    id: UUID
    template_id: UUID
    parent_item_id: UUID | None
    name: str
    sort_order: int


class FolderTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    project_type_id: UUID | None = None


class FolderTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    project_type_id: UUID | None = None
    is_active: bool | None = None


class FolderTemplateResponse(BaseModel):
    id: UUID
    name: str
    project_type_id: UUID | None
    is_active: bool
    created_by: UUID | None
    created_at: datetime
    items: list[FolderTemplateItemResponse] = Field(default_factory=list)


class ArchiveRoomUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=30)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    is_active: bool | None = None


class ArchiveLocationUpdate(BaseModel):
    parent_location_id: UUID | None = None
    location_type: str | None = Field(default=None, min_length=1, max_length=30)
    code: str | None = Field(default=None, min_length=1, max_length=50)
    label: str | None = Field(default=None, max_length=120)
    is_active: bool | None = None


class AuditEventExplorerResponse(BaseModel):
    id: UUID
    action_code: str
    resource_type: str
    resource_id: UUID | None
    actor_employee_id: UUID | None
    actor: EmployeeSummary | None = None
    request_id: UUID | None
    old_values: dict[str, Any] | None
    new_values: dict[str, Any] | None
    metadata: dict[str, Any] | None
    created_at: datetime


class _PatchValidator(BaseModel):
    @model_validator(mode="after")
    def require_any_field(self) -> "_PatchValidator":
        if not self.model_dump(exclude_unset=True):
            raise ValueError("at least one field must be provided")
        return self
