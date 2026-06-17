# Incident Response

## Severity

- Critical: suspected secret leak, public document exposure, auth bypass, data
  loss, or audit-log integrity failure.
- High: API outage, failed uploads/downloads, broken approval/attendance/archive
  workflows, or worker outage affecting required exports.
- Medium: slow pages, degraded worker throughput, notification failures, or
  isolated user-impacting bugs with a workaround.

## First Response

1. Preserve API, worker, Caddy, Supabase, and deployment logs.
2. Stop the affected deployment if exposure or data loss is ongoing.
3. Rotate compromised credentials if a secret is involved.
4. Capture request IDs, user IDs, affected resources, timestamps, and observed
   error codes.
5. Record a timeline and owner in `docs/07_OPEN_ITEMS.md`.

## Containment

- Disable affected credentials or deployments.
- Temporarily block unsafe routes at Caddy only if the backend cannot be fixed
  quickly.
- Prefer disabling a feature flag or queue worker over weakening RLS,
  constraints, or audit requirements.

## Recovery

1. Apply a tested fix or rollback.
2. Validate `/health`, `/ready`, `/v1/me`, file download, audit explorer, and the
   affected workflow.
3. Confirm no service-role key or private bucket object was exposed to the
   browser.
4. Add regression tests or SQL probes for the failure mode.

## Follow-Up

- Write an incident summary.
- Add or update tests.
- Update runbooks/checklists if the response exposed a gap.
- Keep production-only evidence out of Git.
