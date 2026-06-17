# CI/CD Release Gate

Required before production promotion:

- Ruff passes.
- MyPy passes.
- Backend pytest passes.
- Frontend type-check, lint, and production build pass.
- Supabase migration reset passes.
- Phase 5 SQL security probe passes.
- Secret scan passes.
- Backend production images build.
- Docker production exposure review passes.
- Frontend container and Caddy runtime validation pass.
- Backup exists.
- Restore test passes.
- Human approval is recorded.

## Current Local Evidence

- Backend pytest passed locally on 2026-06-17.
- `npx supabase db reset` passed locally on 2026-06-17.
- `supabase/tests/phase5_security_release_gate.sql` passed locally on 2026-06-17.
- `.\scripts\phase5_secret_scan.ps1` passed locally on 2026-06-17.
- `docker compose build api worker scheduler` passed locally on 2026-06-17.
- Local app-schema restore proof passed locally on 2026-06-17.

## Still Required Before Production

- Claude frontend build/container/Caddy validation.
- Managed Supabase backup plan and retention evidence.
- Staging deployment validation.
- Dependency/image vulnerability review.
- Human release approval.
