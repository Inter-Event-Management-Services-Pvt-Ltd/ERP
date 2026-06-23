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
