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
- Local app-schema backup and restore proof passed locally on 2026-06-18.

## Still Required Before Production

- Claude frontend build/container/Caddy validation.
- Managed Supabase backup plan and retention evidence.
- Staging deployment validation.
- Image vulnerability review.
- Human release approval.
