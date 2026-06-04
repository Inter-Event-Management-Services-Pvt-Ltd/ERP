-- IEMS ERP: helper functions, timestamp triggers and audit protections
create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = public, pg_catalog
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

do $$
declare
  tbl text;
begin
  foreach tbl in array array[
    'employees','clients','projects','folders','documents','policies',
    'physical_files','attendance_sessions','tasks','calendar_events'
  ]
  loop
    execute format('drop trigger if exists trg_%I_updated_at on public.%I', tbl, tbl);
    execute format(
      'create trigger trg_%I_updated_at before update on public.%I
       for each row execute function public.set_updated_at()',
      tbl, tbl
    );
  end loop;
end $$;

create or replace function public.prevent_audit_event_mutation()
returns trigger
language plpgsql
set search_path = public, pg_catalog
as $$
begin
  raise exception 'audit_events is append-only';
end;
$$;

drop trigger if exists trg_prevent_audit_event_update on public.audit_events;
create trigger trg_prevent_audit_event_update
before update or delete on public.audit_events
for each row execute function public.prevent_audit_event_mutation();

create or replace function public.current_employee_id()
returns uuid
language sql
stable
security definer
set search_path = public
as $$
  select ua.employee_id
  from public.user_accounts ua
  where ua.id = (select auth.uid())
    and ua.is_active = true
  limit 1
$$;

create or replace function public.is_super_user()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select coalesce((
    select ua.is_super_user
    from public.user_accounts ua
    where ua.id = (select auth.uid()) and ua.is_active = true
  ), false)
$$;

create or replace function public.has_permission(permission_code text)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select public.is_super_user() or exists (
    select 1
    from public.user_role_assignments ura
    join public.role_permissions rp on rp.role_id = ura.role_id
    join public.permissions p on p.id = rp.permission_id
    where ura.user_account_id = (select auth.uid())
      and (ura.expires_at is null or ura.expires_at > now())
      and p.code = permission_code
  )
$$;

create or replace function public.has_project_access(target_project_id uuid)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select public.is_super_user() or exists (
    select 1
    from public.project_members pm
    where pm.project_id = target_project_id
      and pm.employee_id = public.current_employee_id()
      and pm.removed_at is null
  )
$$;

create or replace function public.try_uuid(raw text)
returns uuid
language plpgsql
immutable
set search_path = pg_catalog
as $$
begin
  return raw::uuid;
exception when others then
  return null;
end;
$$;
