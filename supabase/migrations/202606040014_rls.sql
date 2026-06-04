-- IEMS ERP: baseline RLS policies
--
-- The public schema is exposed through Supabase's Data API. Every public table
-- must have RLS enabled. Tables without explicit policies remain default-deny
-- for anon/authenticated clients; sensitive writes go through FastAPI using the
-- service role after RBAC/ABAC validation and audit logging.
alter table public.employees enable row level security;
alter table public.user_accounts enable row level security;
alter table public.employee_department_assignments enable row level security;
alter table public.roles enable row level security;
alter table public.permissions enable row level security;
alter table public.role_permissions enable row level security;
alter table public.user_role_assignments enable row level security;
alter table public.attribute_definitions enable row level security;
alter table public.employee_attribute_values enable row level security;
alter table public.policies enable row level security;
alter table public.super_user_overrides enable row level security;
alter table public.departments enable row level security;
alter table public.project_types enable row level security;
alter table public.project_statuses enable row level security;
alter table public.priority_levels enable row level security;
alter table public.document_types enable row level security;
alter table public.confidentiality_levels enable row level security;
alter table public.leave_types enable row level security;
alter table public.task_statuses enable row level security;
alter table public.approval_types enable row level security;
alter table public.clients enable row level security;
alter table public.client_contacts enable row level security;
alter table public.projects enable row level security;
alter table public.project_members enable row level security;
alter table public.folder_templates enable row level security;
alter table public.folder_template_items enable row level security;
alter table public.folders enable row level security;
alter table public.documents enable row level security;
alter table public.document_versions enable row level security;
alter table public.tags enable row level security;
alter table public.document_tag_assignments enable row level security;
alter table public.document_metadata enable row level security;
alter table public.archive_exports enable row level security;
alter table public.archive_export_items enable row level security;
alter table public.archive_rooms enable row level security;
alter table public.archive_locations enable row level security;
alter table public.physical_files enable row level security;
alter table public.physical_file_checkouts enable row level security;
alter table public.physical_file_movements enable row level security;
alter table public.archive_verifications enable row level security;
alter table public.attendance_sessions enable row level security;
alter table public.leave_requests enable row level security;
alter table public.tasks enable row level security;
alter table public.task_assignees enable row level security;
alter table public.task_comments enable row level security;
alter table public.task_document_links enable row level security;
alter table public.calendar_events enable row level security;
alter table public.calendar_event_attendees enable row level security;
alter table public.approval_requests enable row level security;
alter table public.approval_actions enable row level security;
alter table public.notifications enable row level security;
alter table public.audit_events enable row level security;

create policy employees_read_self_or_privileged
on public.employees for select
using (
  id = public.current_employee_id()
  or public.is_super_user()
  or public.has_permission('employee.view')
);

create policy user_accounts_read_self
on public.user_accounts for select
using (id = (select auth.uid()) or public.is_super_user());

create policy projects_read_accessible
on public.projects for select
using (public.has_project_access(id));

create policy project_members_read_accessible
on public.project_members for select
using (public.has_project_access(project_id));

create policy folders_read_accessible
on public.folders for select
using (public.has_project_access(project_id));

create policy documents_read_accessible
on public.documents for select
using (public.has_project_access(project_id));

create policy document_versions_read_accessible
on public.document_versions for select
using (
  exists (
    select 1 from public.documents d
    where d.id = document_versions.document_id
      and public.has_project_access(d.project_id)
  )
);

create policy attendance_read_own_or_privileged
on public.attendance_sessions for select
using (
  employee_id = public.current_employee_id()
  or public.is_super_user()
  or public.has_permission('attendance.view_all')
);

create policy leave_read_own_or_privileged
on public.leave_requests for select
using (
  employee_id = public.current_employee_id()
  or public.is_super_user()
  or public.has_permission('leave.review')
);

create policy tasks_read_assigned_project_or_privileged
on public.tasks for select
using (
  public.is_super_user()
  or public.has_project_access(project_id)
  or exists (
    select 1 from public.task_assignees ta
    where ta.task_id = tasks.id
      and ta.employee_id = public.current_employee_id()
  )
);

create policy task_assignees_read_visible_tasks
on public.task_assignees for select
using (
  exists (
    select 1 from public.tasks t
    where t.id = task_assignees.task_id
      and (
        public.is_super_user()
        or public.has_project_access(t.project_id)
        or task_assignees.employee_id = public.current_employee_id()
      )
  )
);

create policy calendar_read_project_or_privileged
on public.calendar_events for select
using (
  public.is_super_user()
  or project_id is null
  or public.has_project_access(project_id)
);

create policy approvals_read_involved_or_privileged
on public.approval_requests for select
using (
  public.is_super_user()
  or requested_by = public.current_employee_id()
  or assigned_to = public.current_employee_id()
  or public.has_permission('approval.view_all')
);

create policy notifications_read_own
on public.notifications for select
using (employee_id = public.current_employee_id() or public.is_super_user());

create policy audit_read_privileged
on public.audit_events for select
using (public.is_super_user() or public.has_permission('audit.view'));

create policy physical_files_read_project_or_privileged
on public.physical_files for select
using (public.is_super_user() or public.has_project_access(project_id) or public.has_permission('archive.view'));

create policy physical_checkouts_read_privileged
on public.physical_file_checkouts for select
using (
  public.is_super_user()
  or checked_out_by = public.current_employee_id()
  or public.has_permission('archive.view')
);

-- Writes should go through FastAPI using the service role after ABAC validation.
