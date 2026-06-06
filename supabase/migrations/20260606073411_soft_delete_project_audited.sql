-- IEMS ERP: audited project soft delete.
--
-- Business records are never hard-deleted for audit history. This RPC marks a
-- project as deleted and records the before/after state in audit_events.

create or replace function public.soft_delete_project_audited(
  p_project_id uuid,
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
  old_project public.projects%rowtype;
  updated_project public.projects%rowtype;
begin
  select * into old_project
  from public.projects
  where id = p_project_id
    and deleted_at is null
  for update;

  if old_project.id is null then
    raise exception 'IEMS_PROJECT_NOT_FOUND';
  end if;

  update public.projects
  set deleted_at = now()
  where id = p_project_id
  returning * into updated_project;

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
    'project.deleted',
    'project',
    p_project_id,
    p_request_id,
    to_jsonb(old_project),
    to_jsonb(updated_project),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return to_jsonb(updated_project);
end;
$$;

revoke execute on function public.soft_delete_project_audited(
  uuid, uuid, uuid, uuid, text, text
) from public, anon, authenticated;

grant execute on function public.soft_delete_project_audited(
  uuid, uuid, uuid, uuid, text, text
) to service_role;
