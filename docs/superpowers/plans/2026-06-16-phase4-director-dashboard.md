# Phase 4 Director Dashboard Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first Phase 4 backend slice for Director dashboard read APIs and approval visibility.

**Architecture:** Reuse existing Supabase Director views and normalized project/audit tables through a focused FastAPI service. Keep this slice read-only except for documentation updates, preserving approval actions and admin/policy writes for later Phase 4 tasks.

**Tech Stack:** FastAPI, Pydantic, httpx, Supabase PostgREST, pytest, Ruff, MyPy.

---

### Task 1: Director Dashboard API Tests

**Files:**
- Create: `apps/api/tests/test_director_dashboard_api.py`

- [x] Write failing tests for `GET /v1/director/overview`, `/projects`, `/approvals`, `/overdue-tasks`, `/physical-files`, and `/audit-events`.
- [x] Verify they fail because the routes and service dependency do not exist yet.
- [x] Keep route tests focused on auth dependency wiring, permission enforcement and response shape.

### Task 2: Director Dashboard Service Tests

**Files:**
- Create: `apps/api/tests/test_director_dashboard_service.py`

- [x] Write failing tests for service queries against mocked Supabase responses.
- [x] Verify permission denial for non-Director/non-privileged users.
- [x] Verify data-service errors map to stable API error codes.

### Task 3: Schemas, Service and Routes

**Files:**
- Create: `apps/api/app/schemas/director_dashboard.py`
- Create: `apps/api/app/services/director_dashboard.py`
- Create: `apps/api/app/api/v1/director_dashboard.py`
- Modify: `apps/api/app/api/dependencies.py`
- Modify: `apps/api/app/main.py`

- [x] Add typed response models for overview metrics, projects, approvals, overdue tasks, physical files and audit events.
- [x] Add a service that reads existing `director_*_v` views plus `projects` and `audit_events`.
- [x] Add routes under `/v1/director/*`.
- [x] Enforce Director role or Super User route access according to the Phase 4 security gate.

### Task 4: Documentation and Phase Tracking

**Files:**
- Modify: `docs/api-contract.md`
- Modify: `docs/checklists/PHASE_4_MANAGEMENT_DIRECTOR.md`
- Modify: `docs/12_AGENT_TASK_BOARD.md`
- Modify: `docs/07_OPEN_ITEMS.md`
- Modify: `CHANGELOG.md`

- [x] Document exact request/response shapes and permissions.
- [x] Mark only verified checklist items complete.
- [x] Add Claude handoff for frontend Director Dashboard wiring.
- [x] Record remaining backend Phase 4 work as open or task-board items.

### Task 5: Verification

**Commands:**
- `uv run --directory apps/api --group dev pytest tests/test_director_dashboard_api.py tests/test_director_dashboard_service.py -q`
- `uv run --directory apps/api --group dev pytest -q`
- `uv run --directory apps/api --group dev ruff check .`
- `uv run --directory apps/api --group dev mypy app scripts`
- `git diff --check`

- [x] Confirm no `apps/web/**` changes.
- [x] Confirm security checks remain default-deny and service-role-only.
- [x] Report unresolved risks.
