-- IEMS ERP: Phase 4 admin, policy, audit explorer and Director metric support.
--
-- FastAPI calls the RPCs below with the Supabase service-role key only after
-- JWT, RBAC/ABAC and Super User override checks. RLS remains enabled and direct
-- browser writes remain default-deny.

insert into public.permissions(code, description) values
('employee.manage','Create and update employee administrative records'),
('role.manage','Assign and revoke employee roles'),
('folder_template.manage','Manage project folder templates')
on conflict (code) do update
  set description = excluded.description;

insert into public.role_permissions(role_id, permission_id)
select r.id, p.id
from public.roles r
join public.permissions p on
  (r.code = 'ADMIN' and p.code in ('employee.manage')) or
  (r.code = 'SUPER_ADMIN' and p.code in (
    'employee.manage',
    'role.manage',
    'folder_template.manage'
  ))
on conflict do nothing;

create or replace view public.director_upcoming_events_v
with (security_invoker = true) as
select
  ce.id,
  ce.title,
  ce.event_type,
  ce.starts_at,
  ce.ends_at,
  p.project_code,
  p.name as project_name,
  ce.location
from public.calendar_events ce
left join public.projects p on p.id = ce.project_id
where ce.starts_at >= now();

create or replace view public.director_missing_required_documents_v
with (security_invoker = true) as
select
  p.id as project_id,
  p.project_code,
  p.name as project_name,
  dt.id as document_type_id,
  dt.code as document_type_code,
  dt.name as document_type_name
from public.projects p
cross join public.document_types dt
left join public.documents d
  on d.project_id = p.id
 and d.document_type_id = dt.id
 and d.deleted_at is null
 and d.status <> 'DELETED'
where p.deleted_at is null
  and p.archived_at is null
  and dt.is_required_for_archive = true
  and d.id is null;

create or replace view public.director_archive_verification_due_v
with (security_invoker = true) as
select
  pf.id,
  pf.physical_file_code,
  p.project_code,
  p.name as project_name,
  ar.name as archive_room,
  al.code as archive_location_code,
  pf.last_verified_at,
  pf.next_verification_at
from public.physical_files pf
join public.projects p on p.id = pf.project_id
join public.archive_locations al on al.id = pf.archive_location_id
join public.archive_rooms ar on ar.id = al.archive_room_id
where pf.next_verification_at is not null
  and pf.next_verification_at <= now();

create or replace function public.phase4_record_override_if_needed(
  p_actor_user_account_id uuid,
  p_actor_employee_id uuid,
  p_action_code text,
  p_resource_type text,
  p_resource_id uuid,
  p_override_reason text,
  p_request_id uuid,
  p_ip_address inet,
  p_user_agent text
)
returns void
language plpgsql
set search_path = public, pg_catalog
as $$
declare
  override_id uuid;
begin
  if p_override_reason is null then
    return;
  end if;

  if length(trim(p_override_reason)) < 8 then
    raise exception 'IEMS_SUPER_USER_OVERRIDE_REASON_REQUIRED';
  end if;

  insert into public.super_user_overrides(
    user_account_id,
    action_code,
    resource_type,
    resource_id,
    reason
  )
  values (
    p_actor_user_account_id,
    p_action_code,
    p_resource_type,
    p_resource_id,
    trim(p_override_reason)
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
    ip_address,
    user_agent
  )
  values (
    p_actor_user_account_id,
    p_actor_employee_id,
    'super_user.override_used',
    p_resource_type,
    p_resource_id,
    p_request_id,
    jsonb_build_object(
      'override_id', override_id,
      'override_action_code', p_action_code,
      'reason', trim(p_override_reason)
    ),
    p_ip_address,
    p_user_agent
  );
end;
$$;

create or replace function public.employee_admin_response_json(p_employee_id uuid)
returns jsonb
language sql
stable
set search_path = public, pg_catalog
as $$
  select jsonb_build_object(
    'id', e.id,
    'employee_code', e.employee_code,
    'full_name', e.full_name,
    'official_email', e.official_email,
    'phone', e.phone,
    'designation', e.designation,
    'employment_status', e.employment_status,
    'joined_on', e.joined_on,
    'left_on', e.left_on,
    'created_at', e.created_at,
    'updated_at', e.updated_at,
    'current_department', (
      select jsonb_build_object(
        'id', d.id,
        'code', d.code,
        'name', d.name
      )
      from public.employee_department_assignments eda
      join public.departments d on d.id = eda.department_id
      where eda.employee_id = e.id
        and eda.valid_to is null
      order by eda.valid_from desc
      limit 1
    ),
    'account', (
      select jsonb_build_object(
        'id', ua.id,
        'is_active', ua.is_active,
        'is_super_user', ua.is_super_user
      )
      from public.user_accounts ua
      where ua.employee_id = e.id
      limit 1
    ),
    'roles', coalesce((
      select jsonb_agg(
        jsonb_build_object(
          'employee_id', e.id,
          'user_account_id', ua.id,
          'role', jsonb_build_object(
            'id', r.id,
            'code', r.code,
            'name', r.name,
            'description', r.description
          ),
          'assigned_at', ura.assigned_at,
          'expires_at', ura.expires_at
        )
        order by r.name
      )
      from public.user_accounts ua
      join public.user_role_assignments ura on ura.user_account_id = ua.id
      join public.roles r on r.id = ura.role_id
      where ua.employee_id = e.id
    ), '[]'::jsonb)
  )
  from public.employees e
  where e.id = p_employee_id
