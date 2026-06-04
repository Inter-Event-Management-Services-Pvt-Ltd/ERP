-- IEMS ERP: normalized reference tables
create table public.departments (
  id uuid primary key default gen_random_uuid(),
  code varchar(30) not null unique,
  name varchar(100) not null unique,
  is_active boolean not null default true,
  created_at timestamptz not null default now()
);

create table public.project_types (
  id uuid primary key default gen_random_uuid(),
  code varchar(40) not null unique,
  name varchar(100) not null unique,
  is_active boolean not null default true
);

create table public.project_statuses (
  id uuid primary key default gen_random_uuid(),
  code varchar(30) not null unique,
  name varchar(80) not null unique,
  sort_order integer not null,
  is_terminal boolean not null default false
);

create table public.priority_levels (
  id uuid primary key default gen_random_uuid(),
  code varchar(20) not null unique,
  name varchar(50) not null unique,
  rank smallint not null unique
);

create table public.document_types (
  id uuid primary key default gen_random_uuid(),
  code varchar(50) not null unique,
  name varchar(100) not null unique,
  requires_approval boolean not null default false,
  is_required_for_archive boolean not null default false
);

create table public.confidentiality_levels (
  id uuid primary key default gen_random_uuid(),
  code varchar(30) not null unique,
  name varchar(80) not null unique,
  rank smallint not null unique
);

create table public.leave_types (
  id uuid primary key default gen_random_uuid(),
  code varchar(30) not null unique,
  name varchar(80) not null unique,
  is_paid boolean not null default true,
  is_active boolean not null default true
);

create table public.task_statuses (
  id uuid primary key default gen_random_uuid(),
  code varchar(30) not null unique,
  name varchar(80) not null unique,
  is_terminal boolean not null default false
);

create table public.approval_types (
  id uuid primary key default gen_random_uuid(),
  code varchar(50) not null unique,
  name varchar(100) not null unique
);
