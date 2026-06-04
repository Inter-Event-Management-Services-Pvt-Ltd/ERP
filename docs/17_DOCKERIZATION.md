# Dockerization Plan

Docker is mandatory for local integration, staging, and production deployment.

## Services

```text
web        Next.js frontend
api        FastAPI backend
worker     Celery worker
scheduler  Celery beat scheduler
redis      broker and result backend
caddy      reverse proxy and TLS termination
```

Managed Supabase remains external in production.

Local Supabase is started separately with:

```bash
supabase start
```

## Development

```bash
cp .env.example .env.development
supabase start
docker compose -f compose.dev.yaml up --build
```

## Production

```bash
cp .env.example .env
docker compose up -d --build
```

## Important Rules

- No secrets inside Docker images.
- Secrets come from environment variables or a production secret manager.
- Never commit `.env`.
- Build images as non-root users.
- Use health checks.
- Pin image versions.
- Keep `backend` network internal.
- Expose only Caddy publicly in production.
- Keep Redis private.
- Do not mount the Docker socket.
- Do not use privileged containers.
- Do not use host networking in production.
- Scan images before release.
- Rebuild images regularly for patched base images.
