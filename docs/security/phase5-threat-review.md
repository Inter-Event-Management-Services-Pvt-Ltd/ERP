# Phase 5 Threat Review

Date: 2026-06-20

Scope: IEMS ERP local release candidate covering FastAPI, Next.js, Caddy,
Redis/Celery, local Supabase validation, private Supabase Storage buckets and
production Compose topology.

This review records the local release-candidate threat model. It does not
replace staging validation, managed Supabase backup verification, monitoring
configuration or human production approval.

## Trust Boundaries

- Browser to Caddy over HTTPS.
- Caddy to Next.js web container.
- Caddy to FastAPI API container for `/api/*`.
- FastAPI to Supabase REST/Auth/Storage using server-side credentials.
- FastAPI to Redis/Celery for archive export jobs.
- Celery worker to Supabase Storage for generated archives.
- Human operators to Docker host, GitHub and Supabase dashboards.

## Primary Assets

- Supabase service-role key and JWT/Auth signing configuration.
- Employee identity, roles, permissions and Super User status.
- Project, client, task, approval, attendance and archive records.
- Private document objects and generated archive ZIP files.
- Physical archive QR tokens and movement history.
- Immutable audit events and Super User override records.
- Backup artifacts and restore credentials.

## Reviewed Abuse Paths

| Threat | Existing Control | Remaining Work |
|---|---|---|
| Browser receives service-role key | Web env limited to `NEXT_PUBLIC_*`; secret scan and bundle scan evidence recorded | Re-run scans in staging/prod builds |
| User reads another employee's notification | `/v1/me/notifications` and mark-read route scope by current `employee_id` server-side | Claude browser validation against live endpoint |
| User marks another employee's notification read | PATCH filters by both notification id and current `employee_id`; empty update returns `NOT_FOUND` | None known |
| Direct document access bypasses FastAPI | Buckets private; downloads use short-lived signed URLs; frontend must not upload directly to Supabase | Malware scanning decision remains open in OPEN-001 |
| Project/task/archive IDOR | FastAPI RBAC/ABAC tests and project membership checks | Staging smoke tests with multiple roles |
| Super User silently bypasses controls | Override reason and immutable audit events required | Human review of Super User assignment before production |
| Audit trail tampering | Audit immutability SQL probe passed locally | Managed Supabase backup retention still required |
| Public Redis/API exposure | Production Compose exposes only Caddy; Redis on internal backend network | Human production Compose review remains required |
| Vulnerable container image | Docker Scout critical/high scans pass for app images, Redis and custom Caddy | Re-scan before every production promotion |
| Auth token issuer mismatch in Docker | FastAPI separates REST URL, accepted issuers and JWKS URL; signature, audience and expiry remain verified | Use managed Supabase issuer/JWKS in staging/prod |
| SQL injection | Backend app code uses Supabase PostgREST/RPC calls and typed schemas instead of string-built SQL; backend security scan fails raw SQL string execution patterns | Re-run scan before release |
| Command injection or dynamic code execution | Backend security scan fails shell execution and `eval`/`exec`/`compile` patterns in production app code | Any future exception requires explicit security review |
| Unsafe deserialization | Backend security scan fails `pickle`, `marshal` and unsafe `yaml.load` patterns | Any future parser change requires explicit security review |
| SSRF through arbitrary outbound HTTP | Direct HTTP calls are limited to approved Supabase helper paths; backend routes do not fetch user-supplied URLs | Any new outbound integration needs allowlist and timeout review |
| Brute force or request flooding | Caddy/security headers in place; no app-level limiter yet | Rate-limiting decision documented; provider/proxy enforcement required before production |
| Backup cannot restore after incident | Local app-schema backup/restore proof passed | Managed Supabase database and Storage backup procedures still required |

## Release Decision

The local release candidate has no known critical backend authorization bypass
from this review. Production is still blocked until:

- staging is provisioned and validated,
- production/staging credentials are distinct,
- managed Supabase database backup retention is configured,
- Supabase Storage backup/export procedure is selected,
- monitoring and alerting are configured,
- rate limiting is enforced at the production edge,
- OPEN-001 malware scanning decision is accepted or implemented,
- OPEN-045 admin-tab loading issue is resolved or accepted,
- human release approval is recorded.
