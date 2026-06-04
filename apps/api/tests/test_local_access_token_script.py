from datetime import UTC, datetime

import jwt

from scripts.local_access_token import _is_local_supabase_url, build_access_token


def test_build_access_token_uses_supabase_auth_issuer() -> None:
    token = build_access_token(
        jwt_secret="local-test-jwt-secret-at-least-32-bytes",
        supabase_url="http://127.0.0.1:54321",
        auth_user_id="11111111-1111-4111-8111-111111111111",
        email="dev.user@iemsnewdelhi.com",
        audience="authenticated",
        expires_in_minutes=15,
    )

    claims = jwt.decode(
        token,
        "local-test-jwt-secret-at-least-32-bytes",
        algorithms=["HS256"],
        audience="authenticated",
        issuer="http://127.0.0.1:54321/auth/v1",
    )

    assert claims["sub"] == "11111111-1111-4111-8111-111111111111"
    assert claims["email"] == "dev.user@iemsnewdelhi.com"
    assert claims["role"] == "authenticated"
    assert datetime.fromtimestamp(claims["exp"], tz=UTC) > datetime.now(tz=UTC)


def test_local_supabase_url_guard() -> None:
    assert _is_local_supabase_url("http://127.0.0.1:54321") is True
    assert _is_local_supabase_url("http://localhost:54321") is True
    assert _is_local_supabase_url("https://example.supabase.co") is False
