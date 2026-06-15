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
Decision:
  Phase 2 enforces server-side file-name, MIME-type and size restrictions. Full malware
  scanning is deferred to Phase 5 hardening before production release.
Recommended next action:
  Evaluate ClamAV worker versus an external scanning service during Phase 5. Do not allow
  production uploads without either a scanner or a documented risk acceptance.
Status: Decision recorded; implementation remains open before production
```

### OPEN-002 — Supabase production plan

```text
Category: Operations
Severity: Medium
Question: Which managed Supabase plan and backup-retention settings are required?
Status: Open
```

### OPEN-032 - Phase 3 attendance frontend wiring

```text
Date: 2026-06-13
Category: Frontend Integration
Severity: Medium
Question or issue:
  Codex added backend attendance endpoints:
  - POST /v1/attendance/check-in
  - POST /v1/attendance/check-out
  - GET /v1/attendance/me
  - GET /v1/attendance/team
  - PATCH /v1/attendance/sessions/{session_id}
Why it matters:
  Claude needs to wire the attendance page to the documented contract without
  inventing direct Supabase writes or alternate field names.
Frontend follow-up:
  Use FastAPI only. Show RESOURCE_CONFLICT when the user is already checked in,
  INVALID_STATE when checking out without an open session, and validation errors
  when an admin correction is missing correction_reason. Team attendance should
  be shown only to users whose GET /v1/me permissions include attendance.view_all
  or whose isSuperUser flag is true.
Owner: Claude
Status: Open
```

### OPEN-033 - Phase 3 leave, task and calendar frontend wiring

```text
Date: 2026-06-15
Category: Frontend Integration
Severity: Medium
Question or issue:
  Codex added the remaining Phase 3 backend endpoints:
  - GET /v1/leave-types
  - POST /v1/leave-requests
  - GET /v1/leave-requests/me
  - GET /v1/leave-requests/pending
  - POST /v1/leave-requests/{request_id}/approve
  - POST /v1/leave-requests/{request_id}/reject
  - POST /v1/leave-requests/{request_id}/cancel
  - GET /v1/task-statuses
  - GET /v1/tasks
  - POST /v1/tasks
  - GET /v1/tasks/{task_id}
  - PATCH /v1/tasks/{task_id}
  - POST /v1/tasks/{task_id}/assignees
  - POST /v1/tasks/{task_id}/comments
  - POST /v1/tasks/{task_id}/documents
  - GET /v1/calendar/events
  - POST /v1/calendar/events
  - PATCH /v1/calendar/events/{event_id}
  - GET /v1/director/attendance
Why it matters:
  The Phase 3 backend is ready, but the Employee Dashboard exit criterion still
  depends on Claude wiring the frontend screens to the documented FastAPI
  contract without direct Supabase writes.
Frontend follow-up:
  Use docs/api-contract.md exactly. Show INVALID_STATE for non-pending leave
  review/cancel, ABAC_DENIED for inaccessible project-linked task/calendar
  actions, INVALID_REFERENCE for bad lookup IDs, and RESOURCE_CONFLICT for any
  duplicate resource conflicts. Calendar should display source values
  CALENDAR_EVENT, TASK_DEADLINE, LEAVE and PHYSICAL_FILE_RETURN.
Owner: Claude
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

### OPEN-020 — API has no CORS headers; browser cannot reach it from the frontend

```text
Date: 2026-06-05
Category: API / Local Development
Severity: Critical
Affected module: apps/api/app/main.py
Question or issue:
  The FastAPI application has no CORSMiddleware. Browser preflight (OPTIONS) requests from
  http://localhost:3000 to http://localhost:8000 receive a 405 with zero Access-Control-Allow-*
  headers. The browser blocks all cross-origin requests, so every apiFetch() call in the
  frontend fails with "Failed to fetch" before a token is even evaluated.
  Verified: OPTIONS /v1/projects → HTTP 405, no CORS headers.
Why it matters:
  The frontend is completely unusable in the browser. All project, client, me, and folder
  endpoints fail silently as a CORS network error.
Fix required (backend):
  Add FastAPI CORSMiddleware to apps/api/app/main.py:
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],   # extend for staging/prod origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
  For production, replace the wildcard with explicit allowed origins.
Owner: Codex
Resolution:
  Implemented FastAPI CORSMiddleware with explicit configured origins. Local default is
  http://localhost:3000 through CORS_ALLOWED_ORIGINS.
Verification:
  uv run --group dev pytest tests/test_api_shell.py -q
Status: Resolved in CODEX-PHASE2-001 integration fixes
```

