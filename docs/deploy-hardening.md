# Production: running the demo on one host

The dev compose files are for one machine: they build from the sibling repos, publish every port on `127.0.0.1`, and
use `admin/admin` everywhere. Production uses its own file, `docker-compose/prod/compose.yml`. It is sized for one
8 GB host (Netcup VPS 1000) behind a Cloudflare Tunnel, and it pulls the images CI publishes. This covers the
2026-11-16 review's C1, C2, H4 and M13.

## 1. Start it

```bash
cd docker-compose/prod
cp .env.example .env          # git-ignored; fill in every value, generating each secret on the host
docker compose pull
docker compose up -d --wait   # add --profile tunnel to run cloudflared in the stack too
```

- **Images.** Every Assay image is `ghcr.io/firaskhalife/fyp-grading-<name>`, published from each repo's default
  branch with the tags `latest` and the commit's short SHA. `ASSAY_TAG` in `.env` picks the tag for all of them; pin
  a SHA for a release you can roll back to. The Keycloak image (realm, theme, account console off) is built from
  this repo's `docker-compose/config/keycloak`. So are `fyp-grading-postgres` and `fyp-grading-mongo`
  (`config/postgres`, `config/mongo`): the official images minus `gosu` and unused tools, tagged with the upstream
  version (section 5).
- **Secrets.** All of them come from `.env` (see `.env.example`); compose refuses to start while one is empty. The
  demo personas' password, `assay-demo`, is public on purpose and isn't configured.
- **Config.** The config server clones the public `fyp-grading-config` repository (`git` profile), branch `main`.
- **Data.** Named volumes for the four Postgres databases (admin, notification, rubric, Keycloak), MongoDB and
  RabbitMQ. Redis only holds rate-limit buckets and keeps nothing.
- **Start-up order.** Every service has a health check, and each waits for what it needs to be healthy:
  databases and RabbitMQ, then Eureka, the config server, the four services, Keycloak, the gateway, the edge, and
  cloudflared. Keycloak counts as ready only once the `assay` realm answers: its own `/health/ready` is UP while the
  first start is still importing the realm, and sign-ins would get `503 Bootstrap in progress` for a few seconds more.
  A first start (empty volumes) took 71 s on a 12-core desktop; expect 2–3 minutes on 4 shared vCPUs. The JVMs get a
  120 s grace period, Keycloak 180 s.
- **Logs.** json-file, 10 MB × 3 per container.
- **Restarts.** `unless-stopped`, which also brings a JVM back after an out-of-memory exit (`ExitOnOutOfMemoryError`).
- **Locked down.** Every container runs as a non-root user, with a read-only root filesystem (writable paths are
  small `tmpfs` mounts or the named volumes), `cap_drop: [ALL]` and `no-new-privileges`. The databases start as their
  own users (`user:` in compose), so the root-to-user switch (`gosu`) isn't needed, and the derived database images
  don't have it.
