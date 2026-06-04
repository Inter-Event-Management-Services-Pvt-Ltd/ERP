# Phase 0 Checklist — Foundation Validation

## Environment

- [x] Install Docker. Verified with Docker 29.2.1.
- [x] Install Supabase CLI. Verified with `npx supabase` 2.104.0.
- [x] Run `supabase start`.
- [x] Run `supabase db reset`.
- [x] Record and fix every migration error. No migration/reset failures remained after hardening edits.
- [x] Confirm seed execution.
- [x] Confirm local Studio opens. `http://127.0.0.1:54323` returned HTTP 307 to `/project/default`.
- [x] Confirm no secrets are committed. No actual service-role or `sb_secret_` values found in repository files.

## Database

- [x] Verify all tables exist.
- [x] Verify all foreign keys exist.
- [x] Verify all check constraints exist.
- [x] Verify partial unique indexes exist.
- [x] Verify Director bootstrap seed exists.
- [x] Verify views compile.
- [x] Verify RLS policies compile.
- [x] Verify RLS is enabled on every exposed `public` table. Verified `52/52` public tables.
- [x] Verify private Storage buckets exist.

## Security Gate

- [x] Confirm Storage buckets are private.
- [x] Confirm browser write policies are not broadly enabled.
- [x] Confirm exposed tables default deny unless an explicit read policy exists.
- [x] Confirm audit table is append-only.
- [x] Confirm Super User override reason minimum length is enforced.
- [x] Confirm service-role key appears only in server environment documentation.

## Acceptance Tests

- [x] Duplicate employee email is rejected.
- [x] Duplicate active sibling folder name is rejected.
- [x] Duplicate open attendance session is rejected.
- [x] Duplicate open physical-file checkout is rejected.
- [x] Invalid approval target count is rejected.
- [x] Director auth linking logic is reviewed.

## Exit Criteria

- [x] Local database reset succeeds from a clean environment.
- [x] All issues are documented and fixed or entered in `docs/07_OPEN_ITEMS.md`.
