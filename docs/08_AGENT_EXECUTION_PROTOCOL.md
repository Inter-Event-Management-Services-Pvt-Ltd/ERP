# Agent Execution Protocol

## Before Starting

1. Read `AGENTS.md`.
2. Read `docs/00_START_HERE.md`.
3. Identify the active phase.
4. Read the phase checklist.
5. Read `docs/04_SECURITY_MODEL.md`.
6. Inspect existing implementation before editing.

## During Work

- Keep changes scoped.
- Update tests with code.
- Prefer migrations over manual database changes.
- Add audit logging with sensitive workflows.
- Preserve soft-delete strategy.
- Do not weaken RLS.
- Do not bypass ABAC.
- Use explicit TODOs only with an open-item entry.

## Completion Report Template

```text
Task:
Phase:
Files changed:
Schema changes:
Authorization changes:
Tests added:
Commands run:
Checklist items completed:
Security checks completed:
Known limitations:
Open items created:
```
