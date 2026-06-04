# Phase Roadmap

## Phase 0 — Foundation Validation

Validate generated migrations, local Supabase, seeds, RLS, buckets, bootstrap logic, and developer tooling.

## Phase 1 — App Scaffolding and Authentication

Create Next.js and FastAPI applications, configure auth, establish RBAC/ABAC middleware, and add CI basics.

## Phase 2 — Document and Physical Archive Core

Deliver the primary business workflow:

```text
Create client
→ Create project
→ Create folder tree
→ Upload document
→ Add document version
→ Export ZIP
→ Print QR label
→ Assign physical location
→ Check out and return file
```

## Phase 3 — Employee Operations

Deliver:

```text
attendance
leave
tasks
calendar
notifications
```

## Phase 4 — Management and Director Controls

Deliver:

```text
approvals
Director Dashboard
admin tools
policy management
audit explorer
archive verification
alerts
```

## Phase 5 — Hardening and Deployment

Deliver:

```text
test suite
security validation
backups
restore test
monitoring
staging
CI/CD
production runbook
```

## Phase 6 — Pilot and Rollout

Deliver:

```text
pilot users
feedback
training
data import
production cutover
post-launch verification
```

## Dockerization Requirement

Dockerization is mandatory across implementation phases.

- Phase 1: Create Dockerfiles and development Compose stack.
- Phase 2: Validate worker and archive-job containers.
- Phase 5: Validate production Compose, reverse proxy, TLS, image scanning, restart behaviour, and health checks.

Use:

```text
docs/17_DOCKERIZATION.md
docs/checklists/DOCKERIZATION.md
```
