# Phase 5 Docker Validation

Date: 2026-06-18

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
`--schedule=/tmp/celerybeat-schedule`; scheduler logs confirm Celery beat starts
with `. db -> /tmp/celerybeat-schedule`.

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

- API, worker and scheduler attach to an egress network so they can reach local
  Docker Supabase at `host.docker.internal` without exposing Redis.
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
