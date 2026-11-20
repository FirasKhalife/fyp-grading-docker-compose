# Phase 1: hosting feasibility (2026-11-14)

**Verdict: feasible at about €9/month.** A slimmed demo profile keeps every microservice and uses **2.5 GB RAM**, measured. It fits an 8 GB VPS with plenty of headroom, and a 4 GB VPS at a squeeze.

## 1. Measured resource use

**Setup:**
- Docker 29.9 in WSL2 (12 cores, 11.7 GB).
- `docker stats` sampled every 4 s: 20 samples idle (after settling), then 30 samples under load.
- Load was 4 simulated visitors. Each made about 1 API GET/s through the gateway, fetched the frontend, and did a Keycloak login every ~20 s.
- Every request returned HTTP 200.
- Raw data and scripts are in `phase1-measurement/`.

| Profile | Containers | Idle RAM | Light-load RAM (avg / max) | CPU avg (1.0 = 1 core) | Cold boot to all healthy |
|---|---|---|---|---|---|
| **As-is** (all compose files, 700 MB caps, default JVM) | 24 | **4.56 GB** | 4.63 / 4.70 GB | 0.38 idle, 0.48 load | 3–5 min |
| **Slim demo** | 13 | **2.46 GB** | 2.53 / 2.56 GB | 0.34 idle, 0.34 load | **99 s** |

Your 5–8 GB estimate was high. The JVMs use 270–460 MB each, well under their 700 MB caps. The "Prometheus + Grafana" part of the stack is actually a full Loki "simple scalable" deployment: Loki read, write and backend, MinIO, Alloy, an nginx gateway, Grafana and Prometheus. Those 8 containers alone use **0.93 GB**.

CPU is not a constraint. Almost all the CPU spikes come from the RabbitMQ healthcheck: `rabbitmq-diagnostics` starts a new Erlang VM every 10 s. A TCP check fixes it. Boot is the only CPU-heavy moment. Expect it to take 2–4× longer on 2–4 shared vCPUs than on this desktop.

### As-is breakdown (idle, MiB)
| Container | MiB |
|---|---|
| Keycloak | 626 |
| admin-service | 456 |
| notification-service | 427 |
| grafana | 410 |
| rubric-service | 398 |
| evaluation-service | 350 |
| api-gateway | 335 |
| config-server | 307 |
| registry-server | 267 |
| alloy | 252 |
| mongodb | 138 |
| rabbitmq | 120 |
| minio | 75 |
| loki-write | 74 |
| loki-read | 47 |
| loki-backend | 37 |
| Postgres (4 instances, 46–50 each) | 194 |
| prometheus | 27 |
| redis | 8 |
| grafana-nginx | 8 |
| frontend (nginx) | 3 |

## 2. Slim profile: each cut and what it costs the story

| Cut | Saves (measured) | Cost to the architecture story |
|---|---|---|
| JVM flags on all 7 Spring apps: `-XX:+UseSerialGC -XX:TieredStopAtLevel=1 -Xss256k -XX:ReservedCodeCacheSize=48m -XX:MaxMetaspaceSize=128m -Xmx160m`, with a 320 MB container cap | **−0.99 GB** (2.54 → 1.55 GB) | **None.** Only peak throughput is lower, which doesn't matter for a demo. |
| Leave out the observability stack (Loki ×3, MinIO, Alloy, Grafana, nginx, Prometheus) | **−0.93 GB** | **Medium.** Monitoring is a good talking point. To keep it cheaply, run Prometheus + Grafana + **single-binary Loki** (estimated ~0.5 GB, not measured) as an optional profile, and show it read-only or as screenshots. Grafana currently has anonymous **Admin** access, so it must never be public. |
| Keycloak: `KC_CACHE=local`, heap capped at 320 MB | −0.12 GB | **None.** |
| One Postgres holding 4 databases (admin, notification, rubric, keycloak), `shared_buffers=32MB` | −0.10 GB | **Low.** Each service still owns its own database, which keeps the "database per service" boundary. You can add separate DB users per service so ownership stays visible. |
| MongoDB `--wiredTigerCacheSizeGB 0.25` | +0.04 GB here; this caps growth on a larger host | None. Polyglot persistence stays. |
| *(Not applied)* Drop config-server | ~−0.19 GB | **High.** Centralised config from git is a Spring Cloud showcase. **Keep it.** |
| *(Not applied)* Drop Eureka | ~−0.17 GB | **High.** Every gateway route is `lb://`. **Keep it.** |

