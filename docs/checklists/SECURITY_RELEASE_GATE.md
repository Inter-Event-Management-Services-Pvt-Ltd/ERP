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
- [ ] Backup exists. Local restore proof exists; hosted Supabase database and
  Storage backup evidence must still be recorded before production.
- [x] Restore test passed.
- [ ] Incident contact and rollback owner identified. Required fields are
  documented in `docs/deployment/monitoring-alerting-runbook.md`; names still
  need to be recorded by the release owner.
- [ ] Human approval recorded.
