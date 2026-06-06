-- IEMS ERP: Phase 2 documents, archive exports and physical archive RPCs.
--
-- These functions are called by FastAPI using the Supabase service-role key
-- after JWT, RBAC and ABAC checks. Sensitive state changes and audit events
-- stay in one PostgreSQL transaction.

create or replace function public.folder_response_json(p_folder_id uuid)
returns jsonb
language sql
stable
set search_path = public, pg_catalog
as $$
  select jsonb_build_object(
    'id', f.id,
    'project_id', f.project_id,
    'parent_folder_id', f.parent_folder_id,
    'name', f.name,
    'sort_order', f.sort_order,
    'created_by', f.created_by,
    'created_at', f.created_at,
    'updated_at', f.updated_at,
    'deleted_at', f.deleted_at
  )
  from public.folders f
  where f.id = p_folder_id
$$;

create or replace function public.document_version_response_json(p_document_version_id uuid)
returns jsonb
language sql
stable
set search_path = public, pg_catalog
as $$
  select jsonb_build_object(
    'id', dv.id,
    'document_id', dv.document_id,
    'version_number', dv.version_number,
    'storage_bucket', dv.storage_bucket,
    'storage_key', dv.storage_key,
    'original_filename', dv.original_filename,
    'mime_type', dv.mime_type,
    'size_bytes', dv.size_bytes,
    'checksum_sha256', dv.checksum_sha256,
    'change_note', dv.change_note,
    'uploaded_by', dv.uploaded_by,
    'uploaded_at', dv.uploaded_at,
    'preview_supported', dv.mime_type in (
      'application/pdf',
      'image/jpeg',
      'image/png',
      'text/plain'
    )
  )
  from public.document_versions dv
  where dv.id = p_document_version_id
$$;

create or replace function public.document_response_json(p_document_id uuid)
returns jsonb
language sql
stable
set search_path = public, pg_catalog
as $$
  select jsonb_build_object(
    'id', d.id,
    'project_id', d.project_id,
    'folder_id', d.folder_id,
    'document_type_id', d.document_type_id,
    'document_type', case
      when dt.id is null then null
      else jsonb_build_object('id', dt.id, 'code', dt.code, 'name', dt.name)
    end,
    'confidentiality_level_id', d.confidentiality_level_id,
    'confidentiality_level', jsonb_build_object(
      'id', cl.id,
      'code', cl.code,
      'name', cl.name
    ),
    'display_name', d.display_name,
    'status', d.status,
    'created_by', d.created_by,
    'created_at', d.created_at,
    'updated_at', d.updated_at,
    'deleted_at', d.deleted_at,
    'latest_version', (
      select public.document_version_response_json(dv.id)
      from public.document_versions dv
      where dv.document_id = d.id
      order by dv.version_number desc
      limit 1
    )
  )
  from public.documents d
  left join public.document_types dt on dt.id = d.document_type_id
  join public.confidentiality_levels cl on cl.id = d.confidentiality_level_id
  where d.id = p_document_id
$$;

create or replace function public.archive_export_response_json(p_archive_export_id uuid)
returns jsonb
language sql
stable
set search_path = public, pg_catalog
as $$
  select jsonb_build_object(
    'id', ae.id,
    'project_id', ae.project_id,
    'export_number', ae.export_number,
    'requested_by', ae.requested_by,
    'status', ae.status,
    'storage_bucket', ae.storage_bucket,
    'storage_key', ae.storage_key,
    'manifest_checksum_sha256', ae.manifest_checksum_sha256,
    'requested_at', ae.requested_at,
    'completed_at', ae.completed_at,
    'expires_at', ae.expires_at,
    'item_count', (
      select count(*)
      from public.archive_export_items aei
      where aei.archive_export_id = ae.id
    )
  )
  from public.archive_exports ae
  where ae.id = p_archive_export_id
$$;

create or replace function public.archive_location_response_json(p_location_id uuid)
returns jsonb
language sql
stable
set search_path = public, pg_catalog
as $$
  select jsonb_build_object(
    'id', al.id,
    'archive_room_id', al.archive_room_id,
    'parent_location_id', al.parent_location_id,
    'location_type', al.location_type,
    'code', al.code,
    'label', al.label,
    'qr_token', al.qr_token,
    'is_active', al.is_active
  )
  from public.archive_locations al
  where al.id = p_location_id
$$;

