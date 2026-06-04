---
name: iems-physical-archive-integrity
description: Use when implementing or reviewing IEMS ERP physical archive locations, QR labels, file movements, checkout, return, verification, or offline export manifests. Codex backend-only skill.
---

# IEMS Physical Archive Integrity

Read:

- `docs/03_DATABASE_DESIGN.md`
- `docs/checklists/PHASE_2_DOCUMENT_ARCHIVE_CORE.md`
- `docs/checklists/BACKEND_CODEX.md`

Protect:

- room, rack, shelf, cabinet, box, and file-slot hierarchy
- no hierarchy cycles
- one open checkout per physical file
- transactional checkout and return
- physical movement history
- QR token uniqueness
- archive verification history
- exact export manifest versions
- audit logging

Test:

- second checkout rejected
- invalid return rejected
- invalid location move rejected
- movement log written
- audit event written
