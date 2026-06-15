from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class AttendanceSource(StrEnum):
    WEB = "WEB"
    MOBILE = "MOBILE"
    ADMIN = "ADMIN"
    QR = "QR"
    BIOMETRIC = "BIOMETRIC"
    IMPORT = "IMPORT"


class AttendanceEmployeeSummary(BaseModel):
    id: UUID
    employee_code: str
    full_name: str


class AttendanceCheckInCreate(BaseModel):
    remarks: str | None = Field(default=None, max_length=500)


class AttendanceCheckOutCreate(BaseModel):
    remarks: str | None = Field(default=None, max_length=500)


class AttendanceCorrectionUpdate(BaseModel):
    checked_in_at: datetime | None = None
    checked_out_at: datetime | None = None
    remarks: str | None = Field(default=None, max_length=500)
    correction_reason: str = Field(min_length=5, max_length=500)


class AttendanceSessionResponse(BaseModel):
    id: UUID
    employee_id: UUID
    employee: AttendanceEmployeeSummary | None = None
    checked_in_at: datetime
    checked_out_at: datetime | None
    source: AttendanceSource
    remarks: str | None
    created_by: UUID
    corrected_by: UUID | None
    correction_reason: str | None
    created_at: datetime
    updated_at: datetime
    total_minutes: int | None = None


class DirectorAttendanceSummaryResponse(BaseModel):
    employee_id: UUID
    employee_code: str
    full_name: str
    first_check_in: datetime | None
    last_check_out: datetime | None
    total_minutes: int | None
    attendance_state: str
