\set ON_ERROR_STOP on

do $$
declare
  missing_updated_at_count integer;
  direct_execute_count integer;
  auth_link_config text[];
begin
  select count(*) into missing_updated_at_count
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
  join pg_attribute a on a.attrelid = c.oid
  left join pg_trigger t
    on t.tgrelid = c.oid
   and t.tgname = 'trg_' || c.relname || '_updated_at'
   and not t.tgisinternal
   and t.tgenabled = 'O'
  where c.relkind = 'r'
    and n.nspname = 'public'
    and a.attname = 'updated_at'
    and not a.attisdropped
    and t.oid is null;

  if missing_updated_at_count <> 0 then
    raise exception 'Missing enabled updated_at triggers: %', missing_updated_at_count;
  end if;

  if not exists (
    select 1
    from pg_trigger t
    join pg_class c on c.oid = t.tgrelid
    join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'auth'
      and c.relname = 'users'
      and t.tgname = 'trg_link_auth_user_to_employee'
      and t.tgenabled = 'O'
      and not t.tgisinternal
  ) then
    raise exception 'Auth user link trigger is missing or disabled';
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

  select count(*) into direct_execute_count
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and p.proname in (
      'link_auth_user_to_employee',
      'set_updated_at',
      'prevent_audit_event_mutation'
    )
    and (
      has_function_privilege('anon', p.oid, 'EXECUTE')
      or has_function_privilege('authenticated', p.oid, 'EXECUTE')
    );

  if direct_execute_count <> 0 then
    raise exception 'Custom trigger functions are directly executable by anon/authenticated';
  end if;

  select p.proconfig into auth_link_config
  from pg_proc p
  join pg_namespace n on n.oid = p.pronamespace
  where n.nspname = 'public'
    and p.proname = 'link_auth_user_to_employee';

  if auth_link_config is null or not ('search_path=public, pg_catalog' = any(auth_link_config)) then
    raise exception 'Auth link trigger function search_path is not hardened';
  end if;
end $$;
