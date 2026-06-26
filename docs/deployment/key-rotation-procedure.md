# Key Rotation Procedure

Date: 2026-06-20

Use this procedure for staging and production secret rotation. Never rotate
production secrets from a local development shell unless the release owner has
explicitly approved the maintenance window.

## Secrets Covered

- Supabase service-role key.
- Supabase anon/publishable key.
- Supabase JWT/Auth signing configuration and JWKS issuer settings.
- Google OAuth client secret.
- Redis password / broker credentials.
- Caddy/domain TLS provider credentials if configured externally.

## Rotation Order

1. Create or retrieve the replacement secret in the managed provider.
2. Store it in the deployment secret manager or host environment.
3. Update staging first.
4. Restart affected services.
5. Run smoke tests.
6. Update production during an approved maintenance window.
7. Restart affected services.
8. Verify health, auth, uploads, downloads and background jobs.
9. Revoke the old secret after the new deployment is verified.
10. Record the rotation date, operator and verification evidence.

## Service Restart Map

| Secret | Services to restart |
|---|---|
| Supabase service-role key | `api`, `worker`, `scheduler` |
| Supabase Auth issuer/JWKS config | `api` |
| Supabase anon/publishable key | `web` and any frontend build/runtime using it |
| Google OAuth client secret | Supabase Auth provider config; no app container restart unless env changed |
| Redis credentials | `redis`, `api`, `worker`, `scheduler` |
| Caddy/domain credentials | `caddy` |

## Verification

Run after rotation:

```powershell
docker compose ps
curl.exe -sk https://<domain>/api/health
curl.exe -sk -o NUL -w "%{http_code}" https://<domain>/login
```

Then verify in browser:

- Google sign-in and sign-out.
- `/v1/me` through the app session.
- Project list load.
- Document upload and signed download.
- Archive export worker can produce a test ZIP.
- Notifications load and mark-read works.

## Rollback

If rotation breaks runtime behavior:

1. Restore the previous known-good secret in the secret manager or host env.
2. Restart the affected services from the restart map.
3. Verify health and auth.
4. Keep the new secret disabled until the failure is understood.

Do not revoke the old secret until post-rotation verification has passed.
