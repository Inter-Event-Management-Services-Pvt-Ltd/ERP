# Monitoring And Alerting Runbook

Date: 2026-06-23

Use this before closing Phase 5 monitoring and alerting. The first hosted setup
uses Vercel, Cloudflare Tunnel, Docker Compose, FastAPI, Redis/Celery and
managed Supabase.

## Minimum Signals

Track these before pilot users rely on the system:

- Frontend availability: Vercel deployment status and `/login` HTTP 200.
- Backend availability: `/health` HTTP 200 through the public API hostname.
- Backend readiness: `/ready` HTTP 200 from the backend host.
- API error rate: 5xx count and repeated 401/403/422 spikes.
- API latency: p50 and p95 request duration from FastAPI access logs.
- Supabase availability: failed PostgREST/Auth/Storage requests in API logs.
- Worker health: Celery worker process running and archive exports not stuck in
  `QUEUED` or `GENERATING`.
- Redis health: container healthy and `redis-cli ping` returns `PONG`.
- Storage workflow: document upload, signed download and archive export
  download complete successfully.

## Cheap Initial Setup

For the current low-cost hosting path:

- Use Vercel deployment alerts for frontend build/deployment failures.
- Use Cloudflare notifications for tunnel health once a named tunnel exists.
- Use a free uptime monitor for:
  - `https://<app-domain>/login`
  - `https://<api-domain>/health`
- Keep Docker logs on the backend machine with rotation enabled.
- Review Supabase project logs manually during pilot until a paid observability
  tool is selected.

## Docker Host Checks

Run on the backend machine:

```powershell
docker compose -f compose.yaml -f compose.backend.yaml ps
docker compose -f compose.yaml -f compose.backend.yaml logs --tail 100 api
docker compose -f compose.yaml -f compose.backend.yaml logs --tail 100 worker
docker compose -f compose.yaml -f compose.backend.yaml logs --tail 100 scheduler
```

Expected result:

- `api`, `worker`, `scheduler` and `redis` are running.
- API logs show request IDs and no secret values.
- Worker logs do not show repeated archive export failures.

## Alert Thresholds

Use these starting thresholds during pilot:

- `/health` unavailable for 2 minutes: high alert.
- `/login` unavailable for 2 minutes: high alert.
- API 5xx rate above 5% for 5 minutes: high alert.
- p95 API latency above 2 seconds for 10 minutes: medium alert.
- Archive export stuck in `QUEUED` or `GENERATING` for more than 15 minutes:
  medium alert.
- Supabase Auth, Storage or PostgREST failures repeated for 5 minutes:
  high alert.

Adjust after pilot usage is measurable.

## Incident Routing

Before release approval, record:

- Primary incident contact.
- Backup incident contact.
- Rollback owner.
- Where monitoring alerts are delivered.
- Where deployment credentials are stored.

Do not store actual credentials in this repository.

## Phase 5 Evidence

To mark monitoring and alerting complete, record evidence in
`docs/07_OPEN_ITEMS.md` or the release notes:

- Provider/tool names.
- Monitored URLs.
- Alert recipients.
- Date of a passing test alert.
- Date of a successful `/health` and `/login` uptime check.
