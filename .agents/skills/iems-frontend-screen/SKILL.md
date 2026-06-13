---
name: iems-frontend-screen
description: Use when designing or implementing an IEMS ERP frontend screen, route, component, dashboard, table, form, file explorer, archive view, task view, attendance view, or approval screen. Codex frontend-only skill.
---

# IEMS Frontend Screen

Read:

- `AGENTS.md`
- `docs/14_FRONTEND_DESIGN_SYSTEM.md`
- `docs/15_FRONTEND_SECURITY_MOTION.md`
- `docs/checklists/FRONTEND_CLAUDE.md`
- `docs/api-contract.md`

Workflow:

```text
understand role and task
→ use either Codex Design or Google Stitch where helpful
→ review design output
→ implement in Next.js
→ reuse shared components
→ add loading, empty, error, and permission-denied states
→ validate responsive layout
→ validate accessibility
→ validate reduced-motion behavior
→ run lint, type check, tests, and build
```

Do not edit backend files.

Do not infer permissions from hidden buttons. Backend authorization remains authoritative.
