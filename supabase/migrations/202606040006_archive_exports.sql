-- IEMS ERP: reproducible offline ZIP exports
create table public.archive_exports (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete restrict,
  export_number integer not null check (export_number >= 1),
  requested_by uuid not null references public.employees(id) on delete restrict,
  status varchar(30) not null check (status in ('QUEUED','GENERATING','READY','FAILED','EXPIRED')),
  storage_bucket varchar(100),
  storage_key text,
  manifest_checksum_sha256 char(64),
  requested_at timestamptz not null default now(),
  completed_at timestamptz,
  expires_at timestamptz,
  unique(project_id, export_number)
);

create table public.archive_export_items (
  archive_export_id uuid not null references public.archive_exports(id) on delete cascade,
  document_version_id uuid not null references public.document_versions(id) on delete restrict,
  relative_path text not null,
  checksum_sha256 char(64) not null,
  primary key(archive_export_id, document_version_id)
);