create or replace function public.physical_file_response_json(p_physical_file_id uuid)
returns jsonb
language sql
stable
set search_path = public, pg_catalog
as $$
  select jsonb_build_object(
    'id', pf.id,
    'physical_file_code', pf.physical_file_code,
    'project_id', pf.project_id,
    'project', jsonb_build_object(
      'id', p.id,
      'project_code', p.project_code,
      'name', p.name
    ),
    'archive_location_id', pf.archive_location_id,
    'archive_location', jsonb_build_object(
      'id', al.id,
      'archive_room_id', al.archive_room_id,
      'location_type', al.location_type,
      'code', al.code,
      'label', al.label,
      'qr_token', al.qr_token
    ),
    'archive_room', jsonb_build_object(
      'id', ar.id,
      'code', ar.code,
      'name', ar.name
    ),
    'volume_number', pf.volume_number,
    'status', pf.status,
    'qr_token', pf.qr_token,
    'archived_on', pf.archived_on,
    'archived_by', pf.archived_by,
    'last_verified_at', pf.last_verified_at,
    'next_verification_at', pf.next_verification_at,
    'notes', pf.notes,
    'created_at', pf.created_at,
    'updated_at', pf.updated_at,
    'open_checkout', (
      select jsonb_build_object(
        'id', pfc.id,
        'checked_out_by', pfc.checked_out_by,
        'checked_out_at', pfc.checked_out_at,
        'purpose', pfc.purpose,
        'expected_return_at', pfc.expected_return_at
      )
      from public.physical_file_checkouts pfc
      where pfc.physical_file_id = pf.id
        and pfc.returned_at is null
      limit 1
    )
  )
  from public.physical_files pf
  join public.projects p on p.id = pf.project_id
  join public.archive_locations al on al.id = pf.archive_location_id
  join public.archive_rooms ar on ar.id = al.archive_room_id
  where pf.id = p_physical_file_id
$$;

