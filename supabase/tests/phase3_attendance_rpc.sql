\set ON_ERROR_STOP on

begin;

create temp table phase3_actor as
select id as employee_id
from public.employees
where employee_code = 'IEMS-DEV-001';

do $$
declare
  actor_employee_id uuid := (select employee_id from phase3_actor);
  check_in_payload jsonb;
  check_out_payload jsonb;
  corrected_payload jsonb;
  validation_session_id uuid;
begin
  check_in_payload := public.check_in_attendance_audited(
    actor_employee_id,
    'Phase 3 validation check-in',
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase3-attendance-sql-validation'
  );
  validation_session_id := (check_in_payload->>'id')::uuid;

  if check_in_payload->>'checked_out_at' is not null then
    raise exception 'Check-in RPC returned a closed session';
  end if;

  begin
    perform public.check_in_attendance_audited(
      actor_employee_id,
      'Duplicate check-in should fail',
      null,
      actor_employee_id,
      null,
      '127.0.0.1',
      'phase3-attendance-sql-validation'
    );
    raise exception 'Expected duplicate open attendance session to fail';
  exception
    when raise_exception then
      if sqlerrm <> 'IEMS_ATTENDANCE_SESSION_ALREADY_OPEN' then
        raise;
      end if;
  end;

  check_out_payload := public.check_out_attendance_audited(
    actor_employee_id,
    'Phase 3 validation check-out',
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase3-attendance-sql-validation'
  );

  if check_out_payload->>'checked_out_at' is null then
    raise exception 'Check-out RPC did not close the session';
  end if;

  begin
    perform public.check_out_attendance_audited(
      actor_employee_id,
      'No open session should fail',
      null,
      actor_employee_id,
      null,
      '127.0.0.1',
      'phase3-attendance-sql-validation'
    );
    raise exception 'Expected missing open attendance session to fail';
  exception
    when raise_exception then
      if sqlerrm <> 'IEMS_ATTENDANCE_OPEN_SESSION_NOT_FOUND' then
        raise;
      end if;
  end;

  perform public.check_in_attendance_audited(
    actor_employee_id,
    'Phase 3 validation second check-in',
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase3-attendance-sql-validation'
  );

  perform public.check_out_attendance_audited(
    actor_employee_id,
    'Phase 3 validation second check-out',
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase3-attendance-sql-validation'
  );

  corrected_payload := public.correct_attendance_session_audited(
    validation_session_id,
    jsonb_build_object(
      'remarks', 'Phase 3 validation correction',
      'checked_out_at', (now() + interval '1 minute')::text
    ),
    'Missed scan',
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase3-attendance-sql-validation'
  );

  if corrected_payload->>'correction_reason' <> 'Missed scan' then
    raise exception 'Correction RPC did not record reason';
  end if;

  begin
    perform public.correct_attendance_session_audited(
      validation_session_id,
      jsonb_build_object('remarks', 'Bad correction'),
      'bad',
      null,
      actor_employee_id,
      null,
      '127.0.0.1',
      'phase3-attendance-sql-validation'
    );
    raise exception 'Expected short correction reason to fail';
  exception
    when raise_exception then
      if sqlerrm <> 'IEMS_ATTENDANCE_CORRECTION_REASON_REQUIRED' then
        raise;
      end if;
  end;

  if not exists (
    select 1
    from public.audit_events
    where resource_type = 'attendance_session'
      and resource_id = validation_session_id
      and action_code = 'attendance.checked_in'
  ) then
    raise exception 'Attendance check-in audit event was not written';
  end if;

  if not exists (
    select 1
    from public.audit_events
    where resource_type = 'attendance_session'
      and resource_id = validation_session_id
      and action_code = 'attendance.checked_out'
  ) then
    raise exception 'Attendance check-out audit event was not written';
  end if;

  if not exists (
    select 1
    from public.audit_events
    where resource_type = 'attendance_session'
      and resource_id = validation_session_id
      and action_code = 'attendance.corrected'
  ) then
    raise exception 'Attendance correction audit event was not written';
  end if;

  if has_function_privilege(
    'anon',
    'public.check_in_attendance_audited(uuid, text, uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'anon can execute check_in_attendance_audited';
  end if;

  if has_function_privilege(
    'authenticated',
    'public.correct_attendance_session_audited(uuid, jsonb, text, uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'authenticated can execute correct_attendance_session_audited';
  end if;

  if not has_function_privilege(
    'service_role',
    'public.check_out_attendance_audited(uuid, text, uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'service_role cannot execute check_out_attendance_audited';
  end if;
end $$;

rollback;
