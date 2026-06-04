# Frontend Design System

## Product Tone

The IEMS ERP should feel:

```text
professional
modern
calm
efficient
trustworthy
operational
```

It is not a consumer social app. Avoid decorative clutter.

## Design Workflow

Claude should use either Claude Design or Google Stitch to explore:

- information hierarchy
- dashboard layout
- file explorer patterns
- Director Dashboard density
- attendance states
- archive-room navigation
- responsive behaviour

Generated designs must be reviewed before implementation.

Do not paste generated code into production without:

- removing unsafe dependencies
- checking accessibility
- checking responsiveness
- checking data states
- checking motion behaviour
- checking security implications
- aligning with shared components

## Core Layout

```text
Desktop:
collapsible left navigation
top utility bar
content header
filter and action row
main content
optional right-side detail drawer

Mobile:
compact top bar
drawer navigation
single-column content
sticky primary action where useful
```

## UI Primitives

Prefer shared primitives:

```text
Button
IconButton
Input
Textarea
Select
Combobox
Checkbox
RadioGroup
Switch
Badge
Tooltip
Dialog
AlertDialog
Drawer
DropdownMenu
Tabs
Table
DataTable
Card
StatCard
Breadcrumb
Pagination
Skeleton
EmptyState
ErrorState
PermissionDenied
FilePreview
FolderTree
AuditTimeline
```

## Status Semantics

Use text and iconography in addition to visual styling.

Examples:

```text
ACTIVE
PENDING
APPROVED
REJECTED
OVERDUE
CHECKED_OUT
AVAILABLE
MISSING
UNDER_VERIFICATION
```

Never communicate critical state through color alone.

## Key Screens

### Employee Dashboard

- today's attendance
- assigned tasks
- upcoming calendar entries
- recent projects
- notifications

### Projects

- search
- filters
- project health
- client
- event date
- assigned team
- archive status

### Folder Explorer

- familiar folder tree
- breadcrumbs
- file table
- preview drawer
- upload
- version history
- offline export action
- physical archive metadata

### Director Dashboard

- scannable metrics
- alert prioritization
- project health table
- pending approvals
- overdue tasks
- attendance summary
- physical-file status
- audit feed

## Required States

Every screen must define:

```text
loading
empty
success
validation error
permission denied
server error
offline or degraded state where relevant
```
