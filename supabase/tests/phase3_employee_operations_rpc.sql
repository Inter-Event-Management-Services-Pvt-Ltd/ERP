\set ON_ERROR_STOP on

begin;

create temp table phase3_actor as
select id as employee_id
from public.employees
where employee_code = 'IEMS-MGR-001';

create temp table phase3_employee as
select id as employee_id
from public.employees
where employee_code = 'IEMS-OPS-001';

create temp table phase3_project as
select '30000000-0000-4000-8000-000000000001'::uuid as project_id;

create temp table phase3_folder as
select id as folder_id
from public.folders
where project_id = (select project_id from phase3_project)
  and deleted_at is null
order by parent_folder_id nulls first, sort_order
limit 1;

create temp table phase3_refs as
select
  (select id from public.leave_types where code = 'CASUAL') as leave_type_id,
  (select id from public.task_statuses where code = 'COMPLETED') as completed_status_id,
  (select id from public.priority_levels where code = 'HIGH') as priority_level_id,
  (select id from public.confidentiality_levels where code = 'GENERAL') as confidentiality_level_id;

create temp table phase3_document as
with inserted_document as (
  insert into public.documents(
    project_id,
    folder_id,
    confidentiality_level_id,
    display_name,
    created_by
  )
  values (
    (select project_id from phase3_project),
    (select folder_id from phase3_folder),
    (select confidentiality_level_id from phase3_refs),
    'Phase 3 validation document',
    (select employee_id from phase3_actor)
  )
  returning id as document_id
)
select document_id from inserted_document;

do $$
declare
  actor_employee_id uuid := (select employee_id from phase3_actor);
  validation_employee_id uuid := (select employee_id from phase3_employee);
  validation_project_id uuid := (select project_id from phase3_project);
  validation_folder_id uuid := (select folder_id from phase3_folder);
  validation_document_id uuid := (select document_id from phase3_document);
  validation_leave_id uuid;
  validation_cancel_leave_id uuid;
  validation_task_id uuid;
  validation_event_id uuid;
  leave_payload jsonb;
  approved_leave_payload jsonb;
  cancelled_leave_payload jsonb;
  task_payload jsonb;
  updated_task_payload jsonb;
  comment_payload jsonb;
  linked_task_payload jsonb;
  event_payload jsonb;
  updated_event_payload jsonb;
