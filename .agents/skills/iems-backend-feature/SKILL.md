---
name: iems-backend-feature
description: Use when implementing any FastAPI backend feature for the IEMS ERP, including clients, projects, folders, documents, attendance, tasks, approvals, archives, signed URLs, ABAC, audit logs, or Director endpoints. Codex backend-only skill.
---

# IEMS Backend Feature

Read:

- `CODEX.md`
- `docs/api-contract.md`
- `docs/04_SECURITY_MODEL.md`
- `docs/checklists/BACKEND_CODEX.md`

Implement:

- typed request and response models
- JWT verification
- current employee resolution
- RBAC check
- ABAC check
- transactional write
- audit event where required
- stable error codes
- success tests
- unauthorized tests
- invalid-state tests

Do not edit:

```text
apps/web/**
```

If frontend work is required, record it in `docs/07_OPEN_ITEMS.md`.
