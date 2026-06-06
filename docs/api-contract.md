# FastAPI REST Contract

All writes go through FastAPI. Each protected route performs JWT validation, RBAC/ABAC evaluation, transaction handling and audit logging.

## Platform

```text
GET    /health
GET    /ready
```

Browser clients are allowed from explicit configured origins only. Local
development defaults to:

```text
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

`GET /health` returns service liveness:

```json
{
  "status": "ok",
  "service": "iems-erp-api",
  "version": "0.1.0"
}
```

`GET /ready` returns API readiness checks:

```json
{
  "status": "ready",
  "checks": {
    "api": "ok"
  }
}
```

## Error Envelope

API errors use a stable envelope:

```json
{
  "error": {
    "code": "AUTH_REQUIRED",
    "message": "Authentication required",
    "request_id": "request-id"
  }
}
```

Validation errors may include field-level details without echoing submitted
input values:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "request_id": "request-id",
    "fields": [
      {
        "field": "body.client_id",
        "message": "Input should be a valid UUID",
        "type": "uuid_parsing"
      }
    ]
  }
}
```

The API returns `X-Request-ID` on responses. If the client sends `X-Request-ID`, the same value is echoed.

Stable platform/auth errors:

| HTTP status | Code | Meaning |
|---|---|---|
| 401 | `AUTH_REQUIRED` | Protected route called without an `Authorization` header |
| 401 | `INVALID_TOKEN` | JWT is missing required claims, expired, malformed, or has an invalid signature |
| 403 | `EMAIL_DOMAIN_NOT_ALLOWED` | Supabase user email is outside the approved IEMS domain |
| 403 | `ACCOUNT_NOT_APPROVED` | Supabase user is valid but not linked to an approved employee account |
| 403 | `ACCOUNT_DISABLED` | Linked user account or employee record is disabled |
| 403 | `ACCOUNT_EMAIL_MISMATCH` | JWT email does not match the linked employee official email |
| 403 | `PERMISSION_DENIED` | Authenticated user does not have the required RBAC permission |
| 403 | `ABAC_DENIED` | Authenticated user failed contextual ABAC authorization |
| 403 | `SUPER_USER_REQUIRED` | Sensitive override operation requires a Super User account |
| 403 | `SUPER_USER_OVERRIDE_REASON_REQUIRED` | Sensitive override operation is missing a meaningful override reason |
| 404 | `NOT_FOUND` | Route or resource not found |
| 422 | `VALIDATION_ERROR` | Request validation failed |
| 422 | `INVALID_REFERENCE` | Request referenced an inactive or missing related resource |
| 422 | `INVALID_STATE` | Request violates a business or database state constraint |
| 422 | `INVALID_FILE_NAME` | Uploaded file name failed server-side validation |
| 422 | `INVALID_MIME_TYPE` | Uploaded file MIME type is not allowed |
| 422 | `INVALID_FILE_SIZE` | Uploaded file is empty or larger than the configured limit |
| 409 | `RESOURCE_CONFLICT` | Unique client, project, folder, or member constraint would be violated |
| 409 | `INVALID_PROJECT_MEMBER_STATE` | Project-member change would leave the project without an active manager |
| 409 | `INVALID_PHYSICAL_FILE_STATE` | Physical file checkout, return or move is invalid for the current state |
| 503 | `AUDIT_NOT_CONFIGURED` | Required audit writer settings are missing |
| 503 | `AUDIT_WRITE_FAILED` | Backend failed to write the required audit event |
| 503 | `AUTH_NOT_CONFIGURED` | Required Supabase auth or employee-resolution settings are missing |
| 503 | `AUTH_RESOLUTION_FAILED` | Backend could not resolve the current employee context |
| 503 | `DATA_SERVICE_NOT_CONFIGURED` | Required Supabase data-service settings are missing |
| 503 | `DATA_SERVICE_ERROR` | Backend Supabase data request failed |
| 503 | `DATA_SERVICE_INVALID_RESPONSE` | Backend Supabase data response did not match the expected schema |

