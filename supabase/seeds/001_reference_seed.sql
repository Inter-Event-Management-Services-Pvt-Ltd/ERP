-- IEMS ERP: initial reference data
insert into public.departments(code, name) values
('OPS','Operations'),
('ACCOUNTS','Accounts'),
('ADMIN','Administration'),
('HR','Human Resources'),
('MANAGEMENT','Management')
on conflict do nothing;

insert into public.project_types(code, name) values
('CONFERENCE','Conference'),
('EXHIBITION','Exhibition'),
('CORPORATE_EVENT','Corporate Event'),
('GOVERNMENT_EVENT','Government Event'),
('PRODUCT_LAUNCH','Product Launch'),
('VENDOR_FILE','Vendor File'),
('HR_FILE','HR File'),
('LEGAL_FILE','Legal File')
on conflict do nothing;

insert into public.project_statuses(code, name, sort_order, is_terminal) values
('PLANNING','Planning',10,false),
('ACTIVE','Active',20,false),
('ON_HOLD','On Hold',30,false),
('COMPLETED','Completed',40,true),
('ARCHIVED','Archived',50,true),
('CANCELLED','Cancelled',60,true)
on conflict do nothing;

insert into public.priority_levels(code, name, rank) values
('LOW','Low',10),
('NORMAL','Normal',20),
('HIGH','High',30),
('URGENT','Urgent',40)
on conflict do nothing;

insert into public.document_types(code, name, requires_approval, is_required_for_archive) values
('CLIENT_BRIEF','Client Brief',false,true),
('QUOTATION','Quotation',true,true),
('WORK_ORDER','Work Order',true,true),
('VENUE_DOCUMENT','Venue Document',false,false),
('VENUE_APPROVAL','Venue Approval',true,false),
('VENDOR_DOCUMENT','Vendor Document',false,false),
('VENDOR_BILL','Vendor Bill',false,false),
('EVENT_PLAN','Event Plan',true,false),
('FINAL_INVOICE','Final Invoice',true,true),
('PHOTO_DELIVERABLE','Photo or Deliverable',false,false),
('MISCELLANEOUS','Miscellaneous',false,false)
on conflict do nothing;

insert into public.confidentiality_levels(code, name, rank) values
('GENERAL','General',10),
('INTERNAL','Internal',20),
('CONFIDENTIAL','Confidential',30),
('RESTRICTED','Restricted',40)
on conflict do nothing;

insert into public.leave_types(code, name, is_paid) values
('CASUAL','Casual Leave',true),
('SICK','Sick Leave',true),
('EARNED','Earned Leave',true),
('UNPAID','Unpaid Leave',false)
on conflict do nothing;

insert into public.task_statuses(code, name, is_terminal) values
('TODO','To Do',false),
('IN_PROGRESS','In Progress',false),
('BLOCKED','Blocked',false),
('COMPLETED','Completed',true),
('CANCELLED','Cancelled',true)
on conflict do nothing;

insert into public.approval_types(code, name) values
('DOCUMENT_APPROVAL','Document Approval'),
('PROJECT_CLOSURE','Project Closure'),
('ARCHIVE_CLOSURE','Archive Closure'),
('LEAVE_APPROVAL','Leave Approval')
on conflict do nothing;

insert into public.roles(code, name, description) values
('EMPLOYEE','Employee','Standard employee access'),
('MANAGER','Manager','Team and project management access'),
('ADMIN','Admin','Administrative operations access'),
('SUPER_ADMIN','Super Admin','Platform administration access'),
('SUPER_USER','Super User','Broad override access with mandatory audit reason'),
('DIRECTOR','Director','Director Dashboard and management oversight')
on conflict do nothing;

insert into public.permissions(code, description) values
('employee.view','View employee directory'),
('project.view','View accessible projects'),
('project.manage','Create and edit projects'),
('document.view','View accessible documents'),
('document.upload','Upload documents'),
('document.download','Download documents'),
('archive.view','View physical archive'),
('archive.manage','Manage physical archive locations'),
('archive.export','Generate offline ZIP archives'),
('physical_file.checkout','Check out physical files'),
('attendance.view_all','View all attendance'),
('attendance.correct','Correct attendance'),
('leave.review','Approve or reject leave'),
('task.manage','Assign and manage tasks'),
('approval.view_all','View all approvals'),
('approval.approve','Approve requests'),
('policy.manage','Manage ABAC policies'),
('audit.view','View audit events')
on conflict do nothing;

