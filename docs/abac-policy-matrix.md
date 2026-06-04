# ABAC Policy Matrix

## Baseline

```text
Default outcome: DENY
```

Supabase RLS protects baseline reads. FastAPI evaluates write actions and complex conditions.

| Action | Default allowed users | Required conditions |
|---|---|---|
| View own attendance | Employee | `employee_id == current_employee_id` |
| View all attendance | Admin, Director, Super User | Permission `attendance.view_all` |
| Correct attendance | Admin, Super Admin | Permission `attendance.correct`; correction reason required |
| View project | Project member, Director, Super User | Active membership or override |
| Edit project | Manager, Super Admin | Permission `project.manage`; project access required |
| View document | Project member, Director, Super User | Project access and sufficient confidentiality clearance |
| Upload document | Contributor, Manager | `project_members.access_level in {CONTRIBUTE, MANAGE}` |
| Download document | Project member | Project access; signed URL expires quickly |
| Export project ZIP | Manager, archive-authorised user | Permission `archive.export`; project access |
| Move physical file | Archive-authorised user | Permission `archive.manage` |
| Check out physical file | Archive-authorised user | Permission `physical_file.checkout`; no open checkout |
| Approve document | Assigned approver, Director | Pending approval and permission `approval.approve` |
| View audit events | Super Admin, Director, Super User | Permission `audit.view` |
| Manage policies | Super Admin, Super User | Permission `policy.manage` |
| Override policy | Super User | Mandatory meaningful reason + immutable audit event |

## Director

```text
director@iemsnewdelhi.com
```

- Receives `DIRECTOR` and `SUPER_USER`
- Gets Director Dashboard access
- Can view company-wide data
- Must still provide an override reason for sensitive restricted operations