$$;

create or replace function public.role_assignment_response_json(
  p_employee_id uuid,
  p_role_id uuid
)
returns jsonb
language sql
stable
set search_path = public, pg_catalog
as $$
  select jsonb_build_object(
    'employee_id', e.id,
    'user_account_id', ua.id,
    'role', jsonb_build_object(
      'id', r.id,
      'code', r.code,
      'name', r.name,
      'description', r.description
    ),
    'assigned_at', ura.assigned_at,
    'expires_at', ura.expires_at
  )
  from public.employees e
  join public.user_accounts ua on ua.employee_id = e.id
  join public.user_role_assignments ura on ura.user_account_id = ua.id
  join public.roles r on r.id = ura.role_id
  where e.id = p_employee_id
    and r.id = p_role_id
$$;

create or replace function public.department_assignment_response_json(p_assignment_id uuid)
returns jsonb
language sql
stable
set search_path = public, pg_catalog
as $$
  select jsonb_build_object(
    'id', eda.id,
    'employee_id', eda.employee_id,
    'department', jsonb_build_object(
      'id', d.id,
      'code', d.code,
      'name', d.name
    ),
    'valid_from', eda.valid_from,
    'valid_to', eda.valid_to,
    'assigned_by', eda.assigned_by
  )
  from public.employee_department_assignments eda
  join public.departments d on d.id = eda.department_id
  where eda.id = p_assignment_id
$$;

create or replace function public.policy_response_json(p_policy_id uuid)
returns jsonb
language sql
stable
set search_path = public, pg_catalog
as $$
  select to_jsonb(p)
  from public.policies p
  where p.id = p_policy_id
$$;

create or replace function public.folder_template_response_json(p_template_id uuid)
returns jsonb
language sql
stable
set search_path = public, pg_catalog
as $$
  select jsonb_build_object(
    'id', ft.id,
    'name', ft.name,
    'project_type_id', ft.project_type_id,
    'is_active', ft.is_active,
    'created_by', ft.created_by,
    'created_at', ft.created_at,
    'items', coalesce((
      select jsonb_agg(
        jsonb_build_object(
          'id', fti.id,
          'template_id', fti.template_id,
          'parent_item_id', fti.parent_item_id,
          'name', fti.name,
          'sort_order', fti.sort_order
        )
        order by fti.sort_order, fti.name
      )
      from public.folder_template_items fti
      where fti.template_id = ft.id
    ), '[]'::jsonb)
  )
  from public.folder_templates ft
  where ft.id = p_template_id
$$;

create or replace function public.archive_room_response_json(p_archive_room_id uuid)
returns jsonb
language sql
stable
set search_path = public, pg_catalog
as $$
  select jsonb_build_object(
    'id', ar.id,
    'code', ar.code,
    'name', ar.name,
    'description', ar.description,
    'is_active', ar.is_active
  )
  from public.archive_rooms ar
  where ar.id = p_archive_room_id
$$;

create or replace function public.create_employee_audited(
  p_employee_code text,
  p_full_name text,
  p_official_email text,
  p_phone text,
  p_designation text,
  p_employment_status text,
  p_joined_on date,
  p_actor_user_account_id uuid,
  p_actor_employee_id uuid,
  p_request_id uuid,
  p_ip_address inet,
  p_user_agent text,
  p_override_reason text default null
)
returns jsonb
language plpgsql
set search_path = public, pg_catalog
as $$
declare
  inserted_employee public.employees%rowtype;
  response jsonb;
begin
  insert into public.employees(
    employee_code,
    full_name,
    official_email,
    phone,
    designation,
    employment_status,
    joined_on
  )
  values (
    trim(p_employee_code),
    trim(p_full_name),
    lower(trim(p_official_email))::extensions.citext,
    nullif(trim(coalesce(p_phone, '')), ''),
    nullif(trim(coalesce(p_designation, '')), ''),
    p_employment_status,
    p_joined_on
  )
  returning * into inserted_employee;

  perform public.phase4_record_override_if_needed(
    p_actor_user_account_id,
    p_actor_employee_id,
    'employee.create',
    'employee',
    inserted_employee.id,
    p_override_reason,
    p_request_id,
    p_ip_address,
    p_user_agent
  );

  response := public.employee_admin_response_json(inserted_employee.id);

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
    'employee.created',
    'employee',
    inserted_employee.id,
    p_request_id,
    response,
    p_ip_address,
    p_user_agent
  );

  return response;
