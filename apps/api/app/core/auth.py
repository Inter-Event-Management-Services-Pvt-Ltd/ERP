from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

import jwt
from jwt import InvalidTokenError, PyJWKClient, PyJWKClientError

from app.core.config import Settings


@dataclass(frozen=True)
class TokenClaims:
    subject: UUID
    email: str
    role: str
    issuer: str
    audience: str
    expires_at: datetime


class AuthError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def parse_bearer_token(authorization: str | None) -> str:
    if authorization is None or not authorization.strip():
        raise AuthError(401, "AUTH_REQUIRED", "Authentication required")

    scheme, separator, token = authorization.partition(" ")
    if separator == "" or scheme.lower() != "bearer" or not token.strip():
        raise AuthError(401, "AUTH_REQUIRED", "Authorization Bearer token required")

    return token.strip()


class SupabaseJwtVerifier:
    def __init__(
        self,
        *,
        jwt_secret: str | None,
        issuer: str | None,
        audience: str,
        allowed_email_domain: str | None = None,
        allowed_email_domains: Iterable[str] | None = None,
        issuer_aliases: Iterable[str] | None = None,
        jwks_url: str | None = None,
    ) -> None:
        self._jwt_secret = jwt_secret
        self._issuer = issuer
        self._issuers = _allowed_issuers(issuer=issuer, issuer_aliases=issuer_aliases)
        self._audience = audience
        self._allowed_email_domains = _allowed_domains(
            allowed_email_domain=allowed_email_domain,
            allowed_email_domains=allowed_email_domains,
        )
        self._jwks_url = jwks_url

    @classmethod
    def from_settings(cls, settings: Settings) -> "SupabaseJwtVerifier":
        return cls(
            jwt_secret=settings.supabase_jwt_secret,
            issuer=settings.supabase_auth_issuer,
            audience=settings.supabase_jwt_audience,
            allowed_email_domains=settings.allowed_email_domain_list,
            issuer_aliases=settings.supabase_auth_issuer_list[1:],
            jwks_url=settings.supabase_jwks_url,
        )

    def verify(self, token: str) -> TokenClaims:
        self._ensure_configured()
        header = self._unverified_header(token)
        algorithm = header.get("alg")
        if algorithm not in {"HS256", "RS256", "ES256"}:
            raise AuthError(401, "INVALID_TOKEN", "Unsupported token signing algorithm")

        if algorithm == "HS256":
            payload = self._decode_hs256(token)
        else:
            payload = self._decode_jwks(token, algorithm)

        claims = self._claims_from_payload(payload)
        if claims.issuer not in self._issuers:
            raise AuthError(401, "INVALID_TOKEN", "Invalid access token")
        return claims

    def _ensure_configured(self) -> None:
        if not self._issuers:
            raise AuthError(503, "AUTH_NOT_CONFIGURED", "Supabase Auth issuer is not configured")

    def _unverified_header(self, token: str) -> dict[str, Any]:
        try:
            return jwt.get_unverified_header(token)
        except InvalidTokenError as exc:
            raise AuthError(401, "INVALID_TOKEN", "Invalid access token") from exc

    def _decode_hs256(self, token: str) -> dict[str, object]:
        if self._jwt_secret is None:
            raise AuthError(503, "AUTH_NOT_CONFIGURED", "Supabase JWT secret is not configured")

        return self._decode_with_key(token=token, key=self._jwt_secret, algorithms=["HS256"])

    def _decode_jwks(self, token: str, algorithm: str) -> dict[str, object]:
        if self._jwks_url is None:
            raise AuthError(503, "AUTH_NOT_CONFIGURED", "Supabase JWKS URL is not configured")

        try:
            signing_key: Any = PyJWKClient(self._jwks_url).get_signing_key_from_jwt(token).key
        except PyJWKClientError as exc:
            raise AuthError(401, "INVALID_TOKEN", "Invalid access token") from exc

        return self._decode_with_key(token=token, key=signing_key, algorithms=[algorithm])

    def _decode_with_key(
        self,
        *,
        token: str,
        key: Any,
        algorithms: list[str],
    ) -> dict[str, object]:
        try:
            return cast(
                dict[str, object],
                jwt.decode(
                    token,
                    key,
                    algorithms=algorithms,
                    audience=self._audience,
                    options={"verify_iss": False},
                ),
            )
        except InvalidTokenError as exc:
            raise AuthError(401, "INVALID_TOKEN", "Invalid access token") from exc

    def _claims_from_payload(self, payload: dict[str, object]) -> TokenClaims:
        subject = _uuid_claim(payload, "sub")
        email = _str_claim(payload, "email")
        role = _str_claim(payload, "role")
        issuer = _str_claim(payload, "iss")
        exp = _int_claim(payload, "exp")

        if role != "authenticated":
            raise AuthError(401, "INVALID_TOKEN", "Invalid access token role")

        self._validate_email_domain(email)

        return TokenClaims(
            subject=subject,
            email=email,
            role=role,
            issuer=issuer,
            audience=self._audience,
            expires_at=datetime.fromtimestamp(exp, tz=UTC),
        )

    def _validate_email_domain(self, email: str) -> None:
        _, separator, domain = email.lower().rpartition("@")
        if separator == "" or domain not in self._allowed_email_domains:
            raise AuthError(403, "EMAIL_DOMAIN_NOT_ALLOWED", "Email domain is not allowed")


def _str_claim(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise AuthError(401, "INVALID_TOKEN", f"Token claim `{key}` is missing or invalid")
    return value


def _int_claim(payload: dict[str, object], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise AuthError(401, "INVALID_TOKEN", f"Token claim `{key}` is missing or invalid")
    return value


def _uuid_claim(payload: dict[str, object], key: str) -> UUID:
    value = _str_claim(payload, key)
    try:
        return UUID(value)
    except ValueError as exc:
        raise AuthError(401, "INVALID_TOKEN", f"Token claim `{key}` is invalid") from exc


def _allowed_domains(
    *,
    allowed_email_domain: str | None,
    allowed_email_domains: Iterable[str] | None,
) -> frozenset[str]:
    domains: list[str] = []
    if allowed_email_domains is not None:
        domains.extend(allowed_email_domains)
    if allowed_email_domain is not None:
        domains.append(allowed_email_domain)

    normalized = {
        domain.strip().lower().lstrip("@")
        for domain in domains
        if domain.strip().lstrip("@")
    }
    if not normalized:
        raise AuthError(503, "AUTH_NOT_CONFIGURED", "Allowed email domains are not configured")
    return frozenset(normalized)


def _allowed_issuers(
    *,
    issuer: str | None,
    issuer_aliases: Iterable[str] | None,
) -> frozenset[str]:
    issuers: list[str] = []
    if issuer is not None:
        issuers.append(issuer)
    if issuer_aliases is not None:
        issuers.extend(issuer_aliases)

    normalized = {value.strip().rstrip("/") for value in issuers if value.strip().rstrip("/")}
    return frozenset(normalized)
