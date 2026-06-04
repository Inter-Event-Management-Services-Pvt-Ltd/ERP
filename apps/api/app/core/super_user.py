from typing import Protocol
from uuid import UUID

from app.core.audit import AuditContext
from app.core.rbac import AuthorizationError
from app.schemas.current_user import CurrentUser


class SuperUserOverrideWriter(Protocol):
    async def record_super_user_override(
        self,
        *,
        user_account_id: UUID,
        actor_employee_id: UUID,
        action_code: str,
        resource_type: str,
        resource_id: UUID,
        reason: str,
        context: AuditContext,
        metadata: dict[str, object] | None = None,
    ) -> UUID: ...


class SuperUserOverrideService:
    async def record_override(
        self,
        *,
        current_user: CurrentUser,
        action_code: str,
        resource_type: str,
        resource_id: UUID,
        reason: str | None,
        context: AuditContext,
        writer: SuperUserOverrideWriter,
        metadata: dict[str, object] | None = None,
    ) -> UUID:
        if not current_user.account.is_super_user:
            raise AuthorizationError(403, "SUPER_USER_REQUIRED", "Super User access required")
        if not _valid_override_reason(reason):
            raise AuthorizationError(
                403,
                "SUPER_USER_OVERRIDE_REASON_REQUIRED",
                "A meaningful Super User override reason is required",
            )
        assert reason is not None
        clean_reason = reason.strip()

        return await writer.record_super_user_override(
            user_account_id=current_user.auth_user_id,
            actor_employee_id=current_user.employee.id,
            action_code=action_code,
            resource_type=resource_type,
            resource_id=resource_id,
            reason=clean_reason,
            context=context,
            metadata=metadata,
        )


def _valid_override_reason(reason: str | None) -> bool:
    return reason is not None and len(reason.strip()) >= 8
