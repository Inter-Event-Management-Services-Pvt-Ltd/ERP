# Global Security Checklist

## Secrets

- [x] No secrets committed to Git.
- [x] `.env` is ignored.
- [x] Supabase service-role key is server-only.
- [x] JWT secret is server-only. Backend Docker validation confirms JWT secret is only present in backend-owned service environments and is not baked into images.
- [x] Redis credentials are server-only. Production Compose keeps Redis on the internal backend network and browser-facing services do not receive Redis URLs.
- [ ] Production and staging credentials differ.
- [x] Key rotation procedure exists. See
  `docs/deployment/key-rotation-procedure.md`.

## Authentication

- [x] Google sign-in configured. Docker browser smoke test confirmed sign-in on
  2026-06-20.
- [x] Domain and employee allowlist enforced. Backend tests cover rejected
  outside-domain tokens and employee-account resolution.
- [x] Disabled employees cannot sign in. Backend current-user resolver test
  rejects disabled accounts.
- [x] Director account tested. Backend resolver and Docker auth probes validated
  Director/Super User context.
- [x] Session expiry tested. JWT verifier regression test rejects expired access
  tokens.
- [x] Logout tested. Docker browser smoke test confirmed sign-out on 2026-06-20.

## Authorization

- [x] Default-deny ABAC.
- [x] Server-side checks for writes.
- [x] RLS enabled on exposed tables. Phase 5 local SQL probe passed after clean reset on 2026-06-17.
- [x] Super User override requires reason.
- [x] Override logged.
- [x] Unauthorized tests exist.

## Injection and Abuse Protection

- [x] SQL injection controls reviewed. Backend uses Supabase PostgREST/RPC calls
  and typed request models instead of string-built SQL in application code.
- [x] Command injection controls reviewed. Backend security scan blocks shell
  execution patterns in production app code.
- [x] Dynamic code execution blocked by review guardrail. Backend security scan
  fails `eval`, `exec` and `compile` patterns.
- [x] Unsafe deserialization blocked by review guardrail. Backend security scan
  fails `pickle`, `marshal` and unsafe `yaml.load` patterns.
- [x] SSRF controls reviewed. Direct outbound HTTP is limited to approved
  Supabase helper paths.
- [x] Native API rate limiting implemented. FastAPI now enforces Redis-backed
  route-group limits with stable `429 RATE_LIMIT_EXCEEDED` responses; the
  production edge policy remains documented in
  `docs/deployment/rate-limiting-decision.md`.
- [ ] Production edge rate limiting enforced. Cloudflare/WAF or equivalent
  provider evidence must still be recorded before production promotion.

## Storage

- [x] Buckets private. Phase 5 local SQL probe verified expected buckets are private on 2026-06-17.
- [x] Signed URLs short-lived.
- [x] MIME type validated.
- [x] File size validated.
- [x] Storage keys immutable.
- [x] Downloads logged where required.
- [x] Malware-scanning decision documented. OPEN-001 records that production uploads still require a scanner or explicit risk acceptance.

## Audit

- [x] Audit table append-only. Phase 5 local SQL probe verified the immutability trigger is enabled on 2026-06-17.
- [x] Sensitive operations logged.
- [x] Policy changes logged.
- [x] Attendance corrections logged.
- [x] Physical-file movements logged.
- [x] Audit viewer restricted.

## Deployment

- [ ] Staging tested.
- [x] Dependency scan passed.
- [x] Secret scan passed.
- [x] Backend injection and abuse pattern scan passed.
- [x] Public API documentation exposure is disabled for hosted environments by
  default. Keep `ENABLE_API_DOCS=false` for staging and production unless a
  release owner intentionally enables it for a short debugging window.
- [x] API security headers are emitted by FastAPI, including nosniff, deny
  framing, no-referrer, restrictive permissions policy, COOP and default-deny
  CSP for API responses.
- [ ] Backups enabled. Hosted database and Storage backup requirements are
  documented in `docs/deployment/backup-restore-runbook.md`; dashboard/sync
  evidence still requires human setup.
- [x] Restore tested.
- [ ] Monitoring enabled. Minimum signals and alert thresholds are documented in
  `docs/deployment/monitoring-alerting-runbook.md`; provider setup still
  requires human setup.
- [x] Error logs redact sensitive values.
