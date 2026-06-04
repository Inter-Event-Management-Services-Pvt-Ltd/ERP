# IEMS ERP — Frontend Design Specification

**Task:** CLAUDE-DESIGN-001  
**Date:** 2026-06-04  
**Author:** Claude (frontend agent)  
**Status:** Approved — ready for implementation planning

---

## 1. Visual Direction

### Brand Identity

The IEMS ERP carries the rebrand identity: warm Indian-modern, ink-black and cream-paper surfaces with madder-red and saffron-gold accents. Editorial serif display against precise mono micro-labels, generous negative space, thin hairline rules, and the recurring warm gradient strip. Refined and operational — fitting for a high-end event management house.

### Surface Mode

**Dark (ink-led) throughout.** All surfaces use the ink colour family. No light mode in the initial build.

### Design Tokens

#### Colour

| Token | Hex | Role |
|---|---|---|
| `surface-base` | `#1c1611` | Page background, content area |
| `surface-raised` | `#261d15` | Cards, panels, table rows |
| `surface-deep` | `#15110c` | Top bar, icon rail, drawer |
| `surface-border` | `#352616` | All borders and dividers |
| `text-primary` | `#f3e9cf` | Body text, headings |
| `accent-saffron` | `#d4924a` | Primary accent — links, active states, stat numbers, section titles |
| `accent-madder` | `#8b3a1f` | Active nav item, primary button, danger badge background |
| `accent-warning` | `#f3a86e` | Warning text, overdue indicators |
| `accent-critical` | `#fca5a5` | Critical alert text |
| `gradient-strip` | `#8b3a1f → #d4924a → #f3e9cf` | 2px top-bar accent strip only |

#### Typography

| Role | Font | Style | Usage |
|---|---|---|---|
| Display | Instrument Serif | Italic | Page titles, major section headings, panel titles |
| Body | Geist | Regular / Medium | Table data, body copy, form labels, nav labels |
| Data | JetBrains Mono | Regular / SemiBold | Stat numbers, badges, eyebrows, timestamps, field labels |

**Rules:**
- Serif for the first thing the eye lands on per screen (page title)
- Geist for everything the user reads in quantity (tables, forms, body)
- Mono for everything that needs to be scanned precisely (numbers, codes, statuses)
- Never mix serif and mono in the same UI element

#### Gradient Strip

- Height: 2px
- Placement: immediately below the top bar, spanning full width
- Used once per shell — not repeated on cards or panels
- `background: linear-gradient(90deg, #8b3a1f 0%, #d4924a 55%, #f3e9cf 100%)`

---

## 2. Screen Inventory

### Public

| Route | Screen |
|---|---|
| `/login` | Google Sign-In |
| `/auth/callback` | Auth redirect (no UI) |

### Employee (all authenticated users)

| Route | Screen |
|---|---|
| `/dashboard` | Employee home |
| `/attendance` | Attendance history + check-in/out |
| `/leave` | Leave requests |
| `/tasks` | Personal task list |
| `/calendar` | Shared calendar |
| `/projects` | Project list |
| `/projects/[id]` | Project detail |
| `/projects/[id]/documents` | Folder explorer |
| `/documents/[id]` | Document detail |
| `/approvals` | Approvals queue |
| `/approvals/[id]` | Approval detail |
| `/notifications` | Notifications |

### Physical Archive

| Route | Screen |
|---|---|
| `/archive` | Archive overview |
| `/archive/rooms` | Room list |
| `/archive/rooms/[id]` | Room explorer |
| `/archive/files/[id]` | Physical file detail |
| `/archive/files/[id]/checkout` | Checkout form |
| `/archive/files/[id]/return` | Return form |
| `/archive/files/[id]/verify` | Verification form |

### Admin

| Route | Screen |
|---|---|
| `/admin` | Admin overview |
| `/admin/employees` | Employee management |
| `/admin/departments` | Department management |
| `/admin/roles` | Role assignments |
| `/admin/policies` | ABAC policy viewer |
| `/admin/folder-templates` | Folder template editor |
| `/admin/archive-locations` | Archive location management |
| `/admin/audit` | Full audit log |

### Director

