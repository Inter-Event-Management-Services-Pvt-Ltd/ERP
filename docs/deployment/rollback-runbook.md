# Rollback Runbook

## Trigger

Rollback when staging or production has a confirmed data-loss risk, auth outage,
critical permission leak, broken document upload/download, unavailable API, or
failed worker path for archive exports.

## Backend Rollback

1. Stop the active deployment rollout.
2. Restore the previous API, worker, scheduler, and Caddy image tags.
3. Confirm `/health` and `/ready` on the backend.
4. Confirm `/v1/me` with a known approved account.
5. Confirm document signed download still works.
6. Confirm Redis-backed worker startup and archive-export queue visibility.

## Database Rollback

Database rollback requires human approval.

Prefer forward-fix migrations unless the release owner confirms data corruption
or an unsafe irreversible migration. If restore is approved:

1. Preserve current logs and database state for incident review.
2. Identify the exact backup and restore point.
3. Restore into a separate database first when possible.
4. Validate core tables, RLS, Auth linkage, document metadata, and audit logs.
5. Promote the restored database only after human approval.

## Post-Rollback Validation

- Backend tests pass against the rolled-back target.
- Supabase migration status is understood.
- `docs/07_OPEN_ITEMS.md` has a follow-up item for the incident.
- Changelog or release notes record the rollback.
