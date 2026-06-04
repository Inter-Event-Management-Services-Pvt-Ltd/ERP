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
```

`GET /v1/me` requires:

```text
SUPABASE_URL
SUPABASE_JWT_SECRET
SUPABASE_SERVICE_ROLE_KEY
```

The service-role key is server-only. Do not expose it through any frontend
environment variable.

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