create or replace function public.create_folder_audited(
  p_project_id uuid,
  p_parent_folder_id uuid,
  p_name text,
  p_sort_order integer,
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
  inserted_folder public.folders%rowtype;
begin
  if not exists (
    select 1 from public.projects where id = p_project_id and deleted_at is null
  ) then
    raise exception 'IEMS_PROJECT_NOT_FOUND';
  end if;

  if p_parent_folder_id is not null and not exists (
    select 1 from public.folders
    where id = p_parent_folder_id
      and project_id = p_project_id
      and deleted_at is null
  ) then
    raise exception 'IEMS_PARENT_FOLDER_NOT_FOUND';
  end if;

  insert into public.folders(project_id, parent_folder_id, name, sort_order, created_by)
  values (
    p_project_id,
    p_parent_folder_id,
    trim(p_name),
    coalesce(p_sort_order, 0),
    p_actor_employee_id
  )
  returning * into inserted_folder;

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
    'folder.created',
    'folder',
    inserted_folder.id,
    p_request_id,
    to_jsonb(inserted_folder),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.folder_response_json(inserted_folder.id);
end;
$$;

create or replace function public.update_folder_audited(
  p_folder_id uuid,
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
  old_folder public.folders%rowtype;
  updated_folder public.folders%rowtype;
  requested_parent_id uuid;
begin
  select * into old_folder
  from public.folders
  where id = p_folder_id
    and deleted_at is null
  for update;

  if old_folder.id is null then
    raise exception 'IEMS_FOLDER_NOT_FOUND';
  end if;

  if p_patch ? 'parent_folder_id' then
    requested_parent_id := nullif(p_patch->>'parent_folder_id', '')::uuid;

    if requested_parent_id = old_folder.id then
      raise exception 'IEMS_FOLDER_CYCLE';
    end if;

    if requested_parent_id is not null then
      if not exists (
        select 1
        from public.folders parent
        where parent.id = requested_parent_id
          and parent.project_id = old_folder.project_id
          and parent.deleted_at is null
      ) then
        raise exception 'IEMS_PARENT_FOLDER_NOT_FOUND';
      end if;

      if exists (
        with recursive descendants as (
          select id from public.folders
          where parent_folder_id = old_folder.id
            and deleted_at is null
          union all
          select child.id
          from public.folders child
          join descendants d on d.id = child.parent_folder_id
          where child.deleted_at is null
        )
        select 1 from descendants where id = requested_parent_id
      ) then
        raise exception 'IEMS_FOLDER_CYCLE';
      end if;
    end if;
  else
    requested_parent_id := old_folder.parent_folder_id;
  end if;

  update public.folders
  set
    parent_folder_id = requested_parent_id,
    name = case when p_patch ? 'name' then trim(p_patch->>'name') else name end,
    sort_order = case
      when p_patch ? 'sort_order' then (p_patch->>'sort_order')::integer
      else sort_order
    end
  where id = p_folder_id
  returning * into updated_folder;

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
    'folder.updated',
    'folder',
    updated_folder.id,
    p_request_id,
    to_jsonb(old_folder),
    to_jsonb(updated_folder),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.folder_response_json(updated_folder.id);
end;
$$;

create or replace function public.soft_delete_folder_audited(
  p_folder_id uuid,
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
  old_folder public.folders%rowtype;
  updated_folder public.folders%rowtype;
begin
  select * into old_folder
  from public.folders
  where id = p_folder_id
    and deleted_at is null
  for update;

  if old_folder.id is null then
    raise exception 'IEMS_FOLDER_NOT_FOUND';
  end if;

  if exists (
    select 1 from public.folders
    where parent_folder_id = p_folder_id
      and deleted_at is null
  ) or exists (
    select 1 from public.documents
    where folder_id = p_folder_id
      and deleted_at is null
  ) then
    raise exception 'IEMS_FOLDER_NOT_EMPTY';
  end if;

  update public.folders
  set deleted_at = now()
  where id = p_folder_id
  returning * into updated_folder;

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
    'folder.deleted',
    'folder',
    p_folder_id,
    p_request_id,
    to_jsonb(old_folder),
    to_jsonb(updated_folder),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.folder_response_json(updated_folder.id);
end;
$$;

create or replace function public.create_document_with_version_audited(
  p_document_id uuid,
  p_document_version_id uuid,
  p_folder_id uuid,
  p_document_type_id uuid,
  p_confidentiality_level_id uuid,
  p_display_name text,
  p_storage_bucket text,
  p_storage_key text,
  p_original_filename text,
  p_mime_type text,
  p_size_bytes bigint,
  p_checksum_sha256 text,
  p_change_note text,
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
  target_folder public.folders%rowtype;
  inserted_document public.documents%rowtype;
  inserted_version public.document_versions%rowtype;
begin
  select * into target_folder
  from public.folders
  where id = p_folder_id
    and deleted_at is null
  for share;

  if target_folder.id is null then
    raise exception 'IEMS_FOLDER_NOT_FOUND';
  end if;

  if not exists (
    select 1 from public.projects
    where id = target_folder.project_id
      and deleted_at is null
  ) then
    raise exception 'IEMS_PROJECT_NOT_FOUND';
  end if;

  insert into public.documents(
    id,
    project_id,
    folder_id,
    document_type_id,
    confidentiality_level_id,
    display_name,
    created_by
  )
  values (
    p_document_id,
    target_folder.project_id,
    p_folder_id,
    p_document_type_id,
    p_confidentiality_level_id,
    trim(p_display_name),
    p_actor_employee_id
  )
  returning * into inserted_document;

  insert into public.document_versions(
    id,
    document_id,
    version_number,
    storage_bucket,
    storage_key,
    original_filename,
    mime_type,
    size_bytes,
    checksum_sha256,
    change_note,
    uploaded_by
  )
  values (
    p_document_version_id,
    inserted_document.id,
    1,
    p_storage_bucket,
    p_storage_key,
    p_original_filename,
    p_mime_type,
    p_size_bytes,
    lower(p_checksum_sha256),
    nullif(trim(coalesce(p_change_note, '')), ''),
    p_actor_employee_id
  )
  returning * into inserted_version;

  insert into public.audit_events(
    actor_user_account_id,
    actor_employee_id,
    action_code,
    resource_type,
    resource_id,
    request_id,
    new_values,
    metadata,
    ip_address,
    user_agent
  )
  values (
    p_actor_user_account_id,
    p_actor_employee_id,
    'document.uploaded',
    'document',
    inserted_document.id,
    p_request_id,
    to_jsonb(inserted_document),
    jsonb_build_object('version', to_jsonb(inserted_version)),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.document_response_json(inserted_document.id);
end;
$$;

create or replace function public.create_document_version_audited(
  p_document_id uuid,
  p_document_version_id uuid,
  p_storage_bucket text,
  p_storage_key text,
  p_original_filename text,
  p_mime_type text,
  p_size_bytes bigint,
  p_checksum_sha256 text,
  p_change_note text,
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
  target_document public.documents%rowtype;
  inserted_version public.document_versions%rowtype;
  next_version_number integer;
begin
  select * into target_document
  from public.documents
  where id = p_document_id
    and deleted_at is null
  for update;

  if target_document.id is null then
    raise exception 'IEMS_DOCUMENT_NOT_FOUND';
  end if;

  if not exists (
    select 1 from public.projects
    where id = target_document.project_id
      and deleted_at is null
  ) then
    raise exception 'IEMS_PROJECT_NOT_FOUND';
  end if;

  select coalesce(max(version_number), 0) + 1 into next_version_number
  from public.document_versions
  where document_id = p_document_id;

  insert into public.document_versions(
    id,
    document_id,
    version_number,
    storage_bucket,
    storage_key,
    original_filename,
    mime_type,
    size_bytes,
    checksum_sha256,
    change_note,
    uploaded_by
  )
  values (
    p_document_version_id,
    p_document_id,
    next_version_number,
    p_storage_bucket,
    p_storage_key,
    p_original_filename,
    p_mime_type,
    p_size_bytes,
    lower(p_checksum_sha256),
    nullif(trim(coalesce(p_change_note, '')), ''),
    p_actor_employee_id
  )
  returning * into inserted_version;

  update public.documents
  set status = 'ACTIVE'
  where id = p_document_id;

  insert into public.audit_events(
    actor_user_account_id,
    actor_employee_id,
    action_code,
    resource_type,
    resource_id,
    request_id,
    new_values,
    metadata,
    ip_address,
    user_agent
  )
  values (
    p_actor_user_account_id,
    p_actor_employee_id,
    'document.version_created',
    'document',
    p_document_id,
    p_request_id,
    to_jsonb(inserted_version),
    jsonb_build_object('version_number', inserted_version.version_number),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.document_response_json(p_document_id);
end;
$$;

create or replace function public.record_document_download_audited(
  p_document_version_id uuid,
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
  version_record public.document_versions%rowtype;
  document_record public.documents%rowtype;
begin
  select * into version_record
  from public.document_versions
  where id = p_document_version_id;

  if version_record.id is null then
    raise exception 'IEMS_DOCUMENT_VERSION_NOT_FOUND';
  end if;

  select * into document_record
  from public.documents
  where id = version_record.document_id
    and deleted_at is null;

  if document_record.id is null then
    raise exception 'IEMS_DOCUMENT_NOT_FOUND';
  end if;

  insert into public.audit_events(
    actor_user_account_id,
    actor_employee_id,
    action_code,
    resource_type,
    resource_id,
    request_id,
    metadata,
    ip_address,
    user_agent
  )
  values (
    p_actor_user_account_id,
    p_actor_employee_id,
    'document.downloaded',
    'document',
    document_record.id,
    p_request_id,
    jsonb_build_object('document_version_id', version_record.id),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.document_version_response_json(version_record.id);
end;
$$;

create or replace function public.create_archive_export_audited(
  p_archive_export_id uuid,
  p_project_id uuid,
  p_requested_by uuid,
  p_expires_at timestamptz,
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
  inserted_export public.archive_exports%rowtype;
  next_export_number integer;
begin
  if not exists (
    select 1 from public.projects
    where id = p_project_id
      and deleted_at is null
  ) then
    raise exception 'IEMS_PROJECT_NOT_FOUND';
  end if;

  select coalesce(max(export_number), 0) + 1 into next_export_number
  from public.archive_exports
  where project_id = p_project_id;

  insert into public.archive_exports(
    id,
    project_id,
    export_number,
    requested_by,
    status,
    expires_at
  )
  values (
    p_archive_export_id,
    p_project_id,
    next_export_number,
    p_requested_by,
    'QUEUED',
    p_expires_at
  )
  returning * into inserted_export;

  insert into public.notifications(
    employee_id,
    notification_type,
    title,
    message,
    resource_type,
    resource_id
  )
  values (
    p_requested_by,
    'ARCHIVE_EXPORT',
    'Archive export queued',
    'Your offline archive export has been queued.',
    'archive_export',
    inserted_export.id
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
    'archive.export_requested',
    'archive_export',
    inserted_export.id,
    p_request_id,
    to_jsonb(inserted_export),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.archive_export_response_json(inserted_export.id);
end;
$$;

create or replace function public.complete_archive_export_audited(
  p_archive_export_id uuid,
  p_storage_bucket text,
  p_storage_key text,
  p_manifest_checksum_sha256 text,
  p_items jsonb,
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
  old_export public.archive_exports%rowtype;
  updated_export public.archive_exports%rowtype;
begin
  select * into old_export
  from public.archive_exports
  where id = p_archive_export_id
  for update;

  if old_export.id is null then
    raise exception 'IEMS_ARCHIVE_EXPORT_NOT_FOUND';
  end if;

  delete from public.archive_export_items
  where archive_export_id = p_archive_export_id;

  insert into public.archive_export_items(
    archive_export_id,
    document_version_id,
    relative_path,
    checksum_sha256
  )
  select
    p_archive_export_id,
    (item->>'document_version_id')::uuid,
    item->>'relative_path',
    lower(item->>'checksum_sha256')
  from jsonb_array_elements(coalesce(p_items, '[]'::jsonb)) as item;

  update public.archive_exports
  set
    status = 'READY',
    storage_bucket = p_storage_bucket,
    storage_key = p_storage_key,
    manifest_checksum_sha256 = lower(p_manifest_checksum_sha256),
    completed_at = now()
  where id = p_archive_export_id
  returning * into updated_export;

  insert into public.notifications(
    employee_id,
    notification_type,
    title,
    message,
    resource_type,
    resource_id
  )
  values (
    updated_export.requested_by,
    'ARCHIVE_EXPORT',
    'Archive export ready',
    'Your offline archive export is ready for download.',
    'archive_export',
    updated_export.id
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
    metadata,
    ip_address,
    user_agent
  )
  values (
    p_actor_user_account_id,
    p_actor_employee_id,
    'archive.export_completed',
    'archive_export',
    updated_export.id,
    p_request_id,
    to_jsonb(old_export),
    to_jsonb(updated_export),
    jsonb_build_object('item_count', jsonb_array_length(coalesce(p_items, '[]'::jsonb))),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.archive_export_response_json(updated_export.id);
end;
$$;

create or replace function public.fail_archive_export_audited(
  p_archive_export_id uuid,
  p_error_message text,
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
  old_export public.archive_exports%rowtype;
  updated_export public.archive_exports%rowtype;
begin
  select * into old_export
  from public.archive_exports
  where id = p_archive_export_id
  for update;

  if old_export.id is null then
    raise exception 'IEMS_ARCHIVE_EXPORT_NOT_FOUND';
  end if;

  update public.archive_exports
  set status = 'FAILED'
  where id = p_archive_export_id
  returning * into updated_export;

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
    'archive.export_failed',
    'archive_export',
    updated_export.id,
    p_request_id,
    to_jsonb(old_export),
    to_jsonb(updated_export),
    jsonb_build_object('error', p_error_message),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.archive_export_response_json(updated_export.id);
end;
$$;

create or replace function public.create_archive_room_audited(
  p_code text,
  p_name text,
  p_description text,
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
  inserted_room public.archive_rooms%rowtype;
begin
  insert into public.archive_rooms(code, name, description)
  values (
    upper(trim(p_code)),
    trim(p_name),
    nullif(trim(coalesce(p_description, '')), '')
  )
  returning * into inserted_room;

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
    'archive.room_created',
    'archive_room',
    inserted_room.id,
    p_request_id,
    to_jsonb(inserted_room),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return to_jsonb(inserted_room);
end;
$$;

create or replace function public.create_archive_location_audited(
  p_archive_room_id uuid,
  p_parent_location_id uuid,
  p_location_type text,
  p_code text,
  p_label text,
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
  parent_location public.archive_locations%rowtype;
  inserted_location public.archive_locations%rowtype;
begin
  if not exists (
    select 1 from public.archive_rooms
    where id = p_archive_room_id
      and is_active = true
  ) then
    raise exception 'IEMS_ARCHIVE_ROOM_NOT_FOUND';
  end if;

  if p_parent_location_id is null then
    if p_location_type <> 'RACK' then
      raise exception 'IEMS_INVALID_ARCHIVE_LOCATION_HIERARCHY';
    end if;
  else
    select * into parent_location
    from public.archive_locations
    where id = p_parent_location_id
      and archive_room_id = p_archive_room_id
      and is_active = true;

    if parent_location.id is null then
      raise exception 'IEMS_ARCHIVE_LOCATION_NOT_FOUND';
    end if;

    if not (
      (parent_location.location_type = 'RACK' and p_location_type = 'SHELF')
      or (parent_location.location_type = 'SHELF' and p_location_type = 'CABINET')
      or (parent_location.location_type = 'CABINET' and p_location_type = 'BOX')
      or (parent_location.location_type = 'BOX' and p_location_type = 'FILE_SLOT')
    ) then
      raise exception 'IEMS_INVALID_ARCHIVE_LOCATION_HIERARCHY';
    end if;
  end if;

  insert into public.archive_locations(
    archive_room_id,
    parent_location_id,
    location_type,
    code,
    label
  )
  values (
    p_archive_room_id,
    p_parent_location_id,
    p_location_type,
    upper(trim(p_code)),
    nullif(trim(coalesce(p_label, '')), '')
  )
  returning * into inserted_location;

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
    'archive.location_created',
    'archive_location',
    inserted_location.id,
    p_request_id,
    to_jsonb(inserted_location),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.archive_location_response_json(inserted_location.id);
end;
$$;

create or replace function public.create_physical_file_audited(
  p_physical_file_code text,
  p_project_id uuid,
  p_archive_location_id uuid,
  p_volume_number integer,
  p_archived_on date,
  p_notes text,
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
  target_location public.archive_locations%rowtype;
  inserted_file public.physical_files%rowtype;
begin
  if not exists (
    select 1 from public.projects where id = p_project_id and deleted_at is null
  ) then
    raise exception 'IEMS_PROJECT_NOT_FOUND';
  end if;

  select * into target_location
  from public.archive_locations
  where id = p_archive_location_id
    and is_active = true;

  if target_location.id is null or target_location.location_type <> 'FILE_SLOT' then
    raise exception 'IEMS_ARCHIVE_LOCATION_NOT_FOUND';
  end if;

  insert into public.physical_files(
    physical_file_code,
    project_id,
    archive_location_id,
    volume_number,
    status,
    archived_on,
    archived_by,
    notes
  )
  values (
    upper(trim(p_physical_file_code)),
    p_project_id,
    p_archive_location_id,
    coalesce(p_volume_number, 1),
    'AVAILABLE',
    p_archived_on,
    p_actor_employee_id,
    nullif(trim(coalesce(p_notes, '')), '')
  )
  returning * into inserted_file;

  insert into public.physical_file_movements(
    physical_file_id,
    from_location_id,
    to_location_id,
    movement_type,
    performed_by,
    remarks
  )
  values (
    inserted_file.id,
    null,
    p_archive_location_id,
    'ARCHIVE',
    p_actor_employee_id,
    'Initial archive assignment'
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
    'physical_file.created',
    'physical_file',
    inserted_file.id,
    p_request_id,
    to_jsonb(inserted_file),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.physical_file_response_json(inserted_file.id);
end;
$$;

create or replace function public.checkout_physical_file_audited(
  p_physical_file_id uuid,
  p_purpose text,
  p_expected_return_at timestamptz,
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
  old_file public.physical_files%rowtype;
  updated_file public.physical_files%rowtype;
  inserted_checkout public.physical_file_checkouts%rowtype;
begin
  select * into old_file
  from public.physical_files
  where id = p_physical_file_id
  for update;

  if old_file.id is null then
    raise exception 'IEMS_PHYSICAL_FILE_NOT_FOUND';
  end if;

  if old_file.status <> 'AVAILABLE' then
    raise exception 'IEMS_PHYSICAL_FILE_NOT_AVAILABLE';
  end if;

  insert into public.physical_file_checkouts(
    physical_file_id,
    checked_out_by,
    purpose,
    expected_return_at
  )
  values (
    p_physical_file_id,
    p_actor_employee_id,
    trim(p_purpose),
    p_expected_return_at
  )
  returning * into inserted_checkout;

  update public.physical_files
  set status = 'CHECKED_OUT'
  where id = p_physical_file_id
  returning * into updated_file;

  insert into public.physical_file_movements(
    physical_file_id,
    from_location_id,
    to_location_id,
    movement_type,
    performed_by,
    remarks
  )
  values (
    p_physical_file_id,
    old_file.archive_location_id,
    null,
    'CHECKOUT',
    p_actor_employee_id,
    p_purpose
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
    metadata,
    ip_address,
    user_agent
  )
  values (
    p_actor_user_account_id,
    p_actor_employee_id,
    'physical_file.checked_out',
    'physical_file',
    p_physical_file_id,
    p_request_id,
    to_jsonb(old_file),
    to_jsonb(updated_file),
    jsonb_build_object('checkout', to_jsonb(inserted_checkout)),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.physical_file_response_json(p_physical_file_id);
end;
$$;

create or replace function public.return_physical_file_audited(
  p_physical_file_id uuid,
  p_returned_to_location_id uuid,
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
  old_file public.physical_files%rowtype;
  updated_file public.physical_files%rowtype;
  open_checkout public.physical_file_checkouts%rowtype;
  target_location_id uuid;
begin
  select * into old_file
  from public.physical_files
  where id = p_physical_file_id
  for update;

  if old_file.id is null then
    raise exception 'IEMS_PHYSICAL_FILE_NOT_FOUND';
  end if;

  select * into open_checkout
  from public.physical_file_checkouts
  where physical_file_id = p_physical_file_id
    and returned_at is null
  for update;

  if open_checkout.id is null then
    raise exception 'IEMS_PHYSICAL_CHECKOUT_NOT_FOUND';
  end if;

  target_location_id := coalesce(p_returned_to_location_id, old_file.archive_location_id);

  if not exists (
    select 1 from public.archive_locations
    where id = target_location_id
      and location_type = 'FILE_SLOT'
      and is_active = true
  ) then
    raise exception 'IEMS_ARCHIVE_LOCATION_NOT_FOUND';
  end if;

  update public.physical_file_checkouts
  set
    returned_at = now(),
    returned_to_location_id = target_location_id,
    received_by = p_actor_employee_id,
    remarks = nullif(trim(coalesce(p_remarks, '')), '')
  where id = open_checkout.id;

  update public.physical_files
  set
    status = 'AVAILABLE',
    archive_location_id = target_location_id
  where id = p_physical_file_id
  returning * into updated_file;

  insert into public.physical_file_movements(
    physical_file_id,
    from_location_id,
    to_location_id,
    movement_type,
    performed_by,
    remarks
  )
  values (
    p_physical_file_id,
    old_file.archive_location_id,
    target_location_id,
    'RETURN',
    p_actor_employee_id,
    p_remarks
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
    'physical_file.returned',
    'physical_file',
    p_physical_file_id,
    p_request_id,
    to_jsonb(old_file),
    to_jsonb(updated_file),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.physical_file_response_json(p_physical_file_id);
end;
$$;

create or replace function public.move_physical_file_audited(
  p_physical_file_id uuid,
  p_to_location_id uuid,
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
  old_file public.physical_files%rowtype;
  updated_file public.physical_files%rowtype;
begin
  select * into old_file
  from public.physical_files
  where id = p_physical_file_id
  for update;

  if old_file.id is null then
    raise exception 'IEMS_PHYSICAL_FILE_NOT_FOUND';
  end if;

  if old_file.status = 'CHECKED_OUT' then
    raise exception 'IEMS_PHYSICAL_FILE_CHECKED_OUT';
  end if;

  if not exists (
    select 1 from public.archive_locations
    where id = p_to_location_id
      and location_type = 'FILE_SLOT'
      and is_active = true
  ) then
    raise exception 'IEMS_ARCHIVE_LOCATION_NOT_FOUND';
  end if;

  update public.physical_files
  set archive_location_id = p_to_location_id
  where id = p_physical_file_id
  returning * into updated_file;

  insert into public.physical_file_movements(
    physical_file_id,
    from_location_id,
    to_location_id,
    movement_type,
    performed_by,
    remarks
  )
  values (
    p_physical_file_id,
    old_file.archive_location_id,
    p_to_location_id,
    'MOVE',
    p_actor_employee_id,
    p_remarks
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
    'physical_file.moved',
    'physical_file',
    p_physical_file_id,
    p_request_id,
    to_jsonb(old_file),
    to_jsonb(updated_file),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.physical_file_response_json(p_physical_file_id);
end;
$$;

create or replace function public.verify_physical_file_audited(
  p_physical_file_id uuid,
  p_location_correct boolean,
  p_label_readable boolean,
  p_physical_file_present boolean,
  p_digital_archive_present boolean,
  p_documents_complete boolean,
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
  old_file public.physical_files%rowtype;
  updated_file public.physical_files%rowtype;
  inserted_verification public.archive_verifications%rowtype;
begin
  select * into old_file
  from public.physical_files
  where id = p_physical_file_id
  for update;

  if old_file.id is null then
    raise exception 'IEMS_PHYSICAL_FILE_NOT_FOUND';
  end if;

  insert into public.archive_verifications(
    physical_file_id,
    verified_by,
    location_correct,
    label_readable,
    physical_file_present,
    digital_archive_present,
    documents_complete,
    remarks
  )
  values (
    p_physical_file_id,
    p_actor_employee_id,
    p_location_correct,
    p_label_readable,
    p_physical_file_present,
    p_digital_archive_present,
    p_documents_complete,
    nullif(trim(coalesce(p_remarks, '')), '')
  )
  returning * into inserted_verification;

  update public.physical_files
  set
    last_verified_at = inserted_verification.verified_at,
    next_verification_at = inserted_verification.verified_at + interval '6 months'
  where id = p_physical_file_id
  returning * into updated_file;

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
    'physical_file.verified',
    'physical_file',
    p_physical_file_id,
    p_request_id,
    to_jsonb(old_file),
    to_jsonb(updated_file),
    jsonb_build_object('verification', to_jsonb(inserted_verification)),
    nullif(p_ip_address, '')::inet,
    p_user_agent
  );

  return public.physical_file_response_json(p_physical_file_id);
end;
$$;

revoke execute on function public.folder_response_json(uuid) from public, anon, authenticated;
revoke execute on function public.document_version_response_json(uuid) from public, anon, authenticated;
revoke execute on function public.document_response_json(uuid) from public, anon, authenticated;
revoke execute on function public.archive_export_response_json(uuid) from public, anon, authenticated;
revoke execute on function public.archive_location_response_json(uuid) from public, anon, authenticated;
revoke execute on function public.physical_file_response_json(uuid) from public, anon, authenticated;
revoke execute on function public.create_folder_audited(uuid, uuid, text, integer, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.update_folder_audited(uuid, jsonb, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.soft_delete_folder_audited(uuid, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.create_document_with_version_audited(uuid, uuid, uuid, uuid, uuid, text, text, text, text, text, bigint, text, text, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.create_document_version_audited(uuid, uuid, text, text, text, text, bigint, text, text, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.record_document_download_audited(uuid, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.create_archive_export_audited(uuid, uuid, uuid, timestamptz, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.complete_archive_export_audited(uuid, text, text, text, jsonb, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.fail_archive_export_audited(uuid, text, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.create_archive_room_audited(text, text, text, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.create_archive_location_audited(uuid, uuid, text, text, text, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.create_physical_file_audited(text, uuid, uuid, integer, date, text, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.checkout_physical_file_audited(uuid, text, timestamptz, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.return_physical_file_audited(uuid, uuid, text, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.move_physical_file_audited(uuid, uuid, text, uuid, uuid, uuid, text, text) from public, anon, authenticated;
revoke execute on function public.verify_physical_file_audited(uuid, boolean, boolean, boolean, boolean, boolean, text, uuid, uuid, uuid, text, text) from public, anon, authenticated;

grant execute on function public.folder_response_json(uuid) to service_role;
grant execute on function public.document_version_response_json(uuid) to service_role;
grant execute on function public.document_response_json(uuid) to service_role;
grant execute on function public.archive_export_response_json(uuid) to service_role;
grant execute on function public.archive_location_response_json(uuid) to service_role;
grant execute on function public.physical_file_response_json(uuid) to service_role;
grant execute on function public.create_folder_audited(uuid, uuid, text, integer, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.update_folder_audited(uuid, jsonb, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.soft_delete_folder_audited(uuid, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.create_document_with_version_audited(uuid, uuid, uuid, uuid, uuid, text, text, text, text, text, bigint, text, text, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.create_document_version_audited(uuid, uuid, text, text, text, text, bigint, text, text, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.record_document_download_audited(uuid, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.create_archive_export_audited(uuid, uuid, uuid, timestamptz, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.complete_archive_export_audited(uuid, text, text, text, jsonb, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.fail_archive_export_audited(uuid, text, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.create_archive_room_audited(text, text, text, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.create_archive_location_audited(uuid, uuid, text, text, text, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.create_physical_file_audited(text, uuid, uuid, integer, date, text, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.checkout_physical_file_audited(uuid, text, timestamptz, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.return_physical_file_audited(uuid, uuid, text, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.move_physical_file_audited(uuid, uuid, text, uuid, uuid, uuid, text, text) to service_role;
grant execute on function public.verify_physical_file_audited(uuid, boolean, boolean, boolean, boolean, boolean, text, uuid, uuid, uuid, text, text) to service_role;
