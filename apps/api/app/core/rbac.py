from app.schemas.current_user import CurrentUser


class AuthorizationError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class RBACService:
    def has_permission(self, current_user: CurrentUser, permission_code: str) -> bool:
        if current_user.account.is_super_user:
            return True
        return permission_code in current_user.permissions

    def require_permission(self, current_user: CurrentUser, permission_code: str) -> None:
        if not self.has_permission(current_user, permission_code):
            raise AuthorizationError(403, "PERMISSION_DENIED", "Permission denied")
