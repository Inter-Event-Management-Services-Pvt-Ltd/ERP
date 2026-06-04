"""Create a local Supabase test user and print a backend access token.

This script is for local development only. It reads apps/api/.env, talks to the
local Supabase Auth and REST APIs with the server-only key, then signs a short
lived JWT using the local Supabase JWT secret.
"""

from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import jwt

DEFAULT_EMAIL = "dev.user@iemsnewdelhi.com"
DEFAULT_EMPLOYEE_CODE = "IEMS-DEV-001"
DEFAULT_FULL_NAME = "IEMS Dev User"
DEFAULT_ROLE = "EMPLOYEE"


class LocalTokenError(Exception):
    pass


def main() -> int:
    args = _parse_args()
    env = _load_env(args.env_file)
    supabase_url = _required(env, "SUPABASE_URL").rstrip("/")
    service_key = _required(env, "SUPABASE_SERVICE_ROLE_KEY")
    jwt_secret = _required(env, "SUPABASE_JWT_SECRET")
    audience = env.get("SUPABASE_JWT_AUDIENCE", "authenticated")

    if not args.allow_non_local and not _is_local_supabase_url(supabase_url):
        raise LocalTokenError(
            "Refusing to create a dev token for a non-local Supabase URL. "
            "Pass --allow-non-local only for an intentional disposable environment."
        )

    with httpx.Client(timeout=10.0) as client:
        employee_id = _ensure_employee(
            client,
            supabase_url=supabase_url,
            service_key=service_key,
            email=args.email,
            employee_code=args.employee_code,
            full_name=args.full_name,
        )
        auth_user_id = _ensure_auth_user(
            client,
            supabase_url=supabase_url,
            service_key=service_key,
            email=args.email,
            password=args.password,
            full_name=args.full_name,
        )
        _ensure_user_account(
            client,
            supabase_url=supabase_url,
            service_key=service_key,
            auth_user_id=auth_user_id,
            employee_id=employee_id,
            is_super_user=args.super_user,
        )
        _ensure_role_assignment(
            client,
            supabase_url=supabase_url,
            service_key=service_key,
            auth_user_id=auth_user_id,
            role_code=args.role,
        )

    token = build_access_token(
        jwt_secret=jwt_secret,
        supabase_url=supabase_url,
        auth_user_id=auth_user_id,
        email=args.email,
        audience=audience,
        expires_in_minutes=args.expires_minutes,
    )

    print(f"email: {args.email}")
    print(f"auth_user_id: {auth_user_id}")
    print(f"employee_id: {employee_id}")
    print(f"role: {args.role}")
    print(f"expires_in_minutes: {args.expires_minutes}")
    print()
    print(token)
    print()
    print("PowerShell:")
    print(f'$env:IEMS_ACCESS_TOKEN="{token}"')
    print(
        'curl.exe -i http://localhost:8000/v1/me '
        '-H "Authorization: Bearer $env:IEMS_ACCESS_TOKEN"'
    )
    print(
        'curl.exe -i http://localhost:8000/v1/me/permissions '
        '-H "Authorization: Bearer $env:IEMS_ACCESS_TOKEN"'
    )
    return 0


def build_access_token(
    *,
    jwt_secret: str,
    supabase_url: str,
    auth_user_id: str,
    email: str,
    audience: str,
    expires_in_minutes: int,
) -> str:
    now = datetime.now(tz=UTC)
    return jwt.encode(
        {
            "iss": f"{supabase_url.rstrip('/')}/auth/v1",
            "aud": audience,
            "sub": auth_user_id,
            "email": email,
            "role": "authenticated",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=expires_in_minutes)).timestamp()),
        },
        jwt_secret,
        algorithm="HS256",
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--email", default=DEFAULT_EMAIL)
    parser.add_argument("--password", default="LocalDevPassword123!")
    parser.add_argument("--employee-code", default=DEFAULT_EMPLOYEE_CODE)
    parser.add_argument("--full-name", default=DEFAULT_FULL_NAME)
    parser.add_argument("--role", default=DEFAULT_ROLE)
    parser.add_argument("--super-user", action="store_true")
    parser.add_argument("--expires-minutes", type=int, default=60)
    parser.add_argument("--allow-non-local", action="store_true")
    return parser.parse_args()


def _load_env(path: Path) -> dict[str, str]:
    values = dict(os.environ)
    if not path.exists():
        raise LocalTokenError(f"Env file not found: {path}")

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _required(env: dict[str, str], key: str) -> str:
    value = env.get(key)
    if value is None or value == "":
        raise LocalTokenError(f"Missing required environment value: {key}")
    return value


def _is_local_supabase_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.hostname in {"localhost", "127.0.0.1", "::1"}


