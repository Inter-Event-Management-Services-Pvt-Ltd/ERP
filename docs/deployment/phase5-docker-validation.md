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

## Deferred Frontend/Caddy Runtime Checks

Full `caddy -> web -> api` runtime validation is still Claude-owned because it
requires building and running the Next.js production container under `apps/web`.
See `OPEN-040`.
