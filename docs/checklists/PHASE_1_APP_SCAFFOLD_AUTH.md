# Phase 1 Checklist — Application Scaffolding and Authentication

## Backend

- [ ] Create FastAPI project.
- [ ] Add configuration module.
- [ ] Add Supabase JWT verification.
- [ ] Add current employee resolution.
- [ ] Add centralized RBAC service.
- [ ] Add centralized ABAC service.
- [ ] Add Super User override handler.
- [ ] Add audit-event writer.
- [ ] Add health endpoint.
- [ ] Add structured logging.

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
- [ ] Restrict access to approved IEMS accounts.
- [ ] Test unapproved account rejection.
- [ ] Test disabled employee rejection.
- [ ] Test Director role assignment.
- [ ] Test Super User status.

## Security Gate

- [ ] Confirm service-role key is never exposed to Next.js client bundle.
- [ ] Confirm frontend does not make authorization decisions.
- [ ] Confirm sensitive writes go through FastAPI.
- [ ] Confirm unauthorized API tests exist.
- [ ] Confirm audit record exists for override use.

## Exit Criteria

- [ ] Employee can sign in.
- [ ] Unauthorized user cannot sign in.
- [ ] Director receives the Director Dashboard route.
- [ ] CI runs lint and basic tests.


## Agent Ownership

### Codex

- [ ] Scaffold FastAPI only.
- [ ] Implement auth verification and backend authorization only.
- [ ] Update API contract where required.

### Claude

- [ ] Scaffold Next.js only.
- [ ] Build login and protected-shell UI.
- [ ] Follow `FRONTEND_CLAUDE.md`.
- [ ] Use either Claude Design or Google Stitch for reviewed UI exploration.

## Dockerization

- [ ] Development Compose stack runs.
- [ ] API Dockerfile builds.
- [ ] Web Dockerfile builds.
- [ ] Redis container passes health check.
- [ ] Caddy routing is documented.