end;
$$;

create or replace function public.update_employee_audited(
  p_employee_id uuid,
  p_patch jsonb,
  p_actor_user_account_id uuid,
  p_actor_employee_id uuid,
  p_request_id uuid,
  p_ip_address inet,
  p_user_agent text,
  p_override_reason text default null
)
returns jsonb
language plpgsql
set search_path = public, pg_catalog
as $$
declare
  existing_employee public.employees%rowtype;
  updated_employee public.employees%rowtype;
  response jsonb;
begin
  select * into existing_employee
  from public.employees
  where id = p_employee_id
  for update;

  if existing_employee.id is null then
    raise exception 'IEMS_EMPLOYEE_NOT_FOUND';
  end if;

  update public.employees
  set
    full_name = case when p_patch ? 'full_name' then trim(p_patch->>'full_name') else full_name end,
    phone = case when p_patch ? 'phone' then nullif(trim(coalesce(p_patch->>'phone', '')), '') else phone end,
    designation = case when p_patch ? 'designation' then nullif(trim(coalesce(p_patch->>'designation', '')), '') else designation end,
    employment_status = case when p_patch ? 'employment_status' then p_patch->>'employment_status' else employment_status end,
    joined_on = case when p_patch ? 'joined_on' then (p_patch->>'joined_on')::date else joined_on end,
    left_on = case when p_patch ? 'left_on' then (p_patch->>'left_on')::date else left_on end
  where id = p_employee_id
  returning * into updated_employee;

  perform public.phase4_record_override_if_needed(
    p_actor_user_account_id,
    p_actor_employee_id,
    'employee.update',
    'employee',
    p_employee_id,
    p_override_reason,
    p_request_id,
    p_ip_address,
    p_user_agent
  );

  response := public.employee_admin_response_json(updated_employee.id);

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
    'employee.updated',
    'employee',
    p_employee_id,
    p_request_id,
    to_jsonb(existing_employee),
    response,
    p_ip_address,
    p_user_agent
  );

  return response;
end;
$$;

create or replace function public.assign_employee_role_audited(
  p_employee_id uuid,
  p_role_id uuid,
  p_expires_at timestamptz,
  p_actor_user_account_id uuid,
  p_actor_employee_id uuid,
  p_request_id uuid,
  p_ip_address inet,
  p_user_agent text,
  p_override_reason text default null
)
returns jsonb
language plpgsql
set search_path = public, pg_catalog
as $$
declare
  target_account public.user_accounts%rowtype;
  target_role public.roles%rowtype;
  response jsonb;
begin
  select * into target_account
  from public.user_accounts
  where employee_id = p_employee_id
  for update;

  if target_account.id is null then
    raise exception 'IEMS_EMPLOYEE_ACCOUNT_NOT_FOUND';
  end if;

  select * into target_role
  from public.roles
  where id = p_role_id;

  if target_role.id is null then
    raise exception 'IEMS_ROLE_NOT_FOUND';
  end if;

  if target_role.code = 'SUPER_USER' then
    if target_account.id = p_actor_user_account_id then
      raise exception 'IEMS_SELF_SUPER_USER_CHANGE_DENIED';
    end if;
    if p_override_reason is null or length(trim(p_override_reason)) < 8 then
      raise exception 'IEMS_SUPER_USER_OVERRIDE_REASON_REQUIRED';
    end if;
  end if;

  insert into public.user_role_assignments(
    user_account_id,
    role_id,
    assigned_by,
    assigned_at,
    expires_at
  )
  values (
    target_account.id,
    p_role_id,
    p_actor_user_account_id,
    now(),
    p_expires_at
  )
  on conflict (user_account_id, role_id) do update
    set assigned_by = excluded.assigned_by,
        assigned_at = excluded.assigned_at,
        expires_at = excluded.expires_at;

  if target_role.code = 'SUPER_USER' then
    update public.user_accounts
    set is_super_user = true
    where id = target_account.id;
  end if;

  perform public.phase4_record_override_if_needed(
    p_actor_user_account_id,
    p_actor_employee_id,
    'role.assign',
    'employee',
    p_employee_id,
    p_override_reason,
    p_request_id,
    p_ip_address,
    p_user_agent
  );

  response := public.role_assignment_response_json(p_employee_id, p_role_id);

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
    'role.assigned',
    'employee',
    p_employee_id,
    p_request_id,
    response,
    p_ip_address,
    p_user_agent
  );

  return response;
end;
$$;

create or replace function public.remove_employee_role_audited(
  p_employee_id uuid,
  p_role_id uuid,
  p_actor_user_account_id uuid,
  p_actor_employee_id uuid,
  p_request_id uuid,
  p_ip_address inet,
  p_user_agent text,
  p_override_reason text default null
)
returns jsonb
language plpgsql
set search_path = public, pg_catalog
as $$
declare
  target_account public.user_accounts%rowtype;
  target_role public.roles%rowtype;
  old_assignment jsonb;
