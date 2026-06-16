# Agent Task Board

Move tasks through:

```text
BACKLOG
→ READY
→ IN_PROGRESS
→ REVIEW
→ VERIFIED
→ DONE
```

## Codex Immediate Task

```text
ID: CODEX-PHASE4-002
Owner: Codex
Status: DONE
Task: Build Phase 4 approval workflows.
Checklist:
- docs/checklists/PHASE_4_MANAGEMENT_DIRECTOR.md
- docs/checklists/BACKEND_CODEX.md
Output:
- approval type lookup route
- approval request list, create and detail routes
- approval approve, reject and request-revision routes
- server-side RBAC/ABAC and audited Supabase RPCs
- approval notifications and immutable action history
- backend and SQL validation tests
- updated checklist
```

## Claude Immediate Task

```text
ID: CLAUDE-DESIGN-001
Owner: Claude
Status: DONE
Task: Produce frontend design direction and component inventory.
Tools:
- Used IEMS design system tokens throughout (surface-base/raised/deep, accent-saffron/madder/warning/critical)
- Tailwind + custom design tokens, no external UI library beyond lucide-react
```

## Codex Following Tasks

```text
CODEX-PHASE0-002 Validate constraints and RLS
CODEX-PHASE1-001 Scaffold FastAPI — DONE
CODEX-PHASE1-002 Configure auth verification — DONE
CODEX-PHASE1-003 Add RBAC/ABAC middleware — DONE
CODEX-PHASE1-004 Complete backend Phase 1 audit, logging and CI — DONE
CODEX-PHASE2-001 Build clients and projects API — DONE
CODEX-PHASE2-002 Build folders and documents API — DONE
CODEX-PHASE2-003 Build archive ZIP worker — DONE
CODEX-PHASE2-004 Build physical archive API — DONE
CODEX-PHASE3-001 Build attendance, leave, task and calendar backend APIs — DONE
CODEX-PHASE4-001 Build Director Dashboard read APIs — DONE
CODEX-PHASE4-002 Build approval workflows — DONE
CODEX-PHASE4-003 Build admin, policy and audit explorer APIs — BACKLOG
```

## Claude Following Tasks

```text
CLAUDE-PHASE1-001 Scaffold Next.js — DONE
CLAUDE-PHASE1-002 Build login and app shell — DONE
CLAUDE-PHASE2-001 Build client and project screens — DONE
  - client list, create client (auto-derived code, read-only), deactivate client
  - project list, create project (auto-derived code, read-only), project detail
  - project members panel: add/remove/role-change, 409 handling, self-remove guard
CLAUDE-PHASE2-002 Build folder explorer — DONE
  - folder tree with inline create/rename/delete (canManage gated)
  - document list per folder (GET /v1/documents/search)
  - document upload (multipart), version upload, signed download on click
  - archive export panel with auto-poll and READY download
CLAUDE-PHASE2-003 Build archive and physical-file screens — DONE
  - /archive: rooms overview
  - /archive/rooms: rooms list + create form
  - /archive/rooms/[id]: room detail + add location + location content browser
  - /archive/files/[id]: file detail with state, actions, QR label
  - /archive/files/[id]/checkout|return|move|verify: action forms with error handling
CLAUDE-PHASE3-001 Build attendance, leave, task and calendar screens — READY
CLAUDE-PHASE4-001 Build Director Dashboard — BACKLOG
CLAUDE-PHASE4-002 Build admin and approval screens — BACKLOG
```

## Dockerization Tasks

```text
CODEX-DOCKER-001 Create and validate Compose stack
CODEX-DOCKER-002 Add API, worker, scheduler and Redis container checks
CODEX-DOCKER-003 Validate Caddy routing and backend isolation
CLAUDE-DOCKER-001 Validate Next.js standalone container build
CLAUDE-DOCKER-002 Validate frontend behind reverse proxy
```
