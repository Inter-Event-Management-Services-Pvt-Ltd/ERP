# Open Items and Decisions

Use this document for unresolved questions.

## Format

```text
ID:
Date:
Category:
Severity:
Question or issue:
Why it matters:
Options:
Recommended next action:
Owner:
Status:
```

## Initial Open Items

### OPEN-001 — Storage malware scanning

```text
Category: Security
Severity: Medium
Question: Which malware-scanning mechanism should be used before production?
Options:
- ClamAV worker
- external scanning service
- controlled rollout with file-type restrictions before scanner integration
Status: Open
```

### OPEN-002 — Supabase production plan

```text
Category: Operations
Severity: Medium
Question: Which managed Supabase plan and backup-retention settings are required?
Status: Open
```

### OPEN-003 — Pilot employee list

```text
Category: Rollout
Severity: Low
Question: Which employees should be included in the first pilot?
Status: Open
```

### OPEN-004 — Local Supabase Vector logging container on Windows

```text
Date: 2026-06-04
Category: Local Development
Severity: Low
Question or issue: `supabase_vector_iems-erp` restarts and `npx supabase db reset` exits nonzero after migrations/seeds apply because the local Vector route `POST:/vector/ListVectorBuckets` returns 404.
Why it matters: Core local database, Auth, REST, Storage, and Studio validation pass, but local log/vector bucket setup is incomplete on this Windows Docker Desktop setup.
Options:
- Enable Docker Desktop TCP daemon exposure for local Supabase analytics/log routing.
- Leave disabled for now and use direct container logs during Phase 0/1 development.
Recommended next action: Decide whether local analytics/log routing is required before Phase 1 integration testing.
Owner: Codex
Status: Open
```

### OPEN-016 — Project type / status / priority lookup endpoints missing

```text
Date: 2026-06-05
Category: API Contract
Severity: Medium
Affected module: apps/web/src/app/projects/page.tsx — CreateProjectDialog
Question or issue: POST /v1/projects requires project_type_id, project_status_id, and priority_level_id
  (database UUIDs), but no lookup endpoints exist to retrieve available options.
Why it matters: The Create Project form currently uses static placeholder IDs that will not match
  real database records. Project creation will fail until real IDs are supplied.
Options:
- Add GET /v1/project-types, GET /v1/project-statuses, GET /v1/priority-levels endpoints.
- Embed lookup arrays in GET /v1/projects response or a metadata endpoint.
Recommended next action: Codex adds lookup endpoints; Claude wires them into the Create Project form.
Owner: Codex
Status: Open
```

### OPEN-017 — GET /v1/projects/{id}/members endpoint missing

```text
Date: 2026-06-05
Category: API Contract
Severity: Medium
Affected module: apps/web/src/app/projects/[id]/page.tsx — ProjectMembersPanel
Question or issue: POST and DELETE /v1/projects/{project_id}/members/{employee_id} exist, but there
  is no GET endpoint to list current project members.
Why it matters: The members panel on the project detail page shows an empty list until this endpoint
  is available.
Options:
- Add GET /v1/projects/{project_id}/members returning ProjectMember[].
- Embed members array in GET /v1/projects/{project_id} response.
Recommended next action: Codex adds the GET endpoint; Claude wires it into useProject or a new hook.
Owner: Codex
Status: Open
```

### OPEN-018 — Document/file endpoints deferred to Phase 3

```text
Date: 2026-06-05
Category: Scope
Severity: Low
Affected module: apps/web/src/app/projects/[id]/documents/page.tsx
Question or issue: POST /v1/folders/{folder_id}/documents, GET /v1/documents/{document_id},
  and related file-upload endpoints are not in Phase 2 scope.
Why it matters: The folder explorer shows folder tree but cannot list or upload documents yet.
Recommended next action: Wire document list and upload in Phase 3 when those endpoints ship.
Owner: Codex / Claude
Status: Open
```

### OPEN-014 - Client visibility scope for Phase 2 API

```text
Date: 2026-06-05
Category: Security / API Contract
Severity: Medium
Affected module: apps/api/app/services/clients_projects.py
Question or issue: `GET /v1/clients` currently returns active clients to any user with `project.view` or `project.manage`; unlike projects, clients do not yet have a membership table for row-level scoping.
Why it matters: This is acceptable for an internal ERP if client names are company-wide, but it may be too broad if client visibility should follow project membership.
Reproduction: Authenticate as an approved employee with `project.view` and call `GET /v1/clients`.
Options:
- Keep client directory visible to all approved project users.
- Add a client visibility policy based on active project membership.
- Add explicit client membership/ownership if needed later.
Recommended next action: Human/Codex confirm the desired client visibility rule before production.
Owner: Human / Codex
Status: Open
```

### OPEN-015 - Folder hierarchy import preservation

```text
Date: 2026-06-05
Category: Phase 2 Documents
Severity: Low
Affected module: Phase 2 folder/document import workflow
Question or issue: The Phase 2 checklist item "Preserve existing folder hierarchy during import" is not implemented in CODEX-PHASE2-001.
Why it matters: The clients/projects API creates the default folder tree, but import-specific hierarchy preservation belongs with CODEX-PHASE2-002 folders/documents.
Reproduction: No import endpoint exists yet.
Options:
- Implement hierarchy-preserving import as part of CODEX-PHASE2-002.
- Defer import workflow if MVP only needs manual folder/document creation first.
Recommended next action: Include this explicitly in CODEX-PHASE2-002 planning.
Owner: Codex
Status: Open
```

### OPEN-008 — Frontend local env uses a secret Supabase key

