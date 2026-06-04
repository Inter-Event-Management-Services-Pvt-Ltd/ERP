# Architecture Decision Log

## ADR-001 — Use managed Supabase PostgreSQL

**Status:** Active

Use managed Supabase PostgreSQL in production and local Supabase through Docker during development.

Reason:

- relational ERP schema
- constraints and transactions
- Auth integration
- private Storage
- RLS
- faster MVP delivery
- migration path to self-hosting later if required

## ADR-002 — Keep FastAPI

**Status:** Active

Sensitive business workflows remain in FastAPI:

```text
ABAC
archive exports
signed URLs
QR and PDF generation
approvals
physical-file workflows
audit logging
```

## ADR-003 — Do not use Convex as the active backend

**Status:** Active

Convex was considered temporarily but is not the active implementation direction because the ERP benefits from the existing relational PostgreSQL schema and SQL constraints.

## ADR-004 — Use modular monolith

**Status:** Active

Do not split into microservices during MVP.

## ADR-005 — Use Redis and Celery

**Status:** Active

Use background jobs for ZIP exports, labels, previews, reminders, and cleanup.
