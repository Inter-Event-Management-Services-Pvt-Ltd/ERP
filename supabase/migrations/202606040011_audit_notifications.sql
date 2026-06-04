-- IEMS ERP: immutable audit events and notifications
create table public.audit_events (
  id uuid primary key default gen_random_uuid(),
  actor_user_account_id uuid references public.user_accounts(id) on delete restrict,
  actor_employee_id uuid references public.employees(id) on delete restrict,
  action_code varchar(100) not null,
  resource_type varchar(60) not null,
  resource_id uuid,
  request_id uuid,
  old_values jsonb,
  new_values jsonb,
  metadata jsonb,
  ip_address inet,
  user_agent text,
  created_at timestamptz not null default now()
);

create table public.notifications (
  id uuid primary key default gen_random_uuid(),
  employee_id uuid not null references public.employees(id) on delete cascade,
  notification_type varchar(50) not null,
  title varchar(200) not null,
  message text not null,
  resource_type varchar(60),
  resource_id uuid,
  read_at timestamptz,
  created_at timestamptz not null default now()
);