def _ensure_employee(
    client: httpx.Client,
    *,
    supabase_url: str,
    service_key: str,
    email: str,
    employee_code: str,
    full_name: str,
) -> str:
    existing = _rest_get(
        client,
        supabase_url=supabase_url,
        service_key=service_key,
        path="/rest/v1/employees",
        params={"select": "id", "official_email": f"eq.{email}", "limit": "1"},
    )
    if existing:
        return str(existing[0]["id"])

    created = _rest_post(
        client,
        supabase_url=supabase_url,
        service_key=service_key,
        path="/rest/v1/employees",
        json_body={
            "employee_code": employee_code,
            "full_name": full_name,
            "official_email": email,
            "designation": "Local Dev",
            "employment_status": "ACTIVE",
        },
        params={"select": "id"},
        prefer="return=representation",
    )
    return str(created[0]["id"])


def _ensure_auth_user(
    client: httpx.Client,
    *,
    supabase_url: str,
    service_key: str,
    email: str,
    password: str,
    full_name: str,
) -> str:
    existing_user_id = _find_auth_user_id(
        client,
        supabase_url=supabase_url,
        service_key=service_key,
        email=email,
    )
    if existing_user_id is not None:
        return existing_user_id

    response = client.post(
        f"{supabase_url}/auth/v1/admin/users",
        headers=_admin_headers(service_key),
        json={
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"full_name": full_name},
        },
    )
    if response.status_code >= 400:
        raise LocalTokenError(f"Auth user creation failed: {response.status_code} {response.text}")
    payload = response.json()
    return str(payload["id"])


def _find_auth_user_id(
    client: httpx.Client,
    *,
    supabase_url: str,
    service_key: str,
    email: str,
) -> str | None:
    page = 1
    while True:
        response = client.get(
            f"{supabase_url}/auth/v1/admin/users",
            headers=_admin_headers(service_key),
            params={"page": str(page), "per_page": "100"},
        )
        if response.status_code >= 400:
            raise LocalTokenError(
                f"Auth user lookup failed: {response.status_code} {response.text}"
            )

        users = response.json().get("users", [])
        for user in users:
            if isinstance(user, dict) and str(user.get("email", "")).lower() == email.lower():
                return str(user["id"])
        if not users or len(users) < 100:
            return None
        page += 1


def _ensure_user_account(
    client: httpx.Client,
    *,
    supabase_url: str,
    service_key: str,
    auth_user_id: str,
    employee_id: str,
    is_super_user: bool,
) -> None:
    _rest_post(
        client,
        supabase_url=supabase_url,
        service_key=service_key,
        path="/rest/v1/user_accounts",
        json_body={
            "id": auth_user_id,
            "employee_id": employee_id,
            "is_active": True,
            "is_super_user": is_super_user,
        },
        params={"on_conflict": "id"},
        prefer="resolution=merge-duplicates",
    )


def _ensure_role_assignment(
    client: httpx.Client,
    *,
    supabase_url: str,
    service_key: str,
    auth_user_id: str,
    role_code: str,
) -> None:
    roles = _rest_get(
        client,
        supabase_url=supabase_url,
        service_key=service_key,
        path="/rest/v1/roles",
        params={"select": "id", "code": f"eq.{role_code}", "limit": "1"},
    )
    if not roles:
        raise LocalTokenError(f"Role not found: {role_code}")

    _rest_post(
        client,
        supabase_url=supabase_url,
        service_key=service_key,
        path="/rest/v1/user_role_assignments",
        json_body={"user_account_id": auth_user_id, "role_id": roles[0]["id"]},
        params={"on_conflict": "user_account_id,role_id"},
        prefer="resolution=ignore-duplicates",
    )


def _rest_get(
    client: httpx.Client,
    *,
    supabase_url: str,
    service_key: str,
    path: str,
    params: dict[str, str],
) -> list[dict[str, Any]]:
    response = client.get(
        f"{supabase_url}{path}",
        headers=_rest_headers(service_key),
        params=params,
    )
    if response.status_code >= 400:
        raise LocalTokenError(f"REST GET failed for {path}: {response.status_code} {response.text}")
    payload = response.json()
    if not isinstance(payload, list):
        raise LocalTokenError(f"REST GET returned unexpected payload for {path}")
    return payload


def _rest_post(
    client: httpx.Client,
    *,
    supabase_url: str,
    service_key: str,
    path: str,
    json_body: dict[str, Any],
    params: dict[str, str] | None = None,
    prefer: str,
) -> list[dict[str, Any]]:
    headers = _rest_headers(service_key)
    headers["Prefer"] = prefer
    response = client.post(
        f"{supabase_url}{path}",
        headers=headers,
        params=params,
        json=json_body,
    )
    if response.status_code >= 400:
        raise LocalTokenError(
            f"REST POST failed for {path}: {response.status_code} {response.text}"
        )
    if not response.content:
        return []
    payload = response.json()
    if not isinstance(payload, list):
        raise LocalTokenError(f"REST POST returned unexpected payload for {path}")
    return payload


def _admin_headers(service_key: str) -> dict[str, str]:
    headers = {
        "apikey": service_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if not service_key.startswith("sb_secret_"):
        headers["Authorization"] = f"Bearer {service_key}"
    return headers


def _rest_headers(service_key: str) -> dict[str, str]:
    headers = {
        "apikey": service_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if not service_key.startswith("sb_secret_"):
        headers["Authorization"] = f"Bearer {service_key}"
    return headers


if __name__ == "__main__":
    raise SystemExit(main())
