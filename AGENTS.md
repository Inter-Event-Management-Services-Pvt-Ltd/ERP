# IEMS ERP — Agent Operating Instructions

This repository is the source of truth for the IEMS Internal ERP.

## Active Architecture

Use:

```text
Frontend:
Next.js + TypeScript + Tailwind CSS + shadcn/ui

Backend:
FastAPI

Database:
Managed Supabase PostgreSQL

Development database:
Local Supabase through Docker

Authentication:
Supabase Auth with Google sign-in

Storage:
Supabase Storage private buckets

Authorization:
Supabase RLS + FastAPI RBAC/ABAC

Background jobs:
Redis + Celery

Search:
PostgreSQL full-text search + pg_trgm
```

Do **not** introduce Convex, Firebase, MongoDB, Prisma, microservices, Kubernetes, Kafka, or a second authentication provider unless an approved Architecture Decision Record explicitly changes the plan.

# Agent Ownership

## Claude — Frontend Owner

Claude owns:

```text
apps/web/**
frontend documentation
UI route implementation
component library
responsive layouts
accessibility
motion design
visual QA
Claude Design or Google Stitch design workflow
```

Claude must read:

```text
CLAUDE.md
docs/13_AGENT_OWNERSHIP_MATRIX.md
docs/14_FRONTEND_DESIGN_SYSTEM.md
docs/15_FRONTEND_SECURITY_MOTION.md
docs/checklists/FRONTEND_CLAUDE.md
```

## Codex — Backend Owner

Codex owns:

```text
apps/api/**
supabase/**
backend tests
database migrations
RLS
RBAC and ABAC
audit logs
Celery workers
Redis integration
deployment scripts
backend CI checks
```

Codex must read:

```text
CODEX.md
docs/13_AGENT_OWNERSHIP_MATRIX.md
docs/checklists/BACKEND_CODEX.md
```

## Cross-Boundary Rule

Neither agent may modify the other agent's owned area without documenting the need in:

```text
docs/07_OPEN_ITEMS.md
```

and receiving human approval.

Shared contracts are documented in:

```text
docs/api-contract.md
docs/02_ARCHITECTURE.md
docs/03_DATABASE_DESIGN.md
```

If an API contract change is needed:

```text
Codex updates backend implementation and contract
→ Claude updates frontend integration
```

# Non-Negotiable Rules

1. Read `docs/00_START_HERE.md` before changing code.
2. Work phase-by-phase using `docs/checklists/`.
3. Do not skip security checkpoints.
4. Never expose the Supabase service-role key to the browser.
5. All file-storage buckets remain private.
6. All sensitive writes go through FastAPI.
7. All protected operations require server-side authorization.
8. Super User overrides require a meaningful reason and an immutable audit event.
9. Never weaken database constraints to make application code easier.
10. Do not hard-delete business records that matter for audit history.
11. Migrations are append-only after they are applied to staging.
12. Every completed phase must satisfy its Definition of Done and security gate.
13. Add or update tests with every feature.
14. Keep documentation synchronized with implementation.
15. Stop and document blockers rather than silently bypassing a control.
16. Claude must not implement backend business logic.
17. Codex must not build or redesign frontend screens.

## Required Workflow

For each task:

```text
Read current phase checklist
→ Inspect relevant contracts
→ Implement smallest coherent change
→ Add or update tests
→ Run validation
→ Update checklist
→ Update changelog
→ Report changed files, tests run, and remaining risks
```

# Dockerization Rule

Dockerization is required.

Codex owns:

```text
compose.yaml
compose.dev.yaml
apps/api/Dockerfile
apps/api/.dockerignore
Redis
Celery containers
Caddy integration
container security review
```

Claude owns:

```text
apps/web/Dockerfile
apps/web/.dockerignore
Next.js standalone output
frontend container validation
```

Both agents must follow:

```text
docs/17_DOCKERIZATION.md
docs/checklists/DOCKERIZATION.md
```

# MCP and Skill Setup

Read:

```text
docs/18_MCP_AND_SKILLS_SETUP.md
```

Use project-scoped skills only.

Codex MCP:
- local Supabase MCP by default
- staging read-only only when needed
- never production

Claude MCP:
- Playwright MCP for frontend QA
- Stitch MCP optional later
