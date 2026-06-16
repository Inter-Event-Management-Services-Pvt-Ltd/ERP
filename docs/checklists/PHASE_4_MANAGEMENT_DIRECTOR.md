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
- [ ] Upcoming events.
- [x] Overdue tasks.
- [x] Pending approvals.
- [ ] Missing required documents.
- [x] Checked-out physical files.
- [x] Overdue physical returns.
- [ ] Verification reminders.
- [x] Recent audit activity.

## Admin

- [ ] Employee management.
- [ ] Role assignment.
- [ ] Department history.
- [ ] Folder-template editor.
- [ ] Archive-location editor.
- [ ] Policy management.
- [ ] Audit explorer.

## Security Gate

- [x] Director Dashboard requires Director or authorized Super User.
- [x] Restricted records still log sensitive access.
- [ ] Super User overrides require reason.
- [ ] Policy changes create audit events.
- [x] Approval actions create audit events.
- [ ] Admin cannot silently elevate themselves to Super User.

## Exit Criteria

- [ ] Director can monitor operations from one dashboard.


## Agent Split

### Codex backend

- [ ] Implement Director metrics queries, endpoints, audit access and approval workflows.
  - [x] Director dashboard read metrics and audit-access endpoints.
  - [x] Approval write workflows.
  - [ ] Admin and policy management endpoints.

### Claude frontend

- [ ] Design Director Dashboard using either Claude Design or Google Stitch.
- [ ] Implement scannable executive metrics.
- [ ] Implement alert prioritization.
- [ ] Implement project health tables.
- [ ] Implement approval queue.
- [ ] Implement archive monitoring.
- [ ] Implement audit timeline.
- [ ] Validate accessibility and reduced-motion behaviour.
