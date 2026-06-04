-- IEMS ERP: physical file-room archive
create table public.archive_rooms (
  id uuid primary key default gen_random_uuid(),
  code varchar(30) not null unique,
  name varchar(120) not null unique,
  description text,
  is_active boolean not null default true
);

create table public.archive_locations (
  id uuid primary key default gen_random_uuid(),
  archive_room_id uuid not null references public.archive_rooms(id) on delete restrict,
  parent_location_id uuid references public.archive_locations(id) on delete restrict,
  location_type varchar(30) not null check (location_type in ('RACK','SHELF','CABINET','BOX','FILE_SLOT')),
  code varchar(50) not null,
  label varchar(120),
  qr_token uuid not null unique default gen_random_uuid(),
  is_active boolean not null default true
);
create unique index uq_archive_location_sibling
  on public.archive_locations(
    archive_room_id,
    coalesce(parent_location_id, '00000000-0000-0000-0000-000000000000'::uuid),
    location_type,
    code
  );

create table public.physical_files (
  id uuid primary key default gen_random_uuid(),
  physical_file_code varchar(60) not null unique,
  project_id uuid not null references public.projects(id) on delete restrict,
  archive_location_id uuid not null references public.archive_locations(id) on delete restrict,
  volume_number integer not null default 1 check (volume_number >= 1),
  status varchar(30) not null check (status in ('AVAILABLE','CHECKED_OUT','MISSING','UNDER_VERIFICATION','ARCHIVED')),
  qr_token uuid not null unique default gen_random_uuid(),
  archived_on date,
  archived_by uuid references public.employees(id) on delete restrict,
  last_verified_at timestamptz,
  next_verification_at timestamptz,
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(project_id, volume_number)
);

create table public.physical_file_checkouts (
  id uuid primary key default gen_random_uuid(),
  physical_file_id uuid not null references public.physical_files(id) on delete restrict,
  checked_out_by uuid not null references public.employees(id) on delete restrict,
  checked_out_at timestamptz not null default now(),
  purpose text not null,
  expected_return_at timestamptz,
  returned_at timestamptz,
  returned_to_location_id uuid references public.archive_locations(id) on delete restrict,
  received_by uuid references public.employees(id) on delete restrict,
  remarks text,
  check (returned_at is null or returned_at >= checked_out_at)
);
create unique index uq_one_open_checkout_per_physical_file
  on public.physical_file_checkouts(physical_file_id)
  where returned_at is null;

create table public.physical_file_movements (
  id uuid primary key default gen_random_uuid(),
  physical_file_id uuid not null references public.physical_files(id) on delete restrict,
  from_location_id uuid references public.archive_locations(id) on delete restrict,
  to_location_id uuid references public.archive_locations(id) on delete restrict,
  movement_type varchar(30) not null check (movement_type in ('ARCHIVE','MOVE','CHECKOUT','RETURN','CORRECTION')),
  performed_by uuid not null references public.employees(id) on delete restrict,
  remarks text,
  created_at timestamptz not null default now()
);

create table public.archive_verifications (
  id uuid primary key default gen_random_uuid(),
  physical_file_id uuid not null references public.physical_files(id) on delete restrict,
  verified_by uuid not null references public.employees(id) on delete restrict,
  verified_at timestamptz not null default now(),
  location_correct boolean not null,
  label_readable boolean not null,
  physical_file_present boolean not null,
  digital_archive_present boolean not null,
  documents_complete boolean not null,
  remarks text
);
