# Codex Instructions — Backend Owner for IEMS ERP

Follow `AGENTS.md` first.

# Scope

Codex owns backend, database, infrastructure foundation, and backend security:

```text
apps/api/**
supabase/**
backend tests
Redis and Celery integration
database validation
RLS policies
RBAC and ABAC enforcement
audit logging
signed URL generation
archive jobs
backend CI checks
```

Do not modify:

```text
apps/web/**
frontend layouts
frontend components
visual design
motion design
Google Stitch output
```

If the backend requires a frontend change, update the API contract and record the integration requirement in `docs/07_OPEN_ITEMS.md` for Claude.

# Required Backend Workflow

1. Read the active phase checklist.
2. Inspect existing migrations before changing the schema.
3. Avoid destructive rewrites.
4. Use type-safe request and response models.
5. Validate authorization inside FastAPI before any sensitive write.
6. Add tests for successful paths, unauthorized paths, and invalid-state paths.
7. Run linting, type checks, tests, and migration validation.
8. Update `CHANGELOG.md`.
9. Update the checklist with `[x]` only when verified.
10. Report unverified items clearly.

# Non-Negotiable Backend Security

- no secrets in source files
- no service-role key in frontend files
- no public document buckets
- no direct browser writes for sensitive operations
- no authorization based only on UI state
- no hard-coded bypasses
- default-deny authorization
- mandatory audit events
- mandatory Super User override reasons
- transactional physical-file checkout
- exact manifest tracking for offline exports
- rate-limit and abuse-protection decisions documented before production

# Docker Ownership

Codex owns backend Dockerization and integration:

- production and development Compose files
- API image
- worker image
- scheduler image
- Redis service
- Caddy service
- health checks
- internal networks
- container-security review

Read:

```text
docs/17_DOCKERIZATION.md
docs/checklists/DOCKERIZATION.md
```