## Auth and Current User

```text
GET    /v1/me
GET    /v1/me/permissions
GET    /v1/me/notifications
PATCH  /v1/me/notifications/{notification_id}/read
```

`GET /v1/me` requires `Authorization: Bearer <Supabase access token>`.

Successful response:

```json
{
  "auth_user_id": "11111111-1111-4111-8111-111111111111",
  "account": {
    "is_active": true,
    "is_super_user": false
  },
  "employee": {
    "id": "22222222-2222-4222-8222-222222222222",
    "employee_code": "IEMS-001",
    "full_name": "Example Employee",
    "official_email": "employee@iemsnewdelhi.com",
    "designation": "Coordinator",
    "employment_status": "ACTIVE"
  },
  "roles": ["EMPLOYEE"],
  "permissions": ["document.download", "document.view", "project.view"]
}
```

The backend resolves `roles` and `permissions` from database role assignments.
The frontend must not trust editable Supabase user metadata for authorization.
Approved email domains are configured server-side. `ALLOWED_EMAIL_DOMAIN`
remains the default single-domain setting; `ALLOWED_EMAIL_DOMAINS` can be set to
a comma-separated allowlist for local or staging environments. A valid JWT still
must resolve to an active approved employee account with a matching official
email.

`GET /v1/me/permissions` requires `Authorization: Bearer <Supabase access token>`.

Successful response:

```json
{
  "roles": ["EMPLOYEE"],
  "permissions": ["document.download", "document.view", "project.view"],
  "is_super_user": false,
  "super_user_requires_reason": true
}
```

`is_super_user` means the backend may allow privileged operations only through
server-side checks. Sensitive override operations still require
`X-IEMS-Override-Reason`; frontend permission data is for navigation and UI
state only.

## Employees and Departments

```text
GET    /v1/employees
POST   /v1/employees
GET    /v1/employees/{employee_id}
PATCH  /v1/employees/{employee_id}
POST   /v1/employees/{employee_id}/roles
DELETE /v1/employees/{employee_id}/roles/{role_id}
POST   /v1/employees/{employee_id}/department-assignments
```

`GET /v1/employees` returns a limited employee directory for assignment and
administrative lookup.

Query parameters:

```text
status=ACTIVE|ON_LEAVE|INACTIVE|EXITED  default ACTIVE
search=<employee code, name, email or designation>
limit=1..100                            default 50
offset=0..n                             default 0
```

Users with `employee.view` can filter by any employment status. Users with
`project.manage` but without `employee.view` can only list assignable employees
with `ACTIVE` or `ON_LEAVE` status.

Response:

```json
[
  {
    "id": "22222222-2222-4222-8222-222222222222",
    "employee_code": "IEMS-001",
    "full_name": "Example Employee",
    "official_email": "employee@iemsnewdelhi.com",
    "designation": "Coordinator",
    "employment_status": "ACTIVE"
  }
]
```

## Attendance and Leave

```text
POST   /v1/attendance/check-in
POST   /v1/attendance/check-out
GET    /v1/attendance/me
GET    /v1/attendance/team
PATCH  /v1/attendance/sessions/{session_id}
POST   /v1/leave-requests
GET    /v1/leave-requests/me
GET    /v1/leave-requests/pending
POST   /v1/leave-requests/{request_id}/approve
POST   /v1/leave-requests/{request_id}/reject
```

## Clients and Projects

```text
GET    /v1/clients
POST   /v1/clients
GET    /v1/clients/{client_id}
PATCH  /v1/clients/{client_id}
DELETE /v1/clients/{client_id}

GET    /v1/project-types
GET    /v1/project-statuses
GET    /v1/priority-levels

GET    /v1/projects
POST   /v1/projects
GET    /v1/projects/{project_id}
PATCH  /v1/projects/{project_id}
DELETE /v1/projects/{project_id}
GET    /v1/projects/{project_id}/members
POST   /v1/projects/{project_id}/members
PATCH  /v1/projects/{project_id}/members/{employee_id}
DELETE /v1/projects/{project_id}/members/{employee_id}
```