| Route | Screen |
|---|---|
| `/director` | Director Dashboard (Overview tab) |
| `/director/projects` | All-projects table |
| `/director/attendance` | Company-wide attendance |
| `/director/tasks` | Task workload view |
| `/director/calendar` | Director calendar |
| `/director/approvals` | All pending approvals |
| `/director/archive` | Physical storage-room view |
| `/director/audit` | Audit event feed |

**Total: 35 routes.**

---

## 3. Navigation Structure

### Sidebar

- **Collapsed state:** 44px icon rail
- **Expanded state:** 200px, slides out on hover (`transition: width 180ms ease-out`)
- **Collapsed logo:** single `i` glyph in JetBrains Mono, saffron
- **Expanded logo:** `IEMS` in JetBrains Mono, saffron

### Navigation Groups

| Group | Items | Visibility |
|---|---|---|
| Workspace | Dashboard · Projects · Archive | All roles |
| People | Attendance · Tasks · Calendar | All roles |
| Approvals | Approvals (with live badge count) | All roles |
| Admin | Admin | Admin, Super Admin, Super User only |
| Director | Director zone (`/director/*`) | Director only |

### Role Visibility Rules

- Nav visibility is UX-only — backend enforces all access
- Admin link hidden from Employee, Manager, and Director roles
- Director sees `/director/*` routes instead of the standard Employee Dashboard
- Approval badge count from `GET /v1/approvals` (pending count only — no detail)
- Footer: current user's name and avatar with logout

### Mobile Navigation

Bottom drawer triggered by a ☰ button in the top bar. Full-screen overlay with the same group structure. Closed by tap outside or ✕.

---

## 4. Shared Component Inventory

### Layout & Shell

| Component | Description |
|---|---|
| `AppShell` | Top bar + gradient strip + icon rail + content area |
| `Sidebar` | Hover-expand rail with role-filtered nav groups and badge |
| `TopBar` | Logo, breadcrumb slot, notifications bell, user avatar |
| `PageHeader` | Instrument Serif title + JetBrains Mono subtitle + action slot |
| `ContentArea` | Padded scroll container |
| `DetailDrawer` | Right-side slide-in panel for file preview and metadata |

### Data Display

| Component | Description |
|---|---|
| `StatCard` | Large Mono number + Mono label + optional delta line |
| `DataTable` | Sortable, filterable table with skeleton loading rows |
| `ProjectCard` | Project summary — ID, client, status badge, archive readiness |
| `AuditTimeline` | Feed of timestamped audit events with actor highlight |
| `AlertPanel` | Severity-sorted alert list (critical / high / normal / info) |
| `ProgressBar` | Archive readiness — inline in table rows and standalone |

### Navigation & Wayfinding

| Component | Description |
|---|---|
| `Breadcrumb` | Path from root to current resource |
| `Tabs` | Section tabs (Director Dashboard, Project detail) |
| `Pagination` | Table pagination |
| `SearchBar` | Global search with project/document/archive scope toggle |

### Forms & Inputs

| Component | Description |
|---|---|
| `FormField` | Label + input + accessible error message wrapper |
| `FileUploader` | Drag-and-drop + file picker with upload progress |
| `FolderUploader` | Folder drag-and-drop preserving hierarchy |
| `DatePicker` | Calendar input for dates |
| `ComboSelect` | Searchable select for employee/project/client |
| `CheckboxGroup` | Multi-select for team assignment, document types |

### Status & Feedback

| Component | Description |
|---|---|
| `Badge` | Mono status pill — ACTIVE / PENDING / OVERDUE / APPROVED / etc. |
| `StatusDot` | Coloured dot + label for compact status display |
| `Toast` | Lightweight success/error/info notification (slide-up, 160ms) |
| `ConfirmDialog` | Destructive action confirmation |
| `LoadingSpinner` | Inline spinner for async actions |

### States (required on every screen)

| Component | Description |
|---|---|
| `SkeletonScreen` | Per-screen skeleton matching actual layout, shimmer disabled under `prefers-reduced-motion` |
| `EmptyState` | Icon + Serif heading + body + optional CTA |
| `ErrorState` | Error message + retry action |
| `PermissionDenied` | Generic 403 — no resource name or ID leaked |
| `OfflineBanner` | Top-strip connectivity warning, auto-dismisses on reconnect |

### File & Archive

