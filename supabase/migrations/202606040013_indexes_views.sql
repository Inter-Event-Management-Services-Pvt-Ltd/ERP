-- IEMS ERP: operational indexes and dashboard views
create index idx_employee_department_assignments_employee on public.employee_department_assignments(employee_id);
create index idx_project_members_employee on public.project_members(employee_id);
create index idx_projects_client on public.projects(client_id);
create index idx_projects_manager on public.projects(project_manager_id);
create index idx_folders_project on public.folders(project_id);
create index idx_folders_parent on public.folders(parent_folder_id);
create index idx_documents_folder on public.documents(folder_id);
create index idx_documents_project on public.documents(project_id);
create index idx_document_versions_document on public.document_versions(document_id);
create index idx_archive_exports_project on public.archive_exports(project_id);
create index idx_archive_locations_parent on public.archive_locations(parent_location_id);
create index idx_physical_files_project on public.physical_files(project_id);
create index idx_physical_files_location on public.physical_files(archive_location_id);
create index idx_checkouts_file on public.physical_file_checkouts(physical_file_id);
create index idx_attendance_employee_time on public.attendance_sessions(employee_id, checked_in_at desc);
create index idx_tasks_project on public.tasks(project_id);
create index idx_task_assignees_employee on public.task_assignees(employee_id);
create index idx_approval_pending on public.approval_requests(assigned_to, requested_at) where status = 'PENDING';
create index idx_notifications_unread on public.notifications(employee_id, created_at desc) where read_at is null;
create index idx_audit_created on public.audit_events(created_at desc);

create index idx_projects_name_trgm on public.projects using gin (name extensions.gin_trgm_ops);
create index idx_clients_display_name_trgm on public.clients using gin (display_name extensions.gin_trgm_ops);
create index idx_documents_display_name_trgm on public.documents using gin (display_name extensions.gin_trgm_ops);

create or replace view public.attendance_daily_summary_v
with (security_invoker = true) as
select
  employee_id,
  (checked_in_at at time zone 'Asia/Kolkata')::date as attendance_date,
  min(checked_in_at) as first_check_in,
  max(checked_out_at) as last_check_out,
  coalesce(sum(extract(epoch from (coalesce(checked_out_at, now()) - checked_in_at)) / 60)::integer, 0) as total_minutes,
  count(*) filter (where checked_out_at is null) as open_session_count
from public.attendance_sessions
group by employee_id, (checked_in_at at time zone 'Asia/Kolkata')::date;

create or replace view public.director_attendance_today_v
with (security_invoker = true) as
select
  e.id as employee_id,
  e.employee_code,
  e.full_name,
  s.first_check_in,
  s.last_check_out,
  s.total_minutes,
  case
    when s.employee_id is null then 'ABSENT_OR_NOT_CHECKED_IN'
    when s.open_session_count > 0 then 'CHECKED_IN'
    else 'CHECKED_OUT'
  end as attendance_state
from public.employees e
left join public.attendance_daily_summary_v s
  on s.employee_id = e.id
 and s.attendance_date = (now() at time zone 'Asia/Kolkata')::date
where e.employment_status = 'ACTIVE';

create or replace view public.director_physical_file_status_v
with (security_invoker = true) as
select
  pf.id,
  pf.physical_file_code,
  p.project_code,
  p.name as project_name,
  c.display_name as client_name,
  pf.status,
  ar.name as archive_room,
  al.code as archive_location_code,
  co.checked_out_at,
  co.expected_return_at,
  checkout_employee.full_name as checked_out_by
from public.physical_files pf
join public.projects p on p.id = pf.project_id
join public.clients c on c.id = p.client_id
join public.archive_locations al on al.id = pf.archive_location_id
join public.archive_rooms ar on ar.id = al.archive_room_id
left join public.physical_file_checkouts co
  on co.physical_file_id = pf.id and co.returned_at is null
left join public.employees checkout_employee on checkout_employee.id = co.checked_out_by;

create or replace view public.director_pending_approvals_v
with (security_invoker = true) as
select
  ar.id,
  at.code as approval_type,
  ar.status,
  ar.requested_at,
  requester.full_name as requested_by_name,
  approver.full_name as assigned_to_name,
  p.project_code,
  p.name as project_name
from public.approval_requests ar
join public.approval_types at on at.id = ar.approval_type_id
join public.employees requester on requester.id = ar.requested_by
left join public.employees approver on approver.id = ar.assigned_to
left join public.projects p on p.id = ar.project_id
where ar.status = 'PENDING';

create or replace view public.director_overdue_tasks_v
with (security_invoker = true) as
select
  t.id,
  t.title,
  t.due_at,
  p.project_code,
  p.name as project_name,
  string_agg(e.full_name, ', ' order by e.full_name) as assignees
from public.tasks t
join public.task_statuses ts on ts.id = t.task_status_id
left join public.projects p on p.id = t.project_id
left join public.task_assignees ta on ta.task_id = t.id
left join public.employees e on e.id = ta.employee_id
where t.due_at < now() and ts.is_terminal = false
group by t.id, t.title, t.due_at, p.project_code, p.name;
