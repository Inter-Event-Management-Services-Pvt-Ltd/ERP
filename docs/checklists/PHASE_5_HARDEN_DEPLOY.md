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
- [ ] Deploy staging. Temporary Vercel plus Cloudflare Quick Tunnel smoke
  deployment was exercised on 2026-06-22, but production-like staging still
  requires a stable domain or named tunnel, staging Supabase, and recorded
  runbook evidence.
- [x] Health checks.
- [ ] Manual production promotion.

## Operations

- [ ] Configure staging. Runbook is documented; stable staging domain, named
  tunnel and external staging evidence still require human setup.
- [ ] Configure production.
- [ ] Configure monitoring. Runbook added at
  `docs/deployment/monitoring-alerting-runbook.md`; provider setup and test
  alert evidence still require human setup.
- [ ] Configure alerting. Runbook added at
  `docs/deployment/monitoring-alerting-runbook.md`; alert recipients and a test
  alert still need to be recorded.
- [ ] Configure database backups. Hosted Supabase backup evidence requirements
  are documented in `docs/deployment/backup-restore-runbook.md`; dashboard
  configuration still requires human setup.
- [ ] Configure Storage backups. Supabase Storage sync/offsite backup plan is
  documented in `docs/deployment/backup-restore-runbook.md`; scheduled sync and
  restore evidence still require human setup.
- [x] Test restore.
- [x] Write rollback steps.
- [x] Write incident-response notes.

## Security Gate

- [ ] Complete `SECURITY_GLOBAL.md`.
- [ ] Complete `SECURITY_RELEASE_GATE.md`. Threat review, auth allowlist test
  evidence and native rate limiting are documented; backup, incident owner,
  Cloudflare/WAF evidence and human approval items remain open.
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

- [ ] Staging is production-like.
- [ ] Release candidate is approved.

## Docker Production Gate

- [ ] Complete `docs/checklists/DOCKERIZATION.md`.
- [x] Production Compose config validated.
- [x] Containers run as non-root. API, worker, scheduler, and web all run as
  UID 10001 in Docker validation on 2026-06-18.
- [x] Image scan passes. Web (node:24-alpine): 0C 0H 0M 0L on 2026-06-18.
  Backend API/worker/scheduler (python:3.12-alpine): 0C 0H 0M 0L.
  Redis (redis:7-alpine): 0C 0H 0M 0L. Custom source-built Caddy image:
  0C 0H 0M 0L; OPEN-044 resolved.
- [x] Restart test passes. `docker compose restart api worker scheduler redis` completed and API health/log checks passed after restart on 2026-06-18.
- [x] Only reverse proxy ports are public.