- **Pinned.** Third-party images, and the derived database images, are pinned to an exact version and digest
  (`redis:8.4.8-alpine@sha256:…`, `fyp-grading-postgres:16.16-alpine3.24@sha256:…`); CI fails on one that isn't.
  Dependabot (`docker-compose` ecosystem) proposes updates weekly, and bumps the derived images' bases within their
  major version (a new major can't open the existing volumes without a migration). A derived image update is two
  steps: Dependabot bumps the `FROM` in `config/postgres` or `config/mongo`, `master` CI publishes the new version
  tag, and Dependabot then proposes its tag and digest for `prod/compose.yml`.

## 2. One way in: the edge

```
Cloudflare ── tunnel ── cloudflared ──► edge (nginx, 127.0.0.1:8080) ─┬─ /api/**                       ► api-gateway:9191
                                                                      ├─ /realms/assay/**, /resources/** ► keycloak-server:8080
                                                                      └─ everything else               ► the app (index.html)
```

- The edge is the frontend image with `prod/edge.nginx.conf` mounted over its nginx config. So the app, the API and
  Keycloak's sign-in pages share one origin (`PUBLIC_URL`): no CORS, and one public hostname in Cloudflare.
- **Only the edge publishes a port**, and only on `127.0.0.1` (`EDGE_PORT`, default 8080): for cloudflared installed
  on the host, and for checks over SSH. Docker's port rules bypass ufw, so nothing binds to a public interface. With
  `--profile tunnel`, cloudflared runs in the stack and reaches the edge as `edge:8080`; route the tunnel's public
  hostname to `http://edge:8080` (or `http://localhost:8080` for a cloudflared on the host).
- **Never routed:** Keycloak's admin console and admin API (`/admin`), every other realm (`/realms/master`), the
  management ports, Eureka, the config server and the services' actuators. The edge answers those paths with a plain
  404. There is no RabbitMQ management UI in the image.
- **Rate limiting.** The edge has a fixed address on the `assay` network (172.30.0.10). The gateway believes the
  `CF-Connecting-IP` header (set by Cloudflare) only from it, so every visitor gets their own bucket and nobody else can
  forge the header. Keycloak trusts `X-Forwarded-*` only from the same address.
- Add a Cloudflare rate-limit rule on `/realms/assay/protocol/openid-connect/token`. Brute-force lockout is off in
  the realm (it would lock the shared personas for everyone), so the edge limits sign-in attempts instead.

## 3. Keycloak

1. **First boot** creates the master admin from `KEYCLOAK_ADMIN_USER` / `KEYCLOAK_ADMIN_PASSWORD`.
2. **Then:**
   - In the master realm, create a permanent admin with a strong password and 2FA.
   - Delete the bootstrap user.

   The admin console isn't published. Administer through `docker exec` and `kcadm.sh`, as the script below does.
3. **Every deploy that changes the realm, and nightly (cron):** run
   `scripts/keycloak-reset-personas.sh` (it finds the running `keycloak-server` container, e.g.
   `assay-keycloak-server-1`; or pass its name). A realm import never updates an existing realm, so this script
   applies the realm settings to the running Keycloak. Its admin login defaults to the container's bootstrap admin,
   so once that is replaced (step 2) set `KEYCLOAK_ADMIN_USER` / `KEYCLOAK_ADMIN_PASSWORD` to the permanent admin.
   The SPA origin defaults to the container's `ASSAY_SPA_ORIGIN` (the `PUBLIC_URL`). kcadm.sh keeps its session in
   `/tmp` (the container's root is read-only). CI runs it against the production stack on every pull request. It:
   - disables every required action, so visitors can't trigger a password change or 2FA setup on a shared persona
     through `kc_action`
   - turns brute-force lockout off
   - pins the client's redirect URIs to the app's origin
   - resets every persona to the public demo password, with no pending actions, no OTP and no other credentials
4. **Check:** `e2e/smoke.sh` signs in with `kc_action=UPDATE_PASSWORD` and fails if Keycloak shows the
   change-password form. Against the production stack, every URL is the edge:

   ```bash
   APP_ORIGIN=http://localhost:8080 e2e/smoke.sh http://localhost:8080 http://localhost:8080
   ```

## 4. Memory

Every container has a limit. They add up to **5.3 GiB of the 8 GB**, which leaves about 2.5 GB for the OS, Docker,
the page cache and a short-lived `docker exec`. CI checks that each service has a limit, a health check, log
rotation, a read-only root, no capabilities and no published port but the edge's, and that the limits stay under
6 GiB.

- **JVMs** size their heap from the limit instead of a fixed `-Xmx`: `-XX:MaxRAMPercentage=40` (Keycloak 45), with
  serial GC, C1 only, and capped metaspace, code cache, direct memory and thread stacks (`JDK_JAVA_OPTIONS`). The
  other 55–60% of the limit is for exactly those, which a Spring Boot 4 service on Java 25 needs about 150–200 MB of.
  The GC and compiler flags must stay as they are: the images' AOT cache was trained with them.
- **MongoDB** caps the WiredTiger cache at 0.25 GB (it would otherwise size it from the host's RAM). **Postgres** runs
  with 32 MB of shared buffers and 40 connections. **Redis** is capped at 48 MB.

Measured on 2026-11-18 (WSL2 on a 12-core desktop): a fresh start, the smoke test and the real-stack Playwright suite
(76 tests), `docker stats` every ~5 s. No container was OOM-killed or restarted.

| Container | Limit | Peak | Peak / limit |
| --- | ---: | ---: | ---: |
| keycloak-server | 768 MiB | 587 MiB | 76% |
| admin-service | 512 MiB | 350 MiB | 68% |
| notification-service | 512 MiB | 327 MiB | 64% |
| rubric-service | 448 MiB | 285 MiB | 64% |
| api-gateway | 448 MiB | 270 MiB | 60% |
| mongodb | 512 MiB | 262 MiB | 51% |
| evaluation-service | 448 MiB | 260 MiB | 58% |
| registry-server | 320 MiB | 198 MiB | 62% |
| rabbitmq | 256 MiB | 190 MiB | 74% |
| config-server | 320 MiB | 185 MiB | 58% |
| admin-db, notification-db, rubric-db | 160 MiB each | 39–57 MiB | ≤ 35% |
| keycloak-db | 192 MiB | 49 MiB | 26% |
| redis | 64 MiB | 12 MiB | 19% |
| edge | 64 MiB | 3 MiB | 5% |
| cloudflared (`tunnel` profile, not run locally) | 128 MiB | – | – |
| **Total** | **5.3 GiB** | **3.0 GiB** (sum of peaks) | |

Re-measured on 2026-11-20 with the derived Postgres and MongoDB images (a fresh start, the smoke test, the API checks
and the security checks, 30 samples): mongodb 250 MiB, the Postgres databases 35–46 MiB, Keycloak 603 MiB (79%),
everything else at or below the table; 3.0 GiB in all. The derived images run the same binaries, so this is the expected result. CI's
end-to-end job writes the usage after its checks to the run summary.

Check on the host with `docker stats --no-stream`: a container that stays above about 90% of its limit needs more.

## 5. The images

| Image | Base | What's in it |
| --- | --- | --- |
| the 7 Spring services | `alpine:3.24` with a `jlink` Java 25 runtime | only the JDK modules the service uses (from `jdeps`), the layered app, and an **AOT cache** (`app.aot`) made by a training run at build time. Non-root (uid 10001); `apk` removed; busybox stays for the `wget` health check |
| frontend / edge | `nginxinc/nginx-unprivileged` (Alpine) | the built app with pre-compressed assets; nginx as uid 101 on port 8080; `apk` removed |
| Keycloak | `quay.io/keycloak/keycloak` | the Assay realm, theme and the account console off (unchanged; Red Hat UBI 9 micro) |
| fyp-grading-postgres | `postgres:16.16-alpine3.24` | the official image without `gosu`/`su-exec`; runs as `postgres` (uid 70) |
| fyp-grading-mongo | `mongo:7.0.48` | the official image without `gosu`, `/opt/js-yaml` and the database tools (`mongodump`, `bsondump`, ...); runs as `mongodb` (uid 999). `mongosh` stays for the first-start user creation and the health check |

- **Why jlink on Alpine.** Compared on admin-service: Temurin JRE on Ubuntu 475 MB, Temurin JRE on Alpine 352 MB,
  jlink on Alpine 215 MB, jlink on distroless 236 MB, Chainguard JRE 385 MB. All five had the same findings (they were
  all in the app's own libraries) and started in 10–12 s. jlink on Alpine was the smallest, and it keeps a `wget` for
  Docker health checks. Distroless and Chainguard have no shell or HTTP client for one (Chainguard's free tier also
  only publishes `latest`).
- **AOT cache (JEP 483/514/515).** The build runs the service until its Spring context is refreshed (no database,
  broker, registry or config server needed) and records the classes it loaded and linked. At start, the JVM maps them
  from `app.aot`. Start-up roughly halves (below); the images grow by the cache (77–153 MB) but stay smaller than
  before. The cache only works with the JVM it was made by and the same GC and compiler flags, which the Dockerfile
  pins.
- **CI** (every repo's `image` job): build, scan with Trivy (the full report goes to GitHub code scanning), fail on any
  HIGH or CRITICAL finding that has a fix, then, from the default branch only, push with an SBOM and max-mode
  provenance and sign with cosign (keyless, GitHub OIDC). Findings that can't be fixed yet are listed in each repo's
  `.trivyignore` with a reason and an expiry date. Actions are pinned by commit SHA, base images by digest, and
  Dependabot proposes updates for both, Maven and npm weekly.

Before and after, measured the same way as the memory table (start-up = Spring's "process running for"; Keycloak's
"started in"):

| Image | Size before → after | HIGH + CRITICAL before → after | Start-up before → after |
| --- | ---: | ---: | ---: |
| admin-service | 475 → 368 MB | 6 → 0 | 14.7 → 8.2 s |
| evaluation-service | 443 → 291 MB | 6 → 0 | 9.2 → 4.9 s |
| notification-service | 475 → 364 MB | 6 → 0 | 15.3 → 7.6 s |
| rubric-service | 447 → 323 MB | 2 → 0 | 13.3 → 6.2 s |
| api-gateway | 434 → 273 MB | 2 → 0 | 8.0 → 3.8 s |
| config-server | 407 → 224 MB | 2 → 0 | 4.7 → 2.2 s |
| registry-server | 412 → 239 MB | 3 → 0 | 6.5 → 2.5 s |
| frontend | 64 → 67 MB | 3 → 0 | – |
| keycloak | 664 → 664 MB | 6 → 6 (1 fixable, upstream only; in `.trivyignore`) | 35.8 → 35.6 s |

The service findings were all in Java libraries Spring Boot 4.0.9 manages (`httpcore5`/`httpclient5`, RabbitMQ's
`amqp-client`, Eureka's `guava`). Each service's `pom.xml` pins the fixed versions until Spring Boot ships them.

Third-party images (Trivy 0.76.2, database of 2026-11-20). The derived database images are gated in CI like the
Keycloak image; the others are scanned by hand:

| Image | HIGH + CRITICAL | Where | Notes |
| --- | ---: | --- | --- |
| postgres 16.16-alpine3.24 (official) | 27 | all in `gosu`, built with an old Go | the same in 18.7: every tag ships the same `gosu` |
| **fyp-grading-postgres 16.16-alpine3.24** | **0** | | used in production |
| mongo 7.0.48 (official) | 46 | `gosu` 27, the database tools 16 (Go runtime, `x/net`), the entrypoint's `/opt/js-yaml` 3 | the same in 8.0.38 and 9.0.8 |
| **fyp-grading-mongo 7.0.48** | **0** | | used in production |
| rabbitmq 4.2.9-alpine | 0 | | |
| redis 8.4.8-alpine | 0 | | |
| cloudflared 2026.11.1 | 1 (`x/net`) | the binary itself | the latest release; fixed by the next one (Dependabot). Only in the `tunnel` profile |

Options weighed for the databases: newer upstream tags (no change: the findings are in `gosu` and the tools, not the
database), Bitnami (its free images stopped updating in 2025) and Chainguard (free only as `latest`, so the major
version can change under the data volume). A derived image is one `RUN rm` on top of the official image: Dependabot
bumps its `FROM`, and CI rebuilds, scans and signs it.
