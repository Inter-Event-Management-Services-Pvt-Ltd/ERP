# Backup And Restore Runbook

These scripts prove local IEMS application-schema backup and restore for the
`public` and `app_private` schemas. They intentionally do not replace managed
Supabase platform backups for Auth, Storage internals, Vault, Realtime, or
point-in-time recovery.

## Local Backup

1. Confirm local Supabase is running.
2. Run `.\scripts\supabase_local_backup.ps1`.
3. Store the printed `tmp\backups\iems-local-<timestamp>.dump` path for the
   restore test.

## Local Restore Proof

1. Run `.\scripts\supabase_local_restore_test.ps1 -BackupPath <dump path>`.
2. Confirm `public.employees` is queryable in the restored
   `iems_restore_test` database.
3. Confirm the script prints `Restore test passed.`

## Latest Local Database Evidence

Date: 2026-06-26

- Backup command: `.\scripts\supabase_local_backup.ps1`
- Backup path: `tmp\backups\iems-local-20260626-132448.dump`
- Restore command:
  `.\scripts\supabase_local_restore_test.ps1 -BackupPath tmp\backups\iems-local-20260626-132448.dump`
- Result: restored into the separate local `iems_restore_test` database,
  restored `public.employees` with `employee_count = 5`, and printed
  `Restore test passed.`
- Restore note: the app-schema dump excludes Supabase-managed Auth internals.
  The restore test creates `auth.users` ID stubs from the source local database
  so `public.user_accounts(id) -> auth.users(id)` can be validated without
  restoring the full Auth schema.

Previous local evidence was recorded on 2026-06-17 with the same restore result.

## Production Requirement

Managed Supabase project backups are preferred before production launch.
Retention period and point-in-time recovery availability must be recorded in
`docs/07_OPEN_ITEMS.md` under `OPEN-002`.

Current production finding on 2026-06-26: the Supabase Free plan does not
include managed project backups or PITR for this project. Until the project is
upgraded, Phase 5 requires a manual logical backup plus restore proof against a
separate test target.

## Hosted Supabase Database Backup

Before pilot or production use:

1. Open the hosted Supabase project dashboard.
2. Confirm the database backup feature available on the selected plan.
3. Record the backup retention period.
4. Record whether point-in-time recovery is available.
5. Run a manual logical backup if the plan does not provide enough retention.
6. Restore into a separate test project or database before trusting the backup.

Do not run destructive restore commands against the live project.

## Supabase Storage Backup

The current low-cost plan is:

1. Keep Supabase Storage buckets private.
2. Sync private Storage objects to the backend machine on a schedule.
3. Wake the personal/offsite server when backup sync is due.
4. Sync the backend-machine copy to the offsite server.
5. Clone or sync the offsite copy to a cloud target such as Google Workspace
   Drive or another object storage provider.
6. Test restore of at least one uploaded document and one generated archive ZIP.

The backend machine and offsite server should connect through a private network
such as Tailscale. If Wake-on-LAN is used, document the target MAC address and
the command on the backend machine, but do not commit private network keys or
cloud credentials.

## Evidence To Record

Record these before closing Phase 5:

- Supabase database backup retention.
- Storage sync schedule.
- Offsite backup target.
- Last successful Storage sync time.
- Last restore test date.
- Person responsible for backup checks.

## Latest Local Storage Evidence

Date: 2026-06-26

- Source: local Docker Supabase Storage volume mounted at `/mnt` inside
  `supabase_storage_iems-erp`.
- Backup command:
  `docker cp supabase_storage_iems-erp:/mnt tmp\storage-backups\iems-storage-local-20260626-132727\mnt`
- Backup path: `tmp\storage-backups\iems-storage-local-20260626-132727`
- Private bucket check: local buckets `document-previews`, `generated-archives`,
  `generated-labels`, `profile-assets`, and `project-documents` all had
  `public = false`.
- Payload result: copied 26 Storage payload files.
- Restore spot-check: copied one generated archive payload to
  `tmp\storage-restore-test\archive.zip` and listed it successfully; sample
  contents included `manifest.json` and `document-index.pdf`.
- Restore spot-check: copied one uploaded document payload to
  `tmp\storage-restore-test\document.pdf`; the file was 20754 bytes and started
  with `%PDF`.

This proves the local Storage export/restore mechanics only. Production still
requires a scheduled hosted Storage sync target and offsite restore evidence.
