-- IEMS ERP: clients and projects
create table public.clients (
  id uuid primary key default gen_random_uuid(),
  client_code varchar(30) not null unique,
  legal_name varchar(200) not null,
  display_name varchar(150) not null,
  is_active boolean not null default true,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.client_contacts (
  id uuid primary key default gen_random_uuid(),
  client_id uuid not null references public.clients(id) on delete restrict,
  full_name varchar(150) not null,
  email extensions.citext,
  phone varchar(30),
  designation varchar(100),
  is_primary boolean not null default false
);
create unique index uq_one_primary_contact_per_client
  on public.client_contacts(client_id)
  where is_primary = true;

create table public.projects (
  id uuid primary key default gen_random_uuid(),
  project_code varchar(40) not null unique,
  client_id uuid not null references public.clients(id) on delete restrict,
  project_type_id uuid not null references public.project_types(id) on delete restrict,
  project_status_id uuid not null references public.project_statuses(id) on delete restrict,
  priority_level_id uuid not null references public.priority_levels(id) on delete restrict,
  name varchar(200) not null,
  event_date date,
  venue varchar(250),
  description text,
  project_manager_id uuid references public.employees(id) on delete restrict,
  created_by uuid not null references public.employees(id) on delete restrict,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  archived_at timestamptz,
  deleted_at timestamptz
);

create table public.project_members (
  project_id uuid not null references public.projects(id) on delete cascade,
  employee_id uuid not null references public.employees(id) on delete restrict,
  access_level varchar(20) not null check (access_level in ('VIEW','CONTRIBUTE','MANAGE')),
  assigned_by uuid not null references public.employees(id) on delete restrict,
  assigned_at timestamptz not null default now(),
  removed_at timestamptz,
  primary key (project_id, employee_id)
);