| Component | Description |
|---|---|
| `FolderTree` | Recursive explorer with expand/collapse, active highlighting |
| `FileRow` | File table row — icon, name, size, date, uploader, status badge |
| `FilePreviewOverlay` | Full-screen overlay within content area — PDF/image/Office, page nav, version switcher, approve/download |
| `VersionList` | Version history with current/approved markers |
| `PhysicalLocationBadge` | Room → Rack → Shelf → Box → File inline display |
| `QRDisplay` | QR code render + print action |
| `LabelPrint` | Printable physical folder label layout |

**Total: ~38 components.**

---

## 5. Responsive Layout Rules

| Breakpoint | Behaviour |
|---|---|
| `< 768px` mobile | Rail hidden. Top bar ☰ opens full-screen drawer nav. Single-column layout. Sticky primary action at bottom. |
| `768–1024px` tablet | Rail visible, collapsed (44px). Tables reflow to labelled card-list. |
| `≥ 1024px` desktop | Full layout — rail + hover-expand + content + optional detail drawer. Primary design target. |
| `≥ 1440px` wide | Content area capped at `max-w-7xl`. Stat grids expand to 5-column where data warrants. |

- Tables never scroll horizontally on mobile — reflow to card-list pattern
- Folder tree collapses to breadcrumb-only on mobile
- Detail drawer becomes full-screen sheet on mobile
- File preview overlay becomes full-screen on tablet and below

---

## 6. Accessibility Rules

- Semantic HTML: `<nav>`, `<main>`, `<header>`, `<section>`, logical heading order
- All interactive elements keyboard-reachable; focus ring: `ring-2 ring-saffron` on ink background
- Sidebar icons: `aria-label` required on all icon-only rail items
- Dialogs trap focus; return focus to trigger element on close; first meaningful control focused on open
- Status communicated via text + icon — never colour alone (WCAG 1.4.1)
- Form errors: `aria-describedby` on input + `aria-invalid="true"` on invalid fields
- Touch targets: minimum 44×44px on mobile
- Contrast: `#f3e9cf` on `#1c1611` passes WCAG AA at all body sizes; `#d4924a` (saffron) only used at large or bold sizes — never for body text
- `PermissionDenied` state: generic message only — no resource name, ID, or path leaked

---

## 7. Motion Rules

| Context | Behaviour | Duration |
|---|---|---|
| Sidebar hover-expand | Width 44px → 200px, `ease-out` | 180ms |
| Detail drawer open/close | Slide from right, `ease-out` / `ease-in` | 220ms |
| Dialog open | Fade + scale from 0.96 | 180ms |
| Toast enter/exit | Slide up from bottom-right | 160ms |
| Folder tree node expand | Height + opacity fade | 140ms |
| Skeleton → content crossfade | Opacity only | 120ms |
| Page transition | Opacity fade — no slide between routes | 100ms |
| Stat card stagger load | 40ms delay between cards | 120ms each |
| File preview overlay open | Fade in | 180ms |

**Avoid:** bouncing, parallax, animation on every card hover, long blocking transitions, motion that delays task completion.

**`prefers-reduced-motion`:** All transitions drop to `duration-0` or a simple opacity snap. Skeleton shows but does not pulse-animate. No layout shifts.

**Prefer `opacity` and `transform` only** — never animate layout-triggering properties directly.

---

## 8. Required States

Every screen must implement all of the following:

| State | Implementation |
|---|---|
| Loading | `SkeletonScreen` matching actual layout — shimmer pulse, disabled under `prefers-reduced-motion` |
| Empty | `EmptyState` — icon + Instrument Serif heading + body text + optional CTA button |
| Success | `Toast` — lightweight, auto-dismisses at 4s |
| Validation error | Inline field error via `aria-describedby`, `aria-invalid` — no colour-only signalling |
| Permission denied | `PermissionDenied` — generic message, no resource details |
| Server error | `ErrorState` — friendly message + retry action, no stack trace exposed |
| Offline / degraded | `OfflineBanner` — top strip, not full-screen block; cached data still shown; auto-dismisses on reconnect |

---

## 9. Director Dashboard Layout

### Structure

- Full-height app shell with tabbed content area
- **Stat strip** is persistent across all tabs — always visible above the tab bar
- **Tabs:** Overview · Projects · Attendance · Tasks · Archive · Audit