The slim profile keeps all 7 Spring apps: gateway, Eureka, config server and the 4 domain services. It also keeps Keycloak, RabbitMQ, Redis, Postgres and Mongo, so the microservice story is intact.

**Sizing:**
- Slim: 2.6 GB containers + ~0.4 GB OS/Docker + Caddy or cloudflared ≈ **3 GB**.
- Slim + lean observability: ≈ 3.5 GB.
- As-is: ≈ 5.1 GB, so it needs 8 GB.

## 3. Hosting options (prices verified 2026-11-14, € excl. VAT, 1 € = 1.1052 $)

| Option | RAM | €/month | Runs | Caveats |
|---|---|---|---|---|
| **Hetzner CX33** (4 vCPU x86) | 8 GB | **8.99** (incl. IPv4) | Slim + observability, or as-is | **Hetzner's page shows every CX/CAX plan as "currently unavailable" today.** Check the console. Backups add 20% (€1.80). Stopped servers are billed in full. |
| Hetzner CX23 (2 vCPU) | 4 GB | 5.99 | Slim only, about 1 GB headroom, add swap | Same availability issue. |
| Hetzner CAX21 (4 vCPU ARM) | 8 GB | 10.99 | Slim + observability | Same availability issue. All images are multi-arch. |
| OVH VPS-2 (4 vCPU) | 8 GB | from 7.21 | Slim + observability | Commitment and setup-fee terms not verified. |
| Contabo Cloud VPS 4 | 8 GB | 4.40 (24-month term), ~6.60 monthly | Slim + observability | Oversold CPU is widely reported. Possible setup fee on monthly terms. |
| Netcup VPS 1000 G12.5 | 8 GB | 14.50 | Slim + observability | 12-month minimum. |
| Oracle Always Free A1 | **12 GB** (cut from 24 GB in mid-2026) | **0** | Anything | "Out of capacity" when provisioning. Instances count as idle when 7-day p95 CPU, network and memory are all under 20%. Slim uses about 21% of 12 GB, which is borderline; as-is uses about 38%. Free accounts can be terminated with little recourse. Not reliable enough for a portfolio link. |
| AWS t4g.large us-east-1 (+ IPv4 + 20 GB gp3) | 8 GB | ~49 (Frankfurt ~56) | Anything | 5–6× Hetzner. Free Tier is now credit-based ($100–200, 6 months). |
| AWS t4g.medium | 4 GB | ~27 | Slim only | |
| **Existing Terraform: 9× t2.micro** (+ 9 IPv4) | 9× 1 GB | **~104** | Doesn't work | Keycloak alone uses 0.5–0.65 GB. Retire this for the demo. |
| DigitalOcean 8 GB / Lightsail 8 GB | 8 GB | ~43 / ~40 | Anything | |
| **Scale-to-zero** (EC2 t4g.large stopped, woken by a small proxy or Lambda on visit) | 8 GB | ~6–8 | Anything | First visitor waits for VM start plus stack boot. That's 99 s measured on a fast desktop, **likely 2–4 min** on cloud vCPUs. That ruins the "recruiter clicks once" goal and saves at most ~€3 against a Hetzner box. Fly.io, Railway and Cloud Run would need the stack split into ~13 separate apps, and Fly.io alone is ≥ $18/month for 3 GB. **Not worth it.** |

**Extras (all €0):**
- **Domain:** a subdomain such as `demo.firaskhalife.dev`.
- **TLS:** Caddy auto-TLS, or a **Cloudflare Tunnel**. The tunnel needs no open ports, which keeps the Keycloak admin, RabbitMQ and Grafana consoles unreachable by default.
- **Backups:** the demo resets by design, so its state lives in git (seed scripts plus realm export) and images live in GHCR, which is free for public repos. Hetzner backups (€1.80) are optional.

