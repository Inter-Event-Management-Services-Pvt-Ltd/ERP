from uuid import UUID

from pydantic import BaseModel, Field


class EmployeeProfile(BaseModel):
    id: UUID
    employee_code: str
    full_name: str
    official_email: str
    designation: str | None
    employment_status: str


class UserAccount(BaseModel):
    is_active: bool
    is_super_user: bool


class CurrentUser(BaseModel):
    auth_user_id: UUID
    account: UserAccount
    employee: EmployeeProfile
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)


class CurrentUserPermissions(BaseModel):
    roles: list[str] = Field(default_factory=list)
    permissions: list[str] = Field(default_factory=list)
    is_super_user: bool
    super_user_requires_reason: bool = True
