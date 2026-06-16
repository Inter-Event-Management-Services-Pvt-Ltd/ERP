# Claude Frontend Checklist

## Phase 4 — Approval Workflows (Slice 2)

### Ownership

- [x] Only frontend-owned files modified: `apps/web/src/app/approvals/**`, `apps/web/src/components/approvals/create-approval-dialog.tsx`, `apps/web/src/hooks/use-approvals.ts`, `apps/web/src/lib/api.ts`, `apps/web/src/types/index.ts`.
- [x] Backend requirement noted: none for this slice; all seven endpoints were already available.
- [x] API contract followed exactly per `docs/api-contract.md`; no invented fields or endpoints.

### Design Workflow

- [x] Screen purpose documented (Approval queue with status filter, approval detail with history, create dialog, review actions).
- [x] User role documented: create open to any authenticated user; approve/reject/request-revision gated on `approval.approve` permission OR `isSuperUser`.
- [x] Shared components reused (AppShell, PageHeader, ContentArea, SkeletonScreen, EmptyState, ErrorState, Badge).
- [x] Responsive states implemented (table scrolls horizontally; detail card collapses to single column on small screens).
- [x] Empty state implemented (no approvals for selected status).
- [x] Loading state implemented (SkeletonScreen while data is fetching).
- [x] Error state implemented (all mutations surface error via apiErrorMessage inline under form).
- [x] Permission-denied state implemented (approve/reject/revision buttons hidden for users without `approval.approve` and not Super User).

### Security

- [x] No secrets exposed; no Supabase service-role key referenced.
- [x] All reads/writes go through FastAPI via `lib/api.ts`; no direct Supabase calls.
- [x] No unsafe HTML rendering (no dangerouslySetInnerHTML).
- [x] Approval action history is read-only; the UI does not fake edits or allow re-submission of completed approvals.
- [x] Review actions (approve/reject/revision) disabled client-side for non-PENDING approvals; server-side remains authoritative.

### Accessibility

- [x] Semantic structure (table with `scope="col"` headers, `role="dialog"` and `aria-modal` on create dialog, `role="group"` on target-type and status-filter button groups).
- [x] Keyboard navigation (all action buttons and form fields keyboard-reachable; dialog closeable via backdrop click).
- [x] Accessible labels (`aria-label` on target-type and status-filter button groups; `aria-pressed` on status filter tabs; `aria-label` on UUID input fields).
- [x] Accessible form errors (`role="alert"` on validation and mutation error messages).
- [x] No color-only critical state (badges show text labels alongside color; action buttons include icon + text).

### Motion

- [x] Motion is purposeful (button `transition-colors` only; no decorative animation).
- [x] Reduced-motion supported via the existing global `prefers-reduced-motion` rule in `globals.css`.

### Validation

- [x] Lint passes (`npm run lint`).
- [x] Type check passes (`npm run type-check`).
- [x] Production build passes (`npm run build`).
- [ ] Responsive QA completed for approval list and detail pages.

## Phase 4 — Director Dashboard (Slice 1)

### Ownership

- [x] Only frontend-owned files modified: `apps/web/src/app/director/**`, `apps/web/src/hooks/use-director.ts`, `apps/web/src/lib/api.ts`, `apps/web/src/types/index.ts`, `apps/web/src/components/layout/director-guard.tsx`.
- [x] Backend requirement noted: OPEN-036 (approval write workflows, admin/policy management, upcoming-events feed, missing-documents metric, archive verification reminders still pending Codex).
- [x] API contract followed exactly per `docs/api-contract.md`; no invented fields or alternate routes; audit event `old_values`/`new_values`/`metadata` intentionally omitted.

### Design Workflow

- [x] Screen purpose documented (Director overview, projects, approvals queue, overdue tasks, physical archive, audit feed).
- [x] User role documented: access gated on `DIRECTOR` role OR `me.account.is_super_user`; DirectorGuard enforces both.
- [x] Shared components reused (AppShell, PageHeader, ContentArea, SkeletonScreen, EmptyState, ErrorState, Badge).
- [x] Responsive states implemented (grid collapses to single column; tables scroll horizontally).
- [x] Empty state implemented (all six detail pages handle zero-row responses).
- [x] Loading state implemented (SkeletonScreen while data is fetching).
- [x] Error state implemented (PERMISSION_DENIED maps to "Director access required"; other errors show message + retry).
- [x] Permission-denied state implemented (DirectorGuard renders PermissionDenied without exposing route or resource details).

