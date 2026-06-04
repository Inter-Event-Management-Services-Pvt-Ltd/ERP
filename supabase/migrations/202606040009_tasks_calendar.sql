-- IEMS ERP: tasks and calendar
create table public.tasks (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.projects(id) on delete restrict,
  related_folder_id uuid references public.folders(id) on delete restrict,
  title varchar(250) not null,
  description text,
  task_status_id uuid not null references public.task_statuses(id) on delete restrict,
  priority_level_id uuid not null references public.priority_levels(id) on delete restrict,
  created_by uuid not null references public.employees(id) on delete restrict,
  due_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.task_assignees (
  task_id uuid not null references public.tasks(id) on delete cascade,
  employee_id uuid not null references public.employees(id) on delete restrict,
  assigned_by uuid not null references public.employees(id) on delete restrict,
  assigned_at timestamptz not null default now(),
  primary key(task_id, employee_id)
);

create table public.task_comments (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null references public.tasks(id) on delete cascade,
  employee_id uuid not null references public.employees(id) on delete restrict,
  comment_text text not null,
  created_at timestamptz not null default now(),
  edited_at timestamptz
);

create table public.task_document_links (
  task_id uuid not null references public.tasks(id) on delete cascade,
  document_id uuid not null references public.documents(id) on delete cascade,
  primary key(task_id, document_id)
);

create table public.calendar_events (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.projects(id) on delete restrict,
  related_task_id uuid references public.tasks(id) on delete restrict,
  event_type varchar(40) not null check (event_type in ('MEETING','SITE_VISIT','EVENT','DEADLINE','LEAVE','ARCHIVE_VERIFICATION','PHYSICAL_FILE_RETURN','REMINDER')),
  title varchar(250) not null,
  description text,
  starts_at timestamptz not null,
  ends_at timestamptz,
  location varchar(250),
  created_by uuid not null references public.employees(id) on delete restrict,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check(ends_at is null or ends_at >= starts_at)
);

create table public.calendar_event_attendees (
  calendar_event_id uuid not null references public.calendar_events(id) on delete cascade,
  employee_id uuid not null references public.employees(id) on delete restrict,
  response_status varchar(30) not null default 'NEEDS_ACTION'
    check (response_status in ('NEEDS_ACTION','ACCEPTED','DECLINED','TENTATIVE')),
  primary key(calendar_event_id, employee_id)
);
