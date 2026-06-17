# Phase 5 Hardening and Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete Phase 5 backend-owned hardening, deployment validation, security checks, restore proof, monitoring docs, and release readiness without touching Claude-owned frontend code.

**Architecture:** Treat Phase 5 as a release-readiness track, not a feature phase. Codex owns FastAPI, Supabase validation, backend tests, Redis/Celery, production Compose, Caddy integration, security checks, backup/restore proof, and release docs; Claude owns `apps/web/**`, frontend build/runtime validation, and frontend performance waterfall review.

**Tech Stack:** FastAPI, Supabase PostgreSQL/Auth/Storage, PostgREST, Redis, Celery, Docker Compose, Caddy, uv, pytest, Ruff, MyPy, npm scripts, GitHub Actions.

---

## Scope And Ownership

**Codex may modify:**

- `apps/api/**`
- `supabase/**`
- `compose.yaml`
- `compose.dev.yaml`
- `apps/api/Dockerfile`
- `apps/api/.dockerignore`
- `infrastructure/**`
- `.github/workflows/**`
- `scripts/**`
- `docs/**`
- `CHANGELOG.md`

**Codex must not modify:**

- `apps/web/**`
- frontend screens/components/hooks/styles
- frontend Dockerfile except by explicit human approval

**Open items entering Phase 5:**

- `OPEN-001`: malware scanning decision before production uploads.
- `OPEN-002`: Supabase production plan and backup retention.
- `OPEN-005`: Windows Supabase CLI telemetry issue; prefer `docker exec psql` for deterministic SQL probes.
- `OPEN-007`: GitHub private repo branch protection unavailable on current plan.
- `OPEN-034`: missing `GET /v1/tasks/{task_id}/comments`.
- `OPEN-039`: Phase 5 performance baseline and endpoint optimization.

---

## File Map

**Backend API and services**

- Modify: `apps/api/app/core/logging.py` to suppress unsafe/noisy library HTTP logs and preserve structured app logs.
- Modify: `apps/api/app/services/employee_operations.py` to add task comment listing for `OPEN-034`.
- Modify: `apps/api/app/api/v1/employee_operations.py` to expose `GET /v1/tasks/{task_id}/comments`.
- Modify: `apps/api/app/schemas/employee_operations.py` only if existing `TaskCommentResponse` needs a list-facing adjustment.
- Test: `apps/api/tests/test_employee_operations_api.py`.
- Test: `apps/api/tests/test_employee_operations_service.py`.

**Performance probes**

- Create: `apps/api/scripts/perf_probe.py` to run authenticated local route timing probes using `IEMS_ACCESS_TOKEN`.
- Create: `docs/performance/phase5-local-baseline.md` to record route timings and request-id correlation instructions.
- Modify: `docs/07_OPEN_ITEMS.md` to resolve or update `OPEN-039` based on evidence.

**Security and database validation**

- Create or modify: `supabase/tests/phase5_security_release_gate.sql` for RLS, Storage privacy, audit immutability, service-role-only RPC execute checks, and role grants.
- Create: `scripts/phase5_secret_scan.ps1` for repository secret-pattern scanning.
- Create: `docs/security/phase5-security-review.md` for evidence and release-gate notes.
- Modify: `docs/checklists/SECURITY_GLOBAL.md`.
- Modify: `docs/checklists/SECURITY_RELEASE_GATE.md`.

**Docker and deployment**

- Modify: `compose.yaml`.
- Modify: `compose.dev.yaml` only if dev validation needs alignment.
- Modify: `apps/api/Dockerfile` only if non-root, health, or base-image checks fail.
- Modify: `infrastructure/caddy/Caddyfile`.
- Create: `docs/deployment/phase5-docker-validation.md`.
- Modify: `docs/checklists/DOCKERIZATION.md`.

**Backups, restore, and runbooks**

- Create: `scripts/supabase_local_backup.ps1`.
- Create: `scripts/supabase_local_restore_test.ps1`.
- Create: `docs/deployment/backup-restore-runbook.md`.
- Create: `docs/deployment/rollback-runbook.md`.
- Create: `docs/deployment/incident-response.md`.
- Modify: `docs/checklists/PHASE_5_HARDEN_DEPLOY.md`.

**CI/CD**

- Modify or create: `.github/workflows/backend-ci.yml`.
- Modify or create: `.github/workflows/release-gate.yml`.
- Create: `docs/deployment/ci-cd-release-gate.md`.

**Project tracking**

