# Phase 5 Injection and Abuse Protections

Date: 2026-06-22

Scope: backend-owned FastAPI, Supabase REST/RPC usage, worker code and release
security evidence. This review does not replace staging validation, penetration
testing, production rate limiting, backup retention or malware scanning.

## Implemented Controls

| Risk | Control | Evidence |
|---|---|---|
| SQL injection | FastAPI uses Supabase PostgREST filters, typed Pydantic request models and service-role RPC calls instead of string-built SQL in application code. | `.\scripts\phase5_backend_security_scan.ps1` checks backend app code for raw SQL string execution patterns. |
| Command injection | Backend app code does not call shell execution APIs. | `.\scripts\phase5_backend_security_scan.ps1` fails on `subprocess`, `os.system`, `os.popen`, `commands.getoutput` and `shell=True`. |
| Dynamic code execution | Backend app code does not use runtime `eval`, `exec` or `compile`. | `.\scripts\phase5_backend_security_scan.ps1` fails on those patterns. |
| Unsafe deserialization | Backend app code does not use `pickle`, `marshal` or unsafe `yaml.load`. | `.\scripts\phase5_backend_security_scan.ps1` fails on those patterns. |
| SSRF / arbitrary outbound HTTP | Raw HTTP is limited to approved Supabase helper paths. User-supplied URLs are not fetched by backend routes. | The scan fails on direct `httpx`, `requests`, `urllib` or `client.request` calls except the central Supabase helper and archive worker Supabase helper. |
| IDOR | Protected routes resolve the current user and apply RBAC/ABAC or employee ownership checks server-side. | Backend pytest release-gate coverage and Phase 5 threat review. |
| File upload abuse | Uploads go through FastAPI, validate name, MIME type and size, use immutable private Storage keys and return signed URLs only on demand. | Upload tests and storage SQL probes recorded in `docs/security/phase5-security-review.md`. |
| Secret exposure | Service-role keys remain server-only and tracked-file scans block committed secrets. | `.\scripts\phase5_secret_scan.ps1`. |
| Log disclosure | Supabase request logs record timing and query-key metadata without request bodies, auth headers, service-role values or query values. | Backend test coverage recorded in `docs/security/phase5-security-review.md`. |

## Approved Exceptions

- `apps/api/app/core/supabase_http.py` may call `client.request(...)` because it
  is the central Supabase REST helper using configured server-side Supabase
  settings.
- `apps/api/app/workers/archive_exports.py` may call `client.request(...)`
  because the worker builds Supabase REST and Storage paths from configured
  Supabase settings plus server-side bucket/key values, with Storage keys URL
  quoted before use.

New outbound HTTP clients, shell execution, raw SQL construction or dynamic code
execution require an explicit security review before merge.

## Remaining Required Protections

- Production/staging rate limiting must be enforced at the deployed edge or
  provider layer. The decision is documented in
  `docs/deployment/rate-limiting-decision.md`, but local development does not
  prove production throttling.
- Malware scanning for uploaded files remains tracked by OPEN-001 unless the
  release owner accepts the risk for the local-only testing phase.
- Managed Supabase database backup retention and Supabase Storage backup/export
  procedure must be configured before production.
- Monitoring, alerting, incident contact, rollback owner and human release
  approval are still production readiness requirements.
