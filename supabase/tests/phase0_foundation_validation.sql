begin;

create function pg_temp.phase0_assert(condition boolean, check_name text)
returns void
language plpgsql
as $$
begin
  if not condition then
    raise exception 'Phase 0 validation failed: %', check_name;
  end if;

  raise notice 'ok: %', check_name;
end;
$$;

do $$
declare
  missing_tables text[];
begin
  select array_agg(expected.table_name order by expected.table_name)
  into missing_tables
  from unnest(array[
    'approval_actions',
    'approval_requests',
    'approval_types',
    'archive_export_items',
    'archive_exports',
    'archive_locations',
    'archive_rooms',
    'archive_verifications',
    'attendance_sessions',
    'attribute_definitions',
    'audit_events',
    'calendar_event_attendees',
    'calendar_events',
    'client_contacts',
    'clients',
    'confidentiality_levels',
    'departments',
    'document_metadata',
    'document_tag_assignments',
    'document_types',
    'document_versions',
    'documents',
    'employee_attribute_values',
    'employee_department_assignments',
    'employees',
    'folder_template_items',
    'folder_templates',
    'folders',
    'leave_requests',
    'leave_types',
    'notifications',
    'permissions',
    'physical_file_checkouts',
    'physical_file_movements',
    'physical_files',
    'policies',
    'priority_levels',
    'project_members',
    'project_statuses',
    'project_types',
    'projects',
    'role_permissions',
    'roles',
    'super_user_overrides',
    'tags',
    'task_assignees',
    'task_comments',
    'task_document_links',
    'task_statuses',
    'tasks',
    'user_accounts',
    'user_role_assignments'
  ]::text[]) as expected(table_name)
  where to_regclass(format('public.%I', expected.table_name)) is null;

  perform pg_temp.phase0_assert(missing_tables is null, 'all expected public tables exist');
end;
$$;

select pg_temp.phase0_assert(
  (select count(*)
   from pg_constraint c
   join pg_namespace n on n.oid = c.connamespace
   where n.nspname = 'public' and c.contype = 'f') = 95,
  'all expected public foreign keys exist'
);

select pg_temp.phase0_assert(
  not exists (
    select 1
    from pg_constraint c
    join pg_namespace n on n.oid = c.connamespace
    where n.nspname = 'public'
      and c.contype = 'f'
      and not c.convalidated
  ),
  'all public foreign keys are validated'
);

select pg_temp.phase0_assert(
  (select count(*)
   from pg_constraint c
   join pg_namespace n on n.oid = c.connamespace
   where n.nspname = 'public' and c.contype = 'c') = 30,
  'all expected public check constraints exist'
);

do $$
declare
  missing_indexes text[];
begin
  select array_agg(expected.index_name order by expected.index_name)
  into missing_indexes
  from unnest(array[
    'idx_approval_pending',
    'idx_notifications_unread',
    'uq_document_name_in_folder',
    'uq_employee_current_department',
    'uq_folder_sibling_name',
    'uq_one_open_attendance_session_per_employee',
    'uq_one_open_checkout_per_physical_file',
    'uq_one_primary_contact_per_client',
    'uq_project_root_folder'
  ]::text[]) as expected(index_name)
  where not exists (
    select 1
    from pg_indexes i
    where i.schemaname = 'public'
      and i.indexname = expected.index_name
      and i.indexdef ilike '% where %'
  );

  perform pg_temp.phase0_assert(missing_indexes is null, 'all expected partial unique indexes exist');
end;
$$;

do $$
declare
  missing_views text[];
begin
  select array_agg(expected.view_name order by expected.view_name)
  into missing_views
  from unnest(array[
    'attendance_daily_summary_v',
    'director_attendance_today_v',
    'director_overdue_tasks_v',
    'director_pending_approvals_v',
    'director_physical_file_status_v'
  ]::text[]) as expected(view_name)
  where not exists (
    select 1
    from pg_class c
    join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relname = expected.view_name
      and c.relkind = 'v'
      and coalesce(c.reloptions, array[]::text[]) @> array['security_invoker=true']
  );

  perform pg_temp.phase0_assert(missing_views is null, 'all expected public views compile as security invoker');
end;
$$;

select pg_temp.phase0_assert(
  not exists (
    select 1
    from pg_class c
    join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relkind = 'r'
      and not c.relrowsecurity
  ),
  'RLS is enabled on every public table exposed by the Data API'
);

select pg_temp.phase0_assert(
  (select count(*) from pg_policies where schemaname = 'public') = 17,
  'expected public RLS policies compile'
);

select pg_temp.phase0_assert(
  exists (
    select 1
    from pg_policies
    where schemaname = 'storage'
      and tablename = 'objects'
      and policyname = 'storage_project_documents_read'
      and cmd = 'SELECT'
      and roles = array['authenticated']::name[]
  ),
  'storage read policy is scoped to authenticated users'
);

