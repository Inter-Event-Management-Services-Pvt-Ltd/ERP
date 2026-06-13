-- IEMS ERP: ensure assigned project managers receive project membership.
--
-- Project listing is intentionally scoped to active project_members rows for
-- users without project.manage. Creating or updating a project's
-- project_manager_id must therefore also grant that employee active MANAGE
-- membership, otherwise the assigned manager cannot see their project.

create or replace function public.create_project_with_folder_template(
  p_project_code text,
  p_client_id uuid,
  p_project_type_id uuid,
  p_project_status_id uuid,
  p_priority_level_id uuid,
  p_name text,
  p_event_date date,
  p_venue text,
  p_description text,
  p_project_manager_id uuid,
  p_created_by uuid,
  p_folder_template_id uuid,
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
  inserted_project public.projects%rowtype;
  selected_template_id uuid;
  root_folder_id uuid;
  inserted_count integer;
  template_item record;
  new_folder_id uuid;
begin
  if p_project_manager_id is not null and not exists (
    select 1
    from public.employees
    where id = p_project_manager_id
      and employment_status in ('ACTIVE','ON_LEAVE')
  ) then
    raise exception 'IEMS_EMPLOYEE_NOT_ACTIVE';
  end if;

  insert into public.projects(
    project_code,
    client_id,
    project_type_id,
    project_status_id,
    priority_level_id,
    name,
    event_date,
    venue,
    description,
    project_manager_id,
    created_by
  )
  values (
    upper(trim(p_project_code)),
    p_client_id,
    p_project_type_id,
    p_project_status_id,
    p_priority_level_id,
    trim(p_name),
    p_event_date,
    nullif(trim(coalesce(p_venue, '')), ''),
    nullif(trim(coalesce(p_description, '')), ''),
    p_project_manager_id,
    p_created_by
  )
  returning * into inserted_project;

  insert into public.project_members(project_id, employee_id, access_level, assigned_by)
  values (inserted_project.id, p_created_by, 'MANAGE', p_created_by)
  on conflict (project_id, employee_id) do update
    set access_level = 'MANAGE',
        assigned_by = excluded.assigned_by,
        assigned_at = now(),
        removed_at = null;

  if p_project_manager_id is not null then
    insert into public.project_members(project_id, employee_id, access_level, assigned_by)
    values (inserted_project.id, p_project_manager_id, 'MANAGE', p_created_by)
    on conflict (project_id, employee_id) do update
      set access_level = 'MANAGE',
          assigned_by = excluded.assigned_by,
          assigned_at = now(),
          removed_at = null;
  end if;

  insert into public.folders(project_id, parent_folder_id, name, sort_order, created_by)
  values (inserted_project.id, null, inserted_project.project_code, 0, p_created_by)
  returning id into root_folder_id;

  if p_folder_template_id is not null then
    select id into selected_template_id
    from public.folder_templates
    where id = p_folder_template_id
      and is_active = true;
  else
    select id into selected_template_id
    from public.folder_templates
    where is_active = true
      and (project_type_id = p_project_type_id or project_type_id is null)
    order by
      case when project_type_id = p_project_type_id then 0 else 1 end,
      created_at,
      name
    limit 1;
  end if;

  if p_folder_template_id is not null and selected_template_id is null then
    raise exception 'IEMS_FOLDER_TEMPLATE_NOT_FOUND';
  end if;

  if selected_template_id is not null then
    create temp table if not exists pg_temp.iems_folder_item_map (
      template_item_id uuid primary key,
      folder_id uuid not null
    ) on commit drop;

    truncate table pg_temp.iems_folder_item_map;

    for template_item in
      select id, name, sort_order
      from public.folder_template_items
      where template_id = selected_template_id
        and parent_item_id is null
      order by sort_order, name
    loop
      insert into public.folders(project_id, parent_folder_id, name, sort_order, created_by)
      values (
        inserted_project.id,
        root_folder_id,
        template_item.name,
        template_item.sort_order,
        p_created_by
      )
      returning id into new_folder_id;

      insert into pg_temp.iems_folder_item_map(template_item_id, folder_id)
      values (template_item.id, new_folder_id);
    end loop;

    loop
      inserted_count := 0;

      for template_item in
        select item.id, item.name, item.sort_order, parent_map.folder_id as parent_folder_id
        from public.folder_template_items item
        join pg_temp.iems_folder_item_map parent_map
          on parent_map.template_item_id = item.parent_item_id
        left join pg_temp.iems_folder_item_map existing_map
          on existing_map.template_item_id = item.id
        where item.template_id = selected_template_id
          and existing_map.template_item_id is null
        order by item.sort_order, item.name
      loop
        insert into public.folders(project_id, parent_folder_id, name, sort_order, created_by)
        values (
          inserted_project.id,
          template_item.parent_folder_id,
          template_item.name,
          template_item.sort_order,
          p_created_by
        )
        returning id into new_folder_id;

        insert into pg_temp.iems_folder_item_map(template_item_id, folder_id)
        values (template_item.id, new_folder_id);

        inserted_count := inserted_count + 1;
      end loop;

      exit when inserted_count = 0;
    end loop;
  end if;

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
    p_actor_user_account_id,
    p_actor_employee_id,
    'project.created',
    'project',
    inserted_project.id,
    p_request_id,
    to_jsonb(inserted_project),
    jsonb_build_object(
      'root_folder_id', root_folder_id,
      'folder_template_id', selected_template_id,
      'initial_manage_member_ids',
      (
        select jsonb_agg(pm.employee_id order by pm.employee_id)
        from public.project_members pm
        where pm.project_id = inserted_project.id
          and pm.access_level = 'MANAGE'
          and pm.removed_at is null
      )
    ),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.project_response_json(inserted_project.id);
end;
$$;

create or replace function public.update_project_audited(
  p_project_id uuid,
  p_patch jsonb,
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

  if p_patch ? 'project_manager_id'
    and p_patch->>'project_manager_id' is not null
    and not exists (
      select 1
      from public.employees
      where id = (p_patch->>'project_manager_id')::uuid
        and employment_status in ('ACTIVE','ON_LEAVE')
    )
  then
    raise exception 'IEMS_EMPLOYEE_NOT_ACTIVE';
  end if;

  update public.projects
  set
    client_id = case
      when p_patch ? 'client_id' then (p_patch->>'client_id')::uuid
      else client_id
    end,
    project_type_id = case
      when p_patch ? 'project_type_id' then (p_patch->>'project_type_id')::uuid
      else project_type_id
    end,
    project_status_id = case
      when p_patch ? 'project_status_id' then (p_patch->>'project_status_id')::uuid
      else project_status_id
    end,
    priority_level_id = case
      when p_patch ? 'priority_level_id' then (p_patch->>'priority_level_id')::uuid
      else priority_level_id
    end,
    name = case
      when p_patch ? 'name' then trim(p_patch->>'name')
      else name
    end,
    event_date = case
      when p_patch ? 'event_date' and p_patch->>'event_date' is not null
        then (p_patch->>'event_date')::date
      when p_patch ? 'event_date' then null
      else event_date
    end,
    venue = case
      when p_patch ? 'venue' then nullif(trim(coalesce(p_patch->>'venue', '')), '')
      else venue
    end,
    description = case
      when p_patch ? 'description' then nullif(trim(coalesce(p_patch->>'description', '')), '')
      else description
    end,
    project_manager_id = case
      when p_patch ? 'project_manager_id' and p_patch->>'project_manager_id' is not null
        then (p_patch->>'project_manager_id')::uuid
      when p_patch ? 'project_manager_id' then null
      else project_manager_id
    end,
    archived_at = case
      when p_patch ? 'archived_at' and p_patch->>'archived_at' is not null
        then (p_patch->>'archived_at')::timestamptz
      when p_patch ? 'archived_at' then null
      else archived_at
    end
  where id = p_project_id
  returning * into updated_project;

  if updated_project.project_manager_id is not null then
    insert into public.project_members(project_id, employee_id, access_level, assigned_by)
    values (updated_project.id, updated_project.project_manager_id, 'MANAGE', p_actor_employee_id)
    on conflict (project_id, employee_id) do update
      set access_level = 'MANAGE',
          assigned_by = excluded.assigned_by,
          assigned_at = now(),
          removed_at = null;
  end if;

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
    'project.updated',
    'project',
    updated_project.id,
    p_request_id,
    to_jsonb(old_project),
    to_jsonb(updated_project),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.project_response_json(updated_project.id);
end;
$$;

insert into public.project_members(project_id, employee_id, access_level, assigned_by)
select p.id, p.project_manager_id, 'MANAGE', p.created_by
from public.projects p
join public.employees e on e.id = p.project_manager_id
where p.project_manager_id is not null
  and p.deleted_at is null
  and e.employment_status in ('ACTIVE','ON_LEAVE')
on conflict (project_id, employee_id) do update
  set access_level = 'MANAGE',
      assigned_by = excluded.assigned_by,
      assigned_at = now(),
      removed_at = null;

revoke execute on function public.create_project_with_folder_template(
  text, uuid, uuid, uuid, uuid, text, date, text, text, uuid, uuid, uuid, uuid, uuid, uuid, text, text
) from public, anon, authenticated;
revoke execute on function public.update_project_audited(
  uuid, jsonb, uuid, uuid, uuid, text, text
) from public, anon, authenticated;

grant execute on function public.create_project_with_folder_template(
  text, uuid, uuid, uuid, uuid, text, date, text, text, uuid, uuid, uuid, uuid, uuid, uuid, text, text
) to service_role;
grant execute on function public.update_project_audited(
  uuid, jsonb, uuid, uuid, uuid, text, text
) to service_role;
