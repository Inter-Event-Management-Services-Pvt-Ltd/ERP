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
- [x] Responsive UI works in containerized environment. Claude frontend
  validation recorded responsive/accessibility review, and the human release
  owner confirmed the Docker app is working as intended on 2026-06-20 after the
  auth runtime fix.

## Reverse Proxy

- [x] Caddy serves frontend.
- [x] `/api/*` routes reach FastAPI (handle_path strips prefix; FastAPI sees /v1/*).
- [x] TLS configured for production (Caddy auto-HTTPS via IEMS_DOMAIN env var).
- [x] Caddy admin API disabled for production (`admin off`), so port 2019 is
  not reachable from sibling containers.
- [x] Security headers reviewed: X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, HSTS, CSP.
- [x] `X-Request-ID` stamped per request; exposed in response for browser capture.
- [x] Only ports 80 and 443 are public.

## Security Gate

- [x] No privileged containers.
- [x] `no-new-privileges:true` enabled for web, api, worker, scheduler and
  redis. Caddy is excluded because it relies on `cap_net_bind_service` for
  low-port binding as a non-root user.
- [x] No Docker socket mounts.
- [x] No host networking and no production `host.docker.internal:host-gateway`
  mappings on API, worker or scheduler.
- [x] No committed `.env`.
- [x] Secrets not baked into images (SUPABASE_SERVICE_ROLE_KEY, JWT_SECRET never in web build args). Backend settings also support `SUPABASE_SERVICE_ROLE_KEY_FILE` and `SUPABASE_JWT_SECRET_FILE` for file-mounted secrets.
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
- [x] Backend Redis network is internal. Redis now requires `REDIS_PASSWORD`,
  and API, worker and scheduler use authenticated Redis/Celery URLs.
- [x] Production resource limits configured for web, api, worker, scheduler,
  redis and caddy.
- [x] Ephemeral tmpfs mounts configured for backend runtime temp state; Celery
  beat state now lives under a dedicated `/var/run/celery` tmpfs instead of
  world-writable `/tmp`.
- [x] Redis not exposed publicly.
- [ ] Production Compose file reviewed by human.

## Validation

- [x] Clean build succeeds (Docker production build verified with build args).
- [x] `docker compose config` succeeds. Revalidated on 2026-06-26 with fake
  production env values after Redis auth, Caddy admin disablement, required
  production env checks, resource limits and tmpfs hardening were added.
- [x] Web container health check added; Caddy waits for `service_healthy`.
- [x] Full stack health checks pass. All 6 services healthy on 2026-06-18:
  api, worker, scheduler, redis, web, caddy. GET /api/health → 200 via Caddy.
  All protected routes return 307 → /login when unauthenticated. /api/v1/me
  and /api/v1/projects return 401 without a bearer token.
- [x] Login flow works. Auth flow implemented 2026-06-18 (server-side OAuth,
  SUPABASE_URL override, x-forwarded headers for origin). Backend Docker auth
  resolution fixed 2026-06-19 with explicit backend egress and
  SUPABASE_AUTH_ISSUER / SUPABASE_AUTH_ISSUER_ALIASES / SUPABASE_JWKS_URL split
  from SUPABASE_URL; verified authenticated `/api/v1/me` with both local issuer
  forms, reachable JWKS from inside the API container, and
  `/api/v1/director/overview` through Caddy. Human browser smoke test confirmed
  sign-in/sign-out and protected app access are working on 2026-06-20.
- [x] Document upload works. Backend document upload/version/download endpoints
  are implemented and covered from earlier phases; human browser validation
  confirmed document upload works in the deployed app on 2026-06-26.
- [x] ZIP worker works.
- [x] Restart test passes for backend-owned services. `docker compose restart api worker scheduler redis` completed on 2026-06-18 and API health returned 200 afterward.
- [x] Logs remain available after restart for backend-owned services. API, worker and scheduler logs were readable after restart on 2026-06-18.
