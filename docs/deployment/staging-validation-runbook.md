# Staging Validation Runbook

Date: 2026-06-20

Use this runbook before promoting the IEMS ERP release candidate to production.
Staging must use a separate Supabase project, separate secrets, and a staging
domain. Do not connect staging validation to production Supabase.

## Required Environment

- Staging Supabase project with migrations applied.
- Staging Google OAuth client/redirect URL for the staging domain.
- Staging `SUPABASE_URL`, `SUPABASE_ANON_KEY` and `SUPABASE_SERVICE_ROLE_KEY`.
- Staging `SUPABASE_AUTH_ISSUER`, normally:
  `https://<staging-project>.supabase.co/auth/v1`.
- Staging `SUPABASE_JWKS_URL`, normally:
  `https://<staging-project>.supabase.co/auth/v1/.well-known/jwks.json`.
- `SUPABASE_AUTH_ISSUER_ALIASES` unset unless the staging auth issuer has a
  known second hostname that must be accepted.
- Distinct staging values for Google, JWT, Caddy domain and application secrets.
- Redis, worker, scheduler, API, web and Caddy running from production Compose.

Never paste rendered `docker compose config` output into chat, issues or PRs
because it expands local secret values.

## Deploy

```powershell
docker compose config
docker compose build --pull
docker compose up -d --force-recreate
docker compose ps
```

Expected result:

- `api`, `worker`, `scheduler`, `redis`, `web` and `caddy` are healthy or
  running as expected.
- Only Caddy exposes public ports.
- Redis is not publicly reachable.
- API is reachable only through Caddy.

## Health Checks

Replace `<staging-domain>` with the real staging host.

```powershell
curl.exe -sk https://<staging-domain>/api/health
curl.exe -sk -o NUL -w "%{http_code}" https://<staging-domain>/login
```

Expected results:

- `/api/health` returns:
  `{"status":"ok","service":"iems-erp-api","version":"0.1.0"}`.
- `/login` returns `200`.

## Browser Smoke Test

Use test accounts only.

- Sign in with Google.
- Sign out and confirm protected routes require a new session.
- Load `/projects`, project detail, folder tree and document list.
- Create or edit a test project if the test account has permission.
- Upload and download a small test document through FastAPI only.
- Add a document version and confirm the latest version displays.
- Request an archive export, wait for `READY`, download it, and inspect the ZIP
  folder structure.
- Open `/archive`, archive rooms, file detail and QR label views.
- Register a test physical file, print/preview the QR label, scan or paste the
  QR token, and confirm it resolves through the app.
- Load `/director` with a Director account.
- Load `/admin` with an admin-capable account.
- Load `/approvals`, `/tasks`, `/attendance`, `/leave` and `/calendar`.
- Verify notification list, unread count and read transition once OPEN-045 is
  fixed.

## Security Evidence

Record the command output location or screenshot reference for:

- Ruff, MyPy and backend pytest.
- Frontend type-check, lint, tests and production build from Claude.
- `npx supabase db reset` or equivalent staging migration proof.
- Phase 5 SQL security probe.
- Secret scan.
- Docker Scout critical/high image scan for every production image.
- Non-root container validation.
- Production exposure review: only Caddy public, no Docker socket, no privileged
  containers, no host networking.
- Managed Supabase database backup retention.
- Supabase Storage backup/export procedure.
- Rollback owner and incident contact.

## Exit Criteria

Staging passes only when:

- All required services are healthy.
- Browser auth works end-to-end.
- Core document, archive, physical-file, Director and admin flows are validated.
- Security evidence is recorded.
- Known non-blocking issues are listed in `docs/07_OPEN_ITEMS.md`.
- A human release owner signs off on promotion or explicitly blocks release.
