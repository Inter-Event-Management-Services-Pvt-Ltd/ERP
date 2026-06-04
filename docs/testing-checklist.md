# Testing Checklist

## Database Constraints

- Duplicate employee email rejected
- One active department assignment per employee
- One root folder per project
- Duplicate sibling folder names rejected
- Duplicate active document names in one folder rejected
- Immutable document versions use sequential numbers
- One open physical-file checkout per physical file
- One open attendance session per employee
- Invalid date ranges rejected
- Approval request must reference exactly one target

## RLS

- Employee can read own attendance
- Employee cannot read unrelated attendance
- Project member can read project folders
- Non-member cannot read project folders
- Director can read company-wide views
- Browser cannot write directly to private Storage buckets
- Generated archive access requires server-created signed URL

## Functional

- Create project and apply template
- Import folder tree
- Upload new document
- Create document version
- Generate ZIP preserving hierarchy
- Print label with QR
- Store physical file
- Check out and return physical file
- Audit event created for each sensitive operation