select pg_temp.phase0_assert(
  not exists (
    select 1
    from pg_policies
    where schemaname = 'storage'
      and tablename = 'objects'
      and cmd in ('INSERT', 'UPDATE', 'DELETE', 'ALL')
  ),
  'browser storage write policies are not broadly enabled'
);

select pg_temp.phase0_assert(
  (select count(*)
   from storage.buckets
   where id in (
     'project-documents',
     'generated-archives',
     'generated-labels',
     'document-previews',
     'profile-assets'
   )
   and public = false) = 5,
  'all expected storage buckets exist and are private'
);

select pg_temp.phase0_assert(
  exists (
    select 1
    from public.employees
    where lower(official_email::text) = 'director@iemsnewdelhi.com'
      and employee_code = 'IEMS-DIRECTOR'
      and employment_status = 'ACTIVE'
  ),
  'Director employee seed exists'
);

do $$
declare
  director_auth_id uuid := '11111111-1111-4111-8111-111111111111'::uuid;
  director_employee_id uuid;
  test_employee_id uuid;
  test_client_id uuid;
  test_project_id uuid;
  root_folder_id uuid;
  archive_room_id uuid;
  archive_location_id uuid;
  physical_file_id uuid;
  leave_request_id uuid;
  override_id uuid;
  override_resource_id uuid;
  blocked boolean;
