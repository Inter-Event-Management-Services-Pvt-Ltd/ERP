# FastAPI application

Codex scaffolds this application.

## Local Development

```powershell
uv sync
uv run --group dev pytest
uv run --group dev ruff check .
uv run --group dev mypy app
```

## Shell Endpoints

```text
GET /health
GET /ready
GET /v1/me
```

`GET /v1/me` requires:

```text
SUPABASE_URL
SUPABASE_JWT_SECRET
SUPABASE_SERVICE_ROLE_KEY
```

The service-role key is server-only. Do not expose it through any frontend
environment variable.
