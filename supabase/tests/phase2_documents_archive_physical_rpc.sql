\set ON_ERROR_STOP on

begin;

create temp table phase2_actor as
select id as employee_id
from public.employees
where employee_code = 'IEMS-MGR-001';

create temp table phase2_project as
select '30000000-0000-4000-8000-000000000001'::uuid as project_id;

create temp table phase2_root_folder as
select id as folder_id
from public.folders
where project_id = (select project_id from phase2_project)
  and parent_folder_id is null
  and deleted_at is null
limit 1;

create temp table phase2_refs as
select
  (select id from public.document_types where code = 'CLIENT_BRIEF') as document_type_id,
  (select id from public.confidentiality_levels where code = 'GENERAL') as confidentiality_level_id;

do $$
declare
  actor_employee_id uuid := (select employee_id from phase2_actor);
  validation_project_id uuid := (select project_id from phase2_project);
  validation_root_folder_id uuid := (select folder_id from phase2_root_folder);
  created_folder_payload jsonb;
  updated_folder_payload jsonb;
  document_payload jsonb;
  version_payload jsonb;
  archive_export_payload jsonb;
  completed_export_payload jsonb;
  cancelled_export_payload jsonb;
  room_payload jsonb;
  rack_payload jsonb;
  shelf_payload jsonb;
  cabinet_payload jsonb;
  box_payload jsonb;
  slot_payload jsonb;
  physical_file_payload jsonb;
  checked_out_payload jsonb;
  returned_payload jsonb;
  moved_payload jsonb;
  verified_payload jsonb;
  validation_folder_id uuid;
  validation_document_id uuid := gen_random_uuid();
  validation_version_id uuid := gen_random_uuid();
  validation_export_id uuid := gen_random_uuid();
  validation_cancel_export_id uuid := gen_random_uuid();
  validation_room_id uuid;
  validation_slot_id uuid;
  validation_second_slot_id uuid;
  validation_physical_file_id uuid;
