# Codex Backend Checklist

## Ownership

- [x] Only backend-owned files were modified for Phase 0 validation; `apps/web/**` was not modified.
- [x] Any frontend requirement was recorded for Claude. No frontend requirement was identified.
- [x] API contract updated where required. No API contract change was required.

## Database

- [x] Migration added where needed. Pre-staging foundation migrations were hardened in place; no append-only staging migration was required.
- [x] Migration is reversible or rollback is documented. Rollback path for Phase 0 local validation is `npx supabase db reset` from the edited migration set.
- [x] Constraints preserved.
- [x] Index impact reviewed.
- [x] Local reset passes.
- [x] Seed impact reviewed.

## Authorization

- [ ] JWT verified.
- [ ] Employee account resolved.
- [ ] RBAC checked.
- [ ] ABAC checked.
- [x] Default deny preserved at the database layer for exposed tables without explicit RLS policies.
- [ ] Super User override reason handled where relevant.
- [ ] Audit event written.

## Storage

- [x] Bucket remains private.
- [ ] Signed URL expiry appropriate.
- [ ] File type validated.
- [ ] File size validated.
- [ ] Immutable storage key used.
- [ ] Object-storage error path handled.

## Workflows

- [ ] Transaction boundaries reviewed.
- [ ] Race conditions reviewed.
- [x] Invalid-state tests added.
- [ ] Unauthorized tests added.
- [ ] Success tests added.

## Validation

- [ ] Ruff passes.
- [ ] MyPy passes.
- [ ] Pytest passes.
- [x] Migration reset passes.
- [x] Backend security implications documented.
