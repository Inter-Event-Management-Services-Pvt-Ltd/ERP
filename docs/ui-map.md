# Next.js UI Map

## Public

```text
/login
/auth/callback
```

## Employee

```text
/dashboard
/attendance
/leave
/tasks
/calendar
/projects
/projects/[projectId]
/projects/[projectId]/documents
/documents/[documentId]
/notifications
```

## Physical Archive

```text
/archive
/archive/rooms
/archive/rooms/[roomId]
/archive/files/[physicalFileId]
/archive/files/[physicalFileId]/checkout
/archive/files/[physicalFileId]/return
/archive/files/[physicalFileId]/verify
```

## Approvals

```text
/approvals
/approvals/[approvalId]
```

## Admin

```text
/admin
/admin/employees
/admin/departments
/admin/roles
/admin/policies
/admin/folder-templates
/admin/archive-locations
/admin/audit
```

## Director

```text
/director
/director/projects
/director/attendance
/director/tasks
/director/calendar
/director/approvals
/director/archive
/director/audit
```

## Critical UX Flow

```text
Create client
→ Create event project
→ Apply folder template
→ Upload existing folders or documents
→ Assign project team
→ Generate offline ZIP export
→ Print folder label and index sheet
→ Assign physical room/rack/shelf/box
→ Check out and return physical file by QR scan
```
