# Before the demo goes public

The dev compose files are for one machine: every port is published on `127.0.0.1` only, with `admin/admin`
everywhere. Production uses `docker-compose/prod/compose.prod.yml` on top of them. This covers the 2026-11-16 review's
C1, C2, H4 and M13.

## 1. Secrets and ports

1. Copy `docker-compose/prod/.env.prod.example` to `docker-compose/prod/.env.prod`. That file is git-ignored.
2. Fill in every value. Compose refuses to start if one is missing.
3. Start the stack with the override:

   ```bash
   cd docker-compose
   docker compose $(for f in docker-compose.*.yml; do printf -- '-f %s ' "$f"; done) -f prod/compose.prod.yml \
     --env-file .env --env-file prod/.env.prod up -d
   ```

What the override does:

- **No host ports.** Docker writes its own iptables rules, which skip ufw, so the only safe published port is none.
  cloudflared joins the `fyp-grading` network and reaches `api-gateway:9191` and `keycloak-server:8080` by name.
- **Observability is opt-in.** Grafana, Loki, MinIO, Alloy and Prometheus start only with
  `--profile observability`. When they do, Grafana has anonymous access off and an admin password.
- **No RabbitMQ management UI** in production.

## 2. Cloudflare Tunnel

- Route the public hostname of the app to the frontend, and `/api/**` to `api-gateway:9191`.
- For Keycloak, route **only** `^/realms/assay/` and `^/resources/` to `keycloak-server:8080`. Never route `/admin`
  or `/realms/master`.
- Set `TRUSTED_PROXIES` to cloudflared's address on the Docker network. The gateway then trusts its
  `CF-Connecting-IP` for rate limiting, and ignores the header from anyone else.
- Add a Cloudflare rate-limit rule on `/realms/assay/protocol/openid-connect/token`. Brute-force lockout is off in
  the realm (it would lock the shared personas for everyone), so the edge limits sign-in attempts instead.

## 3. Keycloak

1. **First boot** creates the master admin from `KEYCLOAK_ADMIN_USER` / `KEYCLOAK_ADMIN_PASSWORD`.
2. **Then:**
   - In the master realm, create a permanent admin with a strong password and 2FA.
   - Delete the bootstrap user.
3. **Every deploy that changes the realm, and nightly (cron):** run
   `ASSAY_SPA_ORIGIN=https://… scripts/keycloak-reset-personas.sh`. A realm import never updates an existing realm,
   so this script applies the realm settings to the running Keycloak. Its admin login defaults to `admin/admin`, so
   in production also set `KEYCLOAK_ADMIN_USER` / `KEYCLOAK_ADMIN_PASSWORD` to the permanent admin. It:
   - disables every required action, so visitors can't trigger a password change or 2FA setup on a shared persona
     through `kc_action`
   - turns brute-force lockout off
   - pins the client's redirect URIs to the app's origin
   - resets every persona to the public demo password, with no pending actions, no OTP and no other credentials
4. **Check:** `e2e/smoke.sh` signs in with `kc_action=UPDATE_PASSWORD` and fails if Keycloak shows the
   change-password form.

## 4. Memory

- Each Spring image starts with small-heap JVM flags (`JAVA_OPTS` in its Dockerfile: serial GC, 144 MB heap, capped
  metaspace, code cache and direct memory) and exits on an out-of-memory error.
- Compose caps each service's memory, measured with the full demo running:

  | Service | Limit |
  | --- | --- |
  | admin | 512m |
  | notification | 448m |
  | evaluation, gateway, rubric | 384m |
  | registry | 320m |
  | config | 256m |

- `restart: unless-stopped` brings a service back after an out-of-memory exit.
- The services use at most 40 Tomcat threads, and the Postgres services a pool of 5 connections.
- Check with `docker stats --no-stream`: a service that stays above about 90% of its limit needs more.
