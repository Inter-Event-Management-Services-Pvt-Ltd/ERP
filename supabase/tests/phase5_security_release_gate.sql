\set ON_ERROR_STOP on

begin;

do $$
declare
  missing_rls text[];
  public_buckets text[];
  missing_buckets text[];
  exposed_private_schemas text[];
  policies_using_public_helpers text[];
  public_security_definers text[];
  service_role_missing_execute text[];
begin
  select array_agg(format('%I.%I', n.nspname, c.relname) order by n.nspname, c.relname)
  into missing_rls
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relkind in ('r', 'p')
    and not c.relrowsecurity;

  if coalesce(array_length(missing_rls, 1), 0) > 0 then
    raise exception 'RLS disabled on public tables: %', missing_rls;
  end if;

  select array_agg(id order by id)
  into public_buckets
  from storage.buckets
  where public = true;

  if coalesce(array_length(public_buckets, 1), 0) > 0 then
    raise exception 'Public storage buckets are not allowed: %', public_buckets;
  end if;

  select array_agg(expected.id order by expected.id)
  into missing_buckets
  from unnest(array[
    'project-documents',
    'generated-archives',
    'generated-labels',
    'document-previews',
    'profile-assets'
  ]::text[]) as expected(id)
  where not exists (
    select 1
    from storage.buckets b
    where b.id = expected.id
      and b.public = false
  );

  if coalesce(array_length(missing_buckets, 1), 0) > 0 then
    raise exception 'Expected private storage buckets missing: %', missing_buckets;
  end if;

  if not exists (
    select 1
    from pg_trigger t
    join pg_class c on c.oid = t.tgrelid
    join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relname = 'audit_events'
      and t.tgname = 'trg_prevent_audit_event_update'
      and t.tgenabled = 'O'
      and not t.tgisinternal
  ) then
    raise exception 'Audit immutability trigger is missing or disabled';
  end if;

  select array_agg(n.nspname order by n.nspname)
  into exposed_private_schemas
  from pg_namespace n
  where n.nspname = 'app_private'
    and (
      has_schema_privilege('anon', n.oid, 'USAGE')
      or has_schema_privilege('authenticated', n.oid, 'USAGE')
    );

  if coalesce(array_length(exposed_private_schemas, 1), 0) > 0 then
    raise exception 'Private helper schemas exposed to browser roles: %', exposed_private_schemas;
  end if;

  select array_agg(format('%I.%I.%I', schemaname, tablename, policyname)
                   order by schemaname, tablename, policyname)
  into policies_using_public_helpers
  from pg_policies
  where schemaname in ('public', 'storage')
    and (
      qual like '%public.current_employee_id%'
      or qual like '%public.is_super_user%'
      or qual like '%public.has_permission%'
      or qual like '%public.has_project_access%'
    );

  if coalesce(array_length(policies_using_public_helpers, 1), 0) > 0 then
    raise exception 'Policies still reference public RLS helper functions: %',
      policies_using_public_helpers;
  end if;

  with function_acl as (
    select
      p.oid,
      p.oid::regprocedure::text as function_signature,
      coalesce(p.proacl, acldefault('f', p.proowner)) as acl
    from pg_proc p
    join pg_namespace n on n.oid = p.pronamespace
    where n.nspname = 'public'
      and p.prosecdef
  )
  select array_agg(distinct function_signature order by function_signature)
  into public_security_definers
  from function_acl fa
  join lateral aclexplode(fa.acl) acl on true
  left join pg_roles grantee on grantee.oid = acl.grantee
  where acl.privilege_type = 'EXECUTE'
    and (
      acl.grantee = 0
      or grantee.rolname in ('anon', 'authenticated')
    );

  if coalesce(array_length(public_security_definers, 1), 0) > 0 then
    raise exception
      'SECURITY DEFINER functions executable by PUBLIC/anon/authenticated: %',
      public_security_definers;
  end if;

  select array_agg(p.oid::regprocedure::text order by p.oid::regprocedure::text)
  into service_role_missing_execute
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
  where n.nspname in ('public', 'app_private')
    and p.prosecdef
    and not has_function_privilege('service_role', p.oid, 'EXECUTE');

  if coalesce(array_length(service_role_missing_execute, 1), 0) > 0 then
    raise exception
      'service_role cannot execute required SECURITY DEFINER functions: %',
      service_role_missing_execute;
  end if;
end $$;

rollback;
