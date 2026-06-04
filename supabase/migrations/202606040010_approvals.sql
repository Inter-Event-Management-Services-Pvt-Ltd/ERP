-- IEMS ERP: referentially safe approvals
create table public.approval_requests (
  id uuid primary key default gen_random_uuid(),
  approval_type_id uuid not null references public.approval_types(id) on delete restrict,
  project_id uuid references public.projects(id) on delete restrict,
  document_version_id uuid references public.document_versions(id) on delete restrict,
  archive_export_id uuid references public.archive_exports(id) on delete restrict,
  leave_request_id uuid references public.leave_requests(id) on delete restrict,
  requested_by uuid not null references public.employees(id) on delete restrict,
  assigned_to uuid references public.employees(id) on delete restrict,
  status varchar(30) not null default 'PENDING'
    check (status in ('PENDING','APPROVED','REJECTED','REVISION_REQUESTED','CANCELLED')),
  requested_at timestamptz not null default now(),
  completed_at timestamptz,
  check (num_nonnulls(project_id, document_version_id, archive_export_id, leave_request_id) = 1)
);

create table public.approval_actions (
  id uuid primary key default gen_random_uuid(),
  approval_request_id uuid not null references public.approval_requests(id) on delete restrict,
  action varchar(30) not null
    check (action in ('SUBMITTED','APPROVED','REJECTED','REVISION_REQUESTED','CANCELLED','COMMENTED')),
  performed_by uuid not null references public.employees(id) on delete restrict,
  comment text,
  created_at timestamptz not null default now()
);
