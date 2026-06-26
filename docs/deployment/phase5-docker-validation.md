# Phase 5 Docker Validation

Date: 2026-06-18

Updated: 2026-06-26 for production Compose security hardening.

## Commands

- `docker compose config`
- `docker compose build api worker scheduler`
- `docker compose up -d redis api worker scheduler`
- `docker compose ps`
- `docker compose exec -T api python -c "import os, urllib.request; print(os.getuid()); print(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).read().decode())"`
- `docker compose exec -T worker python -c "import os; print(os.getuid())"`
- `docker compose exec -T scheduler python -c "import os; print(os.getuid())"`
- `docker compose exec -T redis redis-cli ping`
- `docker compose logs --tail=40 scheduler`
- `docker compose restart api worker scheduler redis`
- `docker compose logs --tail=20 api`
- `docker compose logs --tail=20 worker`
- `docker compose logs --tail=20 scheduler`

## Results

Backend production image build passed for `api`, `worker`, and `scheduler`.
The backend images now use `python:3.12-alpine` after Docker Scout found
critical/high Debian `perl` CVEs in the previous `python:3.12-slim` images.

Runtime validation passed for backend-owned services:

| Service | Result | Evidence |
|---|---|---|
| api | healthy | `docker compose ps` showed `Up ... (healthy)` |
| api health | passed | container-local `/health` returned `{"status":"ok","service":"iems-erp-api","version":"0.1.0"}` |
| api user | non-root | UID `10001` |
| worker | running | `docker compose ps` showed worker `Up` |
| worker user | non-root | UID `10001` |
| scheduler | running | `docker compose ps` showed scheduler `Up` |
| scheduler user | non-root | UID `10001` |
| redis | healthy | `redis-cli ping` returned `PONG` |
| restart | passed | `docker compose restart api worker scheduler redis` completed; API returned `/health` 200 afterward |
| logs after restart | passed | API, worker and scheduler logs remained readable after restart |

Image scan evidence from 2026-06-18:

| Image | Result |
|---|---|
| `iems-erp-api:latest` | Docker Scout: 0 critical, 0 high |
| `iems-erp-worker:latest` | Docker Scout: 0 critical, 0 high |
| `iems-erp-scheduler:latest` | Docker Scout: 0 critical, 0 high |
| `redis:7-alpine` | Docker Scout: 0 critical, 0 high |
| `iems-erp-caddy:latest` | Docker Scout: 0 critical, 0 high; custom source-built Caddy image resolves OPEN-044 |

Scheduler initially restarted because Celery beat tried to write
`celerybeat-schedule` under `/app`, which is intentionally non-writable for the
non-root production user. `compose.yaml` now sets
`--schedule=/var/run/celery/celerybeat-schedule` and mounts that directory as a
dedicated uid/gid 10001 tmpfs.

## Production Compose Security Hardening

The production Compose file was tightened on 2026-06-26 after a Docker Compose
security review:

- Redis now requires `REDIS_PASSWORD`.
- API, worker and scheduler use authenticated Redis/Celery URLs.
- Production API, worker and scheduler no longer define
  `host.docker.internal:host-gateway`; managed Supabase URLs must be used for
  hosted deployments.
- Caddy admin API is disabled with `admin off`, and the custom Caddy image no
  longer exposes port 2019.
- `no-new-privileges:true` is enabled for web, API, worker, scheduler and Redis.
  Caddy is excluded because the image uses `cap_net_bind_service` to bind ports
  80/443 as a non-root user.
- CPU and memory limits are declared for every production service.
- API, worker, scheduler, web and Redis use tmpfs for ephemeral state.
- Celery beat state moved from `/tmp` to `/var/run/celery`.
- Production Compose now fails loudly when `IEMS_DOMAIN`,
  `CORS_ALLOWED_ORIGINS`, `REDIS_PASSWORD`, `SUPABASE_URL`,
  `SUPABASE_AUTH_ISSUER`, `SUPABASE_JWKS_URL`, `SUPABASE_ANON_KEY` or
  `NEXT_PUBLIC_SUPABASE_URL` is missing.
- Backend settings support `SUPABASE_SERVICE_ROLE_KEY_FILE` and
  `SUPABASE_JWT_SECRET_FILE` so production can mount these values as files
  instead of only passing raw environment values.

Validation:

- `docker compose config --quiet` passed with fake production env values.
- `docker compose -f compose.yaml -f compose.backend.yaml config --quiet`
  passed with fake production env values.
- Targeted backend tests for auth/settings and API docs passed:
  `22 passed`.

## Production Exposure Review

- Caddy public ports: only `80:80` and `443:443` are published.
- API direct public port: none. `8000/tcp` is exposed inside Docker only.
- Redis public port: none. `6379/tcp` is exposed inside Docker only.
- Backend network: `internal: true`.
- Docker socket mounts: none found in rendered config.
- Privileged containers: none found in rendered config.
- Host networking: none found in rendered config.
- Web service environment: limited to `NODE_ENV` and `NEXT_PUBLIC_*`; server
  secrets are not inherited from `.env`.
- Web service networking: frontend network only; Caddy bridges frontend/backend.

## Evidence Handling Note

`docker compose config` expands values from local `.env`, including local
development secrets. Use the command to validate the rendered service model, but
do not paste raw config output into PRs, issues, chat, or external systems.

## Full-Stack Docker Auth Validation

Additional validation on 2026-06-20 confirmed the local Docker auth topology:

- Previous local Docker auth validation used `host.docker.internal` for local
  Supabase. That mapping is no longer present in production Compose; local
  Supabase testing should use development-specific configuration only.
- `SUPABASE_URL` remains the container-reachable Supabase REST URL.
- `SUPABASE_AUTH_ISSUER` and `SUPABASE_AUTH_ISSUER_ALIASES` define the exact
  token issuers accepted by FastAPI.
- `SUPABASE_JWKS_URL` points to the container-reachable JWKS endpoint.
- FastAPI still verifies JWT signature, audience and expiry.
- API container JWKS fetch from `host.docker.internal` returned HTTP 200.
- Authenticated `GET /api/v1/me` through Caddy returned 200 for both local
  issuer forms.
- Authenticated `GET /api/v1/director/overview` through Caddy returned 200.
- Human browser smoke test confirmed Docker sign-in/sign-out and protected app
  access are working as intended on 2026-06-20.

Remaining browser sign-off for production is covered by the staging validation
runbook, especially document upload/download, admin tab behavior and
notifications.
