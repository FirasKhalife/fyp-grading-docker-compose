# Delivery: from a merged pull request to the live site

[← summary](README.md)

## CI: GitHub Actions in every repository

Each repository has one workflow, `.github/workflows/ci.yml`. It runs on every pull request and on every push to the
default branch (`master`; `main` for `fyp-grading-config`). Nothing is published from a pull request.

| Repository | On every pull request | Also on `master` |
|---|---|---|
| The seven Spring services | Spotless and Checkstyle, the build and every test (unit, slice, Testcontainers), the contract fixtures; the image build and scan | push, sign |
| `fyp-grading-frontend` | ESLint, Prettier, TypeScript, unit and component tests, the build; Playwright end to end with axe accessibility checks, keyboard paths and a 375 px layout; the image build and scan | push, sign |
| `fyp-grading-docker-compose` | ShellCheck, every compose file, the production compose's rules (a memory limit, health check and log rotation on every service, only the edge published, the total fits 8 GB), the realm export, the seed generator's checks; the Keycloak, Postgres and MongoDB image builds and scans; **the production stack end to end**: `./run-demo.sh`, then the smoke test, the API rule checks and the security checks against it | push, sign. Nightly: the production stack end to end from the latest published images. Weekly: the cross-repo check below |
| `fyp-grading-config` | Every file parses; guard rails: nothing that looks like a secret, no actuator endpoint exposed to all | |
| `fyp-grading-iac` | `tofu fmt` and `validate`, ansible-lint, playbook syntax, ShellCheck (and checks for the AWS reference code) | |

The weekly cross-repo job checks out every service and confirms that the code they share by copy (the `common/`
package, `checkstyle.xml`, the `Dockerfile`, the payload fixtures) is identical everywhere, and that each service's
committed seed is exactly what the generator produces.

**Dependabot** opens pull requests every Monday for Maven, npm, base images (digests), compose images and the
GitHub Actions themselves. They go through the same CI, so a dependency update is tested and scanned like any other
change.

## How an image is built

Every image job does the same, in order:

1. **Build** with BuildKit, cached between runs. The Spring services build in three stages: compile, then a
   `jlink` Java runtime with only the modules the service uses, then an Alpine runtime without its package manager,
   running as a non-root user. A training run at build time records an **AOT cache**, which roughly halves start-up
   (admin-service: 14.7 s → 8.2 s).
2. **Scan** with Trivy. The full report goes to GitHub code scanning; the job **fails on any HIGH or CRITICAL
   finding that has a fix**. Findings without a fix yet are listed in `.trivyignore`, each with a reason and an
   expiry date.
