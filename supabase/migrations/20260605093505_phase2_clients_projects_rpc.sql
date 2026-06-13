-- IEMS ERP: Phase 2 audited clients/projects RPCs
--
-- These functions are called only by FastAPI with the Supabase service-role key.
-- They keep business writes and audit events in the same PostgreSQL transaction.

create or replace function public.project_response_json(p_project_id uuid)
returns jsonb
language sql
stable
set search_path = public, pg_catalog
as $$
  select jsonb_build_object(
    'id', p.id,
    'project_code', p.project_code,
    'client_id', p.client_id,
    'client', jsonb_build_object(
      'id', c.id,
      'client_code', c.client_code,
      'display_name', c.display_name
    ),
    'project_type_id', p.project_type_id,
    'project_type', jsonb_build_object(
      'id', pt.id,
      'code', pt.code,
      'name', pt.name
    ),
    'project_status_id', p.project_status_id,
    'project_status', jsonb_build_object(
      'id', ps.id,
      'code', ps.code,
      'name', ps.name
    ),
    'priority_level_id', p.priority_level_id,
    'priority_level', jsonb_build_object(
      'id', pl.id,
      'code', pl.code,
      'name', pl.name
    ),
    'name', p.name,
    'event_date', p.event_date,
    'venue', p.venue,
    'description', p.description,
    'project_manager_id', p.project_manager_id,
    'project_manager', case
      when pm.id is null then null
      else jsonb_build_object(
        'id', pm.id,
        'employee_code', pm.employee_code,
        'full_name', pm.full_name
      )
    end,
    'created_by', p.created_by,
    'created_at', p.created_at,
    'updated_at', p.updated_at,
    'archived_at', p.archived_at,
    'deleted_at', p.deleted_at,
    'root_folder_id', rf.id
  )
  from public.projects p
  join public.clients c on c.id = p.client_id
  join public.project_types pt on pt.id = p.project_type_id
  join public.project_statuses ps on ps.id = p.project_status_id
  join public.priority_levels pl on pl.id = p.priority_level_id
  left join public.employees pm on pm.id = p.project_manager_id
  left join public.folders rf
    on rf.project_id = p.id
   and rf.parent_folder_id is null
   and rf.deleted_at is null
  where p.id = p_project_id
$$;

create or replace function public.create_client_audited(
  p_client_code text,
  p_legal_name text,
  p_display_name text,
  p_notes text,
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
  inserted_client public.clients%rowtype;
begin
  insert into public.clients(client_code, legal_name, display_name, notes)
  values (
    upper(trim(p_client_code)),
    trim(p_legal_name),
    trim(p_display_name),
    nullif(trim(coalesce(p_notes, '')), '')
  )
  returning * into inserted_client;

  insert into public.audit_events(
    actor_user_account_id,
    actor_employee_id,
    action_code,
    resource_type,
    resource_id,
    request_id,
    new_values,
    ip_address,
    user_agent
  )
  values (
    p_actor_user_account_id,
    p_actor_employee_id,
    'client.created',
    'client',
    inserted_client.id,
    p_request_id,
    to_jsonb(inserted_client),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return to_jsonb(inserted_client);
end;
$$;

create or replace function public.update_client_audited(
  p_client_id uuid,
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
  set
    legal_name = case
      when p_patch ? 'legal_name' then trim(p_patch->>'legal_name')
      else legal_name
    end,
    display_name = case
      when p_patch ? 'display_name' then trim(p_patch->>'display_name')
      else display_name
    end,
    is_active = case
      when p_patch ? 'is_active' then (p_patch->>'is_active')::boolean
      else is_active
    end,
    notes = case
      when p_patch ? 'notes' then nullif(trim(coalesce(p_patch->>'notes', '')), '')
      else notes
    end
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
    'client.updated',
    'client',
    updated_client.id,
    p_request_id,
    to_jsonb(old_client),
    to_jsonb(updated_client),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return to_jsonb(updated_client);
end;
$$;

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
      'folder_template_id', selected_template_id
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
  upserted_member public.project_members%rowtype;
begin
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
    new_values,
    ip_address,
    user_agent
  )
  values (
    p_actor_user_account_id,
    p_actor_employee_id,
    'project.member_assigned',
    'project',
    p_project_id,
    p_request_id,
    to_jsonb(upserted_member),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return to_jsonb(upserted_member);
end;
$$;

create or replace function public.remove_project_member_audited(
  p_project_id uuid,
  p_employee_id uuid,
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
  old_member public.project_members%rowtype;
  updated_member public.project_members%rowtype;
  active_manage_count integer;
begin
  select * into old_member
  from public.project_members
  where project_id = p_project_id
    and employee_id = p_employee_id
    and removed_at is null
  for update;

  if old_member.project_id is null then
    raise exception 'IEMS_PROJECT_NOT_FOUND';
  end if;

  if old_member.access_level = 'MANAGE' then
    select count(*) into active_manage_count
    from public.project_members
    where project_id = p_project_id
      and access_level = 'MANAGE'
      and removed_at is null;

    if active_manage_count <= 1 then
      raise exception 'IEMS_LAST_PROJECT_MANAGER';
    end if;
  end if;

  update public.project_members
  set removed_at = now()
  where project_id = p_project_id
    and employee_id = p_employee_id
  returning * into updated_member;

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
    'project.member_removed',
    'project',
    p_project_id,
    p_request_id,
    to_jsonb(old_member),
    to_jsonb(updated_member),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return to_jsonb(updated_member);
end;
$$;

revoke execute on function public.project_response_json(uuid) from public, anon, authenticated;
revoke execute on function public.create_client_audited(text, text, text, text, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.update_client_audited(uuid, jsonb, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.create_project_with_folder_template(text, uuid, uuid, uuid, uuid, text, date, text, text, uuid, uuid, uuid, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.update_project_audited(uuid, jsonb, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.upsert_project_member_audited(uuid, uuid, text, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.remove_project_member_audited(uuid, uuid, uuid, uuid, uuid, text, text) from public, anon, authenticated;

grant execute on function public.project_response_json(uuid) to service_role;
grant execute on function public.create_client_audited(text, text, text, text, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.update_client_audited(uuid, jsonb, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.create_project_with_folder_template(text, uuid, uuid, uuid, uuid, text, date, text, text, uuid, uuid, uuid, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.update_project_audited(uuid, jsonb, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.upsert_project_member_audited(uuid, uuid, text, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.remove_project_member_audited(uuid, uuid, uuid, uuid, uuid, text, text) to service_role;
