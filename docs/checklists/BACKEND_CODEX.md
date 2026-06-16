# Codex Backend Checklist

## Ownership

- [x] Only backend-owned files were modified for Phase 0/Phase 1 backend work; `apps/web/**` was not modified.
- [x] Any frontend requirement was recorded for Claude. Phase 2 endpoint wiring is recorded in OPEN-024.
- [x] API contract updated where required.

## Database

- [x] Migration added where needed. Phase 4 admin/policy/audit migration covers audited admin writes, Director metric views, policy changes and archive editor updates.
- [x] Migration is reversible or rollback is documented. Rollback path for local validation is `npx supabase db reset` from the migration set.
- [x] Constraints preserved.
- [x] Index impact reviewed.
- [x] Local reset passes for latest Phase 4 changes.
- [x] Seed impact reviewed.

## Authorization

- [x] JWT verified.
- [x] Employee account resolved.
- [x] RBAC checked.
- [x] ABAC checked.
- [x] Default deny preserved at the database layer for exposed tables without explicit RLS policies.
- [x] Super User override reason handled where relevant.
- [x] Audit event written.

## Storage

- [x] Bucket remains private.
- [x] Signed URL expiry appropriate.
- [x] File type validated.
- [x] File size validated.
- [x] Immutable storage key used.
- [x] Object-storage error path handled.

## Workflows

- [x] Transaction boundaries reviewed.
- [x] Race conditions reviewed.
- [x] Invalid-state tests added.
- [x] Unauthorized tests added.
- [x] Success tests added.

## Validation

- [x] Ruff passes.
- [x] MyPy passes.
- [x] Pytest passes.
- [x] Migration reset passes for latest Phase 4 changes.
- [x] Backend security implications documented.
