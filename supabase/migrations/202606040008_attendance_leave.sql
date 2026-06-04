-- IEMS ERP: attendance sessions and leave
create table public.attendance_sessions (
  id uuid primary key default gen_random_uuid(),
  employee_id uuid not null references public.employees(id) on delete restrict,
  checked_in_at timestamptz not null default now(),
  checked_out_at timestamptz,
  source varchar(30) not null check (source in ('WEB','MOBILE','ADMIN','QR','BIOMETRIC','IMPORT')),
  remarks text,
  created_by uuid not null references public.employees(id) on delete restrict,
  corrected_by uuid references public.employees(id) on delete restrict,
  correction_reason text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (checked_out_at is null or checked_out_at >= checked_in_at),
  check ((corrected_by is null and correction_reason is null) or
         (corrected_by is not null and length(trim(correction_reason)) >= 5))
);
create unique index uq_one_open_attendance_session_per_employee
  on public.attendance_sessions(employee_id)
  where checked_out_at is null;

create table public.leave_requests (
  id uuid primary key default gen_random_uuid(),
  employee_id uuid not null references public.employees(id) on delete restrict,
  leave_type_id uuid not null references public.leave_types(id) on delete restrict,
  start_date date not null,
  end_date date not null,
  reason text not null,
  status varchar(30) not null default 'PENDING'
    check (status in ('PENDING','APPROVED','REJECTED','CANCELLED')),
  requested_at timestamptz not null default now(),
  reviewed_by uuid references public.employees(id) on delete restrict,
  reviewed_at timestamptz,
  review_comment text,
  check(end_date >= start_date)
);
