-- IEMS ERP: Phase 3 employee operations RPCs.
--
-- FastAPI calls these functions using the Supabase service-role key after JWT,
-- RBAC and ABAC checks. Writes, notifications and audit events stay
-- transactional. RLS remains enabled and write policies remain default-deny.

create or replace function public.leave_request_response_json(p_leave_request_id uuid)
returns jsonb
language sql
stable
set search_path = public, pg_catalog
as $$
  select jsonb_build_object(
    'id', lr.id,
    'employee_id', lr.employee_id,
    'employee', jsonb_build_object(
      'id', e.id,
      'employee_code', e.employee_code,
      'full_name', e.full_name
    ),
    'leave_type_id', lr.leave_type_id,
    'leave_type', jsonb_build_object(
      'id', lt.id,
      'code', lt.code,
      'name', lt.name
    ),
    'start_date', lr.start_date,
    'end_date', lr.end_date,
    'reason', lr.reason,
    'status', lr.status,
    'requested_at', lr.requested_at,
    'reviewed_by', lr.reviewed_by,
    'reviewed_at', lr.reviewed_at,
    'review_comment', lr.review_comment
  )
  from public.leave_requests lr
  join public.employees e on e.id = lr.employee_id
  join public.leave_types lt on lt.id = lr.leave_type_id
  where lr.id = p_leave_request_id
$$;

create or replace function public.task_response_json(p_task_id uuid)
returns jsonb
language sql
stable
set search_path = public, pg_catalog
as $$
  select jsonb_build_object(
    'id', t.id,
    'project_id', t.project_id,
    'project', case
      when p.id is null then null
      else jsonb_build_object('id', p.id, 'project_code', p.project_code, 'name', p.name)
    end,
    'related_folder_id', t.related_folder_id,
    'title', t.title,
    'description', t.description,
    'task_status_id', t.task_status_id,
    'task_status', jsonb_build_object('id', ts.id, 'code', ts.code, 'name', ts.name),
    'priority_level_id', t.priority_level_id,
    'priority_level', jsonb_build_object('id', pl.id, 'code', pl.code, 'name', pl.name),
    'created_by', t.created_by,
    'due_at', t.due_at,
    'completed_at', t.completed_at,
    'created_at', t.created_at,
    'updated_at', t.updated_at,
    'assignees', coalesce((
      select jsonb_agg(
        jsonb_build_object(
          'employee', jsonb_build_object(
            'id', e.id,
            'employee_code', e.employee_code,
            'full_name', e.full_name
          )
        )
        order by e.full_name
      )
      from public.task_assignees ta
      join public.employees e on e.id = ta.employee_id
      where ta.task_id = t.id
    ), '[]'::jsonb),
    'documents', coalesce((
      select jsonb_agg(jsonb_build_object('document_id', tdl.document_id) order by tdl.document_id)
      from public.task_document_links tdl
      where tdl.task_id = t.id
    ), '[]'::jsonb)
  )
  from public.tasks t
  join public.task_statuses ts on ts.id = t.task_status_id
  join public.priority_levels pl on pl.id = t.priority_level_id
  left join public.projects p on p.id = t.project_id
  where t.id = p_task_id
$$;

create or replace function public.task_comment_response_json(p_comment_id uuid)
returns jsonb
language sql
stable
set search_path = public, pg_catalog
as $$
  select jsonb_build_object(
    'id', tc.id,
    'task_id', tc.task_id,
    'employee_id', tc.employee_id,
    'employee', jsonb_build_object(
      'id', e.id,
      'employee_code', e.employee_code,
      'full_name', e.full_name
    ),
    'comment_text', tc.comment_text,
    'created_at', tc.created_at,
    'edited_at', tc.edited_at
  )
  from public.task_comments tc
  join public.employees e on e.id = tc.employee_id
  where tc.id = p_comment_id
$$;