-- Role permission mapping
insert into public.role_permissions(role_id, permission_id)
select r.id, p.id
from public.roles r
join public.permissions p on
  (r.code = 'EMPLOYEE' and p.code in ('project.view','document.view','document.download')) or
  (r.code = 'MANAGER' and p.code in ('project.view','project.manage','document.view','document.upload','document.download','archive.export','task.manage')) or
  (r.code = 'ADMIN' and p.code in ('employee.view','attendance.view_all','attendance.correct','leave.review','archive.view','archive.manage','physical_file.checkout')) or
  (r.code = 'SUPER_ADMIN' and p.code in ('employee.view','project.manage','document.upload','archive.manage','attendance.correct','leave.review','task.manage','approval.view_all','approval.approve','policy.manage','audit.view')) or
  (r.code = 'DIRECTOR' and p.code in ('employee.view','project.view','document.view','document.download','archive.view','attendance.view_all','approval.view_all','audit.view'))
on conflict do nothing;

-- Director employee seed; Auth account links after first Google sign-in.
insert into public.employees(employee_code, full_name, official_email, designation, employment_status)
values ('IEMS-DIRECTOR', 'IEMS Director', 'director@iemsnewdelhi.com', 'Director', 'ACTIVE')
on conflict (official_email) do nothing;

-- Local/demo employees for API and frontend development. Auth accounts are not
-- seeded; use apps/api/scripts/local_access_token.py to create local Auth users.
insert into public.employees(id, employee_code, full_name, official_email, designation, employment_status)
values
('10000000-0000-4000-8000-000000000001','IEMS-DEV-001','IEMS Dev User','dev.user@iemsnewdelhi.com','Local Dev','ACTIVE'),
('10000000-0000-4000-8000-000000000002','IEMS-MGR-001','Aarav Mehta','project.manager@iemsnewdelhi.com','Project Manager','ACTIVE'),
('10000000-0000-4000-8000-000000000003','IEMS-OPS-001','Nisha Rao','ops.coordinator@iemsnewdelhi.com','Operations Coordinator','ACTIVE'),
('10000000-0000-4000-8000-000000000004','IEMS-OPS-006','Deepak','deepak@iemsnewdelhi.com','Local Dev','ACTIVE')
on conflict (official_email) do update
  set employee_code = excluded.employee_code,
      full_name = excluded.full_name,
      designation = excluded.designation,
      employment_status = excluded.employment_status;

-- Standard event project folder template
insert into public.folder_templates(name, project_type_id, created_by)
select 'Standard Event Project', null, null
where not exists (select 1 from public.folder_templates where name = 'Standard Event Project');

with template as (
  select id from public.folder_templates where name = 'Standard Event Project'
)
insert into public.folder_template_items(template_id, name, sort_order)
select template.id, item.name, item.sort_order
from template
cross join (values
  ('01 Client Brief', 10),
  ('02 Quotations', 20),
  ('03 Work Orders', 30),
  ('04 Venue Documents', 40),
  ('05 Vendor Documents', 50),
  ('06 Event Plans', 60),
  ('07 Bills and Invoices', 70),
  ('08 Photos and Deliverables', 80),
  ('09 Final Archive', 90)
) as item(name, sort_order)
where not exists (
  select 1 from public.folder_template_items existing
  where existing.template_id = template.id and existing.name = item.name
);

-- Local/demo clients, projects, memberships and folder trees for Phase 2 testing.
-- These records are deterministic and idempotent so repeated local resets keep
-- stable URLs and predictable frontend fixtures.
insert into public.clients(id, client_code, legal_name, display_name, is_active, notes)
values
('20000000-0000-4000-8000-000000000001','ACME-DEMO','Acme Events Private Limited','Acme Events',true,'Demo client for local project workflow testing.'),
('20000000-0000-4000-8000-000000000002','GOV-DELHI','Delhi Cultural Affairs Department','Delhi Cultural Affairs',true,'Demo government client for local archive workflow testing.')
on conflict (client_code) do update
  set legal_name = excluded.legal_name,
      display_name = excluded.display_name,
      is_active = excluded.is_active,
      notes = excluded.notes;

insert into public.client_contacts(
  id,
  client_id,
  full_name,
  email,
  phone,
  designation,
  is_primary
)
values
('21000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001','Priya Sharma','priya.sharma@example.com','+91-98765-01001','Events Lead',true),
('21000000-0000-4000-8000-000000000002','20000000-0000-4000-8000-000000000002','Rohan Kapoor','rohan.kapoor@example.com','+91-98765-01002','Programme Officer',true)
on conflict (id) do update
  set full_name = excluded.full_name,
      email = excluded.email,
      phone = excluded.phone,
      designation = excluded.designation,
      is_primary = excluded.is_primary;

