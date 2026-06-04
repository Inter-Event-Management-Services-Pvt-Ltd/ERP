-- IEMS ERP: employee identity, RBAC, ABAC and director bootstrap
create table public.employees (
  id uuid primary key default gen_random_uuid(),
  employee_code varchar(30) not null unique,
  full_name varchar(150) not null,
  official_email extensions.citext not null unique,
  phone varchar(30),
  designation varchar(120),
  employment_status varchar(30) not null default 'ACTIVE'
    check (employment_status in ('ACTIVE','INACTIVE','ON_LEAVE','EXITED')),
  joined_on date,
  left_on date,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (left_on is null or joined_on is null or left_on >= joined_on)
);

create table public.user_accounts (
  id uuid primary key references auth.users(id) on delete restrict,
  employee_id uuid not null unique references public.employees(id) on delete restrict,
  is_active boolean not null default true,
  is_super_user boolean not null default false,
  last_login_at timestamptz,
  created_at timestamptz not null default now()
);

create table public.employee_department_assignments (
  id uuid primary key default gen_random_uuid(),
  employee_id uuid not null references public.employees(id) on delete restrict,
  department_id uuid not null references public.departments(id) on delete restrict,
  valid_from date not null,
  valid_to date,
  assigned_by uuid references public.employees(id) on delete restrict,
  check (valid_to is null or valid_to >= valid_from)
);
create unique index uq_employee_current_department
  on public.employee_department_assignments(employee_id)
  where valid_to is null;

create table public.roles (
  id uuid primary key default gen_random_uuid(),
  code varchar(40) not null unique,
  name varchar(100) not null unique,
  description text
);

create table public.permissions (
  id uuid primary key default gen_random_uuid(),
  code varchar(100) not null unique,
  description text
);

create table public.role_permissions (
  role_id uuid not null references public.roles(id) on delete cascade,
  permission_id uuid not null references public.permissions(id) on delete cascade,
  primary key (role_id, permission_id)
);

create table public.user_role_assignments (
  user_account_id uuid not null references public.user_accounts(id) on delete cascade,
  role_id uuid not null references public.roles(id) on delete cascade,
  assigned_by uuid references public.user_accounts(id) on delete restrict,
  assigned_at timestamptz not null default now(),
  expires_at timestamptz,
  primary key (user_account_id, role_id)
);

create table public.attribute_definitions (
  id uuid primary key default gen_random_uuid(),
  entity_type varchar(40) not null,
  attribute_key varchar(100) not null,
  value_type varchar(30) not null
    check (value_type in ('STRING','NUMBER','BOOLEAN','JSON')),
  is_multivalued boolean not null default false,
  description text,
  unique(entity_type, attribute_key)
);

create table public.employee_attribute_values (
  id uuid primary key default gen_random_uuid(),
  employee_id uuid not null references public.employees(id) on delete restrict,
  attribute_definition_id uuid not null references public.attribute_definitions(id) on delete restrict,
  value jsonb not null,
  valid_from timestamptz not null default now(),
  valid_to timestamptz,
  check (valid_to is null or valid_to >= valid_from)
);

create table public.policies (
  id uuid primary key default gen_random_uuid(),
  name varchar(150) not null unique,
  action_code varchar(100) not null,
  effect varchar(10) not null check (effect in ('ALLOW','DENY')),
  priority integer not null default 100,
  conditions jsonb not null default '{}'::jsonb,
  is_active boolean not null default true,
  created_by uuid references public.user_accounts(id) on delete restrict,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.super_user_overrides (
  id uuid primary key default gen_random_uuid(),
  user_account_id uuid not null references public.user_accounts(id) on delete restrict,
  action_code varchar(100) not null,
  resource_type varchar(60) not null,
  resource_id uuid not null,
  reason text not null check (length(trim(reason)) >= 8),
  created_at timestamptz not null default now()
);

create or replace function public.link_auth_user_to_employee()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  matched_employee public.employees%rowtype;
  director_account boolean;
begin
  select * into matched_employee
  from public.employees
  where lower(official_email::text) = lower(new.email)
  limit 1;

  if matched_employee.id is null then
    return new;
  end if;

  director_account := lower(matched_employee.official_email::text) = 'director@iemsnewdelhi.com';

  insert into public.user_accounts(id, employee_id, is_active, is_super_user, last_login_at)
  values (new.id, matched_employee.id, true, director_account, now())
  on conflict (id) do update
    set last_login_at = excluded.last_login_at,
        is_active = true,
        is_super_user = public.user_accounts.is_super_user or excluded.is_super_user;

  if director_account then
    insert into public.user_role_assignments(user_account_id, role_id)
    select new.id, r.id
    from public.roles r
    where r.code in ('DIRECTOR','SUPER_USER')
    on conflict do nothing;
  end if;

  return new;
end;
$$;

drop trigger if exists trg_link_auth_user_to_employee on auth.users;
create trigger trg_link_auth_user_to_employee
after insert or update of email on auth.users
for each row execute function public.link_auth_user_to_employee();
