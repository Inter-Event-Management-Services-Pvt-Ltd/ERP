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
ID: CODEX-PHASE0-001
Owner: Codex
Status: REVIEW
Task: Run local Supabase migrations from a clean environment.
Checklist:
- docs/checklists/PHASE_0_FOUNDATION_VALIDATION.md
- docs/checklists/BACKEND_CODEX.md
Output:
- migration errors
- fixes
- validation results
- updated checklist
```

## Claude Immediate Task

```text
ID: CLAUDE-DESIGN-001
Owner: Claude
Status: READY AFTER API SHELL IS CONFIRMED
Task: Produce frontend design direction and component inventory.
Tools:
- Use either Claude Design or Google Stitch
Checklist:
- docs/checklists/FRONTEND_CLAUDE.md
Output:
- design-system notes
- screen inventory
- component inventory
- responsive notes
- motion notes
- accessibility notes
- reviewed mockup direction
```

## Codex Following Tasks

```text
CODEX-PHASE0-002 Validate constraints and RLS
CODEX-PHASE1-001 Scaffold FastAPI — REVIEW
CODEX-PHASE1-002 Configure auth verification
CODEX-PHASE1-003 Add RBAC/ABAC middleware
CODEX-PHASE2-001 Build clients and projects API
CODEX-PHASE2-002 Build folders and documents API
CODEX-PHASE2-003 Build archive ZIP worker
CODEX-PHASE2-004 Build physical archive API
```

## Claude Following Tasks

```text
CLAUDE-PHASE1-001 Scaffold Next.js
CLAUDE-PHASE1-002 Build login and app shell
CLAUDE-PHASE2-001 Build client and project screens
CLAUDE-PHASE2-002 Build folder explorer
CLAUDE-PHASE2-003 Build archive and physical-file screens
CLAUDE-PHASE3-001 Build attendance, leave, task and calendar screens
CLAUDE-PHASE4-001 Build Director Dashboard
CLAUDE-PHASE4-002 Build admin and approval screens
```

## Dockerization Tasks

```text
CODEX-DOCKER-001 Create and validate Compose stack
CODEX-DOCKER-002 Add API, worker, scheduler and Redis container checks
CODEX-DOCKER-003 Validate Caddy routing and backend isolation
CLAUDE-DOCKER-001 Validate Next.js standalone container build
CLAUDE-DOCKER-002 Validate frontend behind reverse proxy
```
