# FastAPI REST Contract

All writes go through FastAPI. Each protected route performs JWT validation, RBAC/ABAC evaluation, transaction handling and audit logging.

## Auth and Current User

```text
GET    /v1/me
GET    /v1/me/permissions
GET    /v1/me/notifications
PATCH  /v1/me/notifications/{notification_id}/read
```

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

GET    /v1/projects
POST   /v1/projects
GET    /v1/projects/{project_id}
PATCH  /v1/projects/{project_id}
POST   /v1/projects/{project_id}/members
DELETE /v1/projects/{project_id}/members/{employee_id}
```

## Folder and Document Management

```text
GET    /v1/projects/{project_id}/folders/tree
POST   /v1/projects/{project_id}/folders
PATCH  /v1/folders/{folder_id}
DELETE /v1/folders/{folder_id}

POST   /v1/folders/{folder_id}/documents
GET    /v1/documents/{document_id}
POST   /v1/documents/{document_id}/versions
GET    /v1/document-versions/{version_id}/download-url
GET    /v1/documents/search
```

## Offline Archive Export

```text
POST   /v1/projects/{project_id}/exports
GET    /v1/projects/{project_id}/exports
GET    /v1/exports/{export_id}
GET    /v1/exports/{export_id}/download-url
```

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