begin
  select * into target_account
  from public.user_accounts
  where employee_id = p_employee_id
  for update;

  if target_account.id is null then
    raise exception 'IEMS_EMPLOYEE_ACCOUNT_NOT_FOUND';
  end if;

  select * into target_role
  from public.roles
  where id = p_role_id;

  if target_role.id is null then
    raise exception 'IEMS_ROLE_NOT_FOUND';
  end if;

  if target_role.code = 'SUPER_USER' then
    if target_account.id = p_actor_user_account_id then
      raise exception 'IEMS_SELF_SUPER_USER_CHANGE_DENIED';
    end if;
    if p_override_reason is null or length(trim(p_override_reason)) < 8 then
      raise exception 'IEMS_SUPER_USER_OVERRIDE_REASON_REQUIRED';
    end if;
  end if;

  old_assignment := public.role_assignment_response_json(p_employee_id, p_role_id);

  delete from public.user_role_assignments
  where user_account_id = target_account.id
    and role_id = p_role_id;

  if target_role.code = 'SUPER_USER' then
    update public.user_accounts
    set is_super_user = false
    where id = target_account.id;
  end if;

  perform public.phase4_record_override_if_needed(
    p_actor_user_account_id,
    p_actor_employee_id,
    'role.remove',
    'employee',
    p_employee_id,
    p_override_reason,
    p_request_id,
    p_ip_address,
    p_user_agent
  );

  insert into public.audit_events(
    actor_user_account_id,
    actor_employee_id,
    action_code,
    resource_type,
    resource_id,
    request_id,
    old_values,
    ip_address,
    user_agent
  )
  values (
    p_actor_user_account_id,
    p_actor_employee_id,
    'role.removed',
    'employee',
    p_employee_id,
    p_request_id,
    old_assignment,
    p_ip_address,
    p_user_agent
  );

  return jsonb_build_object('removed', true);
end;
$$;

create or replace function public.assign_employee_department_audited(
  p_employee_id uuid,
  p_department_id uuid,
  p_valid_from date,
  p_actor_user_account_id uuid,
  p_actor_employee_id uuid,
  p_request_id uuid,
  p_ip_address inet,
  p_user_agent text,
  p_override_reason text default null
)
returns jsonb
language plpgsql
set search_path = public, pg_catalog
as $$
declare
  inserted_assignment public.employee_department_assignments%rowtype;
  response jsonb;
begin
  if not exists (select 1 from public.employees where id = p_employee_id) then
    raise exception 'IEMS_EMPLOYEE_NOT_FOUND';
  end if;
  if not exists (select 1 from public.departments where id = p_department_id) then
    raise exception 'IEMS_DEPARTMENT_NOT_FOUND';
  end if;

  update public.employee_department_assignments
  set valid_to = greatest(p_valid_from - 1, valid_from)
  where employee_id = p_employee_id
    and valid_to is null;

  insert into public.employee_department_assignments(
    employee_id,
    department_id,
    valid_from,
    assigned_by
  )
  values (
    p_employee_id,
    p_department_id,
    p_valid_from,
    p_actor_employee_id
  )
  returning * into inserted_assignment;

  perform public.phase4_record_override_if_needed(
    p_actor_user_account_id,
    p_actor_employee_id,
    'employee.department_assign',
    'employee',
    p_employee_id,
    p_override_reason,
    p_request_id,
    p_ip_address,
    p_user_agent
  );

  response := public.department_assignment_response_json(inserted_assignment.id);

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
    'employee.department_assigned',
    'employee',
    p_employee_id,
    p_request_id,
    response,
    p_ip_address,
    p_user_agent
  );

  return response;
end;
$$;

create or replace function public.create_policy_audited(
  p_name text,
  p_action_code text,
  p_effect text,
  p_priority integer,
  p_conditions jsonb,
  p_is_active boolean,
  p_actor_user_account_id uuid,
  p_actor_employee_id uuid,
  p_request_id uuid,
  p_ip_address inet,
  p_user_agent text,
  p_override_reason text default null
)
returns jsonb
language plpgsql
set search_path = public, pg_catalog
as $$
declare
  inserted_policy public.policies%rowtype;
  response jsonb;
begin
  insert into public.policies(
    name,
    action_code,
    effect,
    priority,
    conditions,
    is_active,
    created_by
  )
  values (
    trim(p_name),
    trim(p_action_code),
    p_effect,
    p_priority,
    coalesce(p_conditions, '{}'::jsonb),
    p_is_active,
    p_actor_user_account_id
  )
  returning * into inserted_policy;

  perform public.phase4_record_override_if_needed(
    p_actor_user_account_id,
    p_actor_employee_id,
    'policy.create',
    'policy',
    inserted_policy.id,
    p_override_reason,
    p_request_id,
    p_ip_address,
    p_user_agent
  );

  response := public.policy_response_json(inserted_policy.id);

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
    'policy.created',
    'policy',
    inserted_policy.id,
    p_request_id,
    response,
    p_ip_address,
    p_user_agent
  );

  return response;
