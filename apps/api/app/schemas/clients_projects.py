from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProjectAccessLevel(StrEnum):
    VIEW = "VIEW"
    CONTRIBUTE = "CONTRIBUTE"
    MANAGE = "MANAGE"


class ReferenceSummary(BaseModel):
    id: UUID
    code: str
    name: str


class ProjectSummaryClient(BaseModel):
    id: UUID
    client_code: str
    display_name: str


class EmployeeSummary(BaseModel):
    id: UUID
    employee_code: str
    full_name: str


class ClientCreate(BaseModel):
    client_code: str = Field(min_length=1, max_length=30)
    legal_name: str = Field(min_length=1, max_length=200)
    display_name: str = Field(min_length=1, max_length=150)
    notes: str | None = None


class ClientUpdate(BaseModel):
    legal_name: str | None = Field(default=None, min_length=1, max_length=200)
    display_name: str | None = Field(default=None, min_length=1, max_length=150)
    is_active: bool | None = None
    notes: str | None = None


class ClientResponse(BaseModel):
    id: UUID
    client_code: str
    legal_name: str
    display_name: str
    is_active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ProjectCreate(BaseModel):
    project_code: str = Field(min_length=1, max_length=40)
    client_id: UUID
    project_type_id: UUID
    project_status_id: UUID
    priority_level_id: UUID
    name: str = Field(min_length=1, max_length=200)
    event_date: date | None = None
    venue: str | None = Field(default=None, max_length=250)
    description: str | None = None
    project_manager_id: UUID | None = None
    folder_template_id: UUID | None = None


class ProjectUpdate(BaseModel):
    client_id: UUID | None = None
    project_type_id: UUID | None = None
    project_status_id: UUID | None = None
    priority_level_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    event_date: date | None = None
    venue: str | None = Field(default=None, max_length=250)
    description: str | None = None
    project_manager_id: UUID | None = None
    archived_at: datetime | None = None


class ProjectResponse(BaseModel):
    id: UUID
    project_code: str
    client_id: UUID
    client: ProjectSummaryClient | None = None
    project_type_id: UUID
    project_type: ReferenceSummary | None = None
    project_status_id: UUID
    project_status: ReferenceSummary | None = None
    priority_level_id: UUID
    priority_level: ReferenceSummary | None = None
    name: str
    event_date: date | None
    venue: str | None
    description: str | None
    project_manager_id: UUID | None
    project_manager: EmployeeSummary | None = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    deleted_at: datetime | None
    root_folder_id: UUID | None = None


class ProjectMemberCreate(BaseModel):
    employee_id: UUID
    access_level: ProjectAccessLevel


class ProjectMemberUpdate(BaseModel):
    access_level: ProjectAccessLevel


class ProjectMemberResponse(BaseModel):
    project_id: UUID
    employee_id: UUID
    access_level: ProjectAccessLevel
    assigned_by: UUID
    assigned_at: datetime
    removed_at: datetime | None


class ProjectMemberDetailResponse(ProjectMemberResponse):
    employee: EmployeeSummary | None = None


class FolderTreeNode(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: UUID
    project_id: UUID
    parent_folder_id: UUID | None
    name: str
    sort_order: int
    children: list["FolderTreeNode"] = Field(default_factory=list)
