# CI/CD Release Gate

Required before production promotion:

- Ruff passes.
- MyPy passes.
- Backend pytest passes.
- Frontend type-check, lint, and production build pass.
- Supabase migration reset passes.
- Phase 5 SQL security probe passes.
- Secret scan passes.
- Backend dependency audit passes.
- Backend production images build.
- Docker production exposure review passes.
- Frontend container and Caddy runtime validation pass.
- Backup exists.
- Restore test passes.
- Human approval is recorded.

## Current Local Evidence

- Ruff passed locally on 2026-06-18.
- MyPy passed locally on 2026-06-18.
- Backend pytest passed locally on 2026-06-18 (`213 passed`).
- `uv run --group dev pip-audit` passed locally on 2026-06-18 (`No known vulnerabilities found`).
- `npx supabase db reset` passed locally on 2026-06-18.
- `supabase/tests/phase2_documents_archive_physical_rpc.sql` passed locally on 2026-06-18.
- `supabase/tests/phase3_employee_operations_rpc.sql` passed locally on 2026-06-18.
- `supabase/tests/phase5_security_release_gate.sql` passed locally on 2026-06-18.
- `.\scripts\phase5_secret_scan.ps1` passed locally on 2026-06-18.
- `docker compose build api worker scheduler` passed locally on 2026-06-18.
- Backend Docker restart validation passed locally on 2026-06-18.
- Docker Scout critical/high scan passed locally on 2026-06-18 for
  `iems-erp-api:latest`, `iems-erp-worker:latest`, `iems-erp-scheduler:latest`
  and `redis:7-alpine`.
- Docker Scout critical/high scan passed locally on 2026-06-18 for the custom
  source-built Caddy image (`iems-erp-caddy`) after replacing the vulnerable
  official Caddy runtime image.
- Docker auth runtime validation passed locally on 2026-06-20. FastAPI accepts
  the configured local issuer aliases while still verifying JWT signature,
  audience and expiry; the API container fetches JWKS through
  `host.docker.internal`; authenticated `/api/v1/me` and
  `/api/v1/director/overview` pass through Caddy.
- Human browser smoke test on 2026-06-20 confirmed Docker sign-in/sign-out and
  protected app access are working as intended.
- Local app-schema backup and restore proof passed locally on 2026-06-18.

## Still Required Before Production

- Managed Supabase backup plan and retention evidence.
- Supabase Storage backup/export procedure evidence.
- Staging deployment validation using
  `docs/deployment/staging-validation-runbook.md`.
- Monitoring and alerting provider configuration.
- OPEN-045 frontend follow-up for the admin tab and notification wiring, unless
  the release owner explicitly accepts it as a pilot limitation.
- Human release approval.