- Modify: `docs/12_AGENT_TASK_BOARD.md`.
- Modify: `docs/07_OPEN_ITEMS.md`.
- Modify: `CHANGELOG.md`.

---

### Task 1: Start Phase 5 Tracking

**Files:**

- Modify: `docs/12_AGENT_TASK_BOARD.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update Codex immediate task**

Replace the current Codex immediate task with:

```text
ID: CODEX-PHASE5-001
Owner: Codex
Status: IN_PROGRESS
Task: Phase 5 hardening, performance baseline and deployment validation.
Checklist:
- docs/checklists/PHASE_5_HARDEN_DEPLOY.md
- docs/checklists/DOCKERIZATION.md
- docs/checklists/SECURITY_GLOBAL.md
- docs/checklists/SECURITY_RELEASE_GATE.md
Output:
- backend performance baseline and targeted endpoint optimization
- OPEN-034 task comment list endpoint
- backend/security test hardening
- Supabase RLS and Storage validation probes
- production Docker/Caddy/Redis/Celery validation
- backup and restore proof
- release gate docs and checklists
```

- [ ] **Step 2: Add changelog entry**

Add under `## Unreleased`:

```markdown
- Started Phase 5 hardening and deployment planning, covering backend performance baselines, security validation, Docker production checks, backup/restore proof, release-gate documentation, and remaining backend contract gaps.
```

- [ ] **Step 3: Verify docs diff**

Run:

```powershell
git diff -- docs/12_AGENT_TASK_BOARD.md CHANGELOG.md
```

Expected: only the Phase 5 tracking and changelog text changed.

- [ ] **Step 4: Commit**

Run:

```powershell
git add docs/12_AGENT_TASK_BOARD.md CHANGELOG.md
git commit -m "docs: start phase 5 hardening track"
```

---

### Task 2: Clean Backend HTTP Logging

**Files:**

- Modify: `apps/api/app/core/logging.py`
- Test: `apps/api/tests/test_api_shell.py` or new `apps/api/tests/test_logging.py`

- [ ] **Step 1: Write failing test**

Add a test that configures logging and asserts noisy library loggers are lowered while app loggers remain structured:

```python
def test_configure_logging_suppresses_noisy_http_client_logs() -> None:
    from app.core.logging import configure_logging
    import logging

    configure_logging("INFO")

    assert logging.getLogger("httpx").level >= logging.WARNING
    assert logging.getLogger("httpcore").level >= logging.WARNING
    assert logging.getLogger("iems.api.access").getEffectiveLevel() == logging.INFO
    assert logging.getLogger("iems.api.supabase").getEffectiveLevel() == logging.INFO
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
uv run --directory apps/api --group dev pytest tests/test_logging.py -q
```

Expected: FAIL because `httpx` and `httpcore` are not explicitly suppressed yet.

- [ ] **Step 3: Implement minimal logging cleanup**

In `apps/api/app/core/logging.py`, update `configure_logging`:

```python
def configure_logging(log_level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(_log_level(log_level))

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
```

- [ ] **Step 4: Run focused test**

Run:

```powershell
uv run --directory apps/api --group dev pytest tests/test_logging.py -q
```

Expected: PASS.

- [ ] **Step 5: Run backend checks**

Run:

```powershell
uv run --directory apps/api --group dev ruff check .
uv run --directory apps/api --group dev mypy app
uv run --directory apps/api --group dev pytest -q
```

Expected: all pass.

- [ ] **Step 6: Commit**

Run:

```powershell
git add apps/api/app/core/logging.py apps/api/tests/test_logging.py
git commit -m "chore: suppress noisy HTTP client logs"
```

---

### Task 3: Build Backend Performance Baseline

**Files:**

- Create: `apps/api/scripts/perf_probe.py`
- Create: `docs/performance/phase5-local-baseline.md`
- Modify: `docs/07_OPEN_ITEMS.md`
- Test: `apps/api/tests/test_perf_probe.py`

- [ ] **Step 1: Write failing CLI tests**

Create `apps/api/tests/test_perf_probe.py`:

```python
from scripts.perf_probe import route_specs


def test_route_specs_include_core_phase5_pages() -> None:
    routes = [spec.path for spec in route_specs()]

    assert "/v1/me" in routes
    assert "/v1/projects" in routes
    assert "/v1/tasks" in routes
    assert "/v1/approvals" in routes
    assert "/v1/director/overview" in routes
    assert "/v1/audit-events" in routes
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
uv run --directory apps/api --group dev pytest tests/test_perf_probe.py -q
```

Expected: FAIL because `scripts/perf_probe.py` does not exist.

