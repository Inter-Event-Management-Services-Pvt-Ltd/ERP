---
name: iems-supabase-migration-validation
description: Use when validating, fixing, or reviewing IEMS ERP Supabase PostgreSQL migrations, constraints, seeds, views, indexes, RLS policies, or Storage buckets. Codex backend-only skill.
---

# IEMS Supabase Migration Validation

Read:

- `docs/03_DATABASE_DESIGN.md`
- `docs/checklists/PHASE_0_FOUNDATION_VALIDATION.md`
- `docs/checklists/DATABASE_VALIDATION.md`
- `docs/checklists/BACKEND_CODEX.md`

Run:

```bash
supabase start
supabase db reset
supabase status
```

Validate:

- migrations apply cleanly
- seeds execute
- views compile
- RLS policies compile
- private buckets exist
- audit table is append-only
- one root folder per project is enforced
- one open attendance session is enforced
- one open physical checkout is enforced
- approval request target constraint works
- Director bootstrap logic is reviewed

Do not:

- connect MCP to production
- weaken constraints
- disable RLS to make tests pass
- expose secrets
- edit frontend files

Update:

- relevant checklist
- `CHANGELOG.md`
- `docs/07_OPEN_ITEMS.md`