### Overview Tab Layout

```
┌─ Page Header ──────────────────────────────────────────┐
│  "Good morning, Director"  [11 Present] [2 Absent]     │
├─ Tabs ─────────────────────────────────────────────────┤
│  Overview · Projects · Attendance · Tasks · Archive...  │
├─ Stat Strip (5 cards) ─────────────────────────────────┤
│  Active Projects · Overdue Tasks · Approvals ·          │
│  Files Checked Out · Missing Documents                  │
├─ Two-column content ───────────────────────────────────┤
│  Projects table (1.7fr) │ Alerts + Attendance (1fr)    │
├─ Audit feed ───────────────────────────────────────────┤
│  Last 10 events → link to full audit log               │
└────────────────────────────────────────────────────────┘
```

### Key Decisions

- Each stat card is clickable — jumps to the relevant tab
- Projects table includes inline archive-readiness progress bar per row
- Alerts sorted by severity: Critical → High → Normal → Info
- Attendance mini-chart groups by department, bar chart style
- Audit feed actor names highlighted in saffron
- All data sourced from `/v1/director/*` endpoints

---

## 10. Folder Explorer Layout

### Structure

Four-pane layout (left to right):

```
┌─ Rail ─┬─ Folder Tree (220px) ─┬─ File List ────┬─ Detail Drawer (260px) ─┐
│ 44px   │ Project ID + name     │ Breadcrumb bar │ File name + meta        │
│ icons  │ Recursive folder tree │ Action buttons │ Small preview thumbnail  │
│        │ with expand/collapse  │ File rows      │ Status + version list   │
│        │ Active folder         │ Status badges  │ Approve / Download      │
└────────┴───────────────────────┴────────────────┴─────────────────────────┘
```

### File Preview Overlay

Triggered by clicking the Preview button in the detail drawer. Opens as a full-screen overlay within the content area (rail always remains visible).

```
┌─ Preview Bar ─────────────────────────────────────────────┐
│  [Close]  filename.pdf  Page 1 of 3  [Approve] [Download] │
├─ Stage ───────────────────────────────────────────────────┤
│         prev    [ rendered page / image ]    next         │
│                    ● ○ ○  (page dots)                     │
├─ Footer ──────────────────────────────────────────────────┤
│  Version: [v2 — Current] [v1 — 1 Jun]  UNDER REVIEW      │
│                              Uploaded by Rahul · 3 Jun    │
└───────────────────────────────────────────────────────────┘
```

### Key Decisions

- Folder tree preserves exact office naming (`01 Client Brief`, `02 Quotations`, etc.)
- Drawer opens on file click — no page navigation needed for most tasks
- Approve + Download in the preview bar — no need to close preview first
- Version switcher in footer — compare versions without leaving preview
- Prev/next arrows navigate between files in the same folder
- Keyboard: Esc closes · left/right navigates files · 1/2/3 jumps versions
- Download always uses a backend-signed URL (`GET /v1/document-versions/{id}/download-url`)
- Export ZIP triggers async Celery job → toast when ready
- Tablet: tree panel collapses · Mobile: drawer becomes full-screen sheet

---

## 11. Frontend Implementation Phases

### Phase 1 — Scaffold & Auth
*Tasks: CLAUDE-PHASE1-001, CLAUDE-PHASE1-002*

- Next.js app with TypeScript, Tailwind CSS, shadcn/ui
- IEMS design tokens (colours, typography, spacing)
- App shell: top bar, gradient strip, icon rail
- Login page with Google Sign-In via Supabase Auth
- Auth callback handler
- `AppShell`, `Sidebar`, `TopBar`, `PageHeader` components
- Role-based nav filtering (UX only)
- Protected route wrapper

### Phase 2 — Projects & Documents
*Tasks: CLAUDE-PHASE2-001, CLAUDE-PHASE2-002*

- Project list with search, filters, and status badges
- Project detail page with metadata label and team panel
- Folder explorer — four-pane layout
- File upload (single + drag-and-drop)
- Folder upload preserving hierarchy
- Detail drawer with file metadata and version history
- File preview overlay (PDF, image, Office)
- Approval badge and approve/reject/revise actions

