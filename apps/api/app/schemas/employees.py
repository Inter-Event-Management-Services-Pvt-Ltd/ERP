from typing import Literal
from uuid import UUID

from pydantic import BaseModel

EmploymentStatus = Literal["ACTIVE", "INACTIVE", "ON_LEAVE", "EXITED"]


class EmployeeDirectoryResponse(BaseModel):
    id: UUID
    employee_code: str
    full_name: str
    official_email: str
    designation: str | None
    employment_status: EmploymentStatus
