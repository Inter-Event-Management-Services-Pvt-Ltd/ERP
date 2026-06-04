---
name: iems-docker-deployment-check
description: Use when building, reviewing, or deploying IEMS ERP Docker images, Compose services, health checks, Caddy routing, Redis, Celery workers, or server rollout. Codex backend-only skill.
---

# IEMS Docker Deployment Check

Read:

- `docs/17_DOCKERIZATION.md`
- `docs/checklists/DOCKERIZATION.md`
- `docs/checklists/PHASE_5_HARDEN_DEPLOY.md`

Run:

```bash
docker compose config
docker compose -f compose.dev.yaml up --build
docker compose ps
```

Validate:

- API health check
- worker starts
- scheduler starts
- Redis remains private in production
- Caddy routes `/api/*`
- only ports 80 and 443 are public in production
- images run as non-root
- no privileged containers
- no Docker socket mounts
- no host networking
- no secrets baked into images
- restart behavior works

Update checklist and changelog.