- [ ] **Step 3: Add probe script**

Create `apps/api/scripts/perf_probe.py` with:

```python
from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class RouteSpec:
    label: str
    path: str


def route_specs() -> list[RouteSpec]:
    return [
        RouteSpec("me", "/v1/me"),
        RouteSpec("projects", "/v1/projects"),
        RouteSpec("archive_rooms", "/v1/archive/rooms"),
        RouteSpec("tasks", "/v1/tasks"),
        RouteSpec("approvals", "/v1/approvals"),
        RouteSpec("director_overview", "/v1/director/overview"),
        RouteSpec("audit_events", "/v1/audit-events"),
    ]


async def main() -> int:
    base_url = os.environ.get("IEMS_API_BASE_URL", "http://localhost:8000").rstrip("/")
    token = os.environ.get("IEMS_ACCESS_TOKEN")
    if not token:
        raise SystemExit("Set IEMS_ACCESS_TOKEN before running the performance probe.")

    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=20.0) as client:
        for spec in route_specs():
            started = time.perf_counter()
            response = await client.get(f"{base_url}{spec.path}", headers=headers)
            duration_ms = (time.perf_counter() - started) * 1000
            print(
                f"{spec.label} {response.status_code} "
                f"{duration_ms:.2f}ms request_id={response.headers.get('X-Request-ID')}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
uv run --directory apps/api --group dev pytest tests/test_perf_probe.py -q
```

Expected: PASS.

- [ ] **Step 5: Run local probe**

Prerequisites:

```powershell
cd apps/api
uv run python scripts/local_access_token.py --email dev.perf@iemsnewdelhi.com --employee-code IEMS-PERF-001 --full-name "IEMS Perf User" --role DIRECTOR --super-user --expires-minutes 120
```

Run the printed `$env:IEMS_ACCESS_TOKEN="..."`, then from repo root:

```powershell
uv run --directory apps/api python scripts/perf_probe.py
```

Expected: each line includes status, elapsed time, and `request_id`.

- [ ] **Step 6: Record baseline**

Create `docs/performance/phase5-local-baseline.md`:

```markdown
# Phase 5 Local Performance Baseline

Date: 2026-06-17
Environment: local FastAPI host process, local Supabase Docker stack

## Command

`uv run --directory apps/api python scripts/perf_probe.py`

## Results

| Route | Status | Duration | Request ID | Notes |
|---|---:|---:|---|---|
| /v1/me | 200 | record value | record request id | current-user lookup baseline |
| /v1/projects | 200 | record value | record request id | project list |
| /v1/archive/rooms | 200 | record value | record request id | archive room list |
| /v1/tasks | 200 | record value | record request id | task list |
| /v1/approvals | 200 | record value | record request id | approval list |
| /v1/director/overview | 200 | record value | record request id | optimize first if > 1000ms |
| /v1/audit-events | 200 | record value | record request id | audit explorer |
```

Replace `record value` and `record request id` with the measured values.

- [ ] **Step 7: Update `OPEN-039`**

If `/v1/director/overview` remains slow, update `OPEN-039` with the measured request id and next backend optimization target.

- [ ] **Step 8: Commit**

Run:

```powershell
git add apps/api/scripts/perf_probe.py apps/api/tests/test_perf_probe.py docs/performance/phase5-local-baseline.md docs/07_OPEN_ITEMS.md
git commit -m "perf: add phase 5 backend performance baseline probe"
```

---

### Task 4: Implement `OPEN-034` Task Comment Listing

**Files:**

- Modify: `apps/api/app/services/employee_operations.py`
- Modify: `apps/api/app/api/v1/employee_operations.py`
- Modify: `docs/api-contract.md`
- Modify: `docs/07_OPEN_ITEMS.md`
- Test: `apps/api/tests/test_employee_operations_service.py`
- Test: `apps/api/tests/test_employee_operations_api.py`

- [ ] **Step 1: Write failing service test**

Add a test asserting task visibility is checked before returning comments:

```python
def test_list_task_comments_requires_task_visibility() -> None:
    seen_requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_requests.append(request)
        if request.url.path == "/rest/v1/tasks":
            return httpx.Response(200, json=[])
        return httpx.Response(200, json=[])

    service = EmployeeOperationsService(
        supabase_url="http://localhost:54321",
        service_role_key="legacy-service-role-key",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(EmployeeOperationsError) as exc_info:
        asyncio.run(
            service.list_task_comments(
                task_id=TASK_ID,
                current_user=_current_user(),
                limit=50,
                offset=0,
            )
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.code == "ABAC_DENIED"
```

