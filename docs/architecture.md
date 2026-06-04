# Architecture

## Runtime Components

```text
Next.js web app
      ↓
FastAPI API
      ↓
Supabase Auth + PostgreSQL + Storage
      ↓
Redis + Celery worker
```

## Responsibility Boundaries

### Next.js

- Auth callback UI
- Employee Dashboard
- Director Dashboard
- Attendance, tasks, calendar, projects, folders, archives and approvals screens
- Calls FastAPI for sensitive business operations
- May query safe read-only Supabase endpoints where RLS already protects data

### FastAPI

- Verifies Supabase JWTs
- Resolves current ERP employee
- Evaluates RBAC and ABAC
- Performs transactional writes with the Supabase service role
- Creates signed URLs
- Creates Celery jobs
- Writes audit events
- Requires override reasons for Super User actions

### Supabase PostgreSQL

- Source of truth for structured ERP data
- Baseline RLS safety
- Normalized relational constraints
- Director Dashboard views
- Audit trail

### Supabase Storage

- Stores actual file bytes
- Uses private buckets only
- Uses immutable object keys
- Does not replace the relational folder tree

### Celery + Redis

- ZIP archive generation
- Manifest generation
- QR and barcode label PDFs
- Document index PDFs
- Preview generation
- Duplicate checks
- Notifications and reminders