Read routes require `project.view` or `project.manage`.
Write routes require `project.manage`.

Project-specific writes also require contextual project access:

```text
Super User
or active project member with MANAGE access
```

Non-manager project listing is scoped to active project membership. Client listing
is visible to users with project read/manage permission; confirm stricter client
visibility in `docs/07_OPEN_ITEMS.md` before production if needed.

Client response:

```json
{
  "id": "44444444-4444-4444-8444-444444444444",
  "client_code": "ACME",
  "legal_name": "Acme Events Private Limited",
  "display_name": "Acme Events",
  "is_active": true,
  "notes": "Preferred Delhi NCR client",
  "created_at": "2026-06-05T09:00:00Z",
  "updated_at": "2026-06-05T09:30:00Z"
}
```

`DELETE /v1/clients/{client_id}` deactivates the client by setting
`is_active=false`; it never hard-deletes client or project history. The route
requires `project.manage` and writes a `client.deactivated` audit event.

Reference lookup response:

```json
[
  {
    "id": "66666666-6666-4666-8666-666666666666",
    "code": "CONFERENCE",
    "name": "Conference"
  }
]
```

Project response:

```json
{
  "id": "55555555-5555-4555-8555-555555555555",
  "project_code": "IEMS-2026-001",
  "client_id": "44444444-4444-4444-8444-444444444444",
  "client": {
    "id": "44444444-4444-4444-8444-444444444444",
    "client_code": "ACME",
    "display_name": "Acme Events"
  },
  "project_type_id": "66666666-6666-4666-8666-666666666666",
  "project_type": {
    "id": "66666666-6666-4666-8666-666666666666",
    "code": "CONFERENCE",
    "name": "Conference"
  },
  "project_status_id": "77777777-7777-4777-8777-777777777777",
  "project_status": {
    "id": "77777777-7777-4777-8777-777777777777",
    "code": "PLANNING",
    "name": "Planning"
  },
  "priority_level_id": "88888888-8888-4888-8888-888888888888",
  "priority_level": {
    "id": "88888888-8888-4888-8888-888888888888",
    "code": "NORMAL",
    "name": "Normal"
  },
  "name": "Annual Leadership Conference",
  "event_date": "2026-08-12",
  "venue": "New Delhi",
  "description": "Annual client conference",
  "project_manager_id": "22222222-2222-4222-8222-222222222222",
  "created_by": "22222222-2222-4222-8222-222222222222",
  "created_at": "2026-06-05T09:00:00Z",
  "updated_at": "2026-06-05T09:30:00Z",
  "archived_at": null,
  "deleted_at": null,
  "root_folder_id": "99999999-9999-4999-8999-999999999999"
}
```

`POST /v1/projects` creates the project, assigns the creator and selected
`project_manager_id` as active `MANAGE` project members, applies the selected or
default folder template, and writes `project.created` in one database
transaction.

`GET /v1/projects/{project_id}/members` returns active project members visible
to a project reader. Users with only `project.view` must also be active members
of the project. Users with `project.manage` can read project-member lists across
projects.

`DELETE /v1/projects/{project_id}` soft-deletes the project by setting
`deleted_at`; it never hard-deletes project history. The route requires
`project.manage`; non-Super User managers must also have active `MANAGE`
membership on the project. The backend writes a `project.deleted` audit event.
Soft-deleted projects are excluded from normal project list/detail responses.

Project-member detail response:

