\set ON_ERROR_STOP on

begin;

create temp table phase2_actor as
select id as employee_id
from public.employees
where employee_code = 'IEMS-DIRECTOR';

create temp table phase2_manager as
select id as employee_id
from public.employees
where employee_code = 'IEMS-MGR-001';

create temp table phase2_refs as
select
  (select id from public.project_types where code = 'CONFERENCE') as project_type_id,
  (select id from public.project_statuses where code = 'PLANNING') as project_status_id,
  (select id from public.priority_levels where code = 'NORMAL') as priority_level_id;

create temp table phase2_client as
select public.create_client_audited(
  'PHASE2',
  'Phase 2 Validation Private Limited',
  'Phase 2 Validation',
  'Rollback-only Phase 2 RPC validation client',
  null,
  (select employee_id from phase2_actor),
  null,
  '127.0.0.1',
  'phase2-sql-validation'
) as payload;

create temp table phase2_project as
select public.create_project_with_folder_template(
  'IEMS-2026-PHASE2',
  (select (payload->>'id')::uuid from phase2_client),
  (select project_type_id from phase2_refs),
  (select project_status_id from phase2_refs),
  (select priority_level_id from phase2_refs),
  'Phase 2 RPC Validation Project',
  '2026-08-12'::date,
  'New Delhi',
  'Rollback-only Phase 2 RPC validation project',
  (select employee_id from phase2_manager),
  (select employee_id from phase2_actor),
  null,
  null,
  (select employee_id from phase2_actor),
  null,
  '127.0.0.1',
  'phase2-sql-validation'
) as payload;

do $$
declare
  validation_client_id uuid := (select (payload->>'id')::uuid from phase2_client);
  validation_project_id uuid := (select (payload->>'id')::uuid from phase2_project);
  validation_root_folder_id uuid := (select (payload->>'root_folder_id')::uuid from phase2_project);
  folder_count integer;
  audit_count integer;
  deleted_project_payload jsonb;
  deactivated_client_payload jsonb;
begin
  select count(*) into folder_count
  from public.folders
  where project_id = validation_project_id
    and deleted_at is null;

  if folder_count < 10 then
    raise exception 'Expected root folder plus standard template folders, found %', folder_count;
  end if;

  if validation_root_folder_id is null then
    raise exception 'Project RPC did not return a root folder id';
  end if;

  if not exists (
    select 1
    from public.project_members
    where project_id = validation_project_id
      and employee_id = (select employee_id from phase2_actor)
      and access_level = 'MANAGE'
      and removed_at is null
  ) then
    raise exception 'Project creator was not assigned as active MANAGE member';
  end if;

  if not exists (
    select 1
    from public.project_members
    where project_id = validation_project_id
      and employee_id = (select employee_id from phase2_manager)
      and access_level = 'MANAGE'
      and removed_at is null
  ) then
    raise exception 'Project manager was not assigned as active MANAGE member';
  end if;

  perform public.upsert_project_member_audited(
    validation_project_id,
    (select employee_id from phase2_manager),
    'CONTRIBUTE',
    null,
    (select employee_id from phase2_actor),
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );

  if not exists (
    select 1
    from public.project_members
    where project_id = validation_project_id
      and employee_id = (select employee_id from phase2_manager)
      and access_level = 'CONTRIBUTE'
      and removed_at is null
  ) then
    raise exception 'Project member access level update failed';
  end if;

  if not exists (
    select 1
    from public.audit_events
    where resource_type = 'project'
      and resource_id = validation_project_id
      and action_code = 'project.member_updated'
  ) then
    raise exception 'Project member access update audit event was not written';
  end if;

  begin
    perform public.upsert_project_member_audited(
      validation_project_id,
      (select employee_id from phase2_actor),
      'VIEW',
      null,
      (select employee_id from phase2_actor),
      null,
      '127.0.0.1',
      'phase2-sql-validation'
    );

    raise exception 'Expected last MANAGE member demotion to fail';
  exception
    when raise_exception then
      if sqlerrm <> 'IEMS_LAST_PROJECT_MANAGER' then
        raise;
      end if;
  end;

  select count(*) into audit_count
  from public.audit_events
  where (resource_type, resource_id, action_code) in (
    ('client', validation_client_id, 'client.created'),
    ('project', validation_project_id, 'project.created')
  );

  if audit_count <> 2 then
    raise exception 'Expected two Phase 2 audit events, found %', audit_count;
  end if;

  if has_function_privilege(
    'anon',
    'public.create_project_with_folder_template(text, uuid, uuid, uuid, uuid, text, date, text, text, uuid, uuid, uuid, uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'anon can execute create_project_with_folder_template';
  end if;

  if has_function_privilege(
    'authenticated',
    'public.create_project_with_folder_template(text, uuid, uuid, uuid, uuid, text, date, text, text, uuid, uuid, uuid, uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'authenticated can execute create_project_with_folder_template';
  end if;

  if not has_function_privilege(
    'service_role',
    'public.create_project_with_folder_template(text, uuid, uuid, uuid, uuid, text, date, text, text, uuid, uuid, uuid, uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'service_role cannot execute create_project_with_folder_template';
  end if;

  if has_function_privilege(
    'anon',
    'public.soft_delete_project_audited(uuid, uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'anon can execute soft_delete_project_audited';
  end if;

  if has_function_privilege(
    'authenticated',
    'public.soft_delete_project_audited(uuid, uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'authenticated can execute soft_delete_project_audited';
  end if;

  if not has_function_privilege(
    'service_role',
    'public.soft_delete_project_audited(uuid, uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'service_role cannot execute soft_delete_project_audited';
  end if;

  deleted_project_payload := public.soft_delete_project_audited(
    validation_project_id,
    null,
    (select employee_id from phase2_actor),
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );

  if deleted_project_payload->>'deleted_at' is null then
    raise exception 'Project soft delete did not set deleted_at';
  end if;

  if not exists (
    select 1
    from public.audit_events
    where resource_type = 'project'
      and resource_id = validation_project_id
      and action_code = 'project.deleted'
  ) then
    raise exception 'Project soft delete audit event was not written';
  end if;

  if has_function_privilege(
    'anon',
    'public.deactivate_client_audited(uuid, uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'anon can execute deactivate_client_audited';
  end if;

  if has_function_privilege(
    'authenticated',
    'public.deactivate_client_audited(uuid, uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'authenticated can execute deactivate_client_audited';
  end if;

  if not has_function_privilege(
    'service_role',
    'public.deactivate_client_audited(uuid, uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'service_role cannot execute deactivate_client_audited';
  end if;

  deactivated_client_payload := public.deactivate_client_audited(
    validation_client_id,
    null,
    (select employee_id from phase2_actor),
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );

  if (deactivated_client_payload->>'is_active')::boolean is not false then
    raise exception 'Client deactivate did not set is_active=false';
  end if;

  if not exists (
    select 1
    from public.audit_events
    where resource_type = 'client'
      and resource_id = validation_client_id
      and action_code = 'client.deactivated'
  ) then
    raise exception 'Client deactivate audit event was not written';
  end if;
end $$;

rollback;
