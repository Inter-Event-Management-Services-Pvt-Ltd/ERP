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
- [ ] Preserve existing folder hierarchy during import.

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
- [x] Assign file location.
- [x] Print label.
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

- [ ] Complete core workflow passes end-to-end.


## Agent Split

### Codex backend

- [x] Implement API, storage, archive jobs, integrity rules and tests. Backend code, Python tests, local Supabase reset and SQL probes are complete.

### Claude frontend

- [ ] Implement project list.
- [ ] Implement folder explorer.
- [ ] Implement upload interface.
- [ ] Implement preview drawer.
- [ ] Implement ZIP export status UI.
- [ ] Implement physical-file label and checkout screens.
- [ ] Validate responsive, accessibility and reduced-motion states.
