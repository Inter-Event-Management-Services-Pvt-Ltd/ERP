-- IEMS ERP: Phase 4 approval workflow RPCs.
--
-- FastAPI calls these functions with the Supabase service-role key after JWT,
-- RBAC and ABAC checks. Approval writes, notifications and audit events stay
-- transactional. RLS remains enabled and write policies remain default-deny.

alter table public.approval_types
add column if not exists is_active boolean not null default true;

create or replace function public.approval_request_response_json(p_approval_request_id uuid)
returns jsonb
language sql
stable
set search_path = public, pg_catalog
as $$
  select jsonb_build_object(
    'id', ar.id,
    'approval_type_id', ar.approval_type_id,
    'approval_type', jsonb_build_object(
      'id', at.id,
      'code', at.code,
      'name', at.name
    ),
    'project_id', ar.project_id,
    'document_version_id', ar.document_version_id,
    'archive_export_id', ar.archive_export_id,
    'leave_request_id', ar.leave_request_id,
    'requested_by', ar.requested_by,
    'requested_by_employee', jsonb_build_object(
      'id', requested_by_employee.id,
      'employee_code', requested_by_employee.employee_code,
      'full_name', requested_by_employee.full_name
    ),
    'assigned_to', ar.assigned_to,
    'assigned_to_employee', case
      when assigned_to_employee.id is null then null
      else jsonb_build_object(
        'id', assigned_to_employee.id,
        'employee_code', assigned_to_employee.employee_code,
        'full_name', assigned_to_employee.full_name
      )
    end,
    'status', ar.status,
    'requested_at', ar.requested_at,
    'completed_at', ar.completed_at,
    'actions', coalesce((
      select jsonb_agg(
        jsonb_build_object(
          'id', aa.id,
          'approval_request_id', aa.approval_request_id,
          'action', aa.action,
          'performed_by', aa.performed_by,
          'performed_by_employee', jsonb_build_object(
            'id', performed_by_employee.id,
            'employee_code', performed_by_employee.employee_code,
            'full_name', performed_by_employee.full_name
          ),
          'comment', aa.comment,
          'created_at', aa.created_at
        )
        order by aa.created_at asc, aa.id asc
      )
      from public.approval_actions aa
      join public.employees performed_by_employee on performed_by_employee.id = aa.performed_by
      where aa.approval_request_id = ar.id
    ), '[]'::jsonb)
  )
  from public.approval_requests ar
  join public.approval_types at on at.id = ar.approval_type_id
  join public.employees requested_by_employee on requested_by_employee.id = ar.requested_by
  left join public.employees assigned_to_employee on assigned_to_employee.id = ar.assigned_to
  where ar.id = p_approval_request_id
$$;

create or replace function public.create_approval_request_audited(
  p_approval_type_id uuid,
  p_project_id uuid,
  p_document_version_id uuid,
  p_archive_export_id uuid,
  p_leave_request_id uuid,
  p_requested_by uuid,
  p_assigned_to uuid,
  p_comment text,
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
  inserted_request public.approval_requests%rowtype;
begin
  insert into public.approval_requests(
    approval_type_id,
    project_id,
    document_version_id,
    archive_export_id,
    leave_request_id,
    requested_by,
    assigned_to
  )
  values (
    p_approval_type_id,
    p_project_id,
    p_document_version_id,
    p_archive_export_id,
    p_leave_request_id,
    p_requested_by,
    p_assigned_to
  )
  returning * into inserted_request;

  insert into public.approval_actions(
    approval_request_id,
    action,
    performed_by,
    comment
  )
  values (
    inserted_request.id,
    'SUBMITTED',
    p_actor_employee_id,
    nullif(trim(coalesce(p_comment, '')), '')
  );

  if p_assigned_to is not null then
    insert into public.notifications(
      employee_id,
      notification_type,
      title,
      message,
      resource_type,
      resource_id
    )
    values (
      p_assigned_to,
      'APPROVAL',
      'Approval request assigned',
      'An approval request has been assigned to you.',
      'approval_request',
      inserted_request.id
    );
  end if;

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
    'approval.requested',
    'approval_request',
    inserted_request.id,
    p_request_id,
    public.approval_request_response_json(inserted_request.id),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.approval_request_response_json(inserted_request.id);
end;
$$;

create or replace function public.review_approval_request_audited(
  p_approval_request_id uuid,
  p_action text,
  p_comment text,
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
  existing_request public.approval_requests%rowtype;
  updated_request public.approval_requests%rowtype;
  normalized_action text := upper(trim(p_action));
begin
  if normalized_action not in ('APPROVED', 'REJECTED', 'REVISION_REQUESTED') then
    raise exception 'IEMS_APPROVAL_REVIEW_ACTION_INVALID';
  end if;

  if normalized_action = 'REVISION_REQUESTED'
     and nullif(trim(coalesce(p_comment, '')), '') is null then
    raise exception 'IEMS_APPROVAL_REVISION_COMMENT_REQUIRED';
  end if;

  select *
  into existing_request
  from public.approval_requests
  where id = p_approval_request_id
  for update;

  if not found then
    raise exception 'IEMS_APPROVAL_REQUEST_NOT_FOUND';
  end if;

  if existing_request.status <> 'PENDING' then
    raise exception 'IEMS_APPROVAL_NOT_PENDING';
  end if;

  update public.approval_requests
  set status = normalized_action,
      completed_at = now()
  where id = p_approval_request_id
  returning * into updated_request;

  insert into public.approval_actions(
    approval_request_id,
    action,
    performed_by,
    comment
  )
  values (
    updated_request.id,
    normalized_action,
    p_actor_employee_id,
    nullif(trim(coalesce(p_comment, '')), '')
  );

  insert into public.notifications(
    employee_id,
    notification_type,
    title,
    message,
    resource_type,
    resource_id
  )
  values (
    updated_request.requested_by,
    'APPROVAL',
    case normalized_action
      when 'APPROVED' then 'Approval request approved'
      when 'REJECTED' then 'Approval request rejected'
      else 'Approval request needs revision'
    end,
    case normalized_action
      when 'APPROVED' then 'Your approval request has been approved.'
      when 'REJECTED' then 'Your approval request has been rejected.'
      else 'Your approval request needs revision.'
    end,
    'approval_request',
    updated_request.id
  );

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
    case normalized_action
      when 'APPROVED' then 'approval.approved'
      when 'REJECTED' then 'approval.rejected'
      else 'approval.revision_requested'
    end,
    'approval_request',
    updated_request.id,
    p_request_id,
    to_jsonb(existing_request),
    public.approval_request_response_json(updated_request.id),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.approval_request_response_json(updated_request.id);
end;
$$;

revoke execute on function public.approval_request_response_json(uuid) from public, anon, authenticated;
revoke execute on function public.create_approval_request_audited(uuid, uuid, uuid, uuid, uuid, uuid, uuid, text, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.review_approval_request_audited(uuid, text, text, uuid, uuid, uuid, text, text) from public, anon, authenticated;

grant execute on function public.approval_request_response_json(uuid) to service_role;
grant execute on function public.create_approval_request_audited(uuid, uuid, uuid, uuid, uuid, uuid, uuid, text, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.review_approval_request_audited(uuid, text, text, uuid, uuid, uuid, text, text) to service_role;
