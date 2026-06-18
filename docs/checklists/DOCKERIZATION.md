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
- [ ] Images scanned (defer to pre-production gate).
- [ ] Base-image versions reviewed (node:24-alpine, caddy:2-alpine, redis:7-alpine — review before release).
- [x] Backend network is internal.
- [x] Redis not exposed publicly.
- [ ] Production Compose file reviewed by human.

## Validation

- [x] Clean build succeeds (Docker production build verified with build args).
- [x] `docker compose config` succeeds.
- [x] Web container health check added; Caddy waits for `service_healthy`.
- [ ] Full stack health checks pass (requires running stack).
- [ ] Login flow works.
- [ ] Document upload works.
- [x] ZIP worker works.
- [x] Restart test passes for backend-owned services. `docker compose restart api worker scheduler redis` completed on 2026-06-18 and API health returned 200 afterward.
- [x] Logs remain available after restart for backend-owned services. API, worker and scheduler logs were readable after restart on 2026-06-18.
