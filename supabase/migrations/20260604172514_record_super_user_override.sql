-- IEMS ERP: atomic Super User override and audit event recording
create or replace function public.record_super_user_override(
  p_user_account_id uuid,
  p_actor_employee_id uuid,
  p_action_code text,
  p_resource_type text,
  p_resource_id uuid,
  p_reason text,
  p_request_id uuid default null,
  p_metadata jsonb default '{}'::jsonb,
  p_ip_address inet default null,
  p_user_agent text default null
)
returns uuid
language plpgsql
set search_path = public, pg_catalog
as $$
declare
  override_id uuid;
begin
  insert into public.super_user_overrides(
    user_account_id,
    action_code,
    resource_type,
    resource_id,
    reason
  )
  values (
    p_user_account_id,
    p_action_code,
    p_resource_type,
    p_resource_id,
    p_reason
  )
  returning id into override_id;

  insert into public.audit_events(
    actor_user_account_id,
    actor_employee_id,
    action_code,
    resource_type,
    resource_id,
    request_id,
    new_values,
    metadata,
    ip_address,
    user_agent
  )
  values (
    p_user_account_id,
    p_actor_employee_id,
    'super_user.override_used',
    p_resource_type,
    p_resource_id,
    p_request_id,
    jsonb_build_object(
      'override_id', override_id,
      'override_action_code', p_action_code,
      'reason', p_reason
    ),
    coalesce(p_metadata, '{}'::jsonb),
    p_ip_address,
    p_user_agent
  );

  return override_id;
end;
$$;

revoke all on function public.record_super_user_override(
  uuid,
  uuid,
  text,
  text,
  uuid,
  text,
  uuid,
  jsonb,
  inet,
  text
) from public, anon, authenticated;

grant execute on function public.record_super_user_override(
  uuid,
  uuid,
  text,
  text,
  uuid,
  text,
  uuid,
  jsonb,
  inet,
  text
) to service_role;
