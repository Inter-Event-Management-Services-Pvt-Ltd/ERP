from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_employees_service, require_any_permission
from app.schemas.current_user import CurrentUser
from app.schemas.employees import EmployeeDirectoryResponse
from app.services.employees import EmployeesError, EmployeesService

router = APIRouter(prefix="/v1", tags=["employees"])

EmployeeLookupUser = Annotated[
    CurrentUser,
    Depends(require_any_permission({"employee.view", "project.manage"})),
]
EmployeesServiceDep = Annotated[EmployeesService, Depends(get_employees_service)]
EmploymentStatusQuery = Literal["ACTIVE", "INACTIVE", "ON_LEAVE", "EXITED"]


@router.get("/employees", response_model=list[EmployeeDirectoryResponse])
async def list_employees(
    current_user: EmployeeLookupUser,
    service: EmployeesServiceDep,
    status: EmploymentStatusQuery = "ACTIVE",
    search: Annotated[str | None, Query(min_length=1, max_length=150)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[EmployeeDirectoryResponse]:
    try:
        return await service.list_employees(
            current_user=current_user,
            status=status,
            search=search,
            limit=limit,
            offset=offset,
        )
    except EmployeesError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "code": exc.code,
                "message": exc.message,
            },
        ) from exc
