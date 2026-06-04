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

- [ ] Default-deny ABAC.
- [ ] Server-side checks for writes.
- [x] RLS enabled on exposed tables.
- [x] Super User override requires reason.
- [ ] Override logged.
- [ ] Unauthorized tests exist.

## Storage

- [x] Buckets private.
- [ ] Signed URLs short-lived.
- [ ] MIME type validated.
- [ ] File size validated.
- [ ] Storage keys immutable.
- [ ] Downloads logged where required.
- [ ] Malware-scanning decision documented.

## Audit

- [x] Audit table append-only.
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
