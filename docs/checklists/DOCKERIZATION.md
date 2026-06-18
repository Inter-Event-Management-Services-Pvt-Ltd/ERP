# Dockerization Checklist

## Repository

- [x] `compose.yaml` exists.
- [x] `compose.dev.yaml` exists.
- [x] API Dockerfile exists.
- [x] Web Dockerfile exists.
- [x] `.dockerignore` files exist.
- [x] Caddy configuration exists.
- [x] `.env.example` documents required variables.

## Backend — Codex

- [x] FastAPI image builds.
- [x] API health endpoint exists.
- [x] API container runs as non-root.
- [x] Celery worker starts.
- [x] Celery scheduler starts.
- [x] Redis health check passes.
- [x] Redis is private in production.
- [x] API does not expose secrets in logs.
- [x] Container logs are useful and structured.

## Frontend — Claude

- [x] Next.js image builds.
- [x] `output: "standalone"` configured in Next.js.
- [x] Frontend container runs as non-root (uid 10001 / appuser).
- [x] Frontend uses runtime-safe public environment values only.
- [x] No server secret appears in client bundle (bundle-scanned).
- [x] `NEXT_PUBLIC_*` vars passed as Docker build args so client bundle has correct values.
- [x] `HOSTNAME=0.0.0.0` set so standalone server.js listens on all container interfaces.
- [x] `public/` directory created in builder stage to prevent missing-dir COPY failure.
- [x] `.dockerignore` extended to exclude tests, Dockerfile, vitest config.
- [x] Frontend works behind reverse proxy.
- [ ] Responsive UI works in containerized environment (manual sign-off needed — deferred until Docker auth flow is fixed, see OPEN-040).

## Reverse Proxy

- [x] Caddy serves frontend.
- [x] `/api/*` routes reach FastAPI (handle_path strips prefix; FastAPI sees /v1/*).
- [x] TLS configured for production (Caddy auto-HTTPS via IEMS_DOMAIN env var).
- [x] Security headers reviewed: X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, HSTS, CSP.
- [x] `X-Request-ID` stamped per request; exposed in response for browser capture.
- [x] Only ports 80 and 443 are public.

## Security Gate

- [x] No privileged containers.
- [x] No Docker socket mounts.
- [x] No host networking.
- [x] No committed `.env`.
- [x] Secrets not baked into images (SUPABASE_SERVICE_ROLE_KEY, JWT_SECRET never in web build args).
- [x] Images run as non-root (web: uid 10001, api: confirmed by Codex).
- [x] Images scanned. Backend API/worker/scheduler images and Redis scanned
  clean for critical/high findings on 2026-06-18. Web image (node:24-alpine base)
  scanned clean: 0C 0H 0M 0L via Docker Scout on 2026-06-18 (300 packages indexed).
  Custom `iems-erp-caddy` image scanned clean: 0C 0H 0M 0L via Docker Scout on
  2026-06-18; OPEN-044 resolved.
- [x] Base-image versions reviewed. Backend moved from `python:3.12-slim` to
  `python:3.12-alpine` after Docker Scout found unfixed Debian `perl` CVEs.
  `redis:7-alpine` scanned clean. Caddy moved from the vulnerable official
  `caddy:2-alpine` runtime to a source-built Caddy v2.11.4 binary on
  `alpine:3.24`.
- [x] Backend network is internal.
- [x] Redis not exposed publicly.
- [ ] Production Compose file reviewed by human.

## Validation

- [x] Clean build succeeds (Docker production build verified with build args).
- [x] `docker compose config` succeeds.
- [x] Web container health check added; Caddy waits for `service_healthy`.
- [x] Full stack health checks pass. All 6 services healthy on 2026-06-18:
  api, worker, scheduler, redis, web, caddy. GET /api/health → 200 via Caddy.
  All protected routes return 307 → /login when unauthenticated. /api/v1/me
  and /api/v1/projects return 401 without a bearer token.
- [ ] Login flow works. Auth flow implemented 2026-06-18 (server-side OAuth,
  SUPABASE_URL override, x-forwarded headers for origin). Requires manual
  end-to-end verification: set SUPABASE_URL=http://host.docker.internal:54321
  in .env, rebuild web container, navigate to /login and complete Google OAuth.
- [ ] Document upload works. Pending login flow sign-off.
- [x] ZIP worker works.
- [x] Restart test passes for backend-owned services. `docker compose restart api worker scheduler redis` completed on 2026-06-18 and API health returned 200 afterward.
- [x] Logs remain available after restart for backend-owned services. API, worker and scheduler logs were readable after restart on 2026-06-18.