with refs as (
  select
    (select id from public.project_types where code = 'CONFERENCE') as conference_type_id,
    (select id from public.project_types where code = 'GOVERNMENT_EVENT') as government_type_id,
    (select id from public.project_statuses where code = 'ACTIVE') as active_status_id,
    (select id from public.project_statuses where code = 'PLANNING') as planning_status_id,
    (select id from public.priority_levels where code = 'HIGH') as high_priority_id,
    (select id from public.priority_levels where code = 'NORMAL') as normal_priority_id
)
insert into public.projects(
  id,
  project_code,
  client_id,
  project_type_id,
  project_status_id,
  priority_level_id,
  name,
  event_date,
  venue,
  description,
  project_manager_id,
  created_by
)
select demo_project.*
from refs
cross join lateral (values
  (
    '30000000-0000-4000-8000-000000000001'::uuid,
    'IEMS-2026-DEMO-001',
    '20000000-0000-4000-8000-000000000001'::uuid,
    refs.conference_type_id,
    refs.active_status_id,
    refs.high_priority_id,
    'Acme Annual Leadership Conference',
    '2026-08-12'::date,
    'India Habitat Centre, New Delhi',
    'Local demo project with an active document workflow.',
    '10000000-0000-4000-8000-000000000002'::uuid,
    '10000000-0000-4000-8000-000000000001'::uuid
  ),
  (
    '30000000-0000-4000-8000-000000000002'::uuid,
    'IEMS-2026-DEMO-002',
    '20000000-0000-4000-8000-000000000002'::uuid,
    refs.government_type_id,
    refs.planning_status_id,
    refs.normal_priority_id,
    'Delhi Heritage Week Opening Ceremony',
    '2026-10-05'::date,
    'Vigyan Bhawan, New Delhi',
    'Local demo project for archive and approval screen testing.',
    '10000000-0000-4000-8000-000000000002'::uuid,
    '10000000-0000-4000-8000-000000000001'::uuid
  )
) as demo_project(
  id,
  project_code,
  client_id,
  project_type_id,
  project_status_id,
  priority_level_id,
  name,
  event_date,
  venue,
  description,
  project_manager_id,
  created_by
)
on conflict (project_code) do update
  set client_id = excluded.client_id,
      project_type_id = excluded.project_type_id,
      project_status_id = excluded.project_status_id,
      priority_level_id = excluded.priority_level_id,
      name = excluded.name,
      event_date = excluded.event_date,
      venue = excluded.venue,
      description = excluded.description,
      project_manager_id = excluded.project_manager_id;

insert into public.project_members(project_id, employee_id, access_level, assigned_by)
values
('30000000-0000-4000-8000-000000000001','10000000-0000-4000-8000-000000000001','MANAGE','10000000-0000-4000-8000-000000000001'),
('30000000-0000-4000-8000-000000000001','10000000-0000-4000-8000-000000000002','MANAGE','10000000-0000-4000-8000-000000000001'),
('30000000-0000-4000-8000-000000000001','10000000-0000-4000-8000-000000000003','CONTRIBUTE','10000000-0000-4000-8000-000000000001'),
('30000000-0000-4000-8000-000000000002','10000000-0000-4000-8000-000000000001','VIEW','10000000-0000-4000-8000-000000000001'),
('30000000-0000-4000-8000-000000000002','10000000-0000-4000-8000-000000000002','MANAGE','10000000-0000-4000-8000-000000000001'),
('30000000-0000-4000-8000-000000000002','10000000-0000-4000-8000-000000000003','CONTRIBUTE','10000000-0000-4000-8000-000000000001')
on conflict (project_id, employee_id) do update
  set access_level = excluded.access_level,
      assigned_by = excluded.assigned_by,
      removed_at = null;

insert into public.folders(id, project_id, parent_folder_id, name, sort_order, created_by)
select root_folder.id, root_folder.project_id, null, root_folder.name, 0, root_folder.created_by
from (values
  ('31000000-0000-4000-8000-000000000001'::uuid,'30000000-0000-4000-8000-000000000001'::uuid,'IEMS-2026-DEMO-001','10000000-0000-4000-8000-000000000001'::uuid),
  ('31000000-0000-4000-8000-000000000002'::uuid,'30000000-0000-4000-8000-000000000002'::uuid,'IEMS-2026-DEMO-002','10000000-0000-4000-8000-000000000001'::uuid)
) as root_folder(id, project_id, name, created_by)
where not exists (
  select 1
  from public.folders existing
  where existing.project_id = root_folder.project_id
    and existing.parent_folder_id is null
    and existing.deleted_at is null
);

with template_items as (
  select name, sort_order
  from public.folder_template_items
  where template_id = (select id from public.folder_templates where name = 'Standard Event Project')
    and parent_item_id is null
),
project_roots as (
  select id as root_folder_id, project_id, created_by
  from public.folders
  where project_id in (
    '30000000-0000-4000-8000-000000000001',
    '30000000-0000-4000-8000-000000000002'
  )
    and parent_folder_id is null
    and deleted_at is null
)
insert into public.folders(project_id, parent_folder_id, name, sort_order, created_by)
select
  project_roots.project_id,
  project_roots.root_folder_id,
  template_items.name,
  template_items.sort_order,
  project_roots.created_by
from project_roots
cross join template_items
where not exists (
  select 1
  from public.folders existing
  where existing.project_id = project_roots.project_id
    and existing.parent_folder_id = project_roots.root_folder_id
    and lower(existing.name) = lower(template_items.name)
    and existing.deleted_at is null
);
