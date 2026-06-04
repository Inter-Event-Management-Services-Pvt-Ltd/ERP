-- IEMS ERP: private Supabase Storage buckets
insert into storage.buckets (id, name, public, file_size_limit)
values
  ('project-documents', 'project-documents', false, 104857600),
  ('generated-archives', 'generated-archives', false, 1073741824),
  ('generated-labels', 'generated-labels', false, 10485760),
  ('document-previews', 'document-previews', false, 52428800),
  ('profile-assets', 'profile-assets', false, 10485760)
on conflict (id) do nothing;

-- Object names in project-documents must start with the project UUID:
-- <project_uuid>/<document_uuid>/<document_version_uuid>/<filename>
create policy storage_project_documents_read
on storage.objects for select
to authenticated
using (
  bucket_id = 'project-documents'
  and public.has_project_access(public.try_uuid(split_part(name, '/', 1)))
);

-- Generated archives and labels are intentionally served by short-lived
-- server-created signed URLs after FastAPI performs an ABAC check.
-- Browser writes are intentionally not enabled.
