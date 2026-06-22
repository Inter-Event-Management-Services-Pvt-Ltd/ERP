-- IEMS ERP: minimal required hosted/staging seed.
--
-- Purpose:
-- - reference lookup rows needed by forms and API validation
-- - RBAC roles, permissions and role-permission mappings
-- - Director employee bootstrap row
-- - default folder template used when creating projects
--
-- Excludes demo clients, demo projects, demo folders and non-Director demo
-- employees. Run after migrations have been applied.

insert into public.departments(code, name) values
('OPS','Operations'),
('ACCOUNTS','Accounts'),
('ADMIN','Administration'),
('HR','Human Resources'),
('MANAGEMENT','Management')
on conflict (code) do update
  set name = excluded.name;

insert into public.project_types(code, name) values
('CONFERENCE','Conference'),
('EXHIBITION','Exhibition'),
('CORPORATE_EVENT','Corporate Event'),
('GOVERNMENT_EVENT','Government Event'),
('PRODUCT_LAUNCH','Product Launch'),
('VENDOR_FILE','Vendor File'),
('HR_FILE','HR File'),
('LEGAL_FILE','Legal File')
on conflict (code) do update
  set name = excluded.name;

insert into public.project_statuses(code, name, sort_order, is_terminal) values
('PLANNING','Planning',10,false),
('ACTIVE','Active',20,false),
('ON_HOLD','On Hold',30,false),
('COMPLETED','Completed',40,true),
('ARCHIVED','Archived',50,true),
('CANCELLED','Cancelled',60,true)
on conflict (code) do update
  set name = excluded.name,
      sort_order = excluded.sort_order,
      is_terminal = excluded.is_terminal;

insert into public.priority_levels(code, name, rank) values
('LOW','Low',10),
('NORMAL','Normal',20),
('HIGH','High',30),
('URGENT','Urgent',40)
on conflict (code) do update
  set name = excluded.name,
      rank = excluded.rank;

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
on conflict (code) do update
  set name = excluded.name,
      requires_approval = excluded.requires_approval,
      is_required_for_archive = excluded.is_required_for_archive;

insert into public.confidentiality_levels(code, name, rank) values
('GENERAL','General',10),
('INTERNAL','Internal',20),
('CONFIDENTIAL','Confidential',30),
('RESTRICTED','Restricted',40)
on conflict (code) do update
  set name = excluded.name,
      rank = excluded.rank;

insert into public.leave_types(code, name, is_paid) values
('CASUAL','Casual Leave',true),
('SICK','Sick Leave',true),
('EARNED','Earned Leave',true),
('UNPAID','Unpaid Leave',false)
on conflict (code) do update
  set name = excluded.name,
      is_paid = excluded.is_paid;

insert into public.task_statuses(code, name, is_terminal) values
('TODO','To Do',false),
('IN_PROGRESS','In Progress',false),
('BLOCKED','Blocked',false),
('COMPLETED','Completed',true),
('CANCELLED','Cancelled',true)
on conflict (code) do update
  set name = excluded.name,
      is_terminal = excluded.is_terminal;

insert into public.approval_types(code, name) values
('DOCUMENT_APPROVAL','Document Approval'),
('PROJECT_CLOSURE','Project Closure'),
('ARCHIVE_CLOSURE','Archive Closure'),
('LEAVE_APPROVAL','Leave Approval')
on conflict (code) do update
  set name = excluded.name;

insert into public.roles(code, name, description) values
('EMPLOYEE','Employee','Standard employee access'),
('MANAGER','Manager','Team and project management access'),
('ADMIN','Admin','Administrative operations access'),
('SUPER_ADMIN','Super Admin','Platform administration access'),
('SUPER_USER','Super User','Broad override access with mandatory audit reason'),
('DIRECTOR','Director','Director Dashboard and management oversight')
on conflict (code) do update
  set name = excluded.name,
      description = excluded.description;

insert into public.permissions(code, description) values
('employee.view','View employee directory'),
('employee.manage','Create and update employee administrative records'),
('role.manage','Assign and revoke employee roles'),
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
('audit.view','View audit events'),
('folder_template.manage','Manage project folder templates')
on conflict (code) do update
  set description = excluded.description;

insert into public.role_permissions(role_id, permission_id)
select r.id, p.id
from public.roles r
join public.permissions p on
  (r.code = 'EMPLOYEE' and p.code in (
    'project.view',
    'document.view',
    'document.download'
  )) or
  (r.code = 'MANAGER' and p.code in (
    'project.view',
    'project.manage',
    'document.view',
    'document.upload',
    'document.download',
    'archive.export',
    'task.manage'
  )) or
  (r.code = 'ADMIN' and p.code in (
    'employee.view',
    'employee.manage',
    'attendance.view_all',
    'attendance.correct',
    'leave.review',
    'archive.view',
    'archive.manage',
    'physical_file.checkout'
  )) or
  (r.code = 'SUPER_ADMIN' and p.code in (
    'employee.view',
    'employee.manage',
    'role.manage',
    'project.manage',
    'document.upload',
    'archive.manage',
    'attendance.correct',
    'leave.review',
    'task.manage',
    'approval.view_all',
    'approval.approve',
    'policy.manage',
    'audit.view',
    'folder_template.manage'
  )) or
  (r.code = 'DIRECTOR' and p.code in (
    'employee.view',
    'project.view',
    'document.view',
    'document.download',
    'archive.view',
    'attendance.view_all',
    'approval.view_all',
    'audit.view'
  ))
on conflict do nothing;

insert into public.employees(employee_code, full_name, official_email, designation, employment_status)
values ('IEMS-DIRECTOR', 'IEMS Director', 'director@iemsnewdelhi.com', 'Director', 'ACTIVE')
on conflict (official_email) do update
  set employee_code = excluded.employee_code,
      full_name = excluded.full_name,
      designation = excluded.designation,
      employment_status = excluded.employment_status;

insert into public.folder_templates(name, project_type_id, created_by)
select 'Standard Event Project', null, null
where not exists (
  select 1
  from public.folder_templates
  where name = 'Standard Event Project'
);

with template as (
  select id
  from public.folder_templates
  where name = 'Standard Event Project'
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
  select 1
  from public.folder_template_items existing
  where existing.template_id = template.id
    and existing.parent_item_id is null
    and lower(existing.name) = lower(item.name)
);
