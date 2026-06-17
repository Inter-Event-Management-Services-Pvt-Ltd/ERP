# Phase 5 Checklist — Hardening and Deployment

## Tests

- [x] Unit tests.
- [x] Integration tests.
- [x] RLS tests.
- [x] ABAC tests.
- [x] Unauthorized-path tests.
- [x] Migration-reset test.
- [ ] ZIP export test.
- [ ] File checkout race test.
- [x] Restore test.

## CI/CD

- [x] Lint.
- [x] Type check.
- [x] Backend tests.
- [ ] Frontend tests.
- [ ] Build frontend.
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
- [ ] Dependency scan passes.
- [x] Secret scan passes.
- [ ] Service-role key server-only check passes.
- [x] Storage buckets verified private.
- [x] RLS verified enabled.
- [ ] No debug endpoints exposed.
- [ ] Logging excludes secrets.
- [x] Restore test passes.

## Exit Criteria

- [ ] Staging is production-like.
- [ ] Release candidate is approved.

## Docker Production Gate

- [ ] Complete `docs/checklists/DOCKERIZATION.md`.
- [x] Production Compose config validated.
- [ ] Containers run as non-root.
- [ ] Image scan passes.
- [ ] Restart test passes.
- [x] Only reverse proxy ports are public.