begin
  select id
  into director_employee_id
  from public.employees
  where lower(official_email::text) = 'director@iemsnewdelhi.com';

  insert into auth.users (
    instance_id,
    id,
    aud,
    role,
    email,
    encrypted_password,
    email_confirmed_at,
    created_at,
    updated_at,
    raw_app_meta_data,
    raw_user_meta_data
  )
  values (
    '00000000-0000-0000-0000-000000000000',
    director_auth_id,
    'authenticated',
    'authenticated',
    'director@iemsnewdelhi.com',
    '',
    now(),
    now(),
    now(),
    '{}'::jsonb,
    '{}'::jsonb
  );

  perform pg_temp.phase0_assert(
    exists (
      select 1
      from public.user_accounts ua
      where ua.id = director_auth_id
        and ua.employee_id = director_employee_id
        and ua.is_active
        and ua.is_super_user
    ),
    'Director auth sign-in links to active Super User account'
  );

  perform pg_temp.phase0_assert(
    (
      select count(*)
      from public.user_role_assignments ura
      join public.roles r on r.id = ura.role_id
      where ura.user_account_id = director_auth_id
        and r.code in ('DIRECTOR', 'SUPER_USER')
    ) = 2,
    'Director auth sign-in assigns Director and Super User roles'
  );

  insert into public.employees(employee_code, full_name, official_email, employment_status)
  values ('PHASE0-EMP-001', 'Phase 0 Employee', 'phase0.employee@iemsnewdelhi.com', 'ACTIVE')
  returning id into test_employee_id;

  blocked := false;
  begin
    insert into public.employees(employee_code, full_name, official_email, employment_status)
    values ('PHASE0-EMP-002', 'Phase 0 Duplicate', 'PHASE0.Employee@iemsnewdelhi.com', 'ACTIVE');
  exception
    when unique_violation then
      blocked := true;
  end;
  perform pg_temp.phase0_assert(blocked, 'duplicate employee email is rejected');

  blocked := false;
  begin
    insert into public.super_user_overrides(user_account_id, action_code, resource_type, resource_id, reason)
    values (director_auth_id, 'phase0.override', 'project', gen_random_uuid(), 'short');
  exception
    when check_violation then
      blocked := true;
  end;
  perform pg_temp.phase0_assert(blocked, 'Super User override reason minimum length is enforced');

  override_resource_id := gen_random_uuid();
  select public.record_super_user_override(
    director_auth_id,
    director_employee_id,
    'phase1.override',
    'project',
    override_resource_id,
    'Phase 1 validation reason',
    gen_random_uuid(),
    '{"phase":"1"}'::jsonb,
    '127.0.0.1'::inet,
    'phase-validation'
  )
  into override_id;

  perform pg_temp.phase0_assert(
    exists (
      select 1
      from public.super_user_overrides suo
      where suo.id = override_id
        and suo.user_account_id = director_auth_id
        and suo.action_code = 'phase1.override'
        and suo.resource_type = 'project'
        and suo.resource_id = override_resource_id
    ),
    'Super User override RPC writes override record'
  );

  perform pg_temp.phase0_assert(
    exists (
      select 1
      from public.audit_events ae
      where ae.actor_user_account_id = director_auth_id
        and ae.actor_employee_id = director_employee_id
        and ae.action_code = 'super_user.override_used'
        and ae.resource_type = 'project'
        and ae.resource_id = override_resource_id
        and ae.new_values->>'override_id' = override_id::text
    ),
    'Super User override RPC writes audit event'
  );

  insert into public.clients(client_code, legal_name, display_name)
  values ('PHASE0-CLIENT', 'Phase 0 Client Pvt Ltd', 'Phase 0 Client')
  returning id into test_client_id;

  insert into public.projects(
    project_code,
    client_id,
    project_type_id,
    project_status_id,
    priority_level_id,
    name,
    created_by
  )
  select
    'PHASE0-PROJECT',
    test_client_id,
    pt.id,
    ps.id,
    pl.id,
    'Phase 0 Project',
    director_employee_id
  from public.project_types pt
  cross join public.project_statuses ps
  cross join public.priority_levels pl
  where pt.code = 'CONFERENCE'
    and ps.code = 'ACTIVE'
    and pl.code = 'NORMAL'
  returning id into test_project_id;

  insert into public.folders(project_id, name, created_by)
  values (test_project_id, 'Root', director_employee_id)
  returning id into root_folder_id;

  blocked := false;
  begin
    insert into public.folders(project_id, name, created_by)
    values (test_project_id, 'Another Root', director_employee_id);
  exception
    when unique_violation then
      blocked := true;
  end;
  perform pg_temp.phase0_assert(blocked, 'one root folder per project is enforced');

  insert into public.folders(project_id, parent_folder_id, name, created_by)
  values (test_project_id, root_folder_id, 'Contracts', director_employee_id);

  blocked := false;
  begin
    insert into public.folders(project_id, parent_folder_id, name, created_by)
    values (test_project_id, root_folder_id, 'contracts', director_employee_id);
  exception
    when unique_violation then
      blocked := true;
  end;
  perform pg_temp.phase0_assert(blocked, 'duplicate active sibling folder name is rejected');

  insert into public.attendance_sessions(employee_id, source, created_by)
  values (director_employee_id, 'WEB', director_employee_id);

  blocked := false;
  begin
    insert into public.attendance_sessions(employee_id, source, created_by)
    values (director_employee_id, 'WEB', director_employee_id);
  exception
    when unique_violation then
      blocked := true;
  end;
  perform pg_temp.phase0_assert(blocked, 'duplicate open attendance session is rejected');

  insert into public.archive_rooms(code, name)
  values ('PHASE0-ROOM', 'Phase 0 Archive Room')
  returning id into archive_room_id;

  insert into public.archive_locations(archive_room_id, location_type, code, label)
  values (archive_room_id, 'RACK', 'PHASE0-RACK', 'Phase 0 Rack')
  returning id into archive_location_id;

  insert into public.physical_files(
    physical_file_code,
    project_id,
    archive_location_id,
    status,
    archived_by
  )
  values (
    'PHASE0-PF-001',
    test_project_id,
    archive_location_id,
    'AVAILABLE',
    director_employee_id
  )
  returning id into physical_file_id;

  insert into public.physical_file_checkouts(physical_file_id, checked_out_by, purpose)
  values (physical_file_id, director_employee_id, 'Phase 0 validation');

  blocked := false;
  begin
    insert into public.physical_file_checkouts(physical_file_id, checked_out_by, purpose)
    values (physical_file_id, director_employee_id, 'Phase 0 duplicate validation');
  exception
    when unique_violation then
      blocked := true;
  end;
  perform pg_temp.phase0_assert(blocked, 'duplicate open physical-file checkout is rejected');

  insert into public.leave_requests(employee_id, leave_type_id, start_date, end_date, reason)
  select director_employee_id, lt.id, current_date, current_date, 'Phase 0 validation'
  from public.leave_types lt
  where lt.code = 'CASUAL'
  returning id into leave_request_id;

  blocked := false;
  begin
    insert into public.approval_requests(
      approval_type_id,
      project_id,
      leave_request_id,
      requested_by,
      status
    )
    select at.id, test_project_id, leave_request_id, director_employee_id, 'PENDING'
    from public.approval_types at
    where at.code = 'PROJECT_CLOSURE';
  exception
    when check_violation then
      blocked := true;
  end;
  perform pg_temp.phase0_assert(blocked, 'invalid approval target count is rejected');

  insert into public.audit_events(action_code, resource_type, resource_id)
  values ('phase0.audit_validation', 'project', test_project_id)
  returning id into physical_file_id;

  blocked := false;
  begin
    update public.audit_events
    set action_code = 'phase0.audit_mutated'
    where id = physical_file_id;
  exception
    when raise_exception then
      blocked := true;
  end;
  perform pg_temp.phase0_assert(blocked, 'audit table cannot be updated');

  blocked := false;
  begin
    delete from public.audit_events
    where id = physical_file_id;
  exception
    when raise_exception then
      blocked := true;
  end;
  perform pg_temp.phase0_assert(blocked, 'audit table cannot be deleted from');
end;
$$;

rollback;