end;
$$;

create or replace function public.update_policy_audited(
  p_policy_id uuid,
  p_patch jsonb,
  p_actor_user_account_id uuid,
  p_actor_employee_id uuid,
  p_request_id uuid,
  p_ip_address inet,
  p_user_agent text,
  p_override_reason text default null
)
returns jsonb
language plpgsql
set search_path = public, pg_catalog
as $$
declare
  existing_policy public.policies%rowtype;
  updated_policy public.policies%rowtype;
  response jsonb;
begin
  select * into existing_policy
  from public.policies
  where id = p_policy_id
  for update;

  if existing_policy.id is null then
    raise exception 'IEMS_POLICY_NOT_FOUND';
  end if;

  update public.policies
  set
    name = case when p_patch ? 'name' then trim(p_patch->>'name') else name end,
    action_code = case when p_patch ? 'action_code' then trim(p_patch->>'action_code') else action_code end,
    effect = case when p_patch ? 'effect' then p_patch->>'effect' else effect end,
    priority = case when p_patch ? 'priority' then (p_patch->>'priority')::integer else priority end,
    conditions = case when p_patch ? 'conditions' then coalesce(p_patch->'conditions', '{}'::jsonb) else conditions end,
    is_active = case when p_patch ? 'is_active' then (p_patch->>'is_active')::boolean else is_active end
  where id = p_policy_id
  returning * into updated_policy;

  perform public.phase4_record_override_if_needed(
    p_actor_user_account_id,
    p_actor_employee_id,
    'policy.update',
    'policy',
    p_policy_id,
    p_override_reason,
    p_request_id,
    p_ip_address,
    p_user_agent
  );

  response := public.policy_response_json(updated_policy.id);

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
    'policy.changed',
    'policy',
    p_policy_id,
    p_request_id,
    to_jsonb(existing_policy),
    response,
    p_ip_address,
    p_user_agent
  );

  return response;
end;
$$;

create or replace function public.create_folder_template_audited(
  p_name text,
  p_project_type_id uuid,
  p_actor_user_account_id uuid,
  p_actor_employee_id uuid,
  p_request_id uuid,
  p_ip_address inet,
  p_user_agent text,
  p_override_reason text default null
)
returns jsonb
language plpgsql
set search_path = public, pg_catalog
as $$
declare
  inserted_template public.folder_templates%rowtype;
  response jsonb;
begin
  insert into public.folder_templates(name, project_type_id, created_by)
  values (trim(p_name), p_project_type_id, p_actor_employee_id)
  returning * into inserted_template;

  perform public.phase4_record_override_if_needed(
    p_actor_user_account_id,
    p_actor_employee_id,
    'folder_template.create',
    'folder_template',
    inserted_template.id,
    p_override_reason,
    p_request_id,
    p_ip_address,
    p_user_agent
  );

  response := public.folder_template_response_json(inserted_template.id);

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
    'folder_template.created',
    'folder_template',
    inserted_template.id,
    p_request_id,
    response,
    p_ip_address,
    p_user_agent
  );

  return response;
end;
$$;

create or replace function public.update_folder_template_audited(
  p_template_id uuid,
  p_patch jsonb,
  p_actor_user_account_id uuid,
  p_actor_employee_id uuid,
  p_request_id uuid,
  p_ip_address inet,
  p_user_agent text,
  p_override_reason text default null
)
returns jsonb
language plpgsql
set search_path = public, pg_catalog
as $$
declare
  existing_template public.folder_templates%rowtype;
  updated_template public.folder_templates%rowtype;
  response jsonb;
begin
  select * into existing_template
  from public.folder_templates
  where id = p_template_id
  for update;

  if existing_template.id is null then
    raise exception 'IEMS_FOLDER_TEMPLATE_NOT_FOUND';
  end if;

  update public.folder_templates
  set
    name = case when p_patch ? 'name' then trim(p_patch->>'name') else name end,
    project_type_id = case when p_patch ? 'project_type_id' then (p_patch->>'project_type_id')::uuid else project_type_id end,
    is_active = case when p_patch ? 'is_active' then (p_patch->>'is_active')::boolean else is_active end
  where id = p_template_id
  returning * into updated_template;

  perform public.phase4_record_override_if_needed(
    p_actor_user_account_id,
    p_actor_employee_id,
    'folder_template.update',
    'folder_template',
    p_template_id,
    p_override_reason,
    p_request_id,
    p_ip_address,
    p_user_agent
  );

  response := public.folder_template_response_json(updated_template.id);

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
    'folder_template.updated',
    'folder_template',
    p_template_id,
    p_request_id,
    to_jsonb(existing_template),
    response,
    p_ip_address,
    p_user_agent
  );

  return response;
