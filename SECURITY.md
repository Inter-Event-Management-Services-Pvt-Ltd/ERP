# Security Policy

## Reporting

Record implementation security issues in `docs/07_OPEN_ITEMS.md` with:

```text
Severity:
Affected module:
Description:
Reproduction:
Suggested mitigation:
Owner:
Status:
```

## Mandatory Security Baseline

- Private Storage buckets only
- Short-lived signed URLs
- Service-role key is server-only
- Google sign-in restricted to approved IEMS accounts
- RLS enabled for exposed tables
- FastAPI ABAC validation for sensitive writes
- Append-only audit trail
- Mandatory Super User override reasons
- No secrets committed to Git
- Environment-specific credentials
- Database backups and restore tests
- Dependency scanning before releases
- Staging verification before production deploys
- Rate Limiting, XSS Protection, Sql Injection Protection, Brute Force Protection and other type of protection.

See `docs/checklists/SECURITY_GLOBAL.md`.
