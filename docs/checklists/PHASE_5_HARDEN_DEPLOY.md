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
- [ ] Frontend tests. No test files exist; vitest finds zero suites. See OPEN-042.
- [x] Build frontend. `npm run build` passes clean with 42 routes on 2026-06-18.
- [x] Build backend image.
- [x] Run migration validation.
- [ ] Deploy staging.
- [x] Health checks.
- [ ] Manual production promotion.

## Operations

- [ ] Configure staging.
- [ ] Configure production.
- [ ] Configure monitoring.
- [ ] Configure alerting.
- [ ] Configure database backups.
- [ ] Configure Storage backups.
- [x] Test restore.
- [x] Write rollback steps.
- [x] Write incident-response notes.

## Security Gate

- [ ] Complete `SECURITY_GLOBAL.md`.
- [ ] Complete `SECURITY_RELEASE_GATE.md`.
- [x] Dependency scan passes. `uv run --group dev pip-audit` returned no known vulnerabilities on 2026-06-18.
- [x] Secret scan passes.
- [x] Service-role key server-only check passes. Secret scan checks tracked files, backend Docker validation confirms secrets are not baked into images, and frontend bundle secret-scan evidence remains recorded in Dockerization docs.
- [x] Storage buckets verified private.
- [x] RLS verified enabled.
- [x] No debug endpoints exposed. `test_no_debug_or_token_helper_routes_are_registered` passed on 2026-06-18.
- [x] Logging excludes secrets. Supabase timing-log test verifies headers, request payloads and query values are not emitted.
- [x] Restore test passes.

## Exit Criteria

- [ ] Staging is production-like.
- [ ] Release candidate is approved.

## Docker Production Gate

- [ ] Complete `docs/checklists/DOCKERIZATION.md`.
- [x] Production Compose config validated.
- [x] Containers run as non-root. API, worker and scheduler all ran as UID 10001 in Docker validation on 2026-06-18.
- [ ] Image scan passes.
- [x] Restart test passes. `docker compose restart api worker scheduler redis` completed and API health/log checks passed after restart on 2026-06-18.
- [x] Only reverse proxy ports are public.