### OPEN-019 — Local dev sign-in blocked by email domain restriction

```text
Date: 2026-06-05
Category: Local Development / API Contract
Severity: High
Affected modules:
  apps/api/app/core/auth.py:150  (_validate_email_domain)
  apps/api/app/core/config.py:13 (allowed_email_domain = "iemsnewdelhi.com")
Question or issue:
  The API rejects any JWT whose email is not @iemsnewdelhi.com (403 EMAIL_DOMAIN_NOT_ALLOWED).
  The frontend has only Google OAuth sign-in. There is no email/password form in the current build.
  Combined effect: a developer signing in with a personal Gmail account (e.g. @gmail.com) cannot
  reach any authenticated page or see seed data.
Why it matters:
  Makes local development and frontend QA impossible without an @iemsnewdelhi.com Google Workspace
  account. Seed data (demo employees, projects, clients) is unreachable from the browser.
Options:
  1. Add a dev-only email/password login form to the frontend (gated on NODE_ENV=development or an
     env flag). Developer then runs apps/api/scripts/local_access_token.py to create a Supabase
     Auth user for dev.user@iemsnewdelhi.com. This is the safest option; the form never ships.
  2. Allow Codex to relax ALLOWED_EMAIL_DOMAIN to also accept a configurable local dev domain
     (e.g. set ALLOWED_EMAIL_DOMAIN=gmail.com in apps/api/.env for local testing only, with a
     clear warning in .env.example).
  3. Provision a real @iemsnewdelhi.com Google Workspace account for local dev use.
Recommended next action:
  Codex confirms which option is acceptable and either (a) exposes an ALLOWED_EMAIL_DOMAIN_LOCAL
  override or (b) confirms option 2 is safe for local .env only.
  Claude will add the dev-only login form once there is a path to sign in.
Owner: Codex
Resolution:
  Added ALLOWED_EMAIL_DOMAINS as an explicit comma-separated server-side allowlist. This does
  not bypass employee-account approval: a token email must still match an active employee account.
Verification:
  uv run --group dev pytest tests/test_auth_current_user.py -q
Status: Resolved in CODEX-PHASE2-001 integration fixes
```

### OPEN-021 — Employee search endpoint missing; Add Member UI deferred

```text
Date: 2026-06-06
Category: API Contract
Severity: Medium
Affected module: apps/web/src/components/projects/project-members-panel.tsx
Question or issue:
  POST /v1/projects/{project_id}/members accepts an employee_id UUID, but there is no
  endpoint to search or list employees so the user can pick one.
  The "Add member" button is currently rendered as a disabled non-interactive label.
  Showing a raw UUID text input would be unusable and error-prone in production.
Why it matters:
  Project managers cannot assign new team members from the UI until employee search exists.
  Remove (DELETE) still works because employee_id is already known from the members list.
Endpoint needed from Codex:
  GET /v1/employees?status=ACTIVE&search=<term>
  Response per item: { id, employee_code, full_name, official_email, designation }
Recommended next action:
  Codex adds the search endpoint. Claude wires a typeahead/combobox into the Add Member
  form using that endpoint, replacing the current disabled state.
Owner: Codex
Resolution:
  Added authenticated GET /v1/employees with status, search, limit and offset filters.
  Users with employee.view can filter any employment status. Users with project.manage can
  list assignable ACTIVE or ON_LEAVE employees for project-member assignment.
  Response includes id, employee_code, full_name, official_email, designation and employment_status.
Verification:
  uv run --group dev pytest tests/test_employees_api.py tests/test_employees_service.py -q
Status: Resolved in CODEX-PHASE2-001 integration fixes
```

### OPEN-022 — Director cannot open Create Project UI because frontend ignores Super User flag