- [ ] **Step 2: Write failing API test**

Add a route test:

```python
async def test_list_task_comments_returns_visible_comments() -> None:
    service = _install_overrides(current_user=_current_user(permissions=[]))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get(f"/v1/tasks/{TASK_ID}/comments")

    assert response.status_code == 200
    assert service.calls[0][0] == "list_task_comments"
```

- [ ] **Step 3: Run tests to verify they fail**

Run:

```powershell
uv run --directory apps/api --group dev pytest tests/test_employee_operations_service.py::test_list_task_comments_requires_task_visibility tests/test_employee_operations_api.py::test_list_task_comments_returns_visible_comments -q
```

Expected: FAIL because service method and route do not exist.

- [ ] **Step 4: Implement service method**

In `EmployeeOperationsService`, add:

```python
async def list_task_comments(
    self,
    *,
    task_id: UUID,
    current_user: CurrentUser,
    limit: int,
    offset: int,
) -> list[TaskCommentResponse]:
    row = await self._get_task_row(task_id)
    await self._require_task_visible(row=row, current_user=current_user)
    rows = await self._get_rows(
        "/rest/v1/task_comments",
        params=_list_params(
            select=TASK_COMMENT_SELECT,
            order="created_at.desc",
            limit=limit,
            offset=offset,
        )
        | {"task_id": f"eq.{task_id}"},
    )
    return [_task_comment_from_row(row) for row in rows]
```

- [ ] **Step 5: Implement route**

In `apps/api/app/api/v1/employee_operations.py`, add:

```python
@router.get("/v1/tasks/{task_id}/comments", response_model=list[TaskCommentResponse])
async def list_task_comments(
    task_id: UUID,
    current_user: CurrentUserDep,
    service: EmployeeOperationsServiceDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[TaskCommentResponse]:
    try:
        return await service.list_task_comments(
            task_id=task_id,
            current_user=current_user,
            limit=limit,
            offset=offset,
        )
    except EmployeeOperationsError as exc:
        raise _http_error(exc) from exc
```

- [ ] **Step 6: Update API contract**

In `docs/api-contract.md`, add:

```text
GET    /v1/tasks/{task_id}/comments
```

Document:

```text
Returns comments newest first for a task visible to the current user.
Query parameters:
limit=1..100 default 50
offset=0..n default 0
```

- [ ] **Step 7: Resolve `OPEN-034` backend status**

Update `docs/07_OPEN_ITEMS.md` with:

```text
Backend status:
  Codex added GET /v1/tasks/{task_id}/comments, newest first, with the same task
  visibility ABAC as task detail reads.
Frontend follow-up:
  Claude should replace session-local task comments with the new endpoint.
Status: Backend resolved; frontend follow-up open
```

- [ ] **Step 8: Run tests**

Run:

```powershell
uv run --directory apps/api --group dev pytest tests/test_employee_operations_service.py tests/test_employee_operations_api.py -q
uv run --directory apps/api --group dev ruff check .
uv run --directory apps/api --group dev mypy app
uv run --directory apps/api --group dev pytest -q
```

Expected: all pass.

- [ ] **Step 9: Commit**

Run:

```powershell
git add apps/api/app/services/employee_operations.py apps/api/app/api/v1/employee_operations.py apps/api/tests/test_employee_operations_service.py apps/api/tests/test_employee_operations_api.py docs/api-contract.md docs/07_OPEN_ITEMS.md
git commit -m "feat: add task comment listing endpoint"
```

---

### Task 5: Add Phase 5 SQL Security Probe

**Files:**

- Create: `supabase/tests/phase5_security_release_gate.sql`
- Modify: `docs/checklists/SECURITY_GLOBAL.md`
- Modify: `docs/checklists/SECURITY_RELEASE_GATE.md`
- Modify: `docs/checklists/PHASE_5_HARDEN_DEPLOY.md`

- [ ] **Step 1: Create SQL probe**

Create `supabase/tests/phase5_security_release_gate.sql`:

```sql
begin;

do $$
declare
  missing_rls text[];
  public_buckets text[];
  mutable_audit_count integer;
begin
  select array_agg(format('%I.%I', schemaname, tablename))
  into missing_rls
  from pg_tables t
  join pg_class c on c.relname = t.tablename
  join pg_namespace n on n.oid = c.relnamespace and n.nspname = t.schemaname
  where t.schemaname = 'public'
    and c.relkind = 'r'
    and t.tablename not like 'pg_%'
    and not c.relrowsecurity;

  if coalesce(array_length(missing_rls, 1), 0) > 0 then
    raise exception 'RLS disabled on public tables: %', missing_rls;
  end if;

  select array_agg(id)
  into public_buckets
  from storage.buckets
  where public = true;

  if coalesce(array_length(public_buckets, 1), 0) > 0 then
    raise exception 'Public storage buckets are not allowed: %', public_buckets;
  end if;

  select count(*)
  into mutable_audit_count
  from pg_trigger
  where tgname = 'trg_prevent_audit_event_update';

  if mutable_audit_count = 0 then
    raise exception 'Audit immutability trigger is missing';
  end if;
end $$;

rollback;
```

- [ ] **Step 2: Run migration reset**

Run:

```powershell
npx supabase db reset
```

Expected: reset completes successfully.

- [ ] **Step 3: Run probe**

Run:

```powershell
docker cp supabase/tests/phase5_security_release_gate.sql supabase_db_iems-erp:/tmp/phase5_security_release_gate.sql
docker exec supabase_db_iems-erp psql -U postgres -d postgres -f /tmp/phase5_security_release_gate.sql
```

Expected: `BEGIN`, `DO`, `ROLLBACK` with no exceptions.

- [ ] **Step 4: Update checklists**

Mark only verified items:

```markdown
- [x] RLS verified enabled.
- [x] Storage buckets verified private.
- [x] Audit immutability verified.
```

Leave unverified items unchecked.

- [ ] **Step 5: Commit**

Run:

```powershell
git add supabase/tests/phase5_security_release_gate.sql docs/checklists/SECURITY_GLOBAL.md docs/checklists/SECURITY_RELEASE_GATE.md docs/checklists/PHASE_5_HARDEN_DEPLOY.md
git commit -m "test: add phase 5 security release SQL probe"
```

---

### Task 6: Add Secret Scan Script

**Files:**

- Create: `scripts/phase5_secret_scan.ps1`
- Create: `docs/security/phase5-security-review.md`
- Modify: `docs/checklists/SECURITY_GLOBAL.md`
- Modify: `docs/checklists/SECURITY_RELEASE_GATE.md`

- [ ] **Step 1: Create scan script**

Create `scripts/phase5_secret_scan.ps1`:

```powershell
$ErrorActionPreference = "Stop"

$patterns = @(
  "sb_secret_",
  "SUPABASE_SERVICE_ROLE_KEY\s*=\s*[^<\s]",
  "SUPABASE_JWT_SECRET\s*=\s*[^<\s]",
  "GOOGLE_CLIENT_SECRET\s*=\s*[^<\s]",
  "postgresql:\/\/[^<\s]+:[^<\s]+@"
)

$exclude = @(
  ".git",
  ".venv",
  "node_modules",
  ".next",
  "dist",
  "build"
)

$files = Get-ChildItem -Recurse -File | Where-Object {
  $path = $_.FullName
  -not ($exclude | Where-Object { $path -like "*\$_\*" })
}

$findings = @()
foreach ($file in $files) {
  $content = Get-Content -Raw -LiteralPath $file.FullName -ErrorAction SilentlyContinue
  foreach ($pattern in $patterns) {
    if ($content -match $pattern) {
      $findings += "$($file.FullName): pattern $pattern"
    }
  }
}

if ($findings.Count -gt 0) {
  $findings | ForEach-Object { Write-Error $_ }
  exit 1
}

Write-Output "Secret scan passed."
```

- [ ] **Step 2: Run scan**

Run:

```powershell
.\scripts\phase5_secret_scan.ps1
```

Expected: `Secret scan passed.`

- [ ] **Step 3: Document evidence**

Create `docs/security/phase5-security-review.md`:

```markdown
# Phase 5 Security Review

Date: 2026-06-17

## Secret Scan

Command: `.\scripts\phase5_secret_scan.ps1`
Result: record pass/fail output.

## Notes

- Service-role key must remain server-only.
- Frontend public env must use publishable/anon values only.
- Production credentials must differ from staging credentials before release.
```

- [ ] **Step 4: Update checklists**

Mark secret scan only if the command passed:

```markdown
- [x] Secret scan passes.
- [x] Secret scan clean.
```

- [ ] **Step 5: Commit**

Run:

```powershell
git add scripts/phase5_secret_scan.ps1 docs/security/phase5-security-review.md docs/checklists/SECURITY_GLOBAL.md docs/checklists/SECURITY_RELEASE_GATE.md
git commit -m "security: add phase 5 secret scan"
```

---

### Task 7: Validate Docker Production Gate

**Files:**