end;
$$;

create or replace function public.create_folder_template_item_audited(
  p_template_id uuid,
  p_parent_item_id uuid,
  p_name text,
  p_sort_order integer,
  p_actor_user_account_id uuid,
  p_actor_employee_id uuid,
  p_request_id uuid,
  p_ip_address inet,
  p_user_agent text,
  p_override_reason text default null
)
returns jsonb
language plpgsql
set search_path = public, pg_catalog
as $$
declare
  inserted_item public.folder_template_items%rowtype;
  response jsonb;
begin
  if not exists (select 1 from public.folder_templates where id = p_template_id) then
    raise exception 'IEMS_FOLDER_TEMPLATE_NOT_FOUND';
  end if;
  if p_parent_item_id is not null and not exists (
    select 1
    from public.folder_template_items
    where id = p_parent_item_id
      and template_id = p_template_id
  ) then
    raise exception 'IEMS_FOLDER_TEMPLATE_ITEM_PARENT_INVALID';
  end if;

  insert into public.folder_template_items(
    template_id,
    parent_item_id,
    name,
    sort_order
  )
  values (p_template_id, p_parent_item_id, trim(p_name), p_sort_order)
  returning * into inserted_item;

  perform public.phase4_record_override_if_needed(
    p_actor_user_account_id,
    p_actor_employee_id,
    'folder_template.item_create',
    'folder_template_item',
    inserted_item.id,
    p_override_reason,
    p_request_id,
    p_ip_address,
    p_user_agent
  );

  response := public.folder_template_response_json(p_template_id);

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
    'folder_template.item_created',
    'folder_template_item',
    inserted_item.id,
    p_request_id,
    to_jsonb(inserted_item),
    p_ip_address,
    p_user_agent
  );

  return response;
end;
$$;

create or replace function public.update_folder_template_item_audited(
  p_item_id uuid,
  p_patch jsonb,
  p_actor_user_account_id uuid,
  p_actor_employee_id uuid,
  p_request_id uuid,
  p_ip_address inet,
  p_user_agent text,
  p_override_reason text default null
)
returns jsonb
language plpgsql
set search_path = public, pg_catalog
as $$
declare
  existing_item public.folder_template_items%rowtype;
  updated_item public.folder_template_items%rowtype;
  new_parent_id uuid;
  response jsonb;
begin
  select * into existing_item
  from public.folder_template_items
  where id = p_item_id
  for update;

  if existing_item.id is null then
    raise exception 'IEMS_FOLDER_TEMPLATE_ITEM_NOT_FOUND';
  end if;

  new_parent_id := case
    when p_patch ? 'parent_item_id' then (p_patch->>'parent_item_id')::uuid
    else existing_item.parent_item_id
  end;

  if new_parent_id = p_item_id then
    raise exception 'IEMS_FOLDER_TEMPLATE_ITEM_PARENT_INVALID';
  end if;
  if new_parent_id is not null and not exists (
    select 1
    from public.folder_template_items
    where id = new_parent_id
      and template_id = existing_item.template_id
  ) then
    raise exception 'IEMS_FOLDER_TEMPLATE_ITEM_PARENT_INVALID';
  end if;

  update public.folder_template_items
  set
    parent_item_id = new_parent_id,
    name = case when p_patch ? 'name' then trim(p_patch->>'name') else name end,
    sort_order = case when p_patch ? 'sort_order' then (p_patch->>'sort_order')::integer else sort_order end
  where id = p_item_id
  returning * into updated_item;

  perform public.phase4_record_override_if_needed(
    p_actor_user_account_id,
    p_actor_employee_id,
    'folder_template.item_update',
    'folder_template_item',
    p_item_id,
    p_override_reason,
    p_request_id,
    p_ip_address,
    p_user_agent
  );

  response := public.folder_template_response_json(updated_item.template_id);

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
    'folder_template.item_updated',
    'folder_template_item',
    p_item_id,
    p_request_id,
    to_jsonb(existing_item),
    to_jsonb(updated_item),
    p_ip_address,
    p_user_agent
  );

  return response;
end;
$$;

create or replace function public.update_archive_room_audited(
  p_archive_room_id uuid,
  p_patch jsonb,
  p_actor_user_account_id uuid,
  p_actor_employee_id uuid,
  p_request_id uuid,
  p_ip_address inet,
  p_user_agent text
)
returns jsonb
language plpgsql
set search_path = public, pg_catalog
as $$
declare
  existing_room public.archive_rooms%rowtype;
  updated_room public.archive_rooms%rowtype;
  response jsonb;