```text
Date: 2026-06-06
Category: Frontend Authorization / API Contract
Severity: Medium
Affected modules:
  apps/web/src/app/projects/page.tsx
  apps/web/src/app/projects/[id]/page.tsx
Question or issue:
  The backend allows Super User accounts, including the Director bootstrap account, to pass
  project.manage checks. FastAPI RBACService.has_permission returns true when
  current_user.account.is_super_user is true.
  The frontend currently derives canManage with:
    user?.permissions.includes('project.manage')
  This excludes Director because the Director role permission list includes project.view but not
  project.manage; Director's elevated access is returned separately as is_super_user / isSuperUser.
Why it matters:
  Director cannot access the Create Project UI even though POST /v1/projects is supported by
  backend authorization for Super User.
Required frontend fix:
  Use the effective permission check:
    user?.isSuperUser || user?.permissions.includes('project.manage')
  Apply this wherever frontend gates project create/edit/member assignment actions.
Backend status:
  No backend change required. Backend supports Director project creation through Super User RBAC.
Owner: Claude
Resolution:
  Changed canManage derivation in projects/page.tsx and projects/[id]/page.tsx to:
    (user?.isSuperUser || user?.permissions.includes('project.manage')) ?? false
  Super User flag is returned by GET /v1/me as account.is_super_user and mapped to
  AuthUser.isSuperUser in use-me.ts. No backend change required.
Status: Resolved
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
Resolution:
  Added authenticated GET /v1/project-types, GET /v1/project-statuses, and
  GET /v1/priority-levels endpoints returning ReferenceSummary arrays.
Verification:
  uv run --group dev pytest tests/test_clients_projects_api.py tests/test_clients_projects_service.py -q
Status: Resolved in CODEX-PHASE2-001 integration fixes
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
Resolution:
  Added authenticated GET /v1/projects/{project_id}/members returning active members with
  embedded employee summaries. Project-view users still require active membership; project-manage
  users can list members across projects.
Verification:
  uv run --group dev pytest tests/test_clients_projects_api.py tests/test_clients_projects_service.py -q
Status: Resolved in CODEX-PHASE2-001 integration fixes
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
Resolution:
  Codex added Phase 2 backend document endpoints:
  - POST /v1/folders/{folder_id}/documents
  - GET /v1/documents/{document_id}
  - POST /v1/documents/{document_id}/versions
  - GET /v1/document-versions/{version_id}/download-url
  - GET /v1/documents/search
  Endpoints enforce server-side upload validation, immutable private Storage keys,
  document versioning, checksums, project ABAC and short-lived signed URLs.
Status: Resolved in backend; Claude frontend wiring remains
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
Resolution:
  Docker Desktop was started. `npx supabase db reset` passed and both Phase 2 SQL
  probes passed. The pipeline-style `Get-Content ... | docker exec -i ...` command
  intermittently hit a Windows Docker pipe permission issue, so the second probe was
  validated by copying the SQL file into the database container and running `psql -f`.
Status: Resolved
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
Resolution:
  Archive exports now preserve the database folder hierarchy when generating ZIP paths.
  No bulk import endpoint exists yet; if the business needs folder/document import later,
  it should be scoped as a separate import workflow.
Status: Archive hierarchy preservation resolved; bulk import workflow not in current backend contract
```

### OPEN-023 — Local Docker Desktop unavailable for final Phase 2 Supabase validation

```text
Date: 2026-06-06
Category: Local Development / Validation
Severity: Medium
Question or issue:
  `npx supabase db reset` failed because Docker Desktop's Linux engine pipe was unavailable:
  `//./pipe/dockerDesktopLinuxEngine` was not found.
Why it matters:
  Backend Python tests, lint and type checks pass, but Phase 2 cannot be marked fully verified
  until migrations and SQL probes run against local Supabase.
Recommended next action:
  Start Docker Desktop, then run:
    npx supabase db reset
    Get-Content supabase/tests/phase2_clients_projects_rpc.sql | docker exec -i supabase_db_iems-erp psql -U postgres -d postgres
    Get-Content supabase/tests/phase2_documents_archive_physical_rpc.sql | docker exec -i supabase_db_iems-erp psql -U postgres -d postgres
Owner: Human / Codex
Resolution:
  Docker Desktop/local Supabase validation is now available. `npx supabase db reset`
  passed, and both Phase 2 SQL probes passed using `docker cp` plus
  `docker exec psql -f` to avoid intermittent Windows pipe issues.