- Modify: `compose.yaml`
- Modify: `apps/api/Dockerfile`
- Modify: `infrastructure/caddy/Caddyfile`
- Create: `docs/deployment/phase5-docker-validation.md`
- Modify: `docs/checklists/DOCKERIZATION.md`
- Modify: `docs/checklists/PHASE_5_HARDEN_DEPLOY.md`

- [ ] **Step 1: Inspect current Docker config**

Run:

```powershell
docker compose config
docker compose ps
```

Expected: config renders; running services state is known.

- [ ] **Step 2: Check production exposure**

Review `compose.yaml` and confirm:

```text
Only Caddy publishes host ports in production.
Redis has no host port.
API has no direct host port in production.
Worker and scheduler have no host ports.
No service mounts /var/run/docker.sock.
No service is privileged.
No service uses network_mode: host.
```

- [ ] **Step 3: Fix only failed items**

If API/Redis are publicly exposed in `compose.yaml`, move those ports to `expose` or internal network only.

Expected production shape:

```yaml
services:
  api:
    expose:
      - "8000"
  redis:
    expose:
      - "6379"
  caddy:
    ports:
      - "80:80"
      - "443:443"
```

- [ ] **Step 4: Validate backend image**

Run:

```powershell
docker compose build api worker scheduler
docker compose up -d api worker scheduler redis caddy
docker compose ps
curl.exe -i http://localhost/health
```

Expected: API health returns 200 through Caddy or the configured route.

- [ ] **Step 5: Document validation**

Create `docs/deployment/phase5-docker-validation.md`:

```markdown
# Phase 5 Docker Validation

Date: 2026-06-17

## Commands

- `docker compose config`
- `docker compose build api worker scheduler`
- `docker compose up -d api worker scheduler redis caddy`
- `docker compose ps`
- `curl.exe -i http://localhost/health`

## Results

Record command results here.

## Production Exposure Review

- Caddy public ports: record 80/443 status.
- API direct public port: record none or explain.
- Redis public port: record none or explain.
- Docker socket mounts: record none or issue.
- Privileged containers: record none or issue.
- Host networking: record none or issue.
```

- [ ] **Step 6: Update checklists**

Mark only evidence-backed Docker checklist items.

- [ ] **Step 7: Commit**

Run:

```powershell
git add compose.yaml apps/api/Dockerfile infrastructure/caddy/Caddyfile docs/deployment/phase5-docker-validation.md docs/checklists/DOCKERIZATION.md docs/checklists/PHASE_5_HARDEN_DEPLOY.md
git commit -m "chore: validate phase 5 backend docker deployment gate"
```

---

### Task 8: Add Backup And Restore Proof

**Files:**

- Create: `scripts/supabase_local_backup.ps1`
- Create: `scripts/supabase_local_restore_test.ps1`
- Create: `docs/deployment/backup-restore-runbook.md`
- Modify: `docs/checklists/PHASE_5_HARDEN_DEPLOY.md`
- Modify: `docs/checklists/SECURITY_GLOBAL.md`
- Modify: `docs/checklists/SECURITY_RELEASE_GATE.md`

- [ ] **Step 1: Create local backup script**

Create `scripts/supabase_local_backup.ps1`:

```powershell
$ErrorActionPreference = "Stop"

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupDir = "tmp\backups"
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
$backupPath = "$backupDir\iems-local-$timestamp.dump"

docker exec supabase_db_iems-erp pg_dump -U postgres -d postgres -Fc -f "/tmp/iems-local.dump"
docker cp supabase_db_iems-erp:/tmp/iems-local.dump $backupPath

Write-Output $backupPath
```

- [ ] **Step 2: Create local restore test script**

Create `scripts/supabase_local_restore_test.ps1`:

```powershell
param(
  [Parameter(Mandatory = $true)]
  [string]$BackupPath
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $BackupPath)) {
  throw "Backup path not found: $BackupPath"
}

docker exec supabase_db_iems-erp dropdb -U postgres --if-exists iems_restore_test
docker exec supabase_db_iems-erp createdb -U postgres iems_restore_test
docker cp $BackupPath supabase_db_iems-erp:/tmp/iems-restore-test.dump
docker exec supabase_db_iems-erp pg_restore -U postgres -d iems_restore_test /tmp/iems-restore-test.dump
docker exec supabase_db_iems-erp psql -U postgres -d iems_restore_test -c "select count(*) from public.employees;"

