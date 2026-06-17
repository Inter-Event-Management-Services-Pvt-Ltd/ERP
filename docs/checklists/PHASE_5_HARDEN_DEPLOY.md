# Phase 5 Checklist — Hardening and Deployment

## Tests

- [ ] Unit tests.
- [ ] Integration tests.
- [x] RLS tests.
- [ ] ABAC tests.
- [ ] Unauthorized-path tests.
- [x] Migration-reset test.
- [ ] ZIP export test.
- [ ] File checkout race test.
- [ ] Restore test.

## CI/CD

- [ ] Lint.
- [ ] Type check.
- [ ] Backend tests.
- [ ] Frontend tests.
- [ ] Build frontend.
- [x] Build backend image.
- [ ] Run migration validation.
- [ ] Deploy staging.
- [ ] Health checks.
- [ ] Manual production promotion.

## Operations

- [ ] Configure staging.
- [ ] Configure production.
- [ ] Configure monitoring.
- [ ] Configure alerting.
- [ ] Configure database backups.
- [ ] Configure Storage backups.
- [ ] Test restore.
- [ ] Write rollback steps.
- [ ] Write incident-response notes.

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
- [ ] Restore test passes.

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
