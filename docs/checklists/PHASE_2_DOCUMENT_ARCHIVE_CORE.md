# Phase 2 Checklist — Document and Physical Archive Core

## Clients and Projects

- [ ] Create client CRUD.
- [ ] Create project CRUD.
- [ ] Create project-member assignment.
- [ ] Apply folder template.
- [ ] Render folder tree.
- [ ] Preserve existing folder hierarchy during import.

## Documents

- [ ] Upload document.
- [ ] Validate file name.
- [ ] Validate MIME type.
- [ ] Validate size.
- [ ] Store immutable object key.
- [ ] Create document version.
- [ ] Generate checksum.
- [ ] Download through signed URL.
- [ ] Preview supported files.
- [ ] Add duplicate warning.

## Offline Archive

- [ ] Generate ZIP asynchronously.
- [ ] Preserve folder hierarchy.
- [ ] Record exact exported versions.
- [ ] Generate manifest.
- [ ] Generate document index PDF.
- [ ] Generate QR label.
- [ ] Add export expiration.
- [ ] Add export notification.

## Physical Archive

- [ ] Create rooms.
- [ ] Create racks, shelves, cabinets, boxes and file slots.
- [ ] Assign file location.
- [ ] Print label.
- [ ] Check out file.
- [ ] Return file.
- [ ] Record movement.
- [ ] Prevent double checkout.
- [ ] Add verification workflow.

## Security Gate

- [ ] All buckets remain private.
- [ ] Signed URLs expire quickly.
- [ ] Upload actions enforce ABAC.
- [ ] Download actions enforce ABAC.
- [ ] ZIP exports enforce ABAC.
- [ ] Physical checkout enforces ABAC.
- [ ] Audit events exist for upload, download, export, move, checkout and return.
- [ ] File-type restrictions are documented.
- [ ] Malware-scanning decision is recorded.

## Exit Criteria

- [ ] Complete core workflow passes end-to-end.


## Agent Split

### Codex backend

- [ ] Implement API, storage, archive jobs, integrity rules and tests.

### Claude frontend

- [ ] Implement project list.
- [ ] Implement folder explorer.
- [ ] Implement upload interface.
- [ ] Implement preview drawer.
- [ ] Implement ZIP export status UI.
- [ ] Implement physical-file label and checkout screens.
- [ ] Validate responsive, accessibility and reduced-motion states.