create or replace function public.calendar_event_response_json(p_event_id uuid)
returns jsonb
language sql
stable
set search_path = public, pg_catalog
as $$
  select jsonb_build_object(
    'id', ce.id,
    'project_id', ce.project_id,
    'related_task_id', ce.related_task_id,
    'event_type', ce.event_type,
    'title', ce.title,
    'description', ce.description,
    'starts_at', ce.starts_at,
    'ends_at', ce.ends_at,
    'location', ce.location,
    'created_by', ce.created_by,
    'created_at', ce.created_at,
    'updated_at', ce.updated_at
  )
  from public.calendar_events ce
  where ce.id = p_event_id
$$;

create or replace function public.create_leave_request_audited(
  p_employee_id uuid,
  p_leave_type_id uuid,
  p_start_date date,
  p_end_date date,
  p_reason text,
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
  inserted_leave public.leave_requests%rowtype;
begin
  insert into public.leave_requests(employee_id, leave_type_id, start_date, end_date, reason)
  values (p_employee_id, p_leave_type_id, p_start_date, p_end_date, trim(p_reason))
  returning * into inserted_leave;

  insert into public.notifications(
    employee_id,
    notification_type,
    title,
    message,
    resource_type,
    resource_id
  )
  values (
    p_employee_id,
    'LEAVE',
    'Leave request submitted',
    'Your leave request has been submitted for review.',
    'leave_request',
    inserted_leave.id
  );

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
    'leave.requested',
    'leave_request',
    inserted_leave.id,
    p_request_id,
    to_jsonb(inserted_leave),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.leave_request_response_json(inserted_leave.id);
end;
$$;

create or replace function public.review_leave_request_audited(
  p_leave_request_id uuid,
  p_status text,
  p_review_comment text,
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
  existing_leave public.leave_requests%rowtype;
  updated_leave public.leave_requests%rowtype;
  employee_name text;
  calendar_event_id uuid;
begin
  if p_status not in ('APPROVED', 'REJECTED') then
    raise exception 'IEMS_LEAVE_REVIEW_STATUS_INVALID';
  end if;

  select *
  into existing_leave
  from public.leave_requests
  where id = p_leave_request_id
  for update;

  if not found then
    raise exception 'IEMS_LEAVE_REQUEST_NOT_FOUND';
  end if;

  if existing_leave.status <> 'PENDING' then
    raise exception 'IEMS_LEAVE_REQUEST_NOT_PENDING';
  end if;

  update public.leave_requests
  set status = p_status,
      reviewed_by = p_actor_employee_id,
      reviewed_at = now(),
      review_comment = p_review_comment
  where id = p_leave_request_id
  returning * into updated_leave;

  select full_name into employee_name
  from public.employees
  where id = updated_leave.employee_id;

  insert into public.notifications(
    employee_id,
    notification_type,
    title,
    message,
    resource_type,
    resource_id
  )
  values (
    updated_leave.employee_id,
    'LEAVE',
    case when p_status = 'APPROVED' then 'Leave request approved' else 'Leave request rejected' end,
    case when p_status = 'APPROVED'
      then 'Your leave request has been approved.'
      else 'Your leave request has been rejected.'
    end,
    'leave_request',
    updated_leave.id
  );

  if p_status = 'APPROVED' then
    insert into public.calendar_events(
      event_type,
      title,
      description,
      starts_at,
      ends_at,
      created_by
    )
    values (
      'LEAVE',
      'Leave: ' || coalesce(employee_name, 'Employee'),
      updated_leave.reason,
      updated_leave.start_date::timestamptz,
      (updated_leave.end_date + 1)::timestamptz,
      p_actor_employee_id
    )
    returning id into calendar_event_id;

    insert into public.calendar_event_attendees(calendar_event_id, employee_id)
    values (calendar_event_id, updated_leave.employee_id)
    on conflict do nothing;
  end if;

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
    case when p_status = 'APPROVED' then 'leave.approved' else 'leave.rejected' end,
    'leave_request',
    updated_leave.id,
    p_request_id,
    to_jsonb(existing_leave),
    to_jsonb(updated_leave),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.leave_request_response_json(updated_leave.id);
end;
$$;

create or replace function public.cancel_leave_request_audited(
  p_leave_request_id uuid,
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
  existing_leave public.leave_requests%rowtype;
  updated_leave public.leave_requests%rowtype;
begin
  select *
  into existing_leave
  from public.leave_requests
  where id = p_leave_request_id
  for update;

  if not found then
    raise exception 'IEMS_LEAVE_REQUEST_NOT_FOUND';
  end if;

  if existing_leave.employee_id <> p_actor_employee_id then
    raise exception 'IEMS_LEAVE_REQUEST_NOT_OWN';
  end if;

  if existing_leave.status <> 'PENDING' then
    raise exception 'IEMS_LEAVE_REQUEST_NOT_PENDING';
  end if;

  update public.leave_requests
  set status = 'CANCELLED'
  where id = p_leave_request_id
  returning * into updated_leave;

  insert into public.notifications(
    employee_id,
    notification_type,
    title,
    message,
    resource_type,
    resource_id
  )
  values (
    updated_leave.employee_id,
    'LEAVE',
    'Leave request cancelled',
    'Your leave request has been cancelled.',
    'leave_request',
    updated_leave.id
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
    'leave.cancelled',
    'leave_request',
    updated_leave.id,
    p_request_id,
    to_jsonb(existing_leave),
    to_jsonb(updated_leave),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.leave_request_response_json(updated_leave.id);
end;
$$;

create or replace function public.create_task_audited(
  p_project_id uuid,
  p_related_folder_id uuid,
  p_title text,
  p_description text,
  p_task_status_id uuid,
  p_priority_level_id uuid,
  p_due_at timestamptz,
  p_assignee_ids uuid[],
  p_document_ids uuid[],
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
  inserted_task public.tasks%rowtype;
  effective_status_id uuid;
  assignee_id uuid;
begin
  effective_status_id := p_task_status_id;
  if effective_status_id is null then
    select id into effective_status_id
    from public.task_statuses
    where code = 'TODO'
    limit 1;
  end if;

  insert into public.tasks(
    project_id,
    related_folder_id,
    title,
    description,
    task_status_id,
    priority_level_id,
    created_by,
    due_at
  )
  values (
    p_project_id,
    p_related_folder_id,
    trim(p_title),
    p_description,
    effective_status_id,
    p_priority_level_id,
    p_actor_employee_id,
    p_due_at
  )
  returning * into inserted_task;

  insert into public.task_assignees(task_id, employee_id, assigned_by)
  select inserted_task.id, item.employee_id, p_actor_employee_id
  from unnest(coalesce(p_assignee_ids, '{}'::uuid[])) as item(employee_id)
  on conflict do nothing;

  insert into public.task_document_links(task_id, document_id)
  select inserted_task.id, item.document_id
  from unnest(coalesce(p_document_ids, '{}'::uuid[])) as item(document_id)
  on conflict do nothing;

  foreach assignee_id in array coalesce(p_assignee_ids, '{}'::uuid[]) loop
    insert into public.notifications(
      employee_id,
      notification_type,
      title,
      message,
      resource_type,
      resource_id
    )
    values (
      assignee_id,
      'TASK',
      'Task assigned',
      'A task has been assigned to you.',
      'task',
      inserted_task.id
    );
  end loop;

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
    'task.created',
    'task',
    inserted_task.id,
    p_request_id,
    public.task_response_json(inserted_task.id),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.task_response_json(inserted_task.id);
end;
$$;

create or replace function public.update_task_audited(
  p_task_id uuid,
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
  existing_task public.tasks%rowtype;
  updated_task public.tasks%rowtype;
  status_is_terminal boolean;
begin
  select *
  into existing_task
  from public.tasks
  where id = p_task_id
  for update;

  if not found then
    raise exception 'IEMS_TASK_NOT_FOUND';
  end if;

  update public.tasks
  set project_id = case when p_patch ? 'project_id' then (p_patch->>'project_id')::uuid else project_id end,
      related_folder_id = case when p_patch ? 'related_folder_id' then (p_patch->>'related_folder_id')::uuid else related_folder_id end,
      title = case when p_patch ? 'title' then trim(p_patch->>'title') else title end,
      description = case when p_patch ? 'description' then p_patch->>'description' else description end,
      task_status_id = case when p_patch ? 'task_status_id' then (p_patch->>'task_status_id')::uuid else task_status_id end,
      priority_level_id = case when p_patch ? 'priority_level_id' then (p_patch->>'priority_level_id')::uuid else priority_level_id end,
      due_at = case when p_patch ? 'due_at' then (p_patch->>'due_at')::timestamptz else due_at end,
      updated_at = now()
  where id = p_task_id
  returning * into updated_task;

  select is_terminal into status_is_terminal
  from public.task_statuses
  where id = updated_task.task_status_id;

  if status_is_terminal and updated_task.completed_at is null then
    update public.tasks
    set completed_at = now(),
        updated_at = now()
    where id = p_task_id
    returning * into updated_task;
  elsif p_patch ? 'task_status_id' and not status_is_terminal then
    update public.tasks
    set completed_at = null,
        updated_at = now()
    where id = p_task_id
    returning * into updated_task;
  end if;

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
    'task.updated',
    'task',
    updated_task.id,
    p_request_id,
    to_jsonb(existing_task),
    public.task_response_json(updated_task.id),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.task_response_json(updated_task.id);
end;
$$;

create or replace function public.assign_task_assignees_audited(
  p_task_id uuid,
  p_employee_ids uuid[],
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
  existing_task public.tasks%rowtype;
  employee_id uuid;
begin
  select *
  into existing_task
  from public.tasks
  where id = p_task_id
  for update;

  if not found then
    raise exception 'IEMS_TASK_NOT_FOUND';
  end if;

  insert into public.task_assignees(task_id, employee_id, assigned_by)
  select p_task_id, item.employee_id, p_actor_employee_id
  from unnest(coalesce(p_employee_ids, '{}'::uuid[])) as item(employee_id)
  on conflict do nothing;

  foreach employee_id in array coalesce(p_employee_ids, '{}'::uuid[]) loop
    insert into public.notifications(
      employee_id,
      notification_type,
      title,
      message,
      resource_type,
      resource_id
    )
    values (
      employee_id,
      'TASK',
      'Task assigned',
      'A task has been assigned to you.',
      'task',
      p_task_id
    );
  end loop;

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
    'task.assigned',
    'task',
    p_task_id,
    p_request_id,
    to_jsonb(existing_task),
    public.task_response_json(p_task_id),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.task_response_json(p_task_id);
end;
$$;

create or replace function public.add_task_comment_audited(
  p_task_id uuid,
  p_comment_text text,
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
  inserted_comment public.task_comments%rowtype;
begin
  if not exists (select 1 from public.tasks where id = p_task_id) then
    raise exception 'IEMS_TASK_NOT_FOUND';
  end if;

  insert into public.task_comments(task_id, employee_id, comment_text)
  values (p_task_id, p_actor_employee_id, trim(p_comment_text))
  returning * into inserted_comment;

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
    'task.commented',
    'task_comment',
    inserted_comment.id,
    p_request_id,
    public.task_comment_response_json(inserted_comment.id),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.task_comment_response_json(inserted_comment.id);
end;
$$;

create or replace function public.link_task_document_audited(
  p_task_id uuid,
  p_document_id uuid,
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
begin
  if not exists (select 1 from public.tasks where id = p_task_id) then
    raise exception 'IEMS_TASK_NOT_FOUND';
  end if;

  insert into public.task_document_links(task_id, document_id)
  values (p_task_id, p_document_id)
  on conflict do nothing;

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
    'task.document_linked',
    'task',
    p_task_id,
    p_request_id,
    public.task_response_json(p_task_id),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.task_response_json(p_task_id);
end;
$$;

create or replace function public.create_calendar_event_audited(
  p_project_id uuid,
  p_related_task_id uuid,
  p_event_type text,
  p_title text,
  p_description text,
  p_starts_at timestamptz,
  p_ends_at timestamptz,
  p_location text,
  p_attendee_ids uuid[],
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
  inserted_event public.calendar_events%rowtype;
  attendee_id uuid;
begin
  insert into public.calendar_events(
    project_id,
    related_task_id,
    event_type,
    title,
    description,
    starts_at,
    ends_at,
    location,
    created_by
  )
  values (
    p_project_id,
    p_related_task_id,
    p_event_type,
    trim(p_title),
    p_description,
    p_starts_at,
    p_ends_at,
    p_location,
    p_actor_employee_id
  )
  returning * into inserted_event;

  insert into public.calendar_event_attendees(calendar_event_id, employee_id)
  select inserted_event.id, item.employee_id
  from unnest(coalesce(p_attendee_ids, '{}'::uuid[])) as item(employee_id)
  on conflict do nothing;

  foreach attendee_id in array coalesce(p_attendee_ids, '{}'::uuid[]) loop
    insert into public.notifications(
      employee_id,
      notification_type,
      title,
      message,
      resource_type,
      resource_id
    )
    values (
      attendee_id,
      'CALENDAR',
      'Calendar event added',
      'A calendar event has been added.',
      'calendar_event',
      inserted_event.id
    );
  end loop;

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
    'calendar_event.created',
    'calendar_event',
    inserted_event.id,
    p_request_id,
    public.calendar_event_response_json(inserted_event.id),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.calendar_event_response_json(inserted_event.id);
end;
$$;

create or replace function public.update_calendar_event_audited(
  p_event_id uuid,
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
  existing_event public.calendar_events%rowtype;
  updated_event public.calendar_events%rowtype;
begin
  select *
  into existing_event
  from public.calendar_events
  where id = p_event_id
  for update;

  if not found then
    raise exception 'IEMS_CALENDAR_EVENT_NOT_FOUND';
  end if;

  update public.calendar_events
  set title = case when p_patch ? 'title' then trim(p_patch->>'title') else title end,
      description = case when p_patch ? 'description' then p_patch->>'description' else description end,
      starts_at = case when p_patch ? 'starts_at' then (p_patch->>'starts_at')::timestamptz else starts_at end,
      ends_at = case when p_patch ? 'ends_at' then (p_patch->>'ends_at')::timestamptz else ends_at end,
      location = case when p_patch ? 'location' then p_patch->>'location' else location end,
      updated_at = now()
  where id = p_event_id
  returning * into updated_event;

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
    'calendar_event.updated',
    'calendar_event',
    updated_event.id,
    p_request_id,
    to_jsonb(existing_event),
    public.calendar_event_response_json(updated_event.id),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.calendar_event_response_json(updated_event.id);
end;
$$;

revoke execute on function public.leave_request_response_json(uuid) from public, anon, authenticated;
revoke execute on function public.task_response_json(uuid) from public, anon, authenticated;
revoke execute on function public.task_comment_response_json(uuid) from public, anon, authenticated;
revoke execute on function public.calendar_event_response_json(uuid) from public, anon, authenticated;
revoke execute on function public.create_leave_request_audited(uuid, uuid, date, date, text, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.review_leave_request_audited(uuid, text, text, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.cancel_leave_request_audited(uuid, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.create_task_audited(uuid, uuid, text, text, uuid, uuid, timestamptz, uuid[], uuid[], uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.update_task_audited(uuid, jsonb, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.assign_task_assignees_audited(uuid, uuid[], uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.add_task_comment_audited(uuid, text, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.link_task_document_audited(uuid, uuid, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.create_calendar_event_audited(uuid, uuid, text, text, text, timestamptz, timestamptz, text, uuid[], uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.update_calendar_event_audited(uuid, jsonb, uuid, uuid, uuid, text, text) from public, anon, authenticated;

grant execute on function public.leave_request_response_json(uuid) to service_role;
grant execute on function public.task_response_json(uuid) to service_role;
grant execute on function public.task_comment_response_json(uuid) to service_role;
grant execute on function public.calendar_event_response_json(uuid) to service_role;
grant execute on function public.create_leave_request_audited(uuid, uuid, date, date, text, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.review_leave_request_audited(uuid, text, text, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.cancel_leave_request_audited(uuid, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.create_task_audited(uuid, uuid, text, text, uuid, uuid, timestamptz, uuid[], uuid[], uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.update_task_audited(uuid, jsonb, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.assign_task_assignees_audited(uuid, uuid[], uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.add_task_comment_audited(uuid, text, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.link_task_document_audited(uuid, uuid, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.create_calendar_event_audited(uuid, uuid, text, text, text, timestamptz, timestamptz, text, uuid[], uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.update_calendar_event_audited(uuid, jsonb, uuid, uuid, uuid, text, text) to service_role;
