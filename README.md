# IEMS Internal ERP — Starter Kit

This repository starter contains the implementation foundation for the IEMS Internal ERP.

## Included

- Normalized Supabase PostgreSQL migrations
- Reference seed data
- Director bootstrap logic for `director@iemsnewdelhi.com`
- RLS helper functions and baseline policies
- Private Supabase Storage bucket setup
- Director Dashboard SQL views
- ABAC policy matrix
- REST API contract
- UI route and screen map
- Background-job specification
- Deployment and backup checklist
- MVP delivery phases
- Environment-variable template

## Product Scope

The ERP connects:

```text
Employees
  → Attendance and leave
  → Tasks and calendar
  → Clients and event projects
  → Digital folder trees
  → Immutable document versions
  → Offline ZIP exports
  → Printable labels and QR codes
  → Physical records-room files
  → Approvals and audit logs
  → Director Dashboard
```

## Current MVP Stack

```text
Frontend:
Next.js + TypeScript + Tailwind CSS + shadcn/ui

Backend:
FastAPI

Database:
Supabase PostgreSQL

Authentication:
Supabase Auth with Google Workspace login

Authorization:
Supabase RLS + FastAPI ABAC service

Storage:
Supabase Storage private buckets

Background processing:
Celery + Redis

Search:
PostgreSQL full-text search + pg_trgm

Deployment:
Supabase managed initially
Next.js and FastAPI deployed separately
```

## Local Supabase Setup

Install Docker and the Supabase CLI, then run:

```bash
supabase init
supabase start
supabase db reset
```

The migration files are applied in timestamp order. Seed files are configured in `supabase/config.toml`.

## Director Account

The seed creates an employee record for:

```text
director@iemsnewdelhi.com
```

When this email signs in through Supabase Auth, a database trigger links the Auth user to the ERP employee record and assigns:

```text
DIRECTOR
SUPER_USER
```

The Director account receives the dedicated Director Dashboard and broad Super User access. Sensitive overrides must still provide a reason and create an audit event.

## Important Boundary

This starter kit completes the architecture and database implementation foundation. It does **not** include a finished frontend or finished FastAPI application. The backend and frontend can now be scaffolded against a stable schema.


## Agent Ownership

```text
Claude:
Frontend only
Claude Design or Google Stitch design workflow
Next.js UI
Accessibility
Responsive layouts
Motion practices
Frontend security

Codex:
Backend only
FastAPI
PostgreSQL migrations
RLS
RBAC and ABAC
Audit logging
Storage workflows
Redis and Celery
Deployment foundation
```

Read:

```text
docs/13_AGENT_OWNERSHIP_MATRIX.md
docs/14_FRONTEND_DESIGN_SYSTEM.md
docs/15_FRONTEND_SECURITY_MOTION.md
```

## Dockerization

Docker is mandatory.

```bash
supabase start
docker compose -f compose.dev.yaml up --build
```

Production uses:

```bash
docker compose up -d --build
```

Read:

```text
docs/17_DOCKERIZATION.md
docs/checklists/DOCKERIZATION.md
```

## MCP and Skills

This package includes project-scoped MCP templates and custom skills for both agents.

Read:

```text
docs/18_MCP_AND_SKILLS_SETUP.md
```

Validate:

```bash
bash scripts/validate-agent-skills.sh
```
