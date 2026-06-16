\set ON_ERROR_STOP on

begin;

do $$
declare
  actor_employee_id uuid := '99000000-0000-4000-8000-000000000005'::uuid;
  target_employee_id uuid := '99000000-0000-4000-8000-000000000006'::uuid;
  actor_user_account_id uuid := '99000000-0000-4000-8000-000000000001'::uuid;
  target_user_account_id uuid := '99000000-0000-4000-8000-000000000002'::uuid;
  manager_role_id uuid := (select id from public.roles where code = 'MANAGER');
  super_user_role_id uuid := (select id from public.roles where code = 'SUPER_USER');
  ops_department_id uuid := (select id from public.departments where code = 'OPS');
  room_id uuid := '99000000-0000-4000-8000-000000000003'::uuid;
  location_id uuid := '99000000-0000-4000-8000-000000000004'::uuid;
  child_location_id uuid := '99000000-0000-4000-8000-000000000007'::uuid;
  created_employee jsonb;
  employee_id uuid;
  role_payload jsonb;
  department_payload jsonb;
  policy_payload jsonb;
  policy_id uuid;
  template_payload jsonb;
  template_id uuid;
  item_id uuid;
  room_payload jsonb;
  location_payload jsonb;
begin
  insert into public.employees(
    id,
    employee_code,
    full_name,
    official_email,
    designation,
    employment_status
  )
  values
    (actor_employee_id, 'IEMS-PH4-ACTOR', 'Phase 4 Actor', 'phase4.actor@iemsnewdelhi.com', 'Validation Actor', 'ACTIVE'),
    (target_employee_id, 'IEMS-PH4-TARGET', 'Phase 4 Target', 'phase4.target@iemsnewdelhi.com', 'Validation Target', 'ACTIVE');

  insert into auth.users(
    instance_id,
    id,
    aud,
    role,
    email,
    encrypted_password,
    email_confirmed_at,
    created_at,
    updated_at
  )
  values
    ('00000000-0000-0000-0000-000000000000', actor_user_account_id, 'authenticated', 'authenticated', 'phase4.actor@iemsnewdelhi.com', '', now(), now(), now()),
    ('00000000-0000-0000-0000-000000000000', target_user_account_id, 'authenticated', 'authenticated', 'phase4.target@iemsnewdelhi.com', '', now(), now(), now());

  insert into public.user_accounts(id, employee_id, is_active, is_super_user)
  values
    (actor_user_account_id, actor_employee_id, true, true),
    (target_user_account_id, target_employee_id, true, false)
  on conflict (id) do update
    set employee_id = excluded.employee_id,
        is_active = excluded.is_active,
        is_super_user = excluded.is_super_user;

  created_employee := public.create_employee_audited(
    'IEMS-PH4-999',
    'Phase 4 Validation Employee',
    'phase4.validation@iemsnewdelhi.com',
    null,
    'Validation',
    'ACTIVE',
    current_date,
    actor_user_account_id,
    actor_employee_id,
    '99000000-0000-4000-8000-000000000010'::uuid,
    '127.0.0.1',
    'phase4-admin-policy-audit-sql-validation',
    null
  );
  employee_id := (created_employee->>'id')::uuid;

  if created_employee->>'employee_code' <> 'IEMS-PH4-999' then
    raise exception 'create_employee_audited returned wrong employee';
  end if;

  if not exists (
    select 1 from public.audit_events
    where action_code = 'employee.created'
      and resource_id = employee_id
  ) then
    raise exception 'employee create audit event missing';
  end if;

  role_payload := public.assign_employee_role_audited(
    target_employee_id,
    manager_role_id,
    null,
    actor_user_account_id,
    actor_employee_id,
    '99000000-0000-4000-8000-000000000011'::uuid,
    '127.0.0.1',
    'phase4-admin-policy-audit-sql-validation',
    null
  );

  if role_payload->'role'->>'code' <> 'MANAGER' then
    raise exception 'assign_employee_role_audited returned wrong role';
  end if;

  begin
    perform public.assign_employee_role_audited(
      actor_employee_id,
      super_user_role_id,
      null,
      actor_user_account_id,
      actor_employee_id,
      '99000000-0000-4000-8000-000000000012'::uuid,
      '127.0.0.1',
      'phase4-admin-policy-audit-sql-validation',
      'self elevation should fail'
    );
    raise exception 'Expected self Super User role assignment to fail';
  exception
    when raise_exception then
      if sqlerrm <> 'IEMS_SELF_SUPER_USER_CHANGE_DENIED' then
        raise;
      end if;
  end;

  department_payload := public.assign_employee_department_audited(
    target_employee_id,
    ops_department_id,
    current_date,
    actor_user_account_id,
    actor_employee_id,
    '99000000-0000-4000-8000-000000000013'::uuid,
    '127.0.0.1',
    'phase4-admin-policy-audit-sql-validation',
    null
  );

  if department_payload->'department'->>'code' <> 'OPS' then
    raise exception 'department assignment response is invalid';
  end if;

  policy_payload := public.create_policy_audited(
    'Phase 4 validation policy',
    'phase4.validation',
    'ALLOW',
    10,
    '{"scope":"validation"}'::jsonb,
    true,
    actor_user_account_id,
    actor_employee_id,
    '99000000-0000-4000-8000-000000000014'::uuid,
    '127.0.0.1',
    'phase4-admin-policy-audit-sql-validation',
    null
  );
  policy_id := (policy_payload->>'id')::uuid;

  policy_payload := public.update_policy_audited(
    policy_id,
    '{"priority": 20}'::jsonb,
    actor_user_account_id,
    actor_employee_id,
    '99000000-0000-4000-8000-000000000015'::uuid,
    '127.0.0.1',
    'phase4-admin-policy-audit-sql-validation',
    null
  );

  if (policy_payload->>'priority')::integer <> 20 then
    raise exception 'policy update response is invalid';
  end if;

  if not exists (
    select 1 from public.audit_events
    where action_code = 'policy.changed'
      and resource_id = policy_id
  ) then
    raise exception 'policy update audit event missing';
  end if;

  template_payload := public.create_folder_template_audited(
    'Phase 4 Validation Template',
    null,
    actor_user_account_id,
    actor_employee_id,
    '99000000-0000-4000-8000-000000000016'::uuid,
    '127.0.0.1',
    'phase4-admin-policy-audit-sql-validation',
    null
  );
  template_id := (template_payload->>'id')::uuid;

  template_payload := public.create_folder_template_item_audited(
    template_id,
    null,
    '01 Validation',
    10,
    actor_user_account_id,
    actor_employee_id,
    '99000000-0000-4000-8000-000000000017'::uuid,
    '127.0.0.1',
    'phase4-admin-policy-audit-sql-validation',
    null
  );

  item_id := (template_payload->'items'->0->>'id')::uuid;

  template_payload := public.update_folder_template_item_audited(
    item_id,
    '{"name":"01 Updated Validation"}'::jsonb,
    actor_user_account_id,
    actor_employee_id,
    '99000000-0000-4000-8000-000000000018'::uuid,
    '127.0.0.1',
    'phase4-admin-policy-audit-sql-validation',
    null
  );

  if template_payload->'items'->0->>'name' <> '01 Updated Validation' then
    raise exception 'folder template item update failed';
  end if;

  insert into public.archive_rooms(id, code, name)
  values (room_id, 'PH4-ROOM', 'Phase 4 Room');

  insert into public.archive_locations(id, archive_room_id, location_type, code, label)
  values (location_id, room_id, 'RACK', 'PH4-RACK', 'Phase 4 Rack');

  insert into public.archive_locations(id, archive_room_id, parent_location_id, location_type, code, label)
  values (child_location_id, room_id, location_id, 'SHELF', 'PH4-SHELF', 'Phase 4 Shelf');

  room_payload := public.update_archive_room_audited(
    room_id,
    '{"is_active": false}'::jsonb,
    actor_user_account_id,
    actor_employee_id,
    '99000000-0000-4000-8000-000000000019'::uuid,
    '127.0.0.1',
    'phase4-admin-policy-audit-sql-validation'
  );

  if (room_payload->>'is_active')::boolean is not false then
    raise exception 'archive room update failed';
  end if;

  location_payload := public.update_archive_location_audited(
    location_id,
    '{"label": "Updated rack"}'::jsonb,
    actor_user_account_id,
    actor_employee_id,
    '99000000-0000-4000-8000-000000000020'::uuid,
    '127.0.0.1',
    'phase4-admin-policy-audit-sql-validation'
  );

  if location_payload->>'label' <> 'Updated rack' then
    raise exception 'archive location update failed';
  end if;

  begin
    perform public.update_archive_location_audited(
      location_id,
      '{"location_type": "FILE_SLOT"}'::jsonb,
      actor_user_account_id,
      actor_employee_id,
      '99000000-0000-4000-8000-000000000021'::uuid,
      '127.0.0.1',
      'phase4-admin-policy-audit-sql-validation'
    );
    raise exception 'Expected invalid archive location hierarchy to fail';
  exception
    when raise_exception then
      if sqlerrm <> 'IEMS_INVALID_ARCHIVE_LOCATION_HIERARCHY' then
        raise;
      end if;
  end;

  begin
    perform public.update_archive_location_audited(
      location_id,
      jsonb_build_object('parent_location_id', child_location_id),
      actor_user_account_id,
      actor_employee_id,
      '99000000-0000-4000-8000-000000000022'::uuid,
      '127.0.0.1',
      'phase4-admin-policy-audit-sql-validation'
    );
    raise exception 'Expected archive location descendant parent to fail';
  exception
    when raise_exception then
      if sqlerrm <> 'IEMS_ARCHIVE_LOCATION_PARENT_INVALID' then
        raise;
      end if;
  end;

  if not exists (
    select 1 from public.director_missing_required_documents_v
    where project_id = '30000000-0000-4000-8000-000000000001'::uuid
  ) then
    raise exception 'director_missing_required_documents_v returned no rows';
  end if;

  if has_function_privilege(
    'anon',
    'public.create_policy_audited(text, text, text, integer, jsonb, boolean, uuid, uuid, uuid, inet, text, text)',
    'EXECUTE'
  ) then
    raise exception 'anon can execute create_policy_audited';
  end if;

  if has_function_privilege(
    'authenticated',
    'public.assign_employee_role_audited(uuid, uuid, timestamptz, uuid, uuid, uuid, inet, text, text)',
    'EXECUTE'
  ) then
    raise exception 'authenticated can execute assign_employee_role_audited';
  end if;

  if not has_function_privilege(
    'service_role',
    'public.update_archive_location_audited(uuid, jsonb, uuid, uuid, uuid, inet, text)',
    'EXECUTE'
  ) then
    raise exception 'service_role cannot execute update_archive_location_audited';
  end if;
end $$;

rollback;
