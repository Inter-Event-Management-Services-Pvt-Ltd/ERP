# Phase 2 Checklist — Document and Physical Archive Core

## Clients and Projects

- [x] Create client CRUD.
- [x] Soft-delete clients through audited deactivation.
- [x] Create project CRUD.
- [x] Soft-delete projects with audit history.
- [x] Create project-member assignment.
- [x] List active project members.
- [x] Update project-member access level.
- [x] Soft-remove project members.
- [x] Expose limited employee lookup for project-member assignment.
- [x] Expose project type, status and priority reference lookups.
- [x] Apply folder template.
- [x] Render folder tree.
- [x] Preserve existing folder hierarchy during archive export, including empty folders.

## Documents

- [x] Upload document.
- [x] Validate file name.
- [x] Validate MIME type.
- [x] Validate size.
- [x] Store immutable object key.
- [x] Create document version.
- [x] Generate checksum.
- [x] Download through signed URL.
- [x] Preview supported files.
- [x] Add duplicate warning.

## Offline Archive

- [x] Generate ZIP asynchronously.
- [x] Preserve folder hierarchy.
- [x] Record exact exported versions.
- [x] Generate manifest.
- [x] Generate document index PDF.
- [x] Generate QR label.
- [x] Add export expiration.
- [x] Add export notification.

## Physical Archive

- [x] Create rooms.
- [x] Create racks, shelves, cabinets, boxes and file slots.
- [x] List locations by archive room for hierarchy browsing.
- [x] Assign file location.
- [x] List project physical files.
- [x] Print label.
- [x] Resolve scanned physical-file QR tokens through authenticated API.
- [x] Check out file.
- [x] Return file.
- [x] Record movement.
- [x] Prevent double checkout.
- [x] Add verification workflow.

## Security Gate

- [x] All buckets remain private.
- [x] Signed URLs expire quickly.
- [x] Upload actions enforce ABAC.
- [x] Download actions enforce ABAC.
- [x] ZIP exports enforce ABAC.
- [x] Physical checkout enforces ABAC.
- [x] Audit events exist for upload, download, export, move, checkout and return.
- [x] File-type restrictions are documented.
- [x] Malware-scanning decision is recorded.

## Exit Criteria

- [x] Backend core workflow passes end-to-end through API tests, local Supabase reset, SQL probes and Celery worker validation.
- [ ] Full browser workflow passes end-to-end after Claude wires final backend refinements.


## Agent Split

### Codex backend

- [x] Implement API, storage, archive jobs, integrity rules and tests. Backend code, Python tests, local Supabase reset and SQL probes are complete.

### Claude frontend

- [x] Implement project list.
- [x] Implement folder explorer.
- [x] Implement upload interface.
- [x] Implement preview drawer.
- [x] Implement ZIP export status UI.
- [x] Implement physical-file label and checkout screens.
- [x] Validate responsive, accessibility and reduced-motion states.
