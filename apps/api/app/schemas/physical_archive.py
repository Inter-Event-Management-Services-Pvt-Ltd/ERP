from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ArchiveRoomCreate(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class ArchiveRoomResponse(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None
    is_active: bool


class ArchiveLocationCreate(BaseModel):
    archive_room_id: UUID
    parent_location_id: UUID | None = None
    location_type: str = Field(pattern="^(RACK|SHELF|CABINET|BOX|FILE_SLOT)$")
    code: str = Field(min_length=1, max_length=50)
    label: str | None = Field(default=None, max_length=120)


class ArchiveLocationResponse(BaseModel):
    id: UUID
    archive_room_id: UUID
    parent_location_id: UUID | None
    location_type: str
    code: str
    label: str | None
    qr_token: UUID
    is_active: bool


class ArchiveLocationContentsResponse(BaseModel):
    location: ArchiveLocationResponse
    child_locations: list[ArchiveLocationResponse]
    physical_files: list["PhysicalFileResponse"]


class PhysicalFileCreate(BaseModel):
    physical_file_code: str = Field(min_length=1, max_length=60)
    archive_location_id: UUID
    volume_number: int = Field(default=1, ge=1)
    archived_on: date | None = None
    notes: str | None = None


class ProjectSummary(BaseModel):
    id: UUID
    project_code: str
    name: str


class PhysicalArchiveRoomSummary(BaseModel):
    id: UUID
    code: str
    name: str


class PhysicalArchiveLocationSummary(BaseModel):
    id: UUID
    archive_room_id: UUID
    location_type: str
    code: str
    label: str | None
    qr_token: UUID


class OpenCheckoutSummary(BaseModel):
    id: UUID
    checked_out_by: UUID
    checked_out_at: datetime
    purpose: str
    expected_return_at: datetime | None


class PhysicalFileResponse(BaseModel):
    id: UUID
    physical_file_code: str
    project_id: UUID
    project: ProjectSummary | None = None
    archive_location_id: UUID
    archive_location: PhysicalArchiveLocationSummary | None = None
    archive_room: PhysicalArchiveRoomSummary | None = None
    volume_number: int
    status: str
    qr_token: UUID
    archived_on: date | None
    archived_by: UUID | None
    last_verified_at: datetime | None
    next_verification_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    open_checkout: OpenCheckoutSummary | None = None


class PhysicalFileCheckoutCreate(BaseModel):
    purpose: str = Field(min_length=1)
    expected_return_at: datetime | None = None


class PhysicalFileReturnCreate(BaseModel):
    returned_to_location_id: UUID | None = None
    remarks: str | None = None


class PhysicalFileMoveCreate(BaseModel):
    to_location_id: UUID
    remarks: str | None = None


class PhysicalFileVerificationCreate(BaseModel):
    location_correct: bool
    label_readable: bool
    physical_file_present: bool
    digital_archive_present: bool
    documents_complete: bool
    remarks: str | None = None


class PhysicalFileLabelResponse(BaseModel):
    physical_file_id: UUID
    physical_file_code: str
    project_code: str
    project_name: str
    location_code: str
    archive_room: str
    qr_token: UUID
    label_text: str

