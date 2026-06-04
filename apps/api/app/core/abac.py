from dataclasses import dataclass, field

from app.core.rbac import AuthorizationError
from app.schemas.current_user import CurrentUser


@dataclass(frozen=True)
class ABACResource:
    resource_type: str
    attributes: dict[str, object] = field(default_factory=dict)


class ABACService:
    def can_access(
        self,
        current_user: CurrentUser,
        action_code: str,
        resource: ABACResource,
        *,
        override_reason: str | None = None,
    ) -> bool:
        if self._is_self_profile_access(current_user, action_code, resource):
            return True

        if current_user.account.is_super_user and _valid_override_reason(override_reason):
            return True

        return False

    def require_access(
        self,
        current_user: CurrentUser,
        action_code: str,
        resource: ABACResource,
        *,
        override_reason: str | None = None,
    ) -> None:
        if not self.can_access(
            current_user,
            action_code,
            resource,
            override_reason=override_reason,
        ):
            raise AuthorizationError(403, "ABAC_DENIED", "Access denied")

    def _is_self_profile_access(
        self,
        current_user: CurrentUser,
        action_code: str,
        resource: ABACResource,
    ) -> bool:
        if action_code != "employee.profile.view_self":
            return False
        if resource.resource_type != "employee_profile":
            return False
        return resource.attributes.get("employee_id") == str(current_user.employee.id)


def _valid_override_reason(reason: str | None) -> bool:
    return reason is not None and len(reason.strip()) >= 8
