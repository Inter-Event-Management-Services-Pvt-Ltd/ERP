---
name: iems-api-contract-review
description: Use when changing or consuming IEMS ERP API routes, request models, response models, error codes, signed URL flows, auth assumptions, or frontend-backend integration points.
---

# IEMS API Contract Review

Read:

- `docs/api-contract.md`
- `docs/13_AGENT_OWNERSHIP_MATRIX.md`
- `docs/04_SECURITY_MODEL.md`

Validate:

- endpoint path
- HTTP method
- request schema
- response schema
- stable error codes
- authentication requirement
- RBAC requirement
- ABAC requirement
- audit requirement
- signed URL expiry where relevant
- pagination and filtering where relevant
- no sensitive metadata leakage

Ownership rule:

```text
Codex implements server changes
Claude consumes documented contract
```

If a contract change is needed:

- update `docs/api-contract.md`
- add changelog entry
- add tests
- notify the other agent through `docs/07_OPEN_ITEMS.md`
