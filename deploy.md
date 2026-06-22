# IEMS ERP Home-Hosted Staging Deployment Todo

## Target Setup

```text
Vercel frontend
Cloudflare Tunnel API URL
home server backend stack
managed Supabase Free
```

## 1. Prepare the Home Server

- [ ] Move both RAM sticks to the i3-6100T machine if compatible.
- [ ] Install an SSD if available.
- [ ] Install Ubuntu Server 24.04 LTS or Debian 12.
- [ ] Connect with wired Ethernet.
- [ ] Enable SSH.

## 2. Install Server Tools

- [ ] Install Docker.
- [ ] Install Docker Compose plugin.
- [ ] Install Git.
- [ ] Install Cloudflare Tunnel / `cloudflared`.

## 3. Create Managed Supabase Project

- [ ] Create Supabase Free project.
- [ ] Enable Google OAuth.
- [ ] Apply migrations/seeds.
- [ ] Create private Storage buckets.
- [ ] Copy project URL, anon key, service-role key, and JWT settings.

## 4. Deploy Frontend To Vercel

- [ ] Import GitHub repo.
- [ ] Set root directory to `apps/web`.
- [ ] Add frontend env vars:

```text
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_URL=
```

- [ ] Deploy and copy Vercel URL.

## 5. Configure Backend On Home Server

- [ ] Clone repo.
- [ ] Create backend/server `.env` from `.env.server.example`.
- [ ] Set backend env vars:

```text
APP_ENV=staging
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_JWT_SECRET=
CORS_ALLOWED_ORIGINS=https://your-vercel-url.vercel.app
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

- [ ] Start API, Redis, worker, and scheduler with Docker Compose.

Backend-only Compose command for a server where Vercel hosts the frontend:

```bash
cp .env.server.example .env
# edit .env before starting
docker compose -f compose.yaml -f compose.backend.yaml up -d --build api worker scheduler redis
```

The backend API is published only on the server loopback interface:

```text
127.0.0.1:8000
```

Cloudflare Tunnel should point at `http://127.0.0.1:8000`. Redis remains private
inside Docker Compose and is not published to the network.

## 6. Expose API With Cloudflare Tunnel

- [ ] Create tunnel.
- [ ] Route public HTTPS tunnel URL to local backend API:

```text
http://127.0.0.1:8000
```

- [ ] Set Vercel env:

```text
NEXT_PUBLIC_API_URL=https://your-api-tunnel-url
```

- [ ] Add tunnel URL to backend allowed config if needed.

## 7. Configure Auth Redirects

- [ ] In Supabase Auth, set:

```text
Site URL=https://your-vercel-url.vercel.app
Redirect URL=https://your-vercel-url.vercel.app/auth/callback
```

- [ ] In Google Cloud OAuth:
  - [ ] Add the Supabase callback URL.
  - [ ] Add Vercel origin if needed.

## 8. Test

- [ ] `/health`
- [ ] Google sign-in
- [ ] `/projects`
- [ ] `/archive`
- [ ] `/director`
- [ ] Document upload/download
- [ ] Archive export
- [ ] Notifications
- [ ] Admin pages
- [ ] Confirm worker handles archive export jobs.

## 9. Basic Ops

- [ ] Set server auto-start for Docker services.
- [ ] Set Cloudflare Tunnel auto-start.
- [ ] Add disk-space monitoring.
- [ ] Configure Supabase DB and Storage backup process.
- [ ] Write down rollback steps.

## 10. Backup Design

Target backup chain:

```text
Supabase Storage
-> backend machine local backup
-> personal server offsite backup
-> Google Workspace Drive or another online cloud copy
```

Back up both:

```text
Supabase database
Supabase Storage buckets
```

Storage-only backups are not enough. The database contains document metadata,
project links, version records, checksums, permissions, audit events and physical
archive records.

Recommended local backup layout on the backend machine:

```text
/srv/iems/backups/
  db/
  storage/
    current/
      project-documents/
      generated-archives/
    snapshots/
  logs/
```

Recommended tools:

- [ ] `pg_dump` for managed Supabase database backups.
- [ ] `rclone` for Supabase Storage S3-compatible bucket sync.
- [ ] `restic` for encrypted snapshots, deduplication and retention.
- [ ] `rclone` for pushing encrypted backup repositories to Google Workspace Drive.

Recommended flow:

```text
Supabase Storage --rclone--> backend local mirror
Supabase DB --pg_dump--> backend local db dump
backend backup folder --restic encrypted backup--> personal server
personal server/restic repo --rclone--> Google Workspace Drive
```

Retention target for staging/testing:

```text
7 daily backups
4 weekly backups
3 monthly backups
```

Do not blindly mirror deletes into every backup layer. Keep a current mirror plus
dated snapshots so accidental Supabase deletions can still be recovered.

## 11. Backend Machine To Personal Server Connectivity

Preferred local-network setup:

```text
backend machine: always on
personal server: usually off or sleeping
Raspberry Pi: optional always-on wake relay if the personal server is on another LAN
```

If the backend machine and personal server are on the same LAN:

- [ ] Put both machines on wired Ethernet if possible.
- [ ] Prefer wired Ethernet for Wake-on-LAN. Wi-Fi Wake-on-LAN is unreliable on
  many consumer machines and should not be treated as a backup dependency.
- [ ] Give both machines DHCP reservations in the router.
- [ ] Enable SSH on the personal server.
- [ ] Create an SSH key on the backend machine.
- [ ] Add the backend machine public key to the personal server's
  `~/.ssh/authorized_keys`.
- [ ] Enable Wake-on-LAN in the personal server BIOS/UEFI and operating system.
- [ ] Record the personal server's MAC address.
- [ ] Have the backend machine send a Wake-on-LAN magic packet before offsite
  backup sync.

Example same-LAN flow:

```text
backend machine sends Wake-on-LAN packet
backend machine waits for SSH to respond
backend machine runs restic backup to personal server
personal server syncs encrypted backup repo to Google Workspace Drive
```

If the backend machine and personal server are on different networks:

- [ ] Keep a Raspberry Pi or another tiny device always on in the personal
  server's LAN.
- [ ] Connect the backend machine and Raspberry Pi with Tailscale or another
  private VPN.
- [ ] Let the backend machine SSH into the Raspberry Pi.
- [ ] Let the Raspberry Pi send the Wake-on-LAN packet locally to the personal
  server.
- [ ] After the personal server wakes, sync backups over Tailscale/SSH.

Do not expose SSH directly to the public internet unless there is a separate
hardening pass for firewall rules, key-only auth, fail2ban and monitoring.

Recommended security posture:

```text
same LAN: SSH over private LAN only
different networks: SSH over Tailscale/private VPN only
public internet: no direct SSH exposure
```

## 12. Before Real Production

- [ ] Enable Supabase backups.
- [ ] Decide malware scanning.
- [ ] Add rate limiting.
- [ ] Configure monitoring/alerts.
- [ ] Record incident owner and release approval.
