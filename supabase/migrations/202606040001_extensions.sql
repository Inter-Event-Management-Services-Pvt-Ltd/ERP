-- IEMS ERP: required PostgreSQL extensions
create extension if not exists pgcrypto;
create extension if not exists citext with schema extensions;
create extension if not exists pg_trgm with schema extensions;
