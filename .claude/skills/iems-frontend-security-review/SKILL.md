---
name: iems-frontend-security-review
description: Use when reviewing IEMS ERP frontend authentication, protected routes, file downloads, forms, third-party packages, security headers, metadata exposure, error messages, or browser storage. Claude frontend-only skill.
---

# IEMS Frontend Security Review

Read:

- `docs/15_FRONTEND_SECURITY_MOTION.md`
- `docs/checklists/FRONTEND_CLAUDE.md`
- `docs/04_SECURITY_MODEL.md`

Check:

- no service-role key
- no secrets in client bundle
- no unsafe HTML rendering
- no unrestricted third-party scripts
- no sensitive metadata in logs
- no restricted data in hidden UI
- download URLs come from backend signed URL flow
- route guards are UX only, not authorization
- forms have client validation for usability
- backend remains authoritative
- security headers reviewed
- auth tokens are not unnecessarily persisted

Do not modify backend files.
