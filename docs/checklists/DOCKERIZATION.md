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

- [ ] Next.js image builds.
- [ ] `output: "standalone"` configured in Next.js.
- [ ] Frontend container runs as non-root.
- [ ] Frontend uses runtime-safe public environment values only.
- [ ] No server secret appears in client bundle.
- [ ] Frontend works behind reverse proxy.
- [ ] Responsive UI works in containerized environment.

## Reverse Proxy

- [ ] Caddy serves frontend.
- [ ] `/api/*` routes reach FastAPI.
- [ ] TLS configured for production.
- [ ] Security headers reviewed.
- [x] Only ports 80 and 443 are public.

## Security Gate

- [x] No privileged containers.
- [x] No Docker socket mounts.
- [x] No host networking.
- [x] No committed `.env`.
- [x] Secrets not baked into images.
- [ ] Images run as non-root.
- [ ] Images scanned.
- [ ] Base-image versions reviewed.
- [x] Backend network is internal.
- [x] Redis not exposed publicly.
- [ ] Production Compose file reviewed by human.

## Validation

- [ ] Clean build succeeds.
- [x] `docker compose config` succeeds.
- [ ] Health checks pass.
- [ ] Login flow works.
- [ ] Document upload works.
- [x] ZIP worker works.
- [ ] Restart test passes.
- [ ] Logs remain available after restart.
