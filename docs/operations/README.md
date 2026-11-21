# Running Assay in production: the summary

Assay is live at **https://assay.firaskhalife.dev**. This folder explains how it gets there and stays there: where
each piece is hosted, what happens between a merged pull request and the live site, how to deploy and operate it,
and why it is built this way. This page is the short version and the glossary; the other pages go into detail.

| Page | For | What's in it |
|---|---|---|
| [hosting.md](hosting.md) | everyone | Where the code, the images, the server and the DNS live, and what each costs |
| [delivery.md](delivery.md) | developers | CI on every repository, how images are built and secured, and how the server picks up a new version |
| [runbook.md](runbook.md) | whoever deploys | The commands, where each secret lives, the first deploy, day-to-day tasks and troubleshooting |
| [decisions.md](decisions.md) | reviewers | Every choice above, the alternatives weighed, and why this one won |

Related: [../architecture.md](../architecture.md) (how the services fit together),
[../deploy-hardening.md](../deploy-hardening.md) (the production compose, memory limits, image measurements), and
[`fyp-grading-iac/live`](https://github.com/FirasKhalife/fyp-grading-iac/tree/master/live) (the deployment code
and its step-by-step guide).

## The picture

```
 developer ── pull request ──► GitHub repository ── CI: build, test, scan, sign ──► ghcr.io/firaskhalife/*:latest
                                    (merge to master)                                          │
                                                                                               │ pulled every 30 min
                                                                                               ▼
 visitor ── HTTPS ──► Cloudflare (TLS, rate limit, WAF) ══ tunnel ══► one VPS (Docker Compose, 17 containers)
                                                         (outbound from the server; no web port open)
```

- **One server** runs everything: an 8 GB Netcup VPS with Docker Compose. It is enough: the whole stack uses about
  3.6 GB, and every container has a memory limit.
- **Cloudflare** sits in front. The server dials out to Cloudflare through a tunnel, so it opens no web port: its
  firewall lets in SSH only, by key.
- **GitHub** holds the code (one public repository per service), runs CI (GitHub Actions) and stores the images
  (GitHub Container Registry).
- **Nothing pushes to the server.** It pulls new images itself, so GitHub never holds a key to it.

## What happens when a pull request is merged

1. The repository's CI runs again on `master`: lint, tests, the image build, a vulnerability scan that fails on any
   fixable HIGH or CRITICAL finding. If all of that passes, it pushes the image as `:latest` and as the commit's
   short SHA, with an SBOM and provenance, and signs it.
2. Within 30 minutes, a timer on the server (`assay-update`) pulls the app images, sees which ones changed, and
   recreates **only those containers**. Everything else keeps running; the databases are never touched.
3. If a new container doesn't become healthy, the timer puts the previous image back and remembers the bad one so it
   doesn't try it again.

So a typical change is live 10 to 40 minutes after the merge, with nothing to run. Changes to the deployment itself
(the compose file, the server setup, Cloudflare) are the exception: someone runs `./deploy.sh` or `./tofu.sh apply`
on purpose. [delivery.md](delivery.md) has the full table.

## The repositories

All on GitHub under [FirasKhalife](https://github.com/FirasKhalife), public, one per deployable piece:

| Repository | What | Image |
|---|---|---|
| `fyp-grading-admin-service`, `-evaluation-service`, `-notification-service`, `-rubric-service` | The four domain services (Spring Boot) | one each |
| `fyp-grading-api-gateway` | The API gateway: routing, token checks, rate limits | yes |
| `fyp-grading-config-server`, `-registry-server` | Spring Cloud Config and Eureka | one each |
| `fyp-grading-config` | The services' configuration, read by the config server | none (read from GitHub) |
| `fyp-grading-frontend` | The React app, served by nginx, which is also the edge | yes |
| `fyp-grading-docker-compose` (this one) | The compose files, Keycloak realm and theme, the seed, the end-to-end checks, these docs | Keycloak, Postgres, MongoDB |
| `fyp-grading-iac` | `live/`: the real deployment (Ansible, OpenTofu). The rest is an AWS reference that was never applied | none |

## Glossary

| Term | Meaning here |
|---|---|
| **Ansible** | Configures the server over SSH from a list of "make sure this is true" steps; safe to run again. In `fyp-grading-iac/live/ansible` |
| **AOT cache** | A file baked into each Java image at build time that lets the JVM skip loading classes at start: start-up roughly halves |
| **Bootstrap** | The one-time first step on a fresh server: create the `deploy` user, then never sign in as root again |
| **cloudflared** | Cloudflare's tunnel client, one container on the server; it opens the outbound connection visitors' requests come through |
| **Compose project `assay`** | The 17 containers, their network and volumes, described by `docker-compose/prod/compose.yml` |
| **cosign (keyless)** | Signs each image with a short-lived certificate tied to the GitHub workflow that built it; no signing key to keep |
| **Demo copy** | A visitor's private copy of the demo data, created on their first visit and purged every midnight (Paris time) |
| **Edge** | The nginx container that is the only way in: it serves the app and forwards `/api` and `/realms/assay` |
| **GHCR** | GitHub Container Registry, `ghcr.io`: where the images are published |
| **jlink** | Builds a Java runtime with only the modules a service uses, so images are smaller |
| **OpenTofu** | The open-source Terraform: describes the Cloudflare setup as code. In `fyp-grading-iac/live/tofu` |
| **Persona** | One of the shared demo accounts (Rania, Jane, ...); all use the public password `assay-demo` |
| **Provenance, SBOM** | Records attached to each image: how it was built, and every package inside it |
| **Pull-based update** | The server fetches new versions itself on a timer, instead of CI pushing to it |
| **Rollback** | Putting the previous image back when a new one fails its health check; automatic |
| **SCP** | Netcup's server control panel: power, reinstall, the emergency console |
| **State (OpenTofu)** | The file that maps the code to what exists at Cloudflare; kept on the operator's machine, encrypted |
| **Trivy** | The vulnerability scanner CI runs on every image |
| **Tunnel** | The Cloudflare Tunnel: Cloudflare reaches the server through a connection the server opened, so no port is open |
| **`assay-update` / `assay-keycloak-reset`** | The two timers on the server: image updates every 30 min, and the nightly persona reset at 00:05 |
