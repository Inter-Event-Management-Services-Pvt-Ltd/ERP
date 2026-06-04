# Start Here

This package is designed for Codex, Claude, and human contributors.

## Current Status

Planning and the initial Supabase PostgreSQL starter package are complete. The SQL migrations have been generated but still need to be executed and validated locally.

## Active Decision

Use:

```text
Managed Supabase PostgreSQL for production
Local Supabase through Docker for development
FastAPI for server-side business logic
Next.js for the frontend
Redis + Celery for background jobs
```

The temporary Convex direction is not active.

## First Action

Complete:

```text
docs/checklists/PHASE_0_FOUNDATION_VALIDATION.md
```

Do not scaffold the complete frontend or backend before the local database package passes validation.

## Work Sequence

```text
Phase 0: Validate database and local environment
Phase 1: Scaffold applications and authentication
Phase 2: Build project documents and physical archive core
Phase 3: Build attendance, leave, tasks and calendar
Phase 4: Build approvals, Director Dashboard and admin tools
Phase 5: Harden security, testing, backups and deployment
Phase 6: Pilot rollout and production release
```