```json
[
  {
    "project_id": "55555555-5555-4555-8555-555555555555",
    "employee_id": "22222222-2222-4222-8222-222222222222",
    "employee": {
      "id": "22222222-2222-4222-8222-222222222222",
      "employee_code": "IEMS-001",
      "full_name": "Example Employee"
    },
    "access_level": "MANAGE",
    "assigned_by": "22222222-2222-4222-8222-222222222222",
    "assigned_at": "2026-06-05T09:00:00Z",
    "removed_at": null
  }
]
```

`PATCH /v1/projects/{project_id}/members/{employee_id}` changes an active
member's `access_level` to `VIEW`, `CONTRIBUTE` or `MANAGE`. It requires
`project.manage`; non-Super User managers must have active `MANAGE` membership
on the project. The backend writes a `project.member_updated` audit event and
rejects changes that would leave the project without an active `MANAGE` member.

`DELETE /v1/projects/{project_id}/members/{employee_id}` soft-removes the
member by setting `removed_at`; it does not hard-delete assignment history.

## Folder and Document Management

```text
GET    /v1/projects/{project_id}/folders/tree
POST   /v1/projects/{project_id}/folders
PATCH  /v1/folders/{folder_id}
DELETE /v1/folders/{folder_id}

GET    /v1/confidentiality-levels
GET    /v1/document-types
POST   /v1/folders/{folder_id}/documents
GET    /v1/documents/{document_id}
POST   /v1/documents/{document_id}/versions
GET    /v1/document-versions/{version_id}/download-url
GET    /v1/documents/search
```

`GET /v1/projects/{project_id}/folders/tree` requires `project.view` or
`project.manage` and returns the active folder hierarchy:

```json
{
  "id": "99999999-9999-4999-8999-999999999999",
  "project_id": "55555555-5555-4555-8555-555555555555",
  "parent_folder_id": null,
  "name": "IEMS-2026-001",
  "sort_order": 0,
  "children": []
}
```

Folder writes require `project.manage` and active `MANAGE` membership on the
project unless the caller is a Super User. Folder deletes are soft deletes and
are rejected while active child folders or documents exist.

`POST /v1/folders/{folder_id}/documents` accepts multipart form data:

```text
file=<binary file>                    required
confidentiality_level_id=<uuid>        required
document_type_id=<uuid>                optional
display_name=<text>                    optional, defaults to file name
change_note=<text>                     optional
```

`GET /v1/confidentiality-levels` and `GET /v1/document-types` return reference
options as:

```json
[
  {
    "id": "77777777-7777-4777-8777-777777777777",
    "code": "GENERAL",
    "name": "General"
  }
]
```

Uploads require `document.upload` plus active `CONTRIBUTE` or `MANAGE`
membership on the project. FastAPI validates file name, MIME type and size,
stores the object in the private `project-documents` bucket using an immutable
`project/document/version/file` key, records a SHA-256 checksum, creates version
1, and writes `document.uploaded`.

`POST /v1/documents/{document_id}/versions` accepts multipart form data:

```text
file=<binary file>                    required
change_note=<text>                     optional
```

It creates the next immutable version and writes `document.version_created`.

Document response:

```json
{
  "id": "55555555-5555-4555-8555-555555555555",
  "project_id": "33333333-3333-4333-8333-333333333333",
  "folder_id": "44444444-4444-4444-8444-444444444444",
  "document_type_id": null,
  "confidentiality_level_id": "77777777-7777-4777-8777-777777777777",
  "display_name": "brief.pdf",
  "status": "ACTIVE",
  "latest_version": {
    "id": "66666666-6666-4666-8666-666666666666",
    "version_number": 1,
    "storage_bucket": "project-documents",
    "storage_key": "project/document/version/brief.pdf",
    "original_filename": "brief.pdf",
    "mime_type": "application/pdf",
    "size_bytes": 12345,
    "checksum_sha256": "64-character-sha256-hex",
    "preview_supported": true
  }
}
```

`GET /v1/documents/search` supports:

