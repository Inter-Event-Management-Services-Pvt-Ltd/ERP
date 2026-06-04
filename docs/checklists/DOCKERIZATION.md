# Dockerization Checklist

## Repository

- [ ] `compose.yaml` exists.
- [ ] `compose.dev.yaml` exists.
- [ ] API Dockerfile exists.
- [ ] Web Dockerfile exists.
- [ ] `.dockerignore` files exist.
- [ ] Caddy configuration exists.
- [ ] `.env.example` documents required variables.

## Backend — Codex

- [ ] FastAPI image builds.
- [ ] API health endpoint exists.
- [ ] API container runs as non-root.
- [ ] Celery worker starts.
- [ ] Celery scheduler starts.
- [ ] Redis health check passes.
- [ ] Redis is private in production.
- [ ] API does not expose secrets in logs.
- [ ] Container logs are useful and structured.

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
- [ ] Only ports 80 and 443 are public.

## Security Gate

- [ ] No privileged containers.
- [ ] No Docker socket mounts.
- [ ] No host networking.
- [ ] No committed `.env`.
- [ ] Secrets not baked into images.
- [ ] Images run as non-root.
- [ ] Images scanned.
- [ ] Base-image versions reviewed.
- [ ] Backend network is internal.
- [ ] Redis not exposed publicly.
- [ ] Production Compose file reviewed by human.

## Validation

- [ ] Clean build succeeds.
- [ ] `docker compose config` succeeds.
- [ ] Health checks pass.
- [ ] Login flow works.
- [ ] Document upload works.
- [ ] ZIP worker works.
- [ ] Restart test passes.
- [ ] Logs remain available after restart.