begin
  leave_payload := public.create_leave_request_audited(
    validation_employee_id,
    (select leave_type_id from phase3_refs),
    '2026-07-01'::date,
    '2026-07-02'::date,
    'Phase 3 validation leave',
    null,
    validation_employee_id,
    null,
    '127.0.0.1',
    'phase3-employee-operations-sql-validation'
  );
  validation_leave_id := (leave_payload->>'id')::uuid;

  approved_leave_payload := public.review_leave_request_audited(
    validation_leave_id,
    'APPROVED',
    'Approved by validation',
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase3-employee-operations-sql-validation'
  );

  if approved_leave_payload->>'status' <> 'APPROVED' then
    raise exception 'Leave review RPC did not approve request';
  end if;

  if not exists (
    select 1 from public.calendar_events
    where event_type = 'LEAVE'
      and title like 'Leave:%'
      and created_by = actor_employee_id
  ) then
    raise exception 'Approved leave did not create calendar visibility';
  end if;

  begin
    perform public.review_leave_request_audited(
      validation_leave_id,
      'REJECTED',
      'Second review should fail',
      null,
      actor_employee_id,
      null,
      '127.0.0.1',
      'phase3-employee-operations-sql-validation'
    );
    raise exception 'Expected review of non-pending leave request to fail';
  exception
    when raise_exception then
      if sqlerrm <> 'IEMS_LEAVE_REQUEST_NOT_PENDING' then
        raise;
      end if;
  end;

  leave_payload := public.create_leave_request_audited(
    validation_employee_id,
    (select leave_type_id from phase3_refs),
    '2026-07-05'::date,
    '2026-07-05'::date,
    'Phase 3 validation cancellation',
    null,
    validation_employee_id,
    null,
    '127.0.0.1',
    'phase3-employee-operations-sql-validation'
  );
  validation_cancel_leave_id := (leave_payload->>'id')::uuid;

  cancelled_leave_payload := public.cancel_leave_request_audited(
    validation_cancel_leave_id,
    null,
    validation_employee_id,
    null,
    '127.0.0.1',
    'phase3-employee-operations-sql-validation'
  );

  if cancelled_leave_payload->>'status' <> 'CANCELLED' then
    raise exception 'Leave cancel RPC did not cancel request';
  end if;

  task_payload := public.create_task_audited(
    validation_project_id,
    validation_folder_id,
    'Phase 3 validation task',
    'Validate task RPCs',
    null,
    (select priority_level_id from phase3_refs),
    now() + interval '3 days',
    array[validation_employee_id, actor_employee_id],
    array[]::uuid[],
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase3-employee-operations-sql-validation'
  );
  validation_task_id := (task_payload->>'id')::uuid;

  if jsonb_array_length(task_payload->'assignees') <> 2 then
    raise exception 'Task RPC did not assign both employees';
  end if;

  updated_task_payload := public.update_task_audited(
    validation_task_id,
    jsonb_build_object('task_status_id', (select completed_status_id from phase3_refs)),
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase3-employee-operations-sql-validation'
  );

  if updated_task_payload->>'completed_at' is null then
    raise exception 'Task update RPC did not mark completed_at for terminal status';
  end if;

  perform public.assign_task_assignees_audited(
    validation_task_id,
    array[validation_employee_id],
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase3-employee-operations-sql-validation'
  );

  comment_payload := public.add_task_comment_audited(
    validation_task_id,
    'Phase 3 validation comment',
    null,
    validation_employee_id,
    null,
    '127.0.0.1',
    'phase3-employee-operations-sql-validation'
  );

  if comment_payload->>'comment_text' <> 'Phase 3 validation comment' then
    raise exception 'Task comment RPC did not return comment';
  end if;

  linked_task_payload := public.link_task_document_audited(
    validation_task_id,
    validation_document_id,
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase3-employee-operations-sql-validation'
  );

  if jsonb_array_length(linked_task_payload->'documents') <> 1 then
    raise exception 'Task document link RPC did not return linked document';
  end if;

  event_payload := public.create_calendar_event_audited(
    validation_project_id,
    validation_task_id,
    'MEETING',
    'Phase 3 validation meeting',
    'Validate calendar RPCs',
    now() + interval '1 day',
    now() + interval '1 day 1 hour',
    'Validation room',
    array[validation_employee_id],
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase3-employee-operations-sql-validation'
  );
  validation_event_id := (event_payload->>'id')::uuid;

  updated_event_payload := public.update_calendar_event_audited(
    validation_event_id,
    jsonb_build_object('title', 'Phase 3 validation meeting updated'),
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase3-employee-operations-sql-validation'
  );

  if updated_event_payload->>'title' <> 'Phase 3 validation meeting updated' then
    raise exception 'Calendar event update RPC did not update title';
  end if;

  if not exists (
    select 1 from public.audit_events
    where action_code = 'leave.approved'
      and resource_type = 'leave_request'
      and resource_id = validation_leave_id
  ) then
    raise exception 'Leave review audit event was not written';
  end if;

  if not exists (
    select 1 from public.audit_events
    where action_code = 'task.created'
      and resource_type = 'task'
      and resource_id = validation_task_id
  ) then
    raise exception 'Task create audit event was not written';
  end if;

  if not exists (
    select 1 from public.notifications
    where resource_type = 'task'
      and resource_id = validation_task_id
      and employee_id = validation_employee_id
  ) then
    raise exception 'Task assignee notification was not written';
  end if;

  if has_function_privilege(
    'anon',
    'public.create_task_audited(uuid, uuid, text, text, uuid, uuid, timestamptz, uuid[], uuid[], uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'anon can execute create_task_audited';
  end if;

  if has_function_privilege(
    'authenticated',
    'public.review_leave_request_audited(uuid, text, text, uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'authenticated can execute review_leave_request_audited';
  end if;

  if not has_function_privilege(
    'service_role',
    'public.create_calendar_event_audited(uuid, uuid, text, text, text, timestamptz, timestamptz, text, uuid[], uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'service_role cannot execute create_calendar_event_audited';
  end if;
end $$;

rollback;
