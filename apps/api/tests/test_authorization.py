import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
import pytest
from httpx import ASGITransport, AsyncClient, Response

from app.api.dependencies import get_current_user
from app.core.abac import ABACResource, ABACService
from app.core.auth import TokenClaims
from app.core.current_user import SupabaseCurrentUserResolver
from app.core.rbac import AuthorizationError, RBACService
from app.main import app
from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount

AUTH_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
OTHER_EMPLOYEE_ID = UUID("33333333-3333-4333-8333-333333333333")


def _current_user(
    *,
    is_super_user: bool = False,
    permissions: list[str] | None = None,
    employee_id: UUID = EMPLOYEE_ID,
) -> CurrentUser:
    return CurrentUser(
        auth_user_id=AUTH_USER_ID,
        account=UserAccount(is_active=True, is_super_user=is_super_user),
        employee=EmployeeProfile(
            id=employee_id,
            employee_code="IEMS-001",
            full_name="Example Employee",
            official_email="employee@iemsnewdelhi.com",
            designation="Coordinator",
            employment_status="ACTIVE",
        ),
        roles=["EMPLOYEE"],
        permissions=permissions or [],
    )


def _claims() -> TokenClaims:
    return TokenClaims(
        subject=AUTH_USER_ID,
        email="employee@iemsnewdelhi.com",
        role="authenticated",
        issuer="http://localhost:54321/auth/v1",
        audience="authenticated",
        expires_at=datetime.now(tz=UTC) + timedelta(minutes=15),
    )


async def _get(path: str, headers: dict[str, str] | None = None) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path, headers=headers)


def test_rbac_allows_assigned_permission() -> None:
    user = _current_user(permissions=["project.view"])

    assert RBACService().has_permission(user, "project.view") is True


def test_rbac_denies_missing_permission() -> None:
    user = _current_user(permissions=["project.view"])

    with pytest.raises(AuthorizationError) as exc_info:
        RBACService().require_permission(user, "policy.manage")

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "PERMISSION_DENIED"


def test_rbac_allows_super_user_without_listing_permission() -> None:
    user = _current_user(is_super_user=True, permissions=[])

    assert RBACService().has_permission(user, "policy.manage") is True


def test_abac_defaults_to_deny_for_unknown_context() -> None:
    user = _current_user(permissions=["project.view"])
    resource = ABACResource(resource_type="project", attributes={"project_id": "p-1"})

    with pytest.raises(AuthorizationError) as exc_info:
        ABACService().require_access(user, "project.manage", resource)

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "ABAC_DENIED"


def test_abac_allows_current_user_to_view_own_profile() -> None:
    user = _current_user()
    resource = ABACResource(
        resource_type="employee_profile",
        attributes={"employee_id": str(EMPLOYEE_ID)},
    )

    assert ABACService().can_access(user, "employee.profile.view_self", resource) is True


def test_abac_denies_other_employee_profile_without_permission() -> None:
    user = _current_user()
    resource = ABACResource(
        resource_type="employee_profile",
        attributes={"employee_id": str(OTHER_EMPLOYEE_ID)},
    )

    with pytest.raises(AuthorizationError):
        ABACService().require_access(user, "employee.profile.view_self", resource)


def test_current_user_resolver_includes_permissions_and_filters_expired_roles() -> None:
    expired_at = (datetime.now(tz=UTC) - timedelta(days=1)).isoformat()

    resolver = SupabaseCurrentUserResolver(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(
            lambda _request: Response(
                200,
                json=[
                    {
                        "id": str(AUTH_USER_ID),
                        "is_active": True,
                        "is_super_user": False,
                        "employee": {
                            "id": str(EMPLOYEE_ID),
                            "employee_code": "IEMS-001",
                            "full_name": "Example Employee",
                            "official_email": "employee@iemsnewdelhi.com",
                            "designation": "Coordinator",
                            "employment_status": "ACTIVE",
                        },
                        "role_assignments": [
                            {
                                "expires_at": None,
                                "role": {
                                    "code": "EMPLOYEE",
                                    "role_permissions": [
                                        {"permission": {"code": "project.view"}},
                                        {"permission": {"code": "document.view"}},
                                    ],
                                },
                            },
                            {
                                "expires_at": expired_at,
                                "role": {
                                    "code": "ADMIN",
                                    "role_permissions": [
                                        {"permission": {"code": "policy.manage"}},
                                    ],
                                },
                            },
                        ],
                    }
                ],
            )
        ),
    )

    current_user = asyncio.run(resolver.resolve(_claims()))

    assert current_user.roles == ["EMPLOYEE"]
    assert current_user.permissions == ["document.view", "project.view"]


def test_me_permissions_endpoint_returns_effective_permissions() -> None:
    async def override_current_user() -> CurrentUser:
        return _current_user(
            is_super_user=True,
            permissions=["audit.view", "policy.manage"],
        )

    app.dependency_overrides[get_current_user] = override_current_user
    try:
        response = asyncio.run(
            _get("/v1/me/permissions", headers={"Authorization": "Bearer test-token"})
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "roles": ["EMPLOYEE"],
        "permissions": ["audit.view", "policy.manage"],
        "is_super_user": True,
        "super_user_requires_reason": True,
    }