### Security

- [x] No secrets exposed; no Supabase service-role key referenced.
- [x] All reads go through FastAPI via `lib/api.ts`; no direct Supabase calls.
- [x] No unsafe HTML rendering (no dangerouslySetInnerHTML).
- [x] Audit events rendered with only the fields returned by the backend; no `old_values`/`new_values`/`metadata` expected or displayed.
- [x] Approval action buttons not present; the approvals page is read-only, as documented in the API contract.
- [x] Server-side authorization remains authoritative; frontend guard is presentation-only.

### Accessibility

- [x] Semantic structure (tables with `scope="col"` headers, section headings via `h2`, `aria-label` on icon buttons).
- [x] Keyboard navigation (all overview cards and nav links are keyboard-reachable; filter inputs accessible via Tab).
- [x] Accessible labels (CountCard links have visible label text alongside the count; stat rows use `<span>` pairs).
- [x] No color-only critical state (overdue badge shows text "Overdue" not just red; critical counts show numeric value with color).
- [x] No hover-only critical action (all actions/links keyboard-reachable).

### Motion

- [x] Motion is purposeful (CountCard link has `transition-colors` on border hover only; no decorative animation).
- [x] Motion does not block workflow.
- [x] Reduced-motion supported via the existing global `prefers-reduced-motion` rule in `globals.css`.

### Validation

- [x] Lint passes (`npm run lint`).
- [x] Type check passes (`npm run type-check`).
- [x] Production build passes (`npm run build`).
- [ ] Responsive QA completed for director overview, projects, approvals, tasks, archive, audit pages.

## Phase 3 — Employee Operations

### Ownership

- [x] Only frontend-owned files were modified (attendance, leave, tasks, calendar pages/components/hooks under `apps/web/**`).
- [x] Any backend requirement was recorded for Codex (OPEN-034 — task comment list endpoint).
- [x] API contract was followed exactly per docs/api-contract.md (no invented fields or alternate routes).

### Design Workflow

- [x] Screen purpose documented (Attendance, Leave, Tasks list/detail, Calendar, Director Attendance).
- [x] User role documented (`attendance.view_all`, `attendance.correct`, `leave.review`, `task.manage`, `isSuperUser`).
- [x] Shared components reused (AppShell, PageHeader, ContentArea, SkeletonScreen, EmptyState, ErrorState, Badge, ConfirmDialog, FormField).
- [x] Responsive states implemented (tables scroll horizontally on small screens, dialogs constrained to viewport).
- [x] Empty state implemented (no attendance sessions, no leave requests, no tasks, no calendar events this month).
- [x] Loading state implemented (SkeletonScreen, Loader2 spinners on mutations).
- [x] Error state implemented (role="alert" inline errors, apiErrorMessage mapping for RESOURCE_CONFLICT, INVALID_STATE, INVALID_REFERENCE, ABAC_DENIED/PERMISSION_DENIED, VALIDATION_ERROR).
- [x] Permission-denied state implemented (Team Attendance, Pending Review, Correct/New Task/New Event actions hidden by permission, not just disabled).

### Security

- [x] No secrets exposed; no Supabase service-role key referenced.
- [x] All Phase 3 reads/writes go through FastAPI (`lib/api.ts`), no direct Supabase calls.
- [x] No unsafe HTML rendering (no dangerouslySetInnerHTML).
- [x] Server-side permissions remain authoritative; frontend checks (`attendance.view_all`, `attendance.correct`, `leave.review`, `task.manage`, `isSuperUser`) are presentation-only gating.
- [x] Document linking on the task detail page accepts a document ID and calls the documented `POST /v1/tasks/{id}/documents` endpoint only — no storage-path guessing.

### Accessibility