Verification:
  npx supabase db reset
  docker exec supabase_db_iems-erp psql -U postgres -d postgres -f /tmp/phase2_clients_projects_rpc.sql
  docker exec supabase_db_iems-erp psql -U postgres -d postgres -f /tmp/phase2_documents_archive_physical_rpc.sql
Status: Resolved
```

### OPEN-029 - Archive export cancel frontend wiring

```text
Date: 2026-06-06
Category: Frontend / Archive Export
Severity: Low
Affected module: apps/web/src/components/projects/archive-export-panel.tsx
Question or issue:
  The backend now exposes POST /v1/exports/{export_id}/cancel for QUEUED exports.
  The frontend should show a Cancel action only for QUEUED rows and refresh the
  export status after cancellation.
Backend status:
  Codex added POST /v1/exports/{export_id}/cancel. It returns status CANCELLED,
  writes an audit event, and the Celery worker skips cancelled exports before generation.
Frontend follow-up:
  Add a Cancel action only for QUEUED exports. Backend intentionally rejects READY,
  FAILED, EXPIRED and CANCELLED exports with INVALID_STATE.
Resolution:
  Wired POST /v1/exports/{export_id}/cancel via useCancelExport. The export row in
  ArchiveExportPanel now shows a Cancel (X) button only for QUEUED exports; on success
  the list refetches and shows CANCELLED. INVALID_STATE errors are caught and shown as
  "This export can no longer be cancelled." Status labels/colors updated to the real
  ExportStatus union (QUEUED | GENERATING | READY | FAILED | EXPIRED | CANCELLED) —
  the previous PROCESSING placeholder was removed.
Verification:
  uv run --directory apps/api --group dev pytest tests/test_documents_archive_service.py tests/test_documents_archive_api.py tests/test_archive_exports_worker.py -q
Owner: Claude
Status: Resolved
```

### OPEN-028 — QR code rendering: library not installed

```text
Date: 2026-06-06
Category: Frontend / Physical Archive
Severity: Low
Affected module: apps/web/src/app/archive/files/[id]/page.tsx
Question or issue:
  GET /v1/physical-files/{id}/label returns a qr_token string. The physical file label
  page displays this token as text and provides a copy button, but cannot render an
  actual QR code because no QR library is installed in the frontend.
  Currently: token is displayed as text (OPEN-028 note on page).
Required:
  Approval to install qrcode.react (client-side QR generation; no external network calls).
  After approval: add the package and render <QRCodeSVG value={label.qr_token} /> on the label page.