```text
project_id=<uuid>    optional project scope
folder_id=<uuid>     optional folder scope
search=<text>        optional search term
q=<text>             optional alias for search
limit=<1..100>       default 50
offset=<integer>     default 0
```

`GET /v1/document-versions/{version_id}/download-url` requires
`document.download` and project access, records `document.downloaded`, and
returns a short-lived signed URL:

```json
{
  "url": "http://127.0.0.1:54321/storage/v1/object/sign/...",
  "expires_in_seconds": 900,
  "expires_at": "2026-06-06T08:15:00Z"
}
```

## Offline Archive Export

```text
POST   /v1/projects/{project_id}/exports
GET    /v1/projects/{project_id}/exports
GET    /v1/exports/{export_id}
GET    /v1/exports/{export_id}/download-url
POST   /v1/exports/{export_id}/cancel
```

Archive exports require `archive.export` and active project `MANAGE` access.
`POST /v1/projects/{project_id}/exports` returns `202 Accepted` with status
`QUEUED` and enqueues the Celery ZIP generator. The worker records exact latest
document versions, preserves the database folder hierarchy as ZIP paths,
including explicit entries for empty folders, includes `manifest.json` and
`document-index.pdf`, stores the ZIP in the private `generated-archives` bucket,
writes `archive.export_completed`, and notifies the requester. `GET
/v1/exports/{export_id}/download-url` returns a short-lived signed URL only when
the export is `READY` and unexpired. Returned URLs include the Supabase Storage
`/storage/v1/object/sign/...` path. `POST /v1/exports/{export_id}/cancel`
cancels only `QUEUED` exports and returns status `CANCELLED`; other export
states return `INVALID_STATE`.

## Physical Archive

```text
GET    /v1/archive/rooms
POST   /v1/archive/rooms
POST   /v1/archive/locations
GET    /v1/archive/locations/{location_id}/contents

POST   /v1/projects/{project_id}/physical-files
GET    /v1/physical-files/{physical_file_id}
POST   /v1/physical-files/{physical_file_id}/checkout
POST   /v1/physical-files/{physical_file_id}/return
POST   /v1/physical-files/{physical_file_id}/move
POST   /v1/physical-files/{physical_file_id}/verify
GET    /v1/physical-files/{physical_file_id}/label
```

Physical archive writes require `archive.manage`, except checkout which requires
`physical_file.checkout`. Creating a physical file also requires project
`MANAGE` access. Location hierarchy is enforced as:

```text
RACK -> SHELF -> CABINET -> BOX -> FILE_SLOT
```

Physical files can only be assigned to active `FILE_SLOT` locations. Checkout is
transactional, writes a movement row and audit event, and the database prevents
a second open checkout. Return, move and verification also write movement or
verification history plus audit events. Labels return printable metadata and the
file QR token; frontend can render the QR code from that token.

## Tasks and Calendar

```text
GET    /v1/tasks
POST   /v1/tasks
GET    /v1/tasks/{task_id}
PATCH  /v1/tasks/{task_id}
POST   /v1/tasks/{task_id}/assignees
POST   /v1/tasks/{task_id}/comments

GET    /v1/calendar/events
POST   /v1/calendar/events
PATCH  /v1/calendar/events/{event_id}
```

## Approvals

```text
GET    /v1/approvals
POST   /v1/approvals
GET    /v1/approvals/{approval_id}
POST   /v1/approvals/{approval_id}/approve
POST   /v1/approvals/{approval_id}/reject
POST   /v1/approvals/{approval_id}/request-revision
```

## Director Dashboard

```text
GET    /v1/director/overview
GET    /v1/director/attendance
GET    /v1/director/projects
GET    /v1/director/approvals
GET    /v1/director/overdue-tasks
GET    /v1/director/physical-files
GET    /v1/director/audit-events
```

## Super User Override Header

Sensitive override routes require:

```text
X-IEMS-Override-Reason: <meaningful reason>
```

FastAPI records the reason in `super_user_overrides` and `audit_events`.
