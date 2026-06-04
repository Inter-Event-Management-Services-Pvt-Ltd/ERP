# Phase 1 Checklist — Application Scaffolding and Authentication

## Backend

- [x] Create FastAPI project.
- [x] Add configuration module.
- [x] Add Supabase JWT verification.
- [x] Add current employee resolution.
- [x] Add centralized RBAC service.
- [x] Add centralized ABAC service.
- [x] Add Super User override handler.
- [x] Add audit-event writer.
- [x] Add health endpoint.
- [x] Add structured logging.

## Frontend

- [ ] Create Next.js project.
- [ ] Add Tailwind CSS.
- [ ] Add shadcn/ui.
- [ ] Add login screen.
- [ ] Add auth callback.
- [ ] Add protected route handling.
- [ ] Add basic navigation shell.
- [ ] Add Director route guard.

## Auth

- [ ] Configure Google sign-in.
- [x] Restrict access to approved IEMS accounts.
- [x] Test unapproved account rejection.
- [x] Test disabled employee rejection.
- [x] Test Director role assignment.
- [x] Test Super User status.

## Security Gate

- [x] Confirm service-role key is never exposed to Next.js client bundle.
- [x] Confirm frontend does not make authorization decisions.
- [x] Confirm sensitive writes go through FastAPI.
- [x] Confirm unauthorized API tests exist.
- [x] Confirm audit record exists for override use.

## Exit Criteria

- [ ] Employee can sign in.
- [ ] Unauthorized user cannot sign in.
- [ ] Director receives the Director Dashboard route.
- [x] CI runs lint and basic tests.


## Agent Ownership

### Codex

- [x] Scaffold FastAPI only.
- [x] Implement auth verification and backend authorization only.
- [x] Update API contract where required.

### Claude

- [ ] Scaffold Next.js only.
- [ ] Build login and protected-shell UI.
- [ ] Follow `FRONTEND_CLAUDE.md`.
- [ ] Use either Claude Design or Google Stitch for reviewed UI exploration.

## Dockerization

- [ ] Development Compose stack runs.
- [x] API Dockerfile builds.
- [ ] Web Dockerfile builds.
- [ ] Redis container passes health check.
- [ ] Caddy routing is documented.
