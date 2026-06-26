# Security Release Gate

Complete before production deployment.

- [x] Threat review completed. See `docs/security/phase5-threat-review.md`.
- [x] Auth allowlist tested with approved and rejected accounts. Backend tests
  cover accepted IEMS accounts, rejected outside-domain tokens, disabled
  accounts and employee-email mismatch.
- [x] RLS tests pass.
- [x] ABAC tests pass.
- [x] Super User override tests pass.
- [x] Storage bucket privacy verified.
- [x] Signed URL expiry verified.
- [x] Audit immutability verified.
- [x] Audit coverage verified.
- [x] File upload validation verified.
- [x] Native API rate limiting implemented and documented. See
  `docs/deployment/rate-limiting-decision.md`; Cloudflare/WAF edge enforcement
  evidence remains a production deployment task.
- [x] Dependency vulnerabilities reviewed.
- [x] Secret scan clean.
- [x] Backend injection and abuse pattern scan clean.
- [x] Backup exists. Local database backup/restore and local Storage
  export/restore spot-checks passed on 2026-06-26. Hosted Supabase managed
  backups/PITR and hosted Storage backup proof are unavailable on the current
  Free plan and are explicitly risk-accepted in `OPEN-002`.
- [x] Restore test passed.
- [x] Incident contact and rollback owner identified. Pratham is recorded as
  primary incident contact, backup incident contact and rollback owner in
  `docs/deployment/monitoring-alerting-runbook.md`; email is the current alert
  delivery channel.
- [x] Human approval recorded. On 2026-06-26, Pratham confirmed:
  "I, Pratham, reviewed the production Compose file and approve it. I approve
  this release candidate for production. Manual production promotion is
  complete."
