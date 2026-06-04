---
name: iems-release-check
description: Use before staging or production release of the IEMS ERP to verify security, tests, Docker images, migrations, backups, rollback steps, monitoring, and release documentation.
---

# IEMS Release Check

Read:

- `docs/checklists/PHASE_5_HARDEN_DEPLOY.md`
- `docs/checklists/SECURITY_RELEASE_GATE.md`
- `docs/checklists/DOCKERIZATION.md`
- `docs/09_RISK_REGISTER.md`
- `docs/07_OPEN_ITEMS.md`

Verify:

- migration validation
- backend tests
- frontend tests
- unauthorized-path tests
- RLS tests
- ABAC tests
- Docker health checks
- non-root containers
- image scan
- secret scan
- private buckets
- signed URL expiry
- backup exists
- restore test passes
- rollback procedure exists
- monitoring works
- human approval recorded

Do not approve production if any critical security item remains open.