## Recommendation

**Use Hetzner CX33 (8 GB): €8.99/month, about €10.70 if 19% VAT applies to you, everything else €0.** Run the slim profile and add lean observability (Prometheus + Grafana + single-binary Loki) as an internal-only extra. Put Cloudflare Tunnel in front.

The 8 GB box costs €3 more than the 4 GB one. It removes memory risk during the nightly reset and leaves room to show monitoring.

**Fallbacks:**
- If Hetzner still won't sell CX or CAX: **OVH VPS-2 8 GB (~€7.21)**.
- If the budget is strictly €0: Oracle A1, accepting that it may go down.

## Problems found while getting it to run (all phase-2 work, none changed in the repos)

1. **The frontend cannot log in.** It POSTs to `/api/auth/login` and `/signup`, but those endpoints were removed from admin-service when it moved to Keycloak (commit `41716c8`, `cloud-course`). The frontend also hardcodes `http://localhost:9191/api`. One-click demo login means adding Keycloak OIDC to the frontend, which the redesign can include.
2. **Actual roles in the code:** system roles `ADMIN` and `DEV`, and reviewer roles `JURY` and `ADVISOR` per team. **There is no student role.** The demo personas would be Admin, Jury member and Advisor.
3. **None of the 7 Spring Dockerfiles build.** Their base image `openjdk:17-jdk-slim` has been removed from Docker Hub. I measured with `eclipse-temurin:17-jre`.
4. **api-gateway `pom.xml` has no `spring-boot-maven-plugin`**, so it builds a jar that won't start ("no main manifest attribute").
5. **Eureka registration is broken in Docker.** `REGISTRY_SERVER_URL` points at `registry-service` (the container is `registry-server`). The YAML key `default-zone` isn't read; Eureka expects `defaultZone`. Also `RUBRIC_SERVICE_NAME=rubric_service`.
6. **`mongo:latest` has no `mongo` shell**, so the healthcheck never passes and evaluation-service never starts.
7. **Keycloak setup gaps:**
   - It has no healthcheck, but the gateway waits for it to be `service_healthy`, so compose refuses to start.
   - `KC_HOSTNAME=localhost` doesn't match the issuer the services expect.
   - There's no realm import, so it runs on the `master` realm with no `back_app` client.
   - Its `/health/ready` endpoint returns nothing.
8. **Grafana volume typo:** `datasource/yml` instead of `datasource.yml` crashes Grafana. Docker also creates a stray directory there, which I removed. `minio/minio` no longer exists on Docker Hub; I used `chainguard/minio`.
9. **The rate limiter blocks the public demo.** It allows about 1 request/s per client (`RedisRateLimiter(3,3,3)` with cost 3). It keys on `getRemoteAddress().getHostName()`, which does a blocking reverse-DNS lookup. Behind a tunnel or proxy, every visitor shares one IP and one bucket, so it must key on `CF-Connecting-IP` or `X-Forwarded-For` instead.
10. **`:latest` tags everywhere.** `postgres:latest` is now 18, which changes the data directory layout. Pin versions.
11. **Likely bug:** `AuthoritiesConverter` reads a `realm` claim, but Keycloak sends `realm_access`. Roles probably never map without a custom mapper. To be checked in phase 2.

## What's left on your machine
- **Stack:** stopped.
- **Images (~3.6 GB):** `*-service:1.0`, `registry-server:1.0`, `config-server:1.0`, `api-gateway:1.0`, `frontend:1.0`, `keycloak-server`.
- **Volumes:** `admin-db-data`, `notification-db-data`, `rubric-db-data`, `keycloak-db-data`, `mongodb-data`, `demo-pg-data`.
- **MinIO data:** `fyp-grading-docker-compose/docker-compose/.data/`, which is gitignored.
- **Not touched:** your `incrowdapi-mysql-1` container, Docker's `daemon.json`, and the processes using ports 6379 and 3100.
- **To reproduce:** see `phase1-measurement/`. Run `slim-up.sh`, then `measure.sh slim`, both in WSL.
