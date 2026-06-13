-- IEMS ERP: audited archive export cancellation.
--
-- FastAPI performs JWT, RBAC and ABAC checks before calling this RPC with the
-- Supabase service-role key. Cancellation is intentionally limited to QUEUED
-- exports so a worker that has already started writing a ZIP is not interrupted
-- halfway through.

alter table public.archive_exports
  drop constraint if exists archive_exports_status_check;

alter table public.archive_exports
  add constraint archive_exports_status_check
  check (status in ('QUEUED','GENERATING','READY','FAILED','EXPIRED','CANCELLED'));

create or replace function public.prevent_cancelled_archive_export_mutation()
returns trigger
language plpgsql
set search_path = public, pg_catalog
as $$
begin
  if old.status = 'CANCELLED' and to_jsonb(new) <> to_jsonb(old) then
    raise exception 'IEMS_ARCHIVE_EXPORT_CANCELLED';
  end if;
  return new;
end;
$$;

drop trigger if exists trg_prevent_cancelled_archive_export_mutation
  on public.archive_exports;

create trigger trg_prevent_cancelled_archive_export_mutation
before update on public.archive_exports
for each row
execute function public.prevent_cancelled_archive_export_mutation();

create or replace function public.cancel_archive_export_audited(
  p_archive_export_id uuid,
  p_actor_user_account_id uuid,
  p_actor_employee_id uuid,
  p_request_id uuid,
  p_ip_address text,
  p_user_agent text
)
returns jsonb
language plpgsql
set search_path = public, pg_catalog
as $$
declare
  old_export public.archive_exports%rowtype;
  updated_export public.archive_exports%rowtype;
begin
  select * into old_export
  from public.archive_exports
  where id = p_archive_export_id
  for update;

  if old_export.id is null then
    raise exception 'IEMS_ARCHIVE_EXPORT_NOT_FOUND';
  end if;

  if old_export.status <> 'QUEUED' then
    raise exception 'IEMS_ARCHIVE_EXPORT_NOT_CANCELLABLE';
  end if;

  update public.archive_exports
  set status = 'CANCELLED'
  where id = p_archive_export_id
  returning * into updated_export;

  insert into public.notifications(
    employee_id,
    notification_type,
    title,
    message,
    resource_type,
    resource_id
  )
  values (
    updated_export.requested_by,
    'ARCHIVE_EXPORT',
    'Archive export cancelled',
    'Your offline archive export was cancelled before generation started.',
    'archive_export',
    updated_export.id
  );

  insert into public.audit_events(
    actor_user_account_id,
    actor_employee_id,
    action_code,
    resource_type,
    resource_id,
    request_id,
    old_values,
    new_values,
    ip_address,
    user_agent
  )
  values (
    p_actor_user_account_id,
    p_actor_employee_id,
    'archive.export_cancelled',
    'archive_export',
    updated_export.id,
    p_request_id,
    to_jsonb(old_export),
    to_jsonb(updated_export),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.archive_export_response_json(updated_export.id);
end;
$$;

revoke execute on function public.prevent_cancelled_archive_export_mutation() from public, anon, authenticated;
revoke execute on function public.cancel_archive_export_audited(uuid, uuid, uuid, uuid, text, text) from public, anon, authenticated;

grant execute on function public.cancel_archive_export_audited(uuid, uuid, uuid, uuid, text, text) to service_role;
