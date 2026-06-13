from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.clients_projects import ReferenceSummary


class FolderCreate(BaseModel):
    parent_folder_id: UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    sort_order: int = 0


class FolderUpdate(BaseModel):
    parent_folder_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    sort_order: int | None = None


class FolderResponse(BaseModel):
    id: UUID
    project_id: UUID
    parent_folder_id: UUID | None
    name: str
    sort_order: int
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class DocumentVersionResponse(BaseModel):
    id: UUID
    document_id: UUID
    version_number: int
    storage_bucket: str
    storage_key: str
    original_filename: str
    mime_type: str
    size_bytes: int
    checksum_sha256: str
    change_note: str | None
    uploaded_by: UUID
    uploaded_at: datetime
    preview_supported: bool = False


class DocumentResponse(BaseModel):
    id: UUID
    project_id: UUID
    folder_id: UUID
    document_type_id: UUID | None
    document_type: ReferenceSummary | None = None
    confidentiality_level_id: UUID
    confidentiality_level: ReferenceSummary | None = None
    display_name: str
    status: str
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    latest_version: DocumentVersionResponse | None = None


class SignedUrlResponse(BaseModel):
    url: str
    expires_in_seconds: int
    expires_at: datetime


class ArchiveExportCreate(BaseModel):
    expires_in_hours: int | None = Field(default=None, ge=1, le=168)


class ArchiveExportResponse(BaseModel):
    id: UUID
    project_id: UUID
    export_number: int
    requested_by: UUID
    status: str
    storage_bucket: str | None
    storage_key: str | None
    manifest_checksum_sha256: str | None
    requested_at: datetime
    completed_at: datetime | None
    expires_at: datetime | None
    item_count: int = 0


class ArchiveExportItem(BaseModel):
    document_version_id: UUID
    relative_path: str
    checksum_sha256: str

