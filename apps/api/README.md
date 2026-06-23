# FastAPI application

Codex scaffolds this application.

## Local Development

```powershell
uv sync
uv run --group dev pytest
uv run --group dev ruff check .
uv run --group dev mypy app scripts
```

## Shell Endpoints

```text
GET /health
GET /ready
GET /v1/me
GET /v1/me/permissions
GET /v1/employees
GET /v1/project-types
GET /v1/project-statuses
GET /v1/priority-levels
```

`GET /v1/me` requires:

```text
SUPABASE_URL
SUPABASE_JWT_SECRET
SUPABASE_SERVICE_ROLE_KEY
```

The service-role key is server-only. Do not expose it through any frontend
environment variable.

For browser access during local development, keep:

```text
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

For non-IEMS local/staging accounts, set `ALLOWED_EMAIL_DOMAINS` to an explicit
comma-separated allowlist. The current-user resolver still requires an approved
employee account with a matching official email.

## Rate Limiting And Security Headers

The API has native fixed-window rate limiting backed by Redis, with an
in-memory fallback for local/test operation. Keep Redis configured in staging
and production:

```text
RATE_LIMIT_ENABLED=true
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_DEFAULT_REQUESTS=120
RATE_LIMIT_AUTH_REQUESTS=30
RATE_LIMIT_UPLOAD_REQUESTS=20
RATE_LIMIT_EXPORT_REQUESTS=10
RATE_LIMIT_ADMIN_REQUESTS=60
RATE_LIMIT_TRUST_PROXY_HEADERS=true
```

Route groups map to auth/current-user, upload, archive export and admin/audit
paths. Limit responses use `429 RATE_LIMIT_EXCEEDED` and include
`Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`,
`X-RateLimit-Reset` and `X-RateLimit-Policy`.

The API also emits conservative security headers, including
`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`,
`Permissions-Policy`, `Cross-Origin-Opener-Policy` and a default-deny
`Content-Security-Policy` for API responses. Keep Cloudflare/WAF rate limiting
as the outer protection layer for production traffic.

## Workers

Celery uses the app namespace `iems_erp`:

```powershell
uv run celery -A app.workers.celery_app worker --loglevel=INFO
uv run celery -A app.workers.celery_app beat --loglevel=INFO
```

Runtime logs are structured JSON. Configure verbosity with `LOG_LEVEL`.

## Local Access Token

With local Supabase running and `apps/api/.env` populated from local values:

```powershell
uv run python scripts/local_access_token.py
```

The script creates or reuses a local-only development user, links it to an
employee account, assigns the default `EMPLOYEE` role, and prints a short-lived
access token plus ready-to-run PowerShell `curl.exe` commands. It refuses
non-local Supabase URLs unless explicitly overridden for a disposable
environment.
