# Commands Reference

## Local Supabase

```bash
supabase start
supabase db reset
supabase status
```

## Validation

```bash
bash scripts/validate-handoff.sh
```

## Phase 0 Database Validation

After `supabase start` and `supabase db reset`, run the Phase 0 SQL probes:

```bash
docker cp supabase/tests/phase0_foundation_validation.sql supabase_db_iems-erp:/tmp/phase0_foundation_validation.sql
docker exec supabase_db_iems-erp psql -U postgres -d postgres -v ON_ERROR_STOP=1 -f /tmp/phase0_foundation_validation.sql
```

## Future Backend

```bash
cd apps/api
uv sync
uv run --group dev pytest
uv run --group dev ruff check .
uv run --group dev mypy app
```

## Future Frontend

```bash
cd apps/web
npm install
npm run lint
npm run typecheck
npm run test
npm run build
```
