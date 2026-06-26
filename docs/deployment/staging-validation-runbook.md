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
- `REDIS_PASSWORD` set to a strong random value; API, worker and scheduler must
  use authenticated Redis/Celery URLs rendered by production Compose.
- `CORS_ALLOWED_ORIGINS` set to the exact Vercel/app origin.
- `IEMS_DOMAIN` set to the real public Caddy hostname before TLS starts.
- `SUPABASE_SERVICE_ROLE_KEY_FILE` and `SUPABASE_JWT_SECRET_FILE` preferred
  when the deployment host supports file-mounted secrets. Use raw env vars only
  when file-mounted secrets are not available.
- Distinct staging values for Google, JWT, Caddy domain and application secrets.
- Redis, worker, scheduler, API, web and Caddy running from production Compose.

Never paste rendered `docker compose config` output into chat, issues or PRs
because it expands local secret values.

## Current Temporary Staging Shape

The 2026-06-22 deployment used Vercel for the frontend and a Cloudflare Quick
Tunnel to reach the backend server. This is acceptable for early smoke testing,
but it is not production-like staging because the tunnel hostname is temporary
and cannot hold durable Cloudflare WAF/rate-limit policy.

Before marking staging production-like:

- Buy or attach a domain in Cloudflare.
- Use a named Cloudflare Tunnel for the backend.
- Route `api.<domain>` to the backend tunnel.
- Route `app.<domain>` or the selected app hostname to Vercel.
- Set Vercel `NEXT_PUBLIC_API_URL=https://api.<domain>`.
- Set backend `CORS_ALLOWED_ORIGINS` to the Vercel production URL and
  `https://app.<domain>`.
- Re-run this runbook against the stable hostnames.

Do not mark the Phase 5 staging exit criterion complete while the backend is
only reachable through a throwaway `trycloudflare.com` URL.

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
- Redis health check uses authentication and returns healthy.
- Caddy admin API is disabled.
- Production Compose has no `host.docker.internal:host-gateway` mappings.

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

FastAPI documentation must not be publicly exposed on hosted API domains:

```powershell
curl.exe -i https://<api-domain>/docs
curl.exe -i https://<api-domain>/redoc
curl.exe -i https://<api-domain>/openapi.json
```

Expected result:

- Each request returns `404` unless `ENABLE_API_DOCS=true` was intentionally set
  for a short debugging window.

For the current split Vercel plus backend-tunnel setup, also verify CORS before
browser testing:

```powershell
curl.exe -i -X OPTIONS https://<api-domain>/v1/me `
  -H "Origin: https://<vercel-app-domain>" `
  -H "Access-Control-Request-Method: GET" `
  -H "Access-Control-Request-Headers: authorization"
```

Expected result:

- HTTP 200.
- `Access-Control-Allow-Origin` exactly matches the Vercel origin.
- `Access-Control-Allow-Headers` includes `authorization`.

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
