---
name: iems-phase-gate
description: Use before starting or closing any IEMS ERP implementation phase to verify ownership, scope, checklist status, security gate, tests, documentation, and unresolved risks.
---

# IEMS Phase Gate

Read:

- `docs/05_PHASE_ROADMAP.md`
- `docs/06_DEFINITION_OF_DONE.md`
- active phase checklist under `docs/checklists/`
- `docs/07_OPEN_ITEMS.md`

Before starting:

- identify phase
- identify agent owner
- identify allowed directories
- identify dependent API contracts
- identify security gate
- identify acceptance tests

Before marking complete:

- run required commands
- update checklist
- update `CHANGELOG.md`
- record open risks
- confirm no cross-boundary edits
- confirm human review is still required where documented

Never mark a phase done based only on code generation.
