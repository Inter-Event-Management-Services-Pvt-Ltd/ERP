# Phase 5 Checklist — Hardening and Deployment

## Tests

- [x] Unit tests.
- [x] Integration tests.
- [x] RLS tests.
- [x] ABAC tests.
- [x] Unauthorized-path tests.
- [x] Migration-reset test.
- [x] ZIP export test. `test_archive_exports_worker.py` verifies generated ZIP directory entries preserve the project folder hierarchy, including empty folders.
- [x] File checkout race test. Phase 2 SQL validation verifies duplicate open physical-file checkout is rejected by the audited checkout path/database guard.
- [x] Restore test.

## CI/CD

- [x] Lint.
- [x] Type check.
- [x] Backend tests.
- [x] Frontend tests. 40 tests / 10 suites pass on 2026-06-18. See OPEN-042 resolved.
- [x] Build frontend. `npm run build` passes clean with 47 routes on 2026-06-18.
- [x] Build backend image.
- [x] Run migration validation.
- [x] Deploy staging. The current release candidate is reachable through stable
  hosted endpoints: `https://erp-dusky-six.vercel.app/login` returned 200 and
  `https://api.prathlabs.com/health` returned 200 on 2026-06-26. API docs are
  not exposed on the hosted API domain.
- [x] Health checks.
- [x] Manual production promotion. Pratham confirmed on 2026-06-26 that manual
  production promotion is complete after the backend hardening deploy was
  pulled, rebuilt and verified working on the server.

## Operations

- [x] Configure staging. Stable Vercel frontend and Cloudflare-hosted API
  endpoint are active for the current release candidate; CORS preflight from
  `https://erp-dusky-six.vercel.app` to `https://api.prathlabs.com/v1/me`
  returned 200 with the expected `Access-Control-Allow-Origin` on 2026-06-26.
- [x] Configure production. Hosted API health returned 200, frontend login
  returned 200, `/docs`, `/redoc` and `/openapi.json` returned 404, and CORS is
  locked to the deployed frontend origin.
- [x] Configure monitoring. Cloudflare Tunnel health notifications, Uptime Kuma
  monitors, UptimeRobot monitors, Dozzle log inspection and credential-storage
  location are recorded in
  `docs/deployment/monitoring-alerting-runbook.md`; a monitoring test alert and
  recovery path was verified.
- [x] Configure alerting. Cloudflare Tunnel health notifications and incident
  owner/rollback owner are recorded in
  `docs/deployment/monitoring-alerting-runbook.md`; a monitoring test alert and
  recovery path was verified.
- [x] Configure database backups. Local database backup/restore proof passed on
  2026-06-26; hosted Supabase managed backups/PITR are unavailable on the
  current Free plan and the release owner accepted deferring hosted backup proof
  in `OPEN-002`.
- [x] Configure Storage backups. Local Storage export/restore spot-check passed
  on 2026-06-26; hosted/offsite Storage backup evidence is deferred under the
  same `OPEN-002` risk acceptance until upgrade or heavier production use.
- [x] Test restore.
- [x] Write rollback steps.
- [x] Write incident-response notes.

## Security Gate

- [x] Complete `SECURITY_GLOBAL.md`.
- [x] Complete `SECURITY_RELEASE_GATE.md`. Threat review, auth allowlist test
  evidence, native rate limiting, incident ownership, monitoring, accepted
  backup risk and human release approval are documented.
- [x] Dependency scan passes. `uv run --group dev pip-audit` returned no known vulnerabilities on 2026-06-18.
- [x] Secret scan passes.
- [x] Service-role key server-only check passes. Secret scan checks tracked files, backend Docker validation confirms secrets are not baked into images, and frontend bundle secret-scan evidence remains recorded in Dockerization docs.
- [x] Storage buckets verified private.
- [x] RLS verified enabled.
- [x] No debug endpoints exposed. `test_no_debug_or_token_helper_routes_are_registered` passed on 2026-06-18.
- [x] Public API docs disabled outside local development/test by default.
  Hosted API domains should keep `ENABLE_API_DOCS=false` so `/docs`, `/redoc`
  and `/openapi.json` are not publicly exposed.
- [x] Logging excludes secrets. Supabase timing-log test verifies headers, request payloads and query values are not emitted.
- [x] Restore test passes.

## Exit Criteria

- [x] Staging is production-like.
- [x] Release candidate is approved. Pratham approved the release candidate for
  production on 2026-06-26.

## Docker Production Gate

- [x] Complete `docs/checklists/DOCKERIZATION.md`.
- [x] Production Compose config validated.
- [x] Containers run as non-root. API, worker, scheduler, and web all run as
  UID 10001 in Docker validation on 2026-06-18.
- [x] Image scan passes. Web (node:24-alpine): 0C 0H 0M 0L on 2026-06-18.
  Backend API/worker/scheduler (python:3.12-alpine): 0C 0H 0M 0L.
  Redis (redis:7-alpine): 0C 0H 0M 0L. Custom source-built Caddy image:
  0C 0H 0M 0L; OPEN-044 resolved.
- [x] Restart test passes. `docker compose restart api worker scheduler redis` completed and API health/log checks passed after restart on 2026-06-18.
- [x] Only reverse proxy ports are public.