3. On `master` only: **push** to GHCR as `:latest` and `:<short sha>`, with an **SBOM** and **max-mode
   provenance**, then **sign** the pushed digest with **cosign keyless** (a certificate issued to that workflow run
   through GitHub's OIDC; no key is stored anywhere).

Every action is pinned by commit SHA and every base image by digest, so a tag moved upstream can't change a build.
Sizes, scan counts and start-up times before and after are in
[deploy-hardening.md](../deploy-hardening.md#5-the-images).

## How the server picks up a new version

GitHub can't reach the server, and doesn't need to. On the server, `assay-update.timer` starts
`/usr/local/lib/assay/update.sh` at :00 and :30 past every hour (with up to 3 minutes of random delay):

1. **Which services?** Only the app services, the ones whose image is `ghcr.io/firaskhalife/*:latest`: the seven
   services, the frontend/edge and Keycloak. It notes the image each one is running now.
2. **Pull** each of those images, one service at a time. An image that can't be pulled holds back only its own
   service.
3. **Compare.** A service whose freshly pulled image is the same as the running one is left alone. Usually that's
   all of them, and the run ends there ("up to date").
4. **Recreate only what changed**, with `docker compose up -d --wait --no-deps <those services>`. `--no-deps` means
   nothing else is restarted: not the databases, not the other services. `--wait` waits until each new container
   passes its health check (up to 15 minutes).
5. **If one doesn't become healthy, roll back:** tag the previous image back onto `:latest`, recreate the same
   services with it, and record the bad image's ID in `/var/lib/assay-update/failed-images` so the next run doesn't
   try it again. The unit then shows as failed, and the reason is in the journal.
6. If Keycloak was updated, re-run the persona and realm reset, because a realm import never changes an existing
   realm.

So **an update replaces one container, not the server**. While a service's new container starts (2 to 8 seconds
for a service, about 35 for Keycloak), requests to that service fail and the rest of the app keeps working. There is
one copy of each service, so there is no zero-downtime switch; for a demo, a few seconds once in a while is the
accepted price (see [decisions.md](decisions.md#one-copy-of-each-service-no-zero-downtime-switch)).

## What goes live how

| You merge a change to... | It goes live | How |
|---|---|---|
| A service, the gateway, the frontend, the config server or the registry | automatically, 10 to 40 minutes after the merge | CI publishes the image; the timer recreates that one container |
| This repository's Keycloak image (`docker-compose/config/keycloak/`: theme, realm) | automatically | Same; then the persona and realm reset runs |
| `fyp-grading-config` | when a service restarts | Services read their configuration when they start: restart the service, or it happens at its next update |
| This repository's `docker-compose/prod/` (compose file, edge config), the realm-reset script, or a digest bump of Postgres, MongoDB, RabbitMQ, Redis or cloudflared | **only when someone runs `./deploy.sh`** | Deliberately not automatic: these can touch data or the way in |
| `fyp-grading-iac/live/ansible` (the server setup) | **`./deploy.sh`** | |
| `fyp-grading-iac/live/tofu` (Cloudflare) | **`./tofu.sh apply`**, after reading the plan | |
| The demo seed | after the services that carry it are merged | Each service ships its part of the seed in its image |

`./deploy.sh` updates the server's clone of this repository, pulls every image, and recreates only the containers
whose image or settings changed. It is safe to run at any time. The [runbook](runbook.md) has the details.

## Checks after a deploy

`fyp-grading-iac/live/verify.sh` checks the live site from outside, through Cloudflare:

1. **edge:** the landing page, the HTTP → HTTPS redirect, HSTS, a persona token the API accepts, a token from another
   Keycloak client it rejects, and 404 for `/admin`, `/realms/master`, `/actuator` and `/eureka`;
2. **ports:** from the internet, only SSH answers on the server's address;
3. **smoke** (`e2e/smoke.sh`): sign-in, a demo copy, grading, the grade hand-off over RabbitMQ, notifications and the
   live stream, release, scoping, reset, the rate limit;
4. **API rules** (`e2e/api-checks.py`): copy isolation, the grade maths, late submissions, releases, the CSV export,
   sessions and rate limits;
5. **security** (`e2e/security.sh`, on the server): personas can't be changed or locked out, no datastore or console
   answers on the network;
6. **browser:** the frontend's Playwright suite against the live URL, every screen for every persona, light and
   dark, desktop and mobile.

First live run (21 Nov 2026): smoke 27/27, API checks 64/64, security 36/36, browser 82 passed (1 skipped: it needs
short-lived tokens).

Between deploys, `fyp-grading-iac/.github/workflows/uptime.yml` checks every 15 minutes that the landing page loads
and a persona can sign in, and GitHub emails when it fails.

## Rate limits

Three layers, from the outside in:

| Where | What | Limit |
|---|---|---|
| Cloudflare | Keycloak's token endpoint, per IP | 20 per 10 s, then blocked for 10 s |
| API gateway | Every API call, per visitor | bursts of 60, refilled at 20 per second; then `429` with `Retry-After` |
| API gateway | Creating a demo copy (the expensive call) | 1 per minute per visitor |

The gateway knows the visitor's address from the `CF-Connecting-IP` header, which Cloudflare sets. It believes that
header only from the edge's fixed address on the internal network, so nobody can fake it to dodge the limit or get
someone else limited.