begin
  select * into existing_room
  from public.archive_rooms
  where id = p_archive_room_id
  for update;

  if existing_room.id is null then
    raise exception 'IEMS_ARCHIVE_ROOM_NOT_FOUND';
  end if;

  update public.archive_rooms
  set
    code = case when p_patch ? 'code' then trim(p_patch->>'code') else code end,
    name = case when p_patch ? 'name' then trim(p_patch->>'name') else name end,
    description = case when p_patch ? 'description' then nullif(trim(coalesce(p_patch->>'description', '')), '') else description end,
    is_active = case when p_patch ? 'is_active' then (p_patch->>'is_active')::boolean else is_active end
  where id = p_archive_room_id
  returning * into updated_room;

  response := public.archive_room_response_json(updated_room.id);

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
    'archive.room_updated',
    'archive_room',
    p_archive_room_id,
    p_request_id,
    to_jsonb(existing_room),
    response,
    p_ip_address,
    p_user_agent
  );

  return response;
end;
$$;

create or replace function public.update_archive_location_audited(
  p_archive_location_id uuid,
  p_patch jsonb,
  p_actor_user_account_id uuid,
  p_actor_employee_id uuid,
  p_request_id uuid,
  p_ip_address inet,
  p_user_agent text
)
returns jsonb
language plpgsql
set search_path = public, pg_catalog
as $$
declare
  existing_location public.archive_locations%rowtype;
  parent_location public.archive_locations%rowtype;
  updated_location public.archive_locations%rowtype;
  next_parent_id uuid;
  next_location_type text;
  response jsonb;
begin
  select * into existing_location
  from public.archive_locations
  where id = p_archive_location_id
  for update;

  if existing_location.id is null then
    raise exception 'IEMS_ARCHIVE_LOCATION_NOT_FOUND';
  end if;

  next_parent_id := case
    when p_patch ? 'parent_location_id' then (p_patch->>'parent_location_id')::uuid
    else existing_location.parent_location_id
  end;
  next_location_type := case
    when p_patch ? 'location_type' then p_patch->>'location_type'
    else existing_location.location_type
  end;

  if next_parent_id = p_archive_location_id then
    raise exception 'IEMS_ARCHIVE_LOCATION_PARENT_INVALID';
  end if;

  if next_parent_id is null then
    if next_location_type <> 'RACK' then
      raise exception 'IEMS_INVALID_ARCHIVE_LOCATION_HIERARCHY';
    end if;
  else
    select * into parent_location
    from public.archive_locations
    where id = next_parent_id
      and archive_room_id = existing_location.archive_room_id
      and is_active = true;

    if parent_location.id is null then
      raise exception 'IEMS_ARCHIVE_LOCATION_PARENT_INVALID';
    end if;

    if exists (
      with recursive descendants(id) as (
        select id
        from public.archive_locations
        where parent_location_id = p_archive_location_id
        union all
        select child.id
        from public.archive_locations child
        join descendants on descendants.id = child.parent_location_id
      )
      select 1
      from descendants
      where id = next_parent_id
    ) then
      raise exception 'IEMS_ARCHIVE_LOCATION_PARENT_INVALID';
    end if;

    if not (
      (parent_location.location_type = 'RACK' and next_location_type = 'SHELF')
      or (parent_location.location_type = 'SHELF' and next_location_type = 'CABINET')
      or (parent_location.location_type = 'CABINET' and next_location_type = 'BOX')
      or (parent_location.location_type = 'BOX' and next_location_type = 'FILE_SLOT')
    ) then
      raise exception 'IEMS_INVALID_ARCHIVE_LOCATION_HIERARCHY';
    end if;
  end if;

  if exists (
    select 1
    from public.archive_locations child
    where child.parent_location_id = p_archive_location_id
      and not (
        (next_location_type = 'RACK' and child.location_type = 'SHELF')
        or (next_location_type = 'SHELF' and child.location_type = 'CABINET')
        or (next_location_type = 'CABINET' and child.location_type = 'BOX')
        or (next_location_type = 'BOX' and child.location_type = 'FILE_SLOT')
      )
  ) then
    raise exception 'IEMS_INVALID_ARCHIVE_LOCATION_HIERARCHY';
  end if;

  update public.archive_locations
  set
    parent_location_id = next_parent_id,
    location_type = next_location_type,
    code = case when p_patch ? 'code' then trim(p_patch->>'code') else code end,
    label = case when p_patch ? 'label' then nullif(trim(coalesce(p_patch->>'label', '')), '') else label end,
    is_active = case when p_patch ? 'is_active' then (p_patch->>'is_active')::boolean else is_active end
  where id = p_archive_location_id
  returning * into updated_location;

  response := public.archive_location_response_json(updated_location.id);

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
    'archive.location_updated',
    'archive_location',
    p_archive_location_id,
    p_request_id,
    to_jsonb(existing_location),
    response,
    p_ip_address,
    p_user_agent
  );

  return response;
end;
$$;

