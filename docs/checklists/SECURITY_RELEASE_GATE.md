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
- [x] Rate-limiting decision documented. See
  `docs/deployment/rate-limiting-decision.md`; production enforcement remains a
  deployment task.
- [x] Dependency vulnerabilities reviewed.
- [x] Secret scan clean.
- [ ] Backup exists.
- [x] Restore test passed.
- [ ] Incident contact and rollback owner identified.
- [ ] Human approval recorded.
