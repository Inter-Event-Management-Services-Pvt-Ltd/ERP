\set ON_ERROR_STOP on

begin;

create temp table phase4_actor as
select id as employee_id
from public.employees
where employee_code = 'IEMS-MGR-001';

create temp table phase4_reviewer as
select id as employee_id
from public.employees
where employee_code = 'IEMS-DIRECTOR';

create temp table phase4_project as
select '30000000-0000-4000-8000-000000000001'::uuid as project_id;

create temp table phase4_refs as
select id as approval_type_id
from public.approval_types
where code = 'PROJECT_CLOSURE';

do $$
declare
  actor_employee_id uuid := (select employee_id from phase4_actor);
  reviewer_employee_id uuid := (select employee_id from phase4_reviewer);
  validation_project_id uuid := (select project_id from phase4_project);
  approval_type_id uuid := (select approval_type_id from phase4_refs);
  approval_payload jsonb;
  approved_payload jsonb;
  revision_payload jsonb;
  approval_id uuid;
  revision_approval_id uuid;
begin
  approval_payload := public.create_approval_request_audited(
    approval_type_id,
    validation_project_id,
    null,
    null,
    null,
    actor_employee_id,
    reviewer_employee_id,
    'Phase 4 approval validation',
    null,
    actor_employee_id,
    '98000000-0000-4000-8000-000000000001'::uuid,
    '127.0.0.1',
    'phase4-approval-workflows-sql-validation'
  );
  approval_id := (approval_payload->>'id')::uuid;

  if approval_payload->>'status' <> 'PENDING' then
    raise exception 'Approval create RPC did not create a pending request';
  end if;

  if jsonb_array_length(approval_payload->'actions') <> 1 then
    raise exception 'Approval create RPC did not return submitted action history';
  end if;

  if not exists (
    select 1
    from public.approval_actions
    where approval_request_id = approval_id
      and action = 'SUBMITTED'
      and performed_by = actor_employee_id
  ) then
    raise exception 'Approval create RPC did not write SUBMITTED action';
  end if;

  if not exists (
    select 1
    from public.notifications
    where resource_type = 'approval_request'
      and resource_id = approval_id
      and employee_id = reviewer_employee_id
  ) then
    raise exception 'Approval create RPC did not notify reviewer';
  end if;

  if not exists (
    select 1
    from public.audit_events
    where action_code = 'approval.requested'
      and resource_type = 'approval_request'
      and resource_id = approval_id
  ) then
    raise exception 'Approval create RPC did not write audit event';
  end if;

  approved_payload := public.review_approval_request_audited(
    approval_id,
    'APPROVED',
    'Approved by validation',
    null,
    reviewer_employee_id,
    '98000000-0000-4000-8000-000000000002'::uuid,
    '127.0.0.1',
    'phase4-approval-workflows-sql-validation'
  );

  if approved_payload->>'status' <> 'APPROVED' then
    raise exception 'Approval review RPC did not approve request';
  end if;

  if approved_payload->>'completed_at' is null then
    raise exception 'Approval review RPC did not set completed_at';
  end if;

  if jsonb_array_length(approved_payload->'actions') <> 2 then
    raise exception 'Approval review RPC did not return full action history';
  end if;

  if not exists (
    select 1
    from public.notifications
    where resource_type = 'approval_request'
      and resource_id = approval_id
      and employee_id = actor_employee_id
  ) then
    raise exception 'Approval review RPC did not notify requester';
  end if;

  if not exists (
    select 1
    from public.audit_events
    where action_code = 'approval.approved'
      and resource_type = 'approval_request'
      and resource_id = approval_id
  ) then
    raise exception 'Approval review RPC did not write approved audit event';
  end if;

  begin
    perform public.review_approval_request_audited(
      approval_id,
      'REJECTED',
      'Second review should fail',
      null,
      reviewer_employee_id,
      '98000000-0000-4000-8000-000000000003'::uuid,
      '127.0.0.1',
      'phase4-approval-workflows-sql-validation'
    );
    raise exception 'Expected review of non-pending approval request to fail';
  exception
    when raise_exception then
      if sqlerrm <> 'IEMS_APPROVAL_NOT_PENDING' then
        raise;
      end if;
  end;

  revision_payload := public.create_approval_request_audited(
    approval_type_id,
    validation_project_id,
    null,
    null,
    null,
    actor_employee_id,
    reviewer_employee_id,
    'Phase 4 revision validation',
    null,
    actor_employee_id,
    '98000000-0000-4000-8000-000000000004'::uuid,
    '127.0.0.1',
    'phase4-approval-workflows-sql-validation'
  );
  revision_approval_id := (revision_payload->>'id')::uuid;

  begin
    perform public.review_approval_request_audited(
      revision_approval_id,
      'REVISION_REQUESTED',
      '',
      null,
      reviewer_employee_id,
      '98000000-0000-4000-8000-000000000005'::uuid,
      '127.0.0.1',
      'phase4-approval-workflows-sql-validation'
    );
    raise exception 'Expected revision request without comment to fail';
  exception
    when raise_exception then
      if sqlerrm <> 'IEMS_APPROVAL_REVISION_COMMENT_REQUIRED' then
        raise;
      end if;
  end;

  revision_payload := public.review_approval_request_audited(
    revision_approval_id,
    'REVISION_REQUESTED',
    'Attach the signed closure note.',
    null,
    reviewer_employee_id,
    '98000000-0000-4000-8000-000000000006'::uuid,
    '127.0.0.1',
    'phase4-approval-workflows-sql-validation'
  );

  if revision_payload->>'status' <> 'REVISION_REQUESTED' then
    raise exception 'Approval review RPC did not request revision';
  end if;

  if has_function_privilege(
    'anon',
    'public.create_approval_request_audited(uuid, uuid, uuid, uuid, uuid, uuid, uuid, text, uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'anon can execute create_approval_request_audited';
  end if;

  if has_function_privilege(
    'authenticated',
    'public.review_approval_request_audited(uuid, text, text, uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'authenticated can execute review_approval_request_audited';
  end if;

  if not has_function_privilege(
    'service_role',
    'public.review_approval_request_audited(uuid, text, text, uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'service_role cannot execute review_approval_request_audited';
  end if;
end $$;

rollback;
