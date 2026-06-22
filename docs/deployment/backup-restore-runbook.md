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

## Latest Local Evidence

Date: 2026-06-17

- Backup command: `.\scripts\supabase_local_backup.ps1`
- Restore command: `.\scripts\supabase_local_restore_test.ps1 -BackupPath <dump path>`
- Result: restored `public.employees` with `employee_count = 5`; script printed
  `Restore test passed.`

## Production Requirement

Managed Supabase project backups must be enabled before production launch.
Retention period and point-in-time recovery availability must be recorded in
`docs/07_OPEN_ITEMS.md` under `OPEN-002`.
