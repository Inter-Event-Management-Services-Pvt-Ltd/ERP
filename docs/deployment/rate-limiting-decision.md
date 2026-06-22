# Rate-Limiting Decision

Date: 2026-06-20

## Decision

For the MVP release candidate, rate limiting will be enforced at the production
edge before traffic reaches FastAPI:

- Caddy or the hosting provider/load balancer should enforce request limits for
  `/api/*`.
- Supabase Auth remains responsible for OAuth/session protection.
- FastAPI keeps stable authorization, validation and audit controls, but does
  not add an in-process rate limiter in Phase 5.

## Why

- The app currently runs as multiple containers behind Caddy.
- Edge limiting protects both Next.js and FastAPI from request floods.
- In-process FastAPI-only limiting would not cover static/frontend routes and
  would need shared state to behave correctly across multiple API replicas.
- Redis is currently reserved for Celery broker/result use; using it for
  request throttling should be scoped as a separate production hardening task.

## Required Production Policy

The release owner must configure concrete limits in staging before production.
Recommended starting point:

- General `/api/*`: 120 requests/minute per client IP.
- Auth/session routes: 30 requests/minute per client IP.
- Upload endpoints: 20 requests/minute per client IP.
- Archive export creation/cancel: 10 requests/minute per client IP.
- Admin/audit endpoints: 60 requests/minute per client IP.

Adjust after staging load and pilot feedback. Do not treat these numbers as
permanent production tuning.

## Verification

Before production promotion:

- Confirm the selected provider/Caddy configuration is active in staging.
- Send requests above the configured threshold and verify `429 Too Many Requests`.
- Confirm normal browser workflows still pass under expected use.
- Record the final provider/Caddy policy in deployment notes.

## Follow-Up

If the ERP is scaled beyond one API replica or exposed to higher traffic, add a
shared Redis-backed FastAPI limiter with route groups matching this document.