Owner: Human
Status: Resolved (2026-06-06) — qrcode.react installed; QRCodeSVG renders on file detail page
```

### OPEN-030 - Physical archive QR scan route frontend wiring

```text
Date: 2026-06-07
Category: Frontend / Physical Archive
Severity: Medium
Affected module: apps/web/src/app/archive/**
Question or issue:
  Scanning a physical-file label currently returns the raw qr_token UUID string.
  The backend now exposes a resolver endpoint so the frontend can turn that token
  into the physical file record and route the user to the file detail page.
Backend status:
  Codex added GET /v1/physical-files/by-qr/{qr_token}. It requires archive.view
  or archive.manage and returns the same PhysicalFileResponse shape as
  GET /v1/physical-files/{physical_file_id}. The qr_token is an opaque inventory
  identifier only; it is not a Storage URL, download token or auth secret.
Frontend follow-up:
  Add a scanner/deep-link route such as /archive/scan/{qr_token}. After scanning,
  call GET /v1/physical-files/by-qr/{qr_token}, then navigate to
  /archive/files/{physical_file_id}. If lookup returns NOT_FOUND, show a clear
  "label not found" state. Do not call Supabase Storage.
Resolution:
  Added GET /v1/physical-files/by-qr/{qr_token} wiring (lib/api.ts
  getPhysicalFileByQrToken, hooks/use-physical-archive.ts
  usePhysicalFileByQrToken) and a new /archive/scan/[qr_token] route
  (apps/web/src/app/archive/scan/[qr_token]/page.tsx) that resolves the token,
  redirects to /archive/files/{physical_file_id} on success, shows a "Label not
  found" empty state on NOT_FOUND, and a generic ErrorState (via apiErrorMessage)
  for any other failure. Added a "Look up a label by QR token" form on the
  Archive overview page (/archive) so the route is reachable from the UI without
  needing a physical scanner. No Supabase Storage calls involved — qr_token is
  treated as an opaque inventory identifier only.
Verification:
  npx tsc --noEmit && npx eslint src/ --ext .ts,.tsx,.js,.jsx && npx next build   (apps/web)
Owner: Claude
Status: Resolved
```

### OPEN-031 - Project detail cannot list its archived physical files

```text
Date: 2026-06-07
Category: Backend / Physical Archive
Severity: Medium
Affected module: apps/api/app/api/v1/physical_archive.py, apps/web/src/app/projects/[id]/page.tsx
Question or issue:
  The project detail page can register a new physical file via
  POST /v1/projects/{project_id}/physical-files (the "Archive Physical File"
  action), but there is no endpoint to list the physical files already archived
  for a project. Users can only discover existing physical files for a project by
  opening each one directly (e.g. from a freshly created file's redirect, a QR
  scan via /archive/scan/{qr_token}, or by browsing every archive room's location
  tree and reading each file's project field) — there is no project-scoped view.
Backend status:
  Codex added GET /v1/projects/{project_id}/physical-files. It returns
  list[PhysicalFileResponse] newest first and is gated by Super User,
  archive.view, archive.manage or active project membership for that project.
Frontend follow-up:
  Add a "Physical Archive" panel to the project detail page (alongside the existing
  "Archive Physical File" action) listing each physical file's code, status badge,
  current location and volume, linking to /archive/files/{id}, mirroring the
  existing DocumentListPanel pattern.
Verification:
  uv run --directory apps/api --group dev pytest tests/test_physical_archive_api.py tests/test_physical_archive_service.py -q
Owner: Claude
Status: Resolved
Resolution:
  Added a "Physical Archive" panel to the project detail page
  (apps/web/src/app/projects/[id]/page.tsx) that lists every physical file
  archived for the project — file code, status badge, volume number, archive
  room/location, archived-on and last-verified-at dates, and an open-checkout
  indicator — each row linking to /archive/files/{id}. The panel renders for
  any user who can view the project page, matching the backend's Super User /
  archive.view / archive.manage / active-project-membership gating, with
  loading (skeleton), error and "No physical files archived for this project."
  empty states consistent with the rest of the project detail page.
  Files changed:
    - apps/web/src/lib/api.ts (added listProjectPhysicalFiles)
    - apps/web/src/hooks/use-physical-archive.ts (added useProjectPhysicalFiles,
      invalidate on physical-file creation)
    - apps/web/src/components/projects/physical-archive-panel.tsx (new)
    - apps/web/src/app/projects/[id]/page.tsx (render PhysicalArchivePanel)
  Frontend verification:
    cd apps/web && npm run type-check && npm run lint && npm run build
```

### OPEN-027 - Physical archive location hierarchy frontend wiring

```text
Date: 2026-06-06
Category: Frontend / Physical Archive
Severity: Medium
Affected module: apps/web/src/app/archive/rooms/[id]/page.tsx
Question or issue:
  The backend now exposes GET /v1/archive/locations?room_id={room_id}. It returns
  active ArchiveLocationResponse rows for the requested room and preserves
  parent_location_id so the frontend can rebuild the hierarchy.
Backend status:
  Codex added GET /v1/archive/locations?room_id={room_id}. include_inactive=true
  is supported when inactive locations need to be shown.
Frontend follow-up:
  Use this endpoint on room detail instead of requiring users to manually enter
  location UUIDs.
Resolution:
  Wired GET /v1/archive/locations?room_id={room_id} via useLocations. Room detail now
  renders a real expandable tree (lib/locations.ts buildLocationTree, keyed off
  parent_location_id) with click-to-browse contents, replacing the manual UUID-entry
  placeholder. Location creation refetches the list on success and offers a parent
  picker built from the same data. Checkout/return/move forms now use a FileSlotPicker
  (apps/web/src/components/archive/file-slot-picker.tsx) that lists active FILE_SLOT
  locations from the hierarchy instead of free-text UUID inputs.

  While wiring this, found that the entire physical-archive frontend type layer
  (PhysicalLocation, PhysicalFile, PhysicalFileLabel, checkout/return/move/verify
  payloads) used field names that did not match the real Pydantic response/request
  schemas (e.g. file_code vs physical_file_code, state vs status, location vs
  archive_location, notes vs description, location_id vs archive_location_id/
  to_location_id/returned_to_location_id). Corrected all frontend types and consuming
  pages to match apps/api/app/schemas/physical_archive.py exactly (verified via
  model_validate(row) with no field aliasing).
Verification:
  uv run --directory apps/api --group dev pytest tests/test_physical_archive_api.py tests/test_physical_archive_service.py -q
  npx tsc --noEmit && npx next lint --dir src   (apps/web)
Owner: Claude
Status: Resolved
```

### OPEN-026 — Confidentiality level and document type lookup endpoints missing

```text
Date: 2026-06-06
Category: API Contract
Severity: Medium
Affected module: apps/web/src/components/projects/document-upload-dialog.tsx
Question or issue:
  POST /v1/folders/{folder_id}/documents requires a confidentiality_level_id UUID
  (mandatory) and optionally a document_type_id UUID. No GET lookup endpoints exist
  in the API contract to retrieve valid UUIDs for these fields.
  Current state: upload form shows a text input for confidentiality_level_id with a
  placeholder noting this open item. Users must manually enter the UUID.
  The upload will succeed once valid UUIDs are provided, but the UX is unusable for
  non-technical staff without a selector.
Required from Codex:
  GET /v1/confidentiality-levels  (returns [{id, code, name}])
  GET /v1/document-types          (returns [{id, code, name}])
Owner: Codex
Resolution:
  Added authenticated GET /v1/confidentiality-levels and GET /v1/document-types.
  Both return ReferenceSummary arrays: {id, code, name}.
  Frontend: document-upload-dialog.tsx now uses useConfidentialityLevels and
  useDocumentTypes (lib/lookups via ReferenceLookup) to render <select> dropdowns —
  confidentiality level required, document type optional — replacing the raw UUID
  text inputs and the "lookup pending" notes.
Verification:
  uv run --directory apps/api --group dev pytest tests/test_documents_archive_service.py tests/test_documents_archive_api.py -q
Status: Resolved
```

### OPEN-025 — GET /v1/documents/search query parameters undocumented

```text
Date: 2026-06-06
Category: API Contract
Severity: Medium
Affected module: apps/web/src/hooks/use-documents.ts
Question or issue:
  GET /v1/documents/search is documented in the API contract but its accepted query
  parameters are not listed. The frontend uses:
    folder_id=<uuid>     to list documents inside a selected folder
    project_id=<uuid>    for additional project-level scoping
    q=<string>           for text search
  If these parameter names do not match what the backend accepts, folder document
  listing will silently return empty results.
Required from Codex:
  Confirm accepted query parameter names for GET /v1/documents/search and update
  api-contract.md with the parameter table.
Owner: Codex
Resolution:
  Updated docs/api-contract.md with project_id, folder_id, search, q, limit and
  offset. Fixed route ordering so /v1/documents/search is handled before
  /v1/documents/{document_id}. Backend accepts q as an alias for search.
Verification:
  uv run --directory apps/api --group dev pytest tests/test_documents_archive_api.py::test_search_documents_accepts_q_alias -q
Status: Resolved
```

### OPEN-024 — Claude wiring required for new Phase 2 backend endpoints

```text
Date: 2026-06-06
Category: Frontend Integration
Severity: Medium
Question or issue:
  Codex added backend Phase 2 document, archive-export and physical-archive endpoints.
  Claude needs to wire UI screens to the documented API contract without inventing
  alternate backend behavior.
Resolution:
  All four areas wired:
  - Folder CRUD: create/rename/delete with inline editing in FolderTreePanel; INVALID_STATE
    and RESOURCE_CONFLICT errors shown inline.
  - Document upload (multipart FormData), version upload, signed download (on-demand fetch),
    folder document list via GET /v1/documents/search.
  - Archive export: POST/GET with 5s auto-poll while QUEUED or GENERATING, download on READY,
    cancel while QUEUED.
  - Physical archive: rooms list/create, location create, location content browser,
    physical file detail, checkout/return/move/verify action pages, QR label display.
  Follow-up frontend refinements remain in OPEN-027 and OPEN-029 after backend
  endpoints were added.
Owner: Claude
Status: Resolved
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
