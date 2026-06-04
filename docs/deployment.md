# Deployment and Operations

## Managed Services

```text
Supabase managed:
- PostgreSQL
- Auth
- Storage
```

## Deploy Separately

```text
Next.js frontend
FastAPI API
Celery worker
Celery scheduler
Redis
```

## Recommended Environments

```text
local
staging
production
```

Do not develop directly against production.

## Backups

- Enable Supabase database backups appropriate to the selected plan.
- Schedule separate Storage object backups.
- Keep an encrypted off-site copy.
- Test restoration regularly.
- Export database schema migrations to version control.
- Include Storage policies and bucket configuration in migrations.

## Monitoring

Track:

```text
API uptime
Worker failures
Redis availability
Database connection failures
Storage upload errors
Archive export failures
Failed sign-ins
RLS authorization errors
Physical-file overdue count
```

## Security Checklist

- Keep all Storage buckets private.
- Never expose the Supabase service-role key to the browser.
- Use signed URLs with short expiry.
- Restrict Google Workspace login to approved IEMS employees.
- Log sensitive actions.
- Require meaningful override reasons.
- Use staging before production.
