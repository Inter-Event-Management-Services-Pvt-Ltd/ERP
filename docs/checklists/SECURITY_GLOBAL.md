# Global Security Checklist

## Secrets

- [x] No secrets committed to Git.
- [x] `.env` is ignored.
- [x] Supabase service-role key is server-only.
- [ ] JWT secret is server-only.
- [ ] Redis credentials are server-only.
- [ ] Production and staging credentials differ.
- [ ] Key rotation procedure exists.

## Authentication

- [ ] Google sign-in configured.
- [ ] Domain and employee allowlist enforced.
- [ ] Disabled employees cannot sign in.
- [ ] Director account tested.
- [ ] Session expiry tested.
- [ ] Logout tested.

## Authorization

- [x] Default-deny ABAC.
- [ ] Server-side checks for writes.
- [x] RLS enabled on exposed tables. Phase 5 local SQL probe passed after clean reset on 2026-06-17.
- [x] Super User override requires reason.
- [x] Override logged.
- [x] Unauthorized tests exist.

## Storage

- [x] Buckets private. Phase 5 local SQL probe verified expected buckets are private on 2026-06-17.
- [ ] Signed URLs short-lived.
- [ ] MIME type validated.
- [ ] File size validated.
- [ ] Storage keys immutable.
- [ ] Downloads logged where required.
- [ ] Malware-scanning decision documented.

## Audit

- [x] Audit table append-only. Phase 5 local SQL probe verified the immutability trigger is enabled on 2026-06-17.
- [ ] Sensitive operations logged.
- [ ] Policy changes logged.
- [ ] Attendance corrections logged.
- [ ] Physical-file movements logged.
- [ ] Audit viewer restricted.

## Deployment

- [ ] Staging tested.
- [ ] Dependency scan passed.
- [ ] Secret scan passed.
- [ ] Backups enabled.
- [ ] Restore tested.
- [ ] Monitoring enabled.
- [ ] Error logs redact sensitive values.
