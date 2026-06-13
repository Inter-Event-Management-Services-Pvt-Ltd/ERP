-- IEMS ERP: guard project-member role updates.
--
-- Project members can be added, restored or have their access level changed
-- through the audited upsert RPC. Role updates must not leave a project without
-- an active MANAGE member.

create or replace function public.upsert_project_member_audited(
  p_project_id uuid,
  p_employee_id uuid,
  p_access_level text,
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
  existing_member public.project_members%rowtype;
  upserted_member public.project_members%rowtype;
  active_manage_count integer;
begin
  if p_access_level not in ('VIEW', 'CONTRIBUTE', 'MANAGE') then
    raise exception 'IEMS_INVALID_PROJECT_ACCESS_LEVEL';
  end if;

  if not exists (
    select 1 from public.projects
    where id = p_project_id and deleted_at is null
  ) then
    raise exception 'IEMS_PROJECT_NOT_FOUND';
  end if;

  if not exists (
    select 1 from public.employees
    where id = p_employee_id
      and employment_status in ('ACTIVE','ON_LEAVE')
  ) then
    raise exception 'IEMS_EMPLOYEE_NOT_ACTIVE';
  end if;

  select * into existing_member
  from public.project_members
  where project_id = p_project_id
    and employee_id = p_employee_id
    and removed_at is null
  for update;

  if existing_member.project_id is not null
     and existing_member.access_level = 'MANAGE'
     and p_access_level <> 'MANAGE' then
    select count(*) into active_manage_count
    from public.project_members
    where project_id = p_project_id
      and access_level = 'MANAGE'
      and removed_at is null;

    if active_manage_count <= 1 then
      raise exception 'IEMS_LAST_PROJECT_MANAGER';
    end if;
  end if;

  insert into public.project_members(project_id, employee_id, access_level, assigned_by)
  values (p_project_id, p_employee_id, p_access_level, p_actor_employee_id)
  on conflict (project_id, employee_id) do update
    set access_level = excluded.access_level,
        assigned_by = excluded.assigned_by,
        assigned_at = now(),
        removed_at = null
  returning * into upserted_member;

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
    case
      when existing_member.project_id is null then 'project.member_assigned'
      else 'project.member_updated'
    end,
    'project',
    p_project_id,
    p_request_id,
    case
      when existing_member.project_id is null then null
      else to_jsonb(existing_member)
    end,
    to_jsonb(upserted_member),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return to_jsonb(upserted_member);
end;
$$;

revoke execute on function public.upsert_project_member_audited(
  uuid, uuid, text, uuid, uuid, uuid, text, text
) from public, anon, authenticated;

grant execute on function public.upsert_project_member_audited(
  uuid, uuid, text, uuid, uuid, uuid, text, text
) to service_role;
