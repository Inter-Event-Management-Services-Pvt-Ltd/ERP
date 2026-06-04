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