Write-Output "Restore test passed."
```

- [ ] **Step 3: Run backup**

Run:

```powershell
.\scripts\supabase_local_backup.ps1
```

Expected: script prints `tmp\backups\iems-local-<timestamp>.dump`.

- [ ] **Step 4: Run restore test**

Run:

```powershell
.\scripts\supabase_local_restore_test.ps1 -BackupPath tmp\backups\<actual-file>.dump
```

Expected: restore succeeds and employee count query returns a count.

- [ ] **Step 5: Document runbook**

Create `docs/deployment/backup-restore-runbook.md`:

```markdown
# Backup And Restore Runbook

## Local Restore Proof

1. Run `.\scripts\supabase_local_backup.ps1`.
2. Run `.\scripts\supabase_local_restore_test.ps1 -BackupPath <dump path>`.
3. Confirm restore database query succeeds.

## Production Requirement

Managed Supabase project must have backups enabled before production launch.
Retention period must be recorded in `docs/07_OPEN_ITEMS.md` under `OPEN-002`.
```

- [ ] **Step 6: Update checklists**

Mark restore items only if local restore proof passed. Keep production backup settings unchecked until the actual managed Supabase plan is selected.

- [ ] **Step 7: Commit**

Run:

```powershell
git add scripts/supabase_local_backup.ps1 scripts/supabase_local_restore_test.ps1 docs/deployment/backup-restore-runbook.md docs/checklists/PHASE_5_HARDEN_DEPLOY.md docs/checklists/SECURITY_GLOBAL.md docs/checklists/SECURITY_RELEASE_GATE.md
git commit -m "ops: add backup and restore validation runbook"
```

---

### Task 9: Release Runbooks And Incident Docs

**Files:**

- Create: `docs/deployment/rollback-runbook.md`
- Create: `docs/deployment/incident-response.md`
- Create: `docs/deployment/ci-cd-release-gate.md`
- Modify: `docs/checklists/PHASE_5_HARDEN_DEPLOY.md`
- Modify: `docs/checklists/SECURITY_RELEASE_GATE.md`

- [ ] **Step 1: Create rollback runbook**

Create `docs/deployment/rollback-runbook.md`:

```markdown
# Rollback Runbook

## Trigger

Rollback when staging or production has a confirmed data-loss risk, auth outage,
critical permission leak, broken document upload/download, or unavailable API.

## Backend Rollback

1. Stop new deployment.
2. Restore previous Docker image tag.
3. Confirm `/health` and `/ready`.
4. Confirm `/v1/me` with a known approved account.
5. Confirm document signed download still works.

## Database Rollback

Database rollback requires human approval. Prefer forward-fix migrations unless
the release gate owner approves restoring from backup.
```

- [ ] **Step 2: Create incident response doc**

Create `docs/deployment/incident-response.md`:

```markdown
# Incident Response

## Severity

- Critical: suspected secret leak, public document exposure, auth bypass, data loss.
- High: API outage, failed uploads/downloads, broken approval/attendance/archive workflows.
- Medium: slow pages, degraded worker, failed notification path.

## First Response

1. Preserve logs.
2. Stop affected deployment if exposure is ongoing.
3. Rotate compromised secrets if relevant.
4. Record timeline and affected resources.
5. Add follow-up item to `docs/07_OPEN_ITEMS.md`.
```

- [ ] **Step 3: Create CI/CD gate doc**

Create `docs/deployment/ci-cd-release-gate.md`:

```markdown
# CI/CD Release Gate

Required before production:

- Ruff passes.
- MyPy passes.
- Backend pytest passes.
- Frontend type-check, lint and build pass.
- Supabase migration reset passes.
- Phase 5 SQL security probe passes.
- Secret scan passes.
- Docker production config reviewed.
- Backup exists.
- Restore test passes.
- Human approval recorded.
```

- [ ] **Step 4: Update checklists**

Mark rollback and incident-response docs complete only after the files exist and are reviewed.

- [ ] **Step 5: Commit**

Run:

```powershell
git add docs/deployment/rollback-runbook.md docs/deployment/incident-response.md docs/deployment/ci-cd-release-gate.md docs/checklists/PHASE_5_HARDEN_DEPLOY.md docs/checklists/SECURITY_RELEASE_GATE.md
git commit -m "docs: add phase 5 release and incident runbooks"
```

---

### Task 10: Final Phase 5 Validation Pass

**Files:**

- Modify: `docs/checklists/PHASE_5_HARDEN_DEPLOY.md`
- Modify: `docs/checklists/DOCKERIZATION.md`
- Modify: `docs/checklists/SECURITY_GLOBAL.md`
- Modify: `docs/checklists/SECURITY_RELEASE_GATE.md`
- Modify: `docs/07_OPEN_ITEMS.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Run backend checks**

