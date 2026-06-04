import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
import jwt
import pytest
from httpx import ASGITransport, AsyncClient, Response

from app.api.dependencies import get_current_user
from app.core.auth import AuthError, SupabaseJwtVerifier, TokenClaims
from app.core.current_user import CurrentUserError, SupabaseCurrentUserResolver
from app.main import app
from app.schemas.current_user import CurrentUser, EmployeeProfile, UserAccount

AUTH_USER_ID = UUID("11111111-1111-4111-8111-111111111111")
EMPLOYEE_ID = UUID("22222222-2222-4222-8222-222222222222")
ISSUER = "http://localhost:54321/auth/v1"
AUDIENCE = "authenticated"
SECRET = "local-test-jwt-secret-at-least-32-bytes"


def _token(email: str, secret: str = SECRET, subject: UUID = AUTH_USER_ID) -> str:
    now = datetime.now(tz=UTC)
    return jwt.encode(
        {
            "iss": ISSUER,
            "aud": AUDIENCE,
            "sub": str(subject),
            "email": email,
            "role": "authenticated",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=15)).timestamp()),
        },
        secret,
        algorithm="HS256",
    )


def _claims(email: str = "employee@iemsnewdelhi.com") -> TokenClaims:
    return TokenClaims(
        subject=AUTH_USER_ID,
        email=email,
        role="authenticated",
        issuer=ISSUER,
        audience=AUDIENCE,
        expires_at=datetime.now(tz=UTC) + timedelta(minutes=15),
    )


async def _get(path: str, headers: dict[str, str] | None = None) -> Response:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get(path, headers=headers)


def test_me_endpoint_returns_authenticated_employee_context() -> None:
    async def override_current_user() -> CurrentUser:
        return CurrentUser(
            auth_user_id=AUTH_USER_ID,
            account=UserAccount(is_active=True, is_super_user=False),
            employee=EmployeeProfile(
                id=EMPLOYEE_ID,
                employee_code="IEMS-001",
                full_name="Example Employee",
                official_email="employee@iemsnewdelhi.com",
                designation="Coordinator",
                employment_status="ACTIVE",
            ),
            roles=["EMPLOYEE"],
        )

    app.dependency_overrides[get_current_user] = override_current_user
    try:
        response = asyncio.run(_get("/v1/me", headers={"Authorization": "Bearer test-token"}))
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "auth_user_id": str(AUTH_USER_ID),
        "account": {
            "is_active": True,
            "is_super_user": False,
        },
        "employee": {
            "id": str(EMPLOYEE_ID),
            "employee_code": "IEMS-001",
            "full_name": "Example Employee",
            "official_email": "employee@iemsnewdelhi.com",
            "designation": "Coordinator",
            "employment_status": "ACTIVE",
        },
        "roles": ["EMPLOYEE"],
    }


def test_jwt_verifier_accepts_valid_supabase_access_token() -> None:
    verifier = SupabaseJwtVerifier(
        jwt_secret=SECRET,
        issuer=ISSUER,
        audience=AUDIENCE,
        allowed_email_domain="iemsnewdelhi.com",
    )

    claims = verifier.verify(_token("employee@iemsnewdelhi.com"))

    assert claims.subject == AUTH_USER_ID
    assert claims.email == "employee@iemsnewdelhi.com"
    assert claims.role == "authenticated"


def test_jwt_verifier_rejects_invalid_signature() -> None:
    verifier = SupabaseJwtVerifier(
        jwt_secret=SECRET,
        issuer=ISSUER,
        audience=AUDIENCE,
        allowed_email_domain="iemsnewdelhi.com",
    )

    with pytest.raises(AuthError) as exc_info:
        verifier.verify(
            _token("employee@iemsnewdelhi.com", secret="wrong-secret-at-least-32-bytes-long")
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.code == "INVALID_TOKEN"


def test_jwt_verifier_rejects_disallowed_email_domain() -> None:
    verifier = SupabaseJwtVerifier(
        jwt_secret=SECRET,
        issuer=ISSUER,
        audience=AUDIENCE,
        allowed_email_domain="iemsnewdelhi.com",
    )

    with pytest.raises(AuthError) as exc_info:
        verifier.verify(_token("outsider@example.com"))

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "EMAIL_DOMAIN_NOT_ALLOWED"


def test_current_user_resolver_returns_active_employee_context() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        return Response(
            200,
            json=[
                {
                    "id": str(AUTH_USER_ID),
                    "is_active": True,
                    "is_super_user": True,
                    "employee": {
                        "id": str(EMPLOYEE_ID),
                        "employee_code": "IEMS-DIRECTOR",
                        "full_name": "IEMS Director",
                        "official_email": "director@iemsnewdelhi.com",
                        "designation": "Director",
                        "employment_status": "ACTIVE",
                    },
                    "role_assignments": [
                        {"expires_at": None, "role": {"code": "DIRECTOR"}},
                        {"expires_at": None, "role": {"code": "SUPER_USER"}},
                    ],
                }
            ],
        )

    resolver = SupabaseCurrentUserResolver(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    current_user = asyncio.run(resolver.resolve(_claims(email="director@iemsnewdelhi.com")))

    assert current_user.auth_user_id == AUTH_USER_ID
    assert current_user.account.is_super_user is True
    assert current_user.employee.official_email == "director@iemsnewdelhi.com"
    assert current_user.roles == ["DIRECTOR", "SUPER_USER"]
    assert seen_requests[0].headers["apikey"] == "legacy-service-role-key"
    assert seen_requests[0].headers["authorization"] == "Bearer legacy-service-role-key"


def test_current_user_resolver_uses_apikey_only_for_new_secret_keys() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> Response:
        seen_requests.append(request)
        return Response(200, json=[])

    resolver = SupabaseCurrentUserResolver(
        supabase_url="http://localhost:54321",
        service_role_key="sb_secret_test_secret_key_value_123456",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(CurrentUserError):
        asyncio.run(resolver.resolve(_claims()))

    assert seen_requests[0].headers["apikey"] == "sb_secret_test_secret_key_value_123456"
    assert "authorization" not in seen_requests[0].headers


def test_current_user_resolver_rejects_unapproved_account() -> None:
    resolver = SupabaseCurrentUserResolver(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(lambda _request: Response(200, json=[])),
    )

    with pytest.raises(CurrentUserError) as exc_info:
        asyncio.run(resolver.resolve(_claims()))

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "ACCOUNT_NOT_APPROVED"


def test_current_user_resolver_rejects_disabled_account() -> None:
    resolver = SupabaseCurrentUserResolver(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(
            lambda _request: Response(
                200,
                json=[
                    {
                        "id": str(AUTH_USER_ID),
                        "is_active": False,
                        "is_super_user": False,
                        "employee": {
                            "id": str(EMPLOYEE_ID),
                            "employee_code": "IEMS-001",
                            "full_name": "Example Employee",
                            "official_email": "employee@iemsnewdelhi.com",
                            "designation": "Coordinator",
                            "employment_status": "ACTIVE",
                        },
                        "role_assignments": [],
                    }
                ],
            )
        ),
    )

    with pytest.raises(CurrentUserError) as exc_info:
        asyncio.run(resolver.resolve(_claims()))

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "ACCOUNT_DISABLED"


def test_current_user_resolver_rejects_employee_email_mismatch() -> None:
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
                        "role_assignments": [],
                    }
                ],
            )
        ),
    )

    with pytest.raises(CurrentUserError) as exc_info:
        asyncio.run(resolver.resolve(_claims(email="different@iemsnewdelhi.com")))

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "ACCOUNT_EMAIL_MISMATCH"
