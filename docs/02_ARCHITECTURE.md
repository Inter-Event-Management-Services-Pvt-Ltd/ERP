# Active Architecture

## System Diagram

```text
Browser
  ↓
Next.js frontend
  ↓
FastAPI backend
  ├── Supabase JWT verification
  ├── RBAC + ABAC authorization
  ├── business workflows
  ├── signed Storage URLs
  ├── audit logging
  └── Celery job dispatch
        ↓
Managed Supabase
  ├── PostgreSQL
  ├── Auth
  ├── Storage
  └── Realtime where useful
        ↓
Redis + Celery worker
```

## Why PostgreSQL

The ERP is relational and audit-heavy:

```text
Employees
→ projects
→ folder trees
→ document versions
→ export manifests
→ archive locations
→ checkouts
→ approvals
→ audit logs
```

PostgreSQL supports constraints, joins, transactions, recursive folder queries, indexes, and reporting views.

## Responsibility Boundaries

### Browser

- UI only
- Uses anon key where required
- Never receives service-role secrets
- Never decides authorization

### FastAPI

- Sensitive writes
- ABAC policy checks
- audit events
- signed URLs
- ZIP export jobs
- PDF and QR generation
- checkout and return workflows
- approval workflows

### Supabase PostgreSQL

- source of truth for structured records
- constraints
- RLS baseline
- views
- search indexes

### Supabase Storage

- file bytes only
- private buckets only
- immutable object keys

### Redis + Celery

- background generation
- scheduled reminders
- cleanup jobs
