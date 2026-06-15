-- IEMS ERP: Phase 3 audited attendance RPCs
--
-- These functions are called only by FastAPI with the Supabase service-role key.
-- They keep attendance writes and audit events in the same PostgreSQL transaction.

create or replace function public.attendance_session_response_json(p_session_id uuid)
returns jsonb
language sql
stable
set search_path = public, pg_catalog
as $$
  select jsonb_build_object(
    'id', s.id,
    'employee_id', s.employee_id,
    'employee', jsonb_build_object(
      'id', e.id,
      'employee_code', e.employee_code,
      'full_name', e.full_name
    ),
    'checked_in_at', s.checked_in_at,
    'checked_out_at', s.checked_out_at,
    'source', s.source,
    'remarks', s.remarks,
    'created_by', s.created_by,
    'corrected_by', s.corrected_by,
    'correction_reason', s.correction_reason,
    'created_at', s.created_at,
    'updated_at', s.updated_at
  )
  from public.attendance_sessions s
  join public.employees e on e.id = s.employee_id
  where s.id = p_session_id
$$;

create or replace function public.check_in_attendance_audited(
  p_employee_id uuid,
  p_remarks text,
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
  inserted_session public.attendance_sessions%rowtype;
begin
  if exists (
    select 1
    from public.attendance_sessions
    where employee_id = p_employee_id
      and checked_out_at is null
  ) then
    raise exception 'IEMS_ATTENDANCE_SESSION_ALREADY_OPEN';
  end if;

  insert into public.attendance_sessions(
    employee_id,
    source,
    remarks,
    created_by
  )
  values (
    p_employee_id,
    'WEB',
    nullif(trim(coalesce(p_remarks, '')), ''),
    p_actor_employee_id
  )
  returning * into inserted_session;

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
    'attendance.checked_in',
    'attendance_session',
    inserted_session.id,
    p_request_id,
    to_jsonb(inserted_session),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.attendance_session_response_json(inserted_session.id);
end;
$$;

create or replace function public.check_out_attendance_audited(
  p_employee_id uuid,
  p_remarks text,
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
  open_session public.attendance_sessions%rowtype;
  updated_session public.attendance_sessions%rowtype;
begin
  select *
  into open_session
  from public.attendance_sessions
  where employee_id = p_employee_id
    and checked_out_at is null
  for update;

  if not found then
    raise exception 'IEMS_ATTENDANCE_OPEN_SESSION_NOT_FOUND';
  end if;

  update public.attendance_sessions
  set checked_out_at = now(),
      remarks = coalesce(nullif(trim(coalesce(p_remarks, '')), ''), remarks),
      updated_at = now()
  where id = open_session.id
  returning * into updated_session;

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
    'attendance.checked_out',
    'attendance_session',
    updated_session.id,
    p_request_id,
    to_jsonb(open_session),
    to_jsonb(updated_session),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.attendance_session_response_json(updated_session.id);
end;
$$;

create or replace function public.correct_attendance_session_audited(
  p_session_id uuid,
  p_patch jsonb,
  p_correction_reason text,
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
  old_session public.attendance_sessions%rowtype;
  updated_session public.attendance_sessions%rowtype;
  normalized_reason text := nullif(trim(coalesce(p_correction_reason, '')), '');
begin
  if normalized_reason is null or length(normalized_reason) < 5 then
    raise exception 'IEMS_ATTENDANCE_CORRECTION_REASON_REQUIRED';
  end if;

  select *
  into old_session
  from public.attendance_sessions
  where id = p_session_id
  for update;

  if not found then
    raise exception 'IEMS_ATTENDANCE_SESSION_NOT_FOUND';
  end if;

  update public.attendance_sessions
  set checked_in_at = case
        when p_patch ? 'checked_in_at' then (p_patch ->> 'checked_in_at')::timestamptz
        else checked_in_at
      end,
      checked_out_at = case
        when p_patch ? 'checked_out_at' then (p_patch ->> 'checked_out_at')::timestamptz
        else checked_out_at
      end,
      remarks = case
        when p_patch ? 'remarks' then nullif(trim(coalesce(p_patch ->> 'remarks', '')), '')
        else remarks
      end,
      corrected_by = p_actor_employee_id,
      correction_reason = normalized_reason,
      updated_at = now()
  where id = p_session_id
  returning * into updated_session;

  insert into public.audit_events(
    actor_user_account_id,
    actor_employee_id,
    action_code,
    resource_type,
    resource_id,
    request_id,
    old_values,
    new_values,
    metadata,
    ip_address,
    user_agent
  )
  values (
    p_actor_user_account_id,
    p_actor_employee_id,
    'attendance.corrected',
    'attendance_session',
    updated_session.id,
    p_request_id,
    to_jsonb(old_session),
    to_jsonb(updated_session),
    jsonb_build_object('correction_reason', normalized_reason),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.attendance_session_response_json(updated_session.id);
end;
$$;

revoke execute on function public.attendance_session_response_json(uuid) from public, anon, authenticated;
revoke execute on function public.check_in_attendance_audited(uuid, text, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.check_out_attendance_audited(uuid, text, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.correct_attendance_session_audited(uuid, jsonb, text, uuid, uuid, uuid, text, text) from public, anon, authenticated;

grant execute on function public.attendance_session_response_json(uuid) to service_role;
grant execute on function public.check_in_attendance_audited(uuid, text, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.check_out_attendance_audited(uuid, text, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.correct_attendance_session_audited(uuid, jsonb, text, uuid, uuid, uuid, text, text) to service_role;
