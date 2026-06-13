-- IEMS ERP: harden custom trigger function privileges
--
-- Trigger functions should not be callable as public API RPCs. The triggers
-- already exist when this migration runs; revoking direct EXECUTE does not
-- disable trigger execution.

create or replace function public.link_auth_user_to_employee()
returns trigger
language plpgsql
security definer
set search_path = public, pg_catalog
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

revoke execute on function public.link_auth_user_to_employee() from public, anon, authenticated;
revoke execute on function public.set_updated_at() from public, anon, authenticated;
revoke execute on function public.prevent_audit_event_mutation() from public, anon, authenticated;

grant execute on function public.link_auth_user_to_employee() to service_role;
grant execute on function public.set_updated_at() to service_role;
grant execute on function public.prevent_audit_event_mutation() to service_role;