revoke execute on function public.phase4_record_override_if_needed(uuid, uuid, text, text, uuid, text, uuid, inet, text) from public, anon, authenticated;
revoke execute on function public.employee_admin_response_json(uuid) from public, anon, authenticated;
revoke execute on function public.role_assignment_response_json(uuid, uuid) from public, anon, authenticated;
revoke execute on function public.department_assignment_response_json(uuid) from public, anon, authenticated;
revoke execute on function public.policy_response_json(uuid) from public, anon, authenticated;
revoke execute on function public.folder_template_response_json(uuid) from public, anon, authenticated;
revoke execute on function public.archive_room_response_json(uuid) from public, anon, authenticated;
revoke execute on function public.create_employee_audited(text, text, text, text, text, text, date, uuid, uuid, uuid, inet, text, text) from public, anon, authenticated;
revoke execute on function public.update_employee_audited(uuid, jsonb, uuid, uuid, uuid, inet, text, text) from public, anon, authenticated;
revoke execute on function public.assign_employee_role_audited(uuid, uuid, timestamptz, uuid, uuid, uuid, inet, text, text) from public, anon, authenticated;
revoke execute on function public.remove_employee_role_audited(uuid, uuid, uuid, uuid, uuid, inet, text, text) from public, anon, authenticated;
revoke execute on function public.assign_employee_department_audited(uuid, uuid, date, uuid, uuid, uuid, inet, text, text) from public, anon, authenticated;
revoke execute on function public.create_policy_audited(text, text, text, integer, jsonb, boolean, uuid, uuid, uuid, inet, text, text) from public, anon, authenticated;
revoke execute on function public.update_policy_audited(uuid, jsonb, uuid, uuid, uuid, inet, text, text) from public, anon, authenticated;
revoke execute on function public.create_folder_template_audited(text, uuid, uuid, uuid, uuid, inet, text, text) from public, anon, authenticated;
revoke execute on function public.update_folder_template_audited(uuid, jsonb, uuid, uuid, uuid, inet, text, text) from public, anon, authenticated;
revoke execute on function public.create_folder_template_item_audited(uuid, uuid, text, integer, uuid, uuid, uuid, inet, text, text) from public, anon, authenticated;
revoke execute on function public.update_folder_template_item_audited(uuid, jsonb, uuid, uuid, uuid, inet, text, text) from public, anon, authenticated;
revoke execute on function public.update_archive_room_audited(uuid, jsonb, uuid, uuid, uuid, inet, text) from public, anon, authenticated;
revoke execute on function public.update_archive_location_audited(uuid, jsonb, uuid, uuid, uuid, inet, text) from public, anon, authenticated;

grant execute on function public.phase4_record_override_if_needed(uuid, uuid, text, text, uuid, text, uuid, inet, text) to service_role;
grant execute on function public.employee_admin_response_json(uuid) to service_role;
grant execute on function public.role_assignment_response_json(uuid, uuid) to service_role;
grant execute on function public.department_assignment_response_json(uuid) to service_role;
grant execute on function public.policy_response_json(uuid) to service_role;
grant execute on function public.folder_template_response_json(uuid) to service_role;
grant execute on function public.archive_room_response_json(uuid) to service_role;
grant execute on function public.create_employee_audited(text, text, text, text, text, text, date, uuid, uuid, uuid, inet, text, text) to service_role;
grant execute on function public.update_employee_audited(uuid, jsonb, uuid, uuid, uuid, inet, text, text) to service_role;
grant execute on function public.assign_employee_role_audited(uuid, uuid, timestamptz, uuid, uuid, uuid, inet, text, text) to service_role;
grant execute on function public.remove_employee_role_audited(uuid, uuid, uuid, uuid, uuid, inet, text, text) to service_role;
grant execute on function public.assign_employee_department_audited(uuid, uuid, date, uuid, uuid, uuid, inet, text, text) to service_role;
grant execute on function public.create_policy_audited(text, text, text, integer, jsonb, boolean, uuid, uuid, uuid, inet, text, text) to service_role;
grant execute on function public.update_policy_audited(uuid, jsonb, uuid, uuid, uuid, inet, text, text) to service_role;
grant execute on function public.create_folder_template_audited(text, uuid, uuid, uuid, uuid, inet, text, text) to service_role;
grant execute on function public.update_folder_template_audited(uuid, jsonb, uuid, uuid, uuid, inet, text, text) to service_role;
grant execute on function public.create_folder_template_item_audited(uuid, uuid, text, integer, uuid, uuid, uuid, inet, text, text) to service_role;
grant execute on function public.update_folder_template_item_audited(uuid, jsonb, uuid, uuid, uuid, inet, text, text) to service_role;
grant execute on function public.update_archive_room_audited(uuid, jsonb, uuid, uuid, uuid, inet, text) to service_role;
grant execute on function public.update_archive_location_audited(uuid, jsonb, uuid, uuid, uuid, inet, text) to service_role;

grant select on public.director_upcoming_events_v to service_role;
grant select on public.director_missing_required_documents_v to service_role;
grant select on public.director_archive_verification_due_v to service_role;
