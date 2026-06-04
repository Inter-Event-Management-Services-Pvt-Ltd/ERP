---
name: iems-security-review
description: Use when reviewing any IEMS ERP feature, pull request, deployment, storage workflow, authentication flow, authorization rule, or release for security risks.
---

# IEMS Security Review

Read:

- `docs/04_SECURITY_MODEL.md`
- `docs/checklists/SECURITY_GLOBAL.md`
- `docs/checklists/SECURITY_RELEASE_GATE.md`
- `docs/09_RISK_REGISTER.md`

Validate:

- default-deny authorization
- server-side checks for sensitive writes
- no frontend service-role exposure
- private Storage buckets
- short-lived signed URLs
- no secret values in logs
- audit events for sensitive actions
- meaningful Super User override reasons
- no hard-delete of auditable records
- staging before production
- backup and restore readiness

For any issue, add an entry to:

```text
docs/07_OPEN_ITEMS.md
```

Report:

```text
Severity
Affected area
Evidence
Risk
Required fix
Verification step
```