- [x] Semantic structure (tables with `scope="col"` headers, `role="alert"` on form errors, breadcrumb `nav aria-label`).
- [x] Keyboard navigation (all actions are `<button type="button">` or form submit; dialogs trap focus on open and close on Escape).
- [x] Visible focus (`focus-visible:ring-2 focus-visible:ring-accent-saffron` on interactive elements).
- [x] Accessible labels (icon-only buttons such as month navigation have `aria-label`).
- [x] Accessible form errors (`role="alert"`, associated via FormField).
- [x] No color-only critical state (Badge components pair color with text, e.g. leave/task status, calendar source labels).
- [x] No hover-only critical action (Correct, Approve/Reject, Edit, Cancel are all keyboard-reachable buttons/links).

### Motion

- [x] Motion is purposeful (dialog `animate-scale-in`, no decorative animation added).
- [x] Motion does not block workflow (dialogs open/close instantly on click; no animation gates submission).
- [x] Reduced-motion supported via the existing global `prefers-reduced-motion` rule in `globals.css` (no new motion primitives introduced).
- [x] No excessive parallax; no animation on every row/card.
- [x] Opacity/transform preferred (`animate-scale-in` on dialogs only).

### Validation

- [x] Lint passes (`npm run lint`).
- [x] Type check passes (`npm run type-check`).
- [x] Production build passes (`npm run build`).
- [ ] Responsive QA completed for attendance, leave, tasks, calendar and director-attendance pages.

## Ownership

- [x] Only frontend-owned files were modified.
- [x] Any backend requirement was recorded for Codex (OPEN-025, OPEN-026, OPEN-027, OPEN-028, OPEN-029 — all resolved).
- [x] API contract was followed (no invented endpoints; undocumented details noted as OPEN items).

## Design Workflow

- [x] Screen purpose documented.
- [x] User role documented (canManage, canUpload, canExport, physical_file.checkout, archive.manage).
- [ ] Either Claude Design or Google Stitch used where useful.
- [x] Generated output reviewed before implementation.
- [x] Shared components reused (AppShell, PageHeader, ContentArea, SkeletonScreen, ConfirmDialog).
- [x] Responsive states implemented.
- [x] Empty state implemented (no folder selected, no exports, no rooms, no locations, no contents at selected location).
- [x] Loading state implemented (SkeletonScreen, Loader2 spinners, isPending).
- [x] Error state implemented (role="alert" inline errors, apiErrorMessage mapping).
- [x] Permission-denied state implemented (buttons hidden by permission, actions unavailable on wrong state).

## Security

- [x] No secrets exposed.
- [x] No service-role key referenced.
- [x] No direct sensitive write bypass (all uploads go through FastAPI, not Supabase Storage directly).
- [x] No unsafe HTML rendering (no dangerouslySetInnerHTML).
- [x] No restricted metadata leak (permission-denied hides resource details).
- [ ] Security headers reviewed.
- [x] Third-party packages reviewed (no new packages added; existing lucide-react, react-hook-form, zod, date-fns).
- [x] Download links come from backend signed-URL flow (on-demand only via onClick, never pre-fetched).

## Accessibility

- [x] Semantic structure (nav for folder tree, aria-label on breadcrumbs, role="alert" on errors).
- [x] Keyboard navigation (all actions via buttons with type="button", form submit on Enter).
- [x] Visible focus (focus:ring-2 focus:ring-accent-saffron on all interactive elements).
- [x] Accessible labels (aria-label on icon-only ActionBtn buttons).
- [x] Accessible form errors (role="alert" inline, associated with form context).
- [x] No color-only critical state (text labels accompany all status badges).
- [x] No hover-only critical action (all actions have keyboard-reachable equivalents).
- [x] Touch targets checked (py-1.5 px-2 minimum on folder rows, p-0.5 on action icons).
- [ ] Reduced-motion path checked.

## Motion

- [x] Motion is purposeful (folder chevron rotate, opacity on action buttons).
- [x] Motion does not block workflow (transitions are 100-180 ms, no blocking animations).
- [ ] Reduced-motion mode supported (CSS transitions only; prefers-reduced-motion not yet explicitly tested).
- [x] No excessive parallax.
- [x] No animation on every card.
- [x] Opacity and transform preferred (opacity-0/opacity-100 for action reveal, rotate-90 for chevron).
- [x] No major layout shift introduced.

## Validation

- [x] Lint passes.
- [x] Type check passes (npx tsc --noEmit clean after Phase 2 wiring).
- [ ] Tests pass.
- [ ] Production build passes.
- [ ] Responsive QA completed.
- [ ] Screenshot or visual notes added.
