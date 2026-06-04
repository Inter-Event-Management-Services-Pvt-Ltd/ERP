-- IEMS ERP: folder templates, folder hierarchy, documents and immutable versions
create table public.folder_templates (
  id uuid primary key default gen_random_uuid(),
  name varchar(150) not null unique,
  project_type_id uuid references public.project_types(id) on delete restrict,
  is_active boolean not null default true,
  created_by uuid references public.employees(id) on delete restrict,
  created_at timestamptz not null default now()
);

create table public.folder_template_items (
  id uuid primary key default gen_random_uuid(),
  template_id uuid not null references public.folder_templates(id) on delete cascade,
  parent_item_id uuid references public.folder_template_items(id) on delete restrict,
  name varchar(200) not null,
  sort_order integer not null default 0
);
create unique index uq_template_sibling_folder_name
  on public.folder_template_items(template_id, coalesce(parent_item_id, '00000000-0000-0000-0000-000000000000'::uuid), lower(name));

create table public.folders (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete restrict,
  parent_folder_id uuid references public.folders(id) on delete restrict,
  name varchar(255) not null,
  sort_order integer not null default 0,
  created_by uuid not null references public.employees(id) on delete restrict,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz
);
create unique index uq_folder_sibling_name
  on public.folders(project_id, coalesce(parent_folder_id, '00000000-0000-0000-0000-000000000000'::uuid), lower(name))
  where deleted_at is null;
create unique index uq_project_root_folder
  on public.folders(project_id)
  where parent_folder_id is null and deleted_at is null;

create table public.documents (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete restrict,
  folder_id uuid not null references public.folders(id) on delete restrict,
  document_type_id uuid references public.document_types(id) on delete restrict,
  confidentiality_level_id uuid not null references public.confidentiality_levels(id) on delete restrict,
  display_name varchar(255) not null,
  status varchar(30) not null default 'ACTIVE'
    check (status in ('ACTIVE','SUPERSEDED','ARCHIVED','DELETED')),
  created_by uuid not null references public.employees(id) on delete restrict,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  deleted_at timestamptz
);
create unique index uq_document_name_in_folder
  on public.documents(folder_id, lower(display_name))
  where deleted_at is null;

create table public.document_versions (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.documents(id) on delete restrict,
  version_number integer not null check (version_number >= 1),
  storage_bucket varchar(100) not null,
  storage_key text not null unique,
  original_filename varchar(255) not null,
  mime_type varchar(150) not null,
  size_bytes bigint not null check (size_bytes >= 0),
  checksum_sha256 char(64) not null check (checksum_sha256 ~ '^[0-9a-fA-F]{64}$'),
  change_note text,
  uploaded_by uuid not null references public.employees(id) on delete restrict,
  uploaded_at timestamptz not null default now(),
  unique(document_id, version_number)
);

create table public.tags (
  id uuid primary key default gen_random_uuid(),
  name extensions.citext not null unique
);

create table public.document_tag_assignments (
  document_id uuid not null references public.documents(id) on delete cascade,
  tag_id uuid not null references public.tags(id) on delete cascade,
  primary key(document_id, tag_id)
);

create table public.document_metadata (
  document_id uuid primary key references public.documents(id) on delete cascade,
  metadata jsonb not null default '{}'::jsonb
);
