# Phase 5 Security Review

Date: 2026-06-18

## Secret Scan

Command: `.\scripts\phase5_secret_scan.ps1`

Result: `Secret scan passed.`

## Dependency Audit

Command: `uv run --group dev pip-audit` from `apps/api`

Result: `No known vulnerabilities found` on 2026-06-18 after pinning
`cryptography>=48.0.1` and `starlette>=1.3.1`.

## SQL Security Probe

Commands:

- `npx supabase db reset`
- `docker exec supabase_db_iems-erp psql -U postgres -d postgres -f /tmp/phase5_security_release_gate.sql`

Result: passed locally on 2026-06-18.

## Injection and Abuse Pattern Scan

Command: `.\scripts\phase5_backend_security_scan.ps1`

Result: `Backend security pattern scan passed.` on 2026-06-22.

The scan covers backend production Python files under `apps/api/app` and fails on
shell command execution, runtime code execution, unsafe deserialization,
string-built raw SQL execution and direct outbound HTTP outside approved
Supabase helper paths.

## Release-Gate Tests

Command: `uv run --group dev pytest -q` from `apps/api`

Result: `213 passed` on 2026-06-18.

Relevant release-gate coverage:

- ZIP export hierarchy preservation, including empty folder entries.
- Duplicate physical-file checkout rejection through SQL validation.
- ABAC and unauthorized-path tests.
- Super User override reason and audit-context tests.
- Signed download URL flow and expiry configuration tests.
- Upload MIME-type and file-size validation tests.
- No debug or local token-helper routes registered in FastAPI.
- Supabase request timing logs exclude service-role values, auth headers, request bodies and query values.

## Docker Security

Backend Docker validation on 2026-06-18 confirmed:

- API, worker and scheduler run as UID 10001.
- Redis is private on the backend network.
- API health returns 200 after `docker compose restart api worker scheduler redis`.
- Backend container logs remain readable after restart.
- `docker compose config` renders local environment values; do not paste its raw output into PRs, issues or external systems.
- Backend production images were moved from `python:3.12-slim` to
  `python:3.12-alpine` after Docker Scout found critical/high Debian `perl`
  CVEs.
- Docker Scout critical/high scans now pass for `iems-erp-api:latest`,
  `iems-erp-worker:latest`, `iems-erp-scheduler:latest` and `redis:7-alpine`.
- Docker Scout critical/high scan passes for the custom source-built Caddy
  image (`iems-erp-caddy`); OPEN-044 is resolved.
- Docker auth runtime validation on 2026-06-20 keeps JWT signature, audience and
  expiry verification enabled while allowing only the configured local issuer
  aliases. JWKS resolution uses `host.docker.internal` inside the API container
  for local Docker; staging and production should use their managed Supabase
  issuer and JWKS URLs directly.

## Notes

- Supabase service-role keys must remain server-only.
- Frontend public environment variables must use publishable/anon values only.
- Production and staging credentials must differ before release.
- Malware scanning for uploads remains an open production decision.
- Injection and abuse-protection evidence is recorded in
  `docs/security/phase5-injection-abuse-protections.md`.
- Staging deployment, managed Supabase backup retention, Supabase Storage backup
  procedure, monitoring/alerting and human release approval remain required
  before production.
- OPEN-045 tracks the frontend admin-tab and notification-wiring issue.
