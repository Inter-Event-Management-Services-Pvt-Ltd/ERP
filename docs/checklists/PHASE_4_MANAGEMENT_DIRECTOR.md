# Phase 4 Checklist — Management and Director Controls

## Approvals

- [x] Document approval.
- [x] Project closure approval.
- [x] Archive closure approval.
- [x] Leave approval.
- [x] Revision request.
- [x] Approval comment history.

## Director Dashboard

- [x] Attendance metrics.
- [x] Active-project metrics.
- [x] Upcoming events.
- [x] Overdue tasks.
- [x] Pending approvals.
- [x] Missing required documents.
- [x] Checked-out physical files.
- [x] Overdue physical returns.
- [x] Verification reminders.
- [x] Recent audit activity.

## Admin

- [x] Employee management.
- [x] Role assignment.
- [x] Department history.
- [x] Folder-template editor.
- [x] Archive-location editor.
- [x] Policy management.
- [x] Audit explorer.

## Security Gate

- [x] Director Dashboard requires Director or authorized Super User.
- [x] Restricted records still log sensitive access.
- [x] Super User overrides require reason.
- [x] Policy changes create audit events.
- [x] Approval actions create audit events.
- [x] Admin cannot silently elevate themselves to Super User.

## Exit Criteria

- [ ] Director can monitor operations from one dashboard.


## Agent Split

### Codex backend

- [x] Implement Director metrics queries, endpoints, audit access and approval workflows.
  - [x] Director dashboard read metrics and audit-access endpoints.
  - [x] Approval write workflows.
  - [x] Admin and policy management endpoints.

### Claude frontend

- [ ] Design Director Dashboard using either Claude Design or Google Stitch.
- [ ] Implement scannable executive metrics.
- [ ] Implement alert prioritization.
- [ ] Implement project health tables.
- [ ] Implement approval queue.
- [ ] Implement archive monitoring.
- [ ] Implement audit timeline.
- [ ] Validate accessibility and reduced-motion behaviour.
