-- Move RLS helper functions behind a non-exposed schema. Browser roles still
-- need EXECUTE for policy evaluation, but direct calls are blocked because the
-- schema itself is not exposed to anon/authenticated.

create schema if not exists app_private;

revoke all on schema app_private from public, anon, authenticated;
grant usage on schema app_private to service_role;

create or replace function app_private.current_employee_id()
returns uuid
language sql
stable
security definer
set search_path = public, pg_catalog
as $$
  select ua.employee_id
  from public.user_accounts ua
  where ua.id = (select auth.uid())
    and ua.is_active = true
  limit 1
$$;

create or replace function app_private.is_super_user()
returns boolean
language sql
stable
security definer
set search_path = public, pg_catalog
as $$
  select coalesce((
    select ua.is_super_user
    from public.user_accounts ua
    where ua.id = (select auth.uid()) and ua.is_active = true
  ), false)
$$;

create or replace function app_private.has_permission(permission_code text)
returns boolean
language sql
stable
security definer
set search_path = public, pg_catalog
as $$
  select app_private.is_super_user() or exists (
    select 1
    from public.user_role_assignments ura
    join public.role_permissions rp on rp.role_id = ura.role_id
    join public.permissions p on p.id = rp.permission_id
    where ura.user_account_id = (select auth.uid())
      and (ura.expires_at is null or ura.expires_at > now())
      and p.code = permission_code
  )
$$;

create or replace function app_private.has_project_access(target_project_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public, pg_catalog
as $$
  select app_private.is_super_user() or exists (
    select 1
    from public.project_members pm
    where pm.project_id = target_project_id
      and pm.employee_id = app_private.current_employee_id()
      and pm.removed_at is null
  )
$$;

revoke all on function app_private.current_employee_id() from public, anon, authenticated;
revoke all on function app_private.is_super_user() from public, anon, authenticated;
revoke all on function app_private.has_permission(text) from public, anon, authenticated;
revoke all on function app_private.has_project_access(uuid) from public, anon, authenticated;

grant execute on function app_private.current_employee_id() to authenticated, service_role;
grant execute on function app_private.is_super_user() to authenticated, service_role;
grant execute on function app_private.has_permission(text) to authenticated, service_role;
grant execute on function app_private.has_project_access(uuid) to authenticated, service_role;

alter policy employees_read_self_or_privileged
on public.employees
using (
  id = app_private.current_employee_id()
  or app_private.is_super_user()
  or app_private.has_permission('employee.view')
);

alter policy user_accounts_read_self
on public.user_accounts
using (id = (select auth.uid()) or app_private.is_super_user());

alter policy projects_read_accessible
on public.projects
using (app_private.has_project_access(id));

alter policy project_members_read_accessible
on public.project_members
using (app_private.has_project_access(project_id));

alter policy folders_read_accessible
on public.folders
using (app_private.has_project_access(project_id));

alter policy documents_read_accessible
on public.documents
using (app_private.has_project_access(project_id));

alter policy document_versions_read_accessible
on public.document_versions
using (
  exists (
    select 1 from public.documents d
    where d.id = document_versions.document_id
      and app_private.has_project_access(d.project_id)
  )
);

alter policy attendance_read_own_or_privileged
on public.attendance_sessions
using (
  employee_id = app_private.current_employee_id()
  or app_private.is_super_user()
  or app_private.has_permission('attendance.view_all')
);

alter policy leave_read_own_or_privileged
on public.leave_requests
using (
  employee_id = app_private.current_employee_id()
  or app_private.is_super_user()
  or app_private.has_permission('leave.review')
);

alter policy tasks_read_assigned_project_or_privileged
on public.tasks
using (
  app_private.is_super_user()
  or app_private.has_project_access(project_id)
  or exists (
    select 1 from public.task_assignees ta
    where ta.task_id = tasks.id
      and ta.employee_id = app_private.current_employee_id()
  )
);

alter policy task_assignees_read_visible_tasks
on public.task_assignees
using (
  exists (
    select 1 from public.tasks t
    where t.id = task_assignees.task_id
      and (
        app_private.is_super_user()
        or app_private.has_project_access(t.project_id)
        or task_assignees.employee_id = app_private.current_employee_id()
      )
  )
);

alter policy calendar_read_project_or_privileged
on public.calendar_events
using (
  app_private.is_super_user()
  or project_id is null
  or app_private.has_project_access(project_id)
);

alter policy approvals_read_involved_or_privileged
on public.approval_requests
using (
  app_private.is_super_user()
  or requested_by = app_private.current_employee_id()
  or assigned_to = app_private.current_employee_id()
  or app_private.has_permission('approval.view_all')
);

alter policy notifications_read_own
on public.notifications
using (employee_id = app_private.current_employee_id() or app_private.is_super_user());

alter policy audit_read_privileged
on public.audit_events
using (app_private.is_super_user() or app_private.has_permission('audit.view'));

alter policy physical_files_read_project_or_privileged
on public.physical_files
using (
  app_private.is_super_user()
  or app_private.has_project_access(project_id)
  or app_private.has_permission('archive.view')
);

alter policy physical_checkouts_read_privileged
on public.physical_file_checkouts
using (
  app_private.is_super_user()
  or checked_out_by = app_private.current_employee_id()
  or app_private.has_permission('archive.view')
);

alter policy storage_project_documents_read
on storage.objects
using (
  bucket_id = 'project-documents'
  and app_private.has_project_access(public.try_uuid(split_part(name, '/', 1)))
);

revoke execute on function public.current_employee_id() from public, anon, authenticated;
revoke execute on function public.is_super_user() from public, anon, authenticated;
revoke execute on function public.has_permission(text) from public, anon, authenticated;
revoke execute on function public.has_project_access(uuid) from public, anon, authenticated;

grant execute on function public.current_employee_id() to service_role;
grant execute on function public.is_super_user() to service_role;
grant execute on function public.has_permission(text) to service_role;
grant execute on function public.has_project_access(uuid) to service_role;