Run:

```powershell
uv run --directory apps/api --group dev ruff check .
uv run --directory apps/api --group dev mypy app
uv run --directory apps/api --group dev pytest -q
```

Expected: all pass.

- [ ] **Step 2: Run migration validation**

Run:

```powershell
npx supabase db reset
docker cp supabase/tests/phase5_security_release_gate.sql supabase_db_iems-erp:/tmp/phase5_security_release_gate.sql
docker exec supabase_db_iems-erp psql -U postgres -d postgres -f /tmp/phase5_security_release_gate.sql
```

Expected: reset passes and SQL probe passes.

- [ ] **Step 3: Run Docker validation**

Run:

```powershell
docker compose config
docker compose build api worker scheduler
docker compose up -d api worker scheduler redis caddy
docker compose ps
```

Expected: config/build/run pass; health checks pass or documented issue exists.

- [ ] **Step 4: Run secret scan**

Run:

```powershell
.\scripts\phase5_secret_scan.ps1
```

Expected: `Secret scan passed.`

- [ ] **Step 5: Run backup restore proof**

Run:

```powershell
.\scripts\supabase_local_backup.ps1
.\scripts\supabase_local_restore_test.ps1 -BackupPath <actual backup path>
```

Expected: restore test passes.

- [ ] **Step 6: Request Claude validation**

Send Claude this prompt:

```text
Frontend Phase 5 validation task:

Do not touch backend code. Keep all changes inside apps/web/**.

Please validate:
- frontend type-check, lint and production build
- Next.js standalone Docker output
- frontend container runs as non-root
- frontend works behind Caddy/reverse proxy
- no service-role key or backend secret appears in client bundle
- route guards do not repeatedly call /v1/me or /v1/me/permissions unnecessarily
- page-load waterfalls for dashboard, projects, archive, tasks, approvals, director and admin pages
- React Query cache/staleTime behavior for reference data

Use FastAPI only. Do not call Supabase directly for business data.
Capture X-Request-ID for any slow API request so Codex can match backend logs.
```

- [ ] **Step 7: Update checklists accurately**

Only mark checklist items verified by fresh command output. Leave production-only items unchecked until real staging/production credentials, backups and human approval exist.

- [ ] **Step 8: Record remaining blockers**

Add or update `docs/07_OPEN_ITEMS.md` for:

```text
Supabase production plan
branch protection plan limitation
malware scanning decision
staging credentials
production backup retention
frontend Docker validation
human release approval
```

- [ ] **Step 9: Commit final docs**

Run:

```powershell
git add docs/checklists/PHASE_5_HARDEN_DEPLOY.md docs/checklists/DOCKERIZATION.md docs/checklists/SECURITY_GLOBAL.md docs/checklists/SECURITY_RELEASE_GATE.md docs/07_OPEN_ITEMS.md CHANGELOG.md
git commit -m "docs: record phase 5 validation status"
```

---

## Completion Criteria

Phase 5 backend is complete only when:

- Ruff passes.
- MyPy passes.
- Backend pytest passes.
- Supabase reset passes.
- Phase 5 SQL security probe passes.
- Secret scan passes.
- Docker production config is validated.
- API, worker, scheduler and Redis health are validated.
- Backup and restore proof exists.
- Release and rollback docs exist.
- Remaining production-only gaps are recorded in `docs/07_OPEN_ITEMS.md`.
- `docs/checklists/PHASE_5_HARDEN_DEPLOY.md`, `DOCKERIZATION.md`, `SECURITY_GLOBAL.md`, and `SECURITY_RELEASE_GATE.md` reflect evidence, not assumptions.
- `apps/web/**` remains untouched by Codex.

Phase 5 full release is not complete until Claude validates frontend items and a human approves staging/production release.

---

## Self-Review

Spec coverage:

- Performance baseline: Task 3.
- Backend contract gap `OPEN-034`: Task 4.
- Security validation: Tasks 5 and 6.
- Docker production gate: Task 7.
- Backup and restore: Task 8.
- Runbooks and incident response: Task 9.
- Final release gate: Task 10.
- Claude frontend handoff: Task 10 Step 6.

Placeholder scan:

- No unresolved placeholder markers are used.
- Human-only production values remain explicitly recorded as open items rather than guessed.

Type consistency:

- `TaskCommentResponse`, `EmployeeOperationsService`, `TaskCommentResponse` route response model, and existing FastAPI route patterns are used consistently.