begin
  created_folder_payload := public.create_folder_audited(
    validation_project_id,
    validation_root_folder_id,
    'Phase 2 Validation Folder',
    110,
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );
  validation_folder_id := (created_folder_payload->>'id')::uuid;

  updated_folder_payload := public.update_folder_audited(
    validation_folder_id,
    jsonb_build_object('name', 'Phase 2 Validation Folder Updated', 'sort_order', 111),
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );

  if updated_folder_payload->>'name' <> 'Phase 2 Validation Folder Updated' then
    raise exception 'Folder update RPC did not update name';
  end if;

  document_payload := public.create_document_with_version_audited(
    validation_document_id,
    validation_version_id,
    validation_folder_id,
    (select document_type_id from phase2_refs),
    (select confidentiality_level_id from phase2_refs),
    'Phase 2 Validation Brief.pdf',
    'project-documents',
    validation_project_id || '/' || validation_document_id || '/' || validation_version_id || '/brief.pdf',
    'brief.pdf',
    'application/pdf',
    7,
    repeat('a', 64),
    'Initial validation upload',
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );

  if (document_payload->'latest_version'->>'version_number')::integer <> 1 then
    raise exception 'Document upload RPC did not create version 1';
  end if;

  version_payload := public.record_document_download_audited(
    validation_version_id,
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );

  if version_payload->>'storage_bucket' <> 'project-documents' then
    raise exception 'Document download audit RPC did not return version storage data';
  end if;

  archive_export_payload := public.create_archive_export_audited(
    validation_export_id,
    validation_project_id,
    actor_employee_id,
    now() + interval '24 hours',
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );

  if archive_export_payload->>'status' <> 'QUEUED' then
    raise exception 'Archive export was not queued';
  end if;

  perform public.create_archive_export_audited(
    validation_cancel_export_id,
    validation_project_id,
    actor_employee_id,
    now() + interval '24 hours',
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );

  cancelled_export_payload := public.cancel_archive_export_audited(
    validation_cancel_export_id,
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );

  if cancelled_export_payload->>'status' <> 'CANCELLED' then
    raise exception 'Archive export was not cancelled';
  end if;

  begin
    perform public.complete_archive_export_audited(
      validation_cancel_export_id,
      'generated-archives',
      validation_project_id || '/' || validation_cancel_export_id || '/archive.zip',
      repeat('b', 64),
      '[]'::jsonb,
      null,
      actor_employee_id,
      null,
      '127.0.0.1',
      'phase2-sql-validation'
    );
    raise exception 'Cancelled archive export was completed';
  exception
    when others then
      if sqlerrm not like '%IEMS_ARCHIVE_EXPORT_CANCELLED%' then
        raise;
      end if;
  end;

  completed_export_payload := public.complete_archive_export_audited(
    validation_export_id,
    'generated-archives',
    validation_project_id || '/' || validation_export_id || '/archive.zip',
    repeat('b', 64),
    jsonb_build_array(jsonb_build_object(
      'document_version_id', validation_version_id,
      'relative_path', 'IEMS-2026-DEMO-001/Phase 2 Validation Folder Updated/brief.pdf',
      'checksum_sha256', repeat('a', 64)
    )),
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );

  if completed_export_payload->>'status' <> 'READY' then
    raise exception 'Archive export was not completed';
  end if;

  if not exists (
    select 1
    from public.archive_export_items
    where archive_export_id = validation_export_id
      and document_version_id = validation_version_id
  ) then
    raise exception 'Archive export item was not recorded';
  end if;

  room_payload := public.create_archive_room_audited(
    'P2',
    'Phase 2 Validation Room',
    'Rollback-only validation room',
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );
  validation_room_id := (room_payload->>'id')::uuid;

  rack_payload := public.create_archive_location_audited(
    validation_room_id,
    null,
    'RACK',
    'R1',
    'Rack 1',
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );

  shelf_payload := public.create_archive_location_audited(
    validation_room_id,
    (rack_payload->>'id')::uuid,
    'SHELF',
    'S1',
    'Shelf 1',
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );

  cabinet_payload := public.create_archive_location_audited(
    validation_room_id,
    (shelf_payload->>'id')::uuid,
    'CABINET',
    'C1',
    'Cabinet 1',
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );

  box_payload := public.create_archive_location_audited(
    validation_room_id,
    (cabinet_payload->>'id')::uuid,
    'BOX',
    'B1',
    'Box 1',
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );

  slot_payload := public.create_archive_location_audited(
    validation_room_id,
    (box_payload->>'id')::uuid,
    'FILE_SLOT',
    'F1',
    'File Slot 1',
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );
  validation_slot_id := (slot_payload->>'id')::uuid;

  validation_second_slot_id := (
    public.create_archive_location_audited(
      validation_room_id,
      (box_payload->>'id')::uuid,
      'FILE_SLOT',
      'F2',
      'File Slot 2',
      null,
      actor_employee_id,
      null,
      '127.0.0.1',
      'phase2-sql-validation'
    )->>'id'
  )::uuid;

  physical_file_payload := public.create_physical_file_audited(
    'P2-PF-001',
    validation_project_id,
    validation_slot_id,
    99,
    current_date,
    'Rollback-only validation physical file',
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );
  validation_physical_file_id := (physical_file_payload->>'id')::uuid;

  checked_out_payload := public.checkout_physical_file_audited(
    validation_physical_file_id,
    'Validation checkout',
    now() + interval '2 days',
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );

  if checked_out_payload->>'status' <> 'CHECKED_OUT' then
    raise exception 'Physical checkout did not update status';
  end if;

  begin
    perform public.checkout_physical_file_audited(
      validation_physical_file_id,
      'Second checkout should fail',
      now() + interval '2 days',
      null,
      actor_employee_id,
      null,
      '127.0.0.1',
      'phase2-sql-validation'
    );
    raise exception 'Expected duplicate physical checkout to fail';
  exception
    when raise_exception then
      if sqlerrm <> 'IEMS_PHYSICAL_FILE_NOT_AVAILABLE' then
        raise;
      end if;
  end;

  returned_payload := public.return_physical_file_audited(
    validation_physical_file_id,
    validation_slot_id,
    'Validation return',
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );

  if returned_payload->>'status' <> 'AVAILABLE' then
    raise exception 'Physical return did not restore availability';
  end if;

  moved_payload := public.move_physical_file_audited(
    validation_physical_file_id,
    validation_second_slot_id,
    'Validation move',
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );

  if moved_payload->>'archive_location_id' <> validation_second_slot_id::text then
    raise exception 'Physical move did not update location';
  end if;

  verified_payload := public.verify_physical_file_audited(
    validation_physical_file_id,
    true,
    true,
    true,
    true,
    true,
    'Validation verification',
    null,
    actor_employee_id,
    null,
    '127.0.0.1',
    'phase2-sql-validation'
  );

  if verified_payload->>'last_verified_at' is null then
    raise exception 'Physical verification did not update last_verified_at';
  end if;

  if not exists (
    select 1
    from public.audit_events
    where (resource_type, action_code) in (
      ('document', 'document.uploaded'),
      ('document', 'document.downloaded'),
      ('archive_export', 'archive.export_completed'),
      ('physical_file', 'physical_file.checked_out'),
      ('physical_file', 'physical_file.returned'),
      ('physical_file', 'physical_file.moved'),
      ('physical_file', 'physical_file.verified')
    )
  ) then
    raise exception 'Expected Phase 2 audit events were not written';
  end if;

  if has_function_privilege(
    'anon',
    'public.create_document_with_version_audited(uuid, uuid, uuid, uuid, uuid, text, text, text, text, text, bigint, text, text, uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'anon can execute create_document_with_version_audited';
  end if;

  if has_function_privilege(
    'authenticated',
    'public.checkout_physical_file_audited(uuid, text, timestamptz, uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'authenticated can execute checkout_physical_file_audited';
  end if;

  if not has_function_privilege(
    'service_role',
    'public.complete_archive_export_audited(uuid, text, text, text, jsonb, uuid, uuid, uuid, text, text)',
    'EXECUTE'
  ) then
    raise exception 'service_role cannot execute complete_archive_export_audited';
  end if;
end $$;

rollback;
