-- IEMS ERP: audited client soft delete.
--
-- Client rows remain available for project history. This RPC deactivates a
-- client and records the before/after state in audit_events.

create or replace function public.deactivate_client_audited(
  p_client_id uuid,
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
  old_client public.clients%rowtype;
  updated_client public.clients%rowtype;
begin
  select * into old_client
  from public.clients
  where id = p_client_id
  for update;

  if old_client.id is null then
    raise exception 'IEMS_CLIENT_NOT_FOUND';
  end if;

  update public.clients
  set is_active = false
  where id = p_client_id
  returning * into updated_client;

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
    'client.deactivated',
    'client',
    p_client_id,
    p_request_id,
    to_jsonb(old_client),
    to_jsonb(updated_client),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return to_jsonb(updated_client);
end;
$$;

revoke execute on function public.deactivate_client_audited(
  uuid, uuid, uuid, uuid, text, text
) from public, anon, authenticated;

grant execute on function public.deactivate_client_audited(
  uuid, uuid, uuid, uuid, text, text
) to service_role;