```text
Date: 2026-06-05
Category: Security
Severity: Critical
Question or issue: `apps/web/.env.local` set `NEXT_PUBLIC_SUPABASE_ANON_KEY` to the service-role key (sb_secret_...) instead of the publishable key.
Resolution: `apps/web/.env.local` updated to use the Supabase publishable key (sb_publishable_...).
  The service-role key remains only in `apps/api/.env`.
Owner: Claude
Status: Closed (2026-06-05)
```

### OPEN-009 — Google OAuth client secret is present in tracked Supabase config

```text
Date: 2026-06-05
Category: Security
Severity: Critical
Question or issue: `supabase/config.toml` previously contained a Google OAuth client secret under `[auth.external.google]`.
Current state: config.toml now uses `env(SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID)` and `env(SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_SECRET)`. The hardcoded secret is gone from tracked config.
Resolution: Google OAuth secret rotated in Google Cloud Console. New credentials stored in
  gitignored `supabase/.env` as SUPABASE_AUTH_EXTERNAL_GOOGLE_CLIENT_ID / SECRET.
Owner: Human
Status: Closed (2026-06-05)
```

### OPEN-010 — Frontend type-check fails on Vitest globals

```text
Date: 2026-06-05
Category: Frontend Tooling
Severity: Medium
Question or issue: `npm run type-check` failed because Vitest globals (test, expect, describe, vi) were unknown to TypeScript.
Resolution: Added `apps/web/src/vitest.d.ts` with `/// <reference types="vitest/globals" />`.
  `npm run type-check` now passes clean.
Owner: Claude
Status: Closed (2026-06-05)
```

### OPEN-011 — Frontend lint script is interactive/deprecated

```text
Date: 2026-06-05
Category: Frontend Tooling
Severity: Medium
Question or issue: `npm run lint` ran `next lint` which is deprecated in Next.js 15 and prompted interactively without an ESLint config.
Resolution: Added `apps/web/.eslintrc.json` (extends next/core-web-vitals), added `eslint` and
  `eslint-config-next` to devDependencies. Updated lint script to `eslint src/ --ext .ts,.tsx,.js,.jsx`.
  `npm run lint` now runs non-interactively.
Owner: Claude
Status: Closed (2026-06-05)
```

### OPEN-012 — Frontend build warns about Supabase client in Edge runtime

```text
Date: 2026-06-05
Category: Frontend Auth
Severity: Medium
Question or issue: Build warned that @supabase/supabase-js uses Node.js APIs (process.version) unsupported in Edge runtime, because middleware ran in Edge by default.
Resolution: Added `export const runtime = 'nodejs'` to `apps/web/src/middleware.ts` to opt middleware
  into Node.js runtime. Build now completes with no Edge runtime warnings.
Owner: Claude
Status: Closed (2026-06-05)
```

### OPEN-013 — Frontend shell includes Phase 2+ route placeholders

```text
Date: 2026-06-05
Category: Scope
Severity: Low
Question or issue: The frontend shell contains routes for projects, documents, archive, attendance, approvals, Director subpages, and admin screens before Phase 2+ backend APIs exist.
Resolution: Verified all Phase 2+ routes are pure placeholder pages (SkeletonScreen only, no API calls,
  no invented backend contracts). Acceptable as navigation stubs until Phase 2 begins.
Owner: Claude
Status: Closed (2026-06-05)
```

### OPEN-005 — Supabase CLI telemetry rename warning on Windows

```text
Date: 2026-06-04
Category: Local Development
Severity: Low
Question or issue: One `npx supabase db query` metadata check failed while renaming `C:\Users\prath\.supabase\telemetry.json.tmp...` to `telemetry.json`.
Why it matters: Validation continued through direct local Postgres `psql`, but the CLI telemetry path may intermittently fail in this Windows profile.
Options:
- Fix local file permissions for `C:\Users\prath\.supabase`.
- Prefer `docker exec ... psql` for deterministic local SQL validation.
Recommended next action: Use the documented `docker exec` Phase 0 validation command until the local Supabase CLI telemetry file permissions are fixed.
Owner: Codex
Status: Open
```

### OPEN-007 — GitHub `main` branch protection unavailable on current plan

```text
Date: 2026-06-04
Category: Operations
Severity: Medium
Question or issue: GitHub rejected branch protection and repository rulesets for the private ERP repository with "Upgrade to GitHub Pro or make this repository public to enable this feature."
Why it matters: PR review discipline is documented, but GitHub cannot currently enforce protected-branch rules on `main`.
Options:
- Upgrade the GitHub plan and enable branch protection/rulesets for `main`.
- Keep the repository private and rely on manual PR-only discipline until the plan is upgraded.
Recommended next action: Upgrade the GitHub plan before staging or production development depends on protected-branch enforcement.
Owner: Human
Status: Open
```

### OPEN-006 — Frontend API shape refinements from Claude shell plan

```text
Date: 2026-06-04
Category: API Contract
Severity: Medium
Question or issue: Claude's tracked frontend plan identifies API fields that still need exact response-shape confirmation before frontend business workflows start.
Why it matters: The frontend shell is paused. `GET /v1/me` and `GET /v1/me/permissions` are now documented, but later screens still need stable shapes for notification unread counts, project archive readiness, export ZIP status, and Director overview metrics.
Options:
- Defer detailed business response shapes until Phase 2/4 endpoint implementation.
Recommended next action: During Phase 2/4, update `docs/api-contract.md` before Claude wires business views.
Owner: Codex
Status: Open
```