### Phase 3 — Archive & Physical Records
*Tasks: CLAUDE-PHASE2-003*

- Archive room explorer — rack/shelf/box tree
- Physical file detail with location badge
- Checkout and return forms
- QR code display component
- Printable folder label layout
- Export ZIP async flow with toast feedback

### Phase 4 — Employee Operations
*Tasks: CLAUDE-PHASE3-001*

- Employee dashboard — attendance status, check-in/out, tasks, calendar, recent projects, notifications
- Attendance history page
- Leave request list and form
- Task list — personal kanban or table view
- Shared calendar view

### Phase 5 — Director Dashboard & Admin
*Tasks: CLAUDE-PHASE4-001, CLAUDE-PHASE4-002*

- Director Dashboard — tabbed layout, stat strip, project table with archive readiness, alerts, attendance mini-chart, audit feed
- All `/director/*` sub-pages
- Approvals queue and detail page
- Admin screens — employees, departments, roles, policies, folder templates, archive locations, audit log

### Phase 6 — Frontend Docker & QA
*Tasks: CLAUDE-DOCKER-001, CLAUDE-DOCKER-002*

- Next.js standalone Dockerfile
- `.dockerignore`
- Container build validation
- Reverse-proxy compatibility check
- Responsive QA across all breakpoints
- Accessibility audit
- Reduced-motion path check

---

## 12. Security Considerations

- **No secrets in the browser** — Supabase service-role key never referenced in frontend code
- **Route guards are UX only** — all authorization enforced server-side by FastAPI + RLS
- **Signed download URLs** — all file downloads use `GET /v1/document-versions/{id}/download-url`, never direct storage paths
- **Safe HTML rendering** — React's default escaping used throughout; raw HTML injection avoided
- **No restricted metadata leaked** — `PermissionDenied` state shows a generic message only
- **CSP and security headers** configured in `next.config.mjs`
- **Auth tokens** stored in secure HTTP-only cookies managed by Supabase — not `localStorage`
- **Error messages** are user-friendly but contain no stack traces or internal paths
- **Third-party components** reviewed before installation
- **Super User override** header (`X-IEMS-Override-Reason`) sent only after user explicitly provides a reason in the UI

---

## 13. Unresolved API Needs for Codex

The following frontend requirements depend on backend responses not yet confirmed in `docs/api-contract.md`:

| Need | Proposed endpoint | Notes |
|---|---|---|
| Approval pending count (badge) | `GET /v1/approvals?status=pending&count=true` | Count-only response to avoid fetching full list for the badge |
| Archive readiness score per project | `archive_readiness_pct` field on project response | Integer 0–100, needed in project table and Director Dashboard |
| Director overview metrics | `GET /v1/director/overview` | Already in contract — confirm shape includes all 10 metrics |
| Folder tree with file counts | `GET /v1/projects/{id}/folders/tree` | Need `file_count` per node for tree panel badge |
| Export ZIP status | `GET /v1/exports/{id}` | Need `status` field: `pending` / `processing` / `ready` / `failed` |
| Notification unread count | `GET /v1/me/notifications?unread=true&count=true` | For the top-bar bell badge |

These should be confirmed with Codex before Phase 2 implementation begins.

---

## 14. Accessibility Checklist (per screen)

- [ ] Semantic structure — correct heading order, landmark elements
- [ ] Keyboard navigation — all interactive elements reachable
- [ ] Visible focus indicators — `ring-2 ring-saffron`
- [ ] `aria-label` on all icon-only buttons
- [ ] Form errors via `aria-describedby` + `aria-invalid`
- [ ] Status not communicated by colour alone
- [ ] Touch targets at least 44×44px on mobile
- [ ] `prefers-reduced-motion` path tested
- [ ] `PermissionDenied` state leaks no resource details
- [ ] Dialog focus trap and focus-return on close

---

## 15. Motion Checklist (per screen)

- [ ] Motion is purposeful — improves orientation or confirms completion
- [ ] No motion that blocks workflow
- [ ] `prefers-reduced-motion` respected — all transitions drop to instant or opacity snap
- [ ] No parallax
- [ ] No animation on every card hover
- [ ] `opacity` and `transform` only — no layout-property animation
- [ ] No major layout shift introduced
