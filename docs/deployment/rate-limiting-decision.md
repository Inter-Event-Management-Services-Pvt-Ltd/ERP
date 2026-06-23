# Rate-Limiting Decision

Date: 2026-06-23

## Decision

The API enforces native fixed-window rate limiting in FastAPI, backed by Redis
and grouped by route sensitivity. Cloudflare or the production edge must remain
the outer protection layer for volumetric traffic before requests reach the
server.

- FastAPI enforces per-client limits for `/v1/*` API traffic.
- Redis is the production shared state store; the in-memory fallback is for
  local/test continuity only.
- Caddy, Cloudflare or the hosting provider/load balancer should also enforce
  request limits for the public API hostname.
- Supabase Auth remains responsible for OAuth/session protection.
- FastAPI keeps stable authorization, validation, audit controls and structured
  `429 RATE_LIMIT_EXCEEDED` responses.

## Why

- The app currently runs as multiple containers behind Caddy.
- Edge limiting protects both Next.js and FastAPI from request floods.
- Native API limiting protects the FastAPI process if edge policy is missing or
  misconfigured.
- Redis provides shared state if the API is scaled beyond one replica.
- The native limiter does not replace Cloudflare/WAF controls because it only
  runs after traffic reaches the backend host.

## Native API Policy

Default policy:

- General `/v1/*`: 120 requests/minute per client.
- Auth/current-user routes: 30 requests/minute per client.
- Upload endpoints: 20 requests/minute per client.
- Archive export creation/cancel: 10 requests/minute per client.
- Admin/audit/director endpoints: 60 requests/minute per client.

The client key is the bearer-token hash for authenticated requests, otherwise
the client IP. With `RATE_LIMIT_TRUST_PROXY_HEADERS=true`, the API uses
`CF-Connecting-IP` first, then the first `X-Forwarded-For` value.

Tune limits through:

```text
RATE_LIMIT_ENABLED=true
RATE_LIMIT_WINDOW_SECONDS=60
RATE_LIMIT_DEFAULT_REQUESTS=120
RATE_LIMIT_AUTH_REQUESTS=30
RATE_LIMIT_UPLOAD_REQUESTS=20
RATE_LIMIT_EXPORT_REQUESTS=10
RATE_LIMIT_ADMIN_REQUESTS=60
RATE_LIMIT_TRUST_PROXY_HEADERS=true
```

## Vercel And Cloudflare Tunnel Path

For the current deployment shape, keep Cloudflare rate limiting on the stable
API hostname as defense in depth:

- `api.<domain>/v1/me*` and auth-adjacent backend routes if added later:
  30 requests/minute per client IP.
- `api.<domain>/v1/folders/*/documents` and
  `api.<domain>/v1/documents/*/versions`: 20 requests/minute per client IP.
- `api.<domain>/v1/projects/*/exports` and `api.<domain>/v1/exports/*/cancel`:
  10 requests/minute per client IP.
- `api.<domain>/v1/admin`, `api.<domain>/v1/audit-events` and
  `api.<domain>/v1/director`: 60 requests/minute per client IP.
- All other `api.<domain>/v1/*`: 120 requests/minute per client IP.

Cloudflare Quick Tunnel hostnames under `trycloudflare.com` are temporary and
should not be used as the final rate-limit enforcement point.

## Verification

Before production promotion:

- Confirm Redis is reachable from API containers.
- Send requests above the native API threshold and verify
  `429 RATE_LIMIT_EXCEEDED`.
- Confirm rate-limit responses include `Retry-After`, `X-RateLimit-Limit`,
  `X-RateLimit-Remaining`, `X-RateLimit-Reset` and `X-RateLimit-Policy`.
- Confirm the selected Cloudflare/provider policy is active in staging.
- Confirm normal browser workflows still pass under expected use.
- Record the final native settings and provider policy in deployment notes.
