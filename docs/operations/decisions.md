# Decisions: why it is deployed this way

[← summary](README.md)

Each section is one decision: what was chosen, what else was considered, and the trade-off accepted. The goal behind
all of them: **an always-on demo a visitor can open with one click, at the cost of a small VPS, that one person can
run safely, with the code in public.** The hosting study behind the first two is
[PHASE1-REPORT.md](../project/PHASE1-REPORT.md).

## One VPS instead of a cloud platform

**Chosen:** one 8 GB VPS running the whole stack with Docker Compose.

**Considered:** AWS (one 8 GB instance is about €49+/month; the original nine small instances couldn't hold Keycloak
and would cost about €104); managed container platforms such as Fly.io, Railway or Cloud Run (the stack would become
about 13 separately billed apps, from about $18/month for the memory alone); scale-to-zero (2 to 4 minutes for the
first visitor to wait while the machine and 17 containers start); Oracle's free tier (12 GB, but instances can be
reclaimed when idle).

**Why:** the measured stack needs about 3.6 GB. A recruiter clicks once and should see the app at once, so cold
starts are out, and a one-person demo doesn't need several machines. The AWS version is still in
`fyp-grading-iac` (Terraform and CDK) as a reference design, never applied.

**Trade-off:** one machine is a single point of failure. For a demo, a rebuild from git in about 15 minutes is
acceptable recovery.

## Netcup

**Chosen:** Netcup VPS 1000 G12.5 (4 vCPU, 8 GB, 128 GB SSD), on a monthly term first.

**Considered:** Hetzner (the 8 GB CX plans were discontinued and the replacement costs about $36/month), OVH (no stock
in any region at the time), Oracle Free (above).

**Why:** the best price for 8 GB in Europe that was actually available, with IPv4 and IPv6 included. A one-month term
first, to prove the setup before a cheaper longer term.

**Trade-off:** Netcup has no API to order or reinstall servers, so those two steps are manual; everything after the
OS install is code.

## Docker Compose instead of Kubernetes

**Chosen:** the production `compose.yml` with health checks, memory limits, read-only root filesystems, dropped
capabilities and one internal network.

**Considered:** k3s or another small Kubernetes.

**Why:** on one machine, Kubernetes adds a control plane (memory), and a second set of manifests, without adding what
it is good at (several nodes, rescheduling). Compose gives what one host needs: dependencies with health conditions,
restarts, limits. The same file runs the live site, CI's end-to-end job and `./run-demo.sh` on any laptop, so what is
tested is what runs.

**Trade-off:** no rolling updates across replicas (next decision).

## One copy of each service, no zero-downtime switch

**Chosen:** an update recreates the one container whose image changed; it is unavailable for the few seconds it takes
to start.

**Considered:** two replicas behind the gateway, or blue-green switching at the edge.

**Why:** both double the memory of every service for an event that happens a few times a week and lasts seconds. The
AOT cache cut start-up to between 2 and 8 seconds per service, which made the gap small enough.

## Cloudflare Tunnel instead of open ports

**Chosen:** cloudflared on the server dials out to Cloudflare; the firewall lets in SSH only.

**Considered:** opening 80/443 with nginx and Let's Encrypt, with or without Cloudflare's proxy in front.

**Why:** with no inbound web port, the server can't be scanned or attacked directly, even by someone who learns its
address, and there are no certificates to renew. Cloudflare's free plan adds TLS, a rate limit and WAF rules at no
cost. It also needed the domain's DNS on Cloudflare, which was moved there; the portfolio stays on Vercel.

**Trade-off:** the demo depends on Cloudflare being up, and the free plan allows only one rate-limiting rule (spent on
the token endpoint; the finer limits are in the gateway).

## GitHub for code, CI and images

**Chosen:** public GitHub repositories, GitHub Actions, and GitHub Container Registry.

**Considered:** Jenkins (the project once had a `Jenkinsfile`), GitLab CI, Docker Hub.

**Why GitHub Actions:** free and unlimited for public repositories, and no CI server to host, patch and pay for.
Jenkins would have needed its own machine, or a share of the 8 GB the demo uses. Actions also gives each run a short-lived
identity (OIDC), which is what makes keyless signing possible.

**Why GHCR rather than Docker Hub:**
- **No secret to manage.** CI pushes with the workflow's own `GITHUB_TOKEN`. Docker Hub needs an account token
  stored as a secret in each of eleven repositories, to rotate and to protect.
- **No pull limits that matter.** Docker Hub rate-limits anonymous pulls; the server and anyone running
  `./run-demo.sh` pull public GHCR packages without logging in.
- **Next to the code.** Each package is linked to its repository: visibility and permissions follow it, and the
  image's SBOM, provenance and signature sit next to the commit that built it.
- **Free** for public packages, like the rest.

**Trade-off:** everything depends on one provider. The images are standard OCI images; moving registries means
changing the image names and the push step.

## Pull-based updates instead of deploying from CI

**Chosen:** a timer on the server pulls new images every 30 minutes.

**Considered:** a CI job that SSHes into the server and runs the update after each build (push-based).

**Why:**
- **GitHub never holds a key to the server.** A compromised workflow, action or GitHub account can publish a bad
  image, but it can't run commands on the server. A push-based deploy would put an SSH key with sudo in eleven
  repositories' secrets.
- **The server stays closed.** Port 22 doesn't have to accept GitHub's large and changing address ranges.
- **It fixes itself.** If the server was down or the registry briefly failed, the next run catches up; nothing to
  re-trigger.
- **It rolls back by itself.** A new image that doesn't become healthy is replaced by the previous one and skipped
  from then on.

**Trade-off:** a merged change takes up to 30 minutes longer to appear (`sudo assay-update` skips the wait), and only
images update automatically. The compose file, the server's setup and Cloudflare change only with a deliberate
command, because those can touch data or the way in.

## `latest` plus a timer, with SHA tags to pin

**Chosen:** the server follows `:latest`, which only `master` builds that passed every check can publish. Every image
is also tagged with its short commit SHA.

**Why:** "merged to master" is the release decision; nothing extra to bump. Pinning `assay_image_tag` to a SHA
freezes the whole stack on a known version when needed.

## Secure images, checked on every build

**Chosen:** minimal images (a `jlink` runtime on Alpine, no package manager, non-root), slimmed Postgres and MongoDB
images without `gosu` and unused tools, a Trivy gate on every build, SBOM and provenance on every push, cosign
keyless signatures, and every action and base image pinned.

**Considered:** distroless and Chainguard bases (no shell for the health checks, and Chainguard's free images only
publish `latest`), Bitnami database images (no longer updated for free).

**Why:** a public demo should not ship known, fixable vulnerabilities, and a reviewer can check how each image was
built. The measurements are in [deploy-hardening.md](../deploy-hardening.md#5-the-images): every service image went
to 0 HIGH or CRITICAL findings, 22 to 45% smaller, and starts in about half the time.

## OpenTofu for Cloudflare, Ansible for the server

**Chosen:** OpenTofu with the Cloudflare provider; Ansible for everything on the server.

**Considered:** Terraform; cloud-init; clicking in the dashboards.

**Why OpenTofu:** the same language as Terraform under an open-source licence, and it can **encrypt its state**,
which matters here because the state holds the tunnel's secret.

**Why Ansible:** Netcup has no API to provision a server, so the server is set up over SSH after the OS install. Ansible
is idempotent (run it again and only differences change), readable, and has no agent on the server.

**Why not the dashboards:** a setup that is code can be reviewed, repeated after a reinstall, and checked in CI.

## Local, encrypted OpenTofu state

**Chosen:** the state file stays on the operator's machine, encrypted with a passphrase.

**Considered:** a remote backend (S3, Terraform Cloud).

**Why:** one operator, one small state; a remote backend would add an account and credentials to manage. Encryption
means the file is safe even if copied.

**Trade-off:** the file and the passphrase must be kept. Losing them is recoverable: the two resources can be imported
again.

## Secrets generated where they are used

**Chosen:** the server generates its own database and service passwords on the first deploy; they never leave it.
GitHub holds no secret at all.

**Why:** a secret that never travels can't leak in transit, in a log, or from a CI variable. The repositories are
public, so the rule is simply that no secret is ever in one; the only public credential is the demo password, by
design.

## No backups of the data

**Chosen:** no database backups.

**Why:** the demo's data is disposable by design: each visitor gets a private copy rebuilt from the seed in git, and
every copy is deleted at midnight. What matters (code, configuration, realm, seed) is in git, and the images are in
GHCR. Only the server's `.env` is unique to it, and an encrypted copy can be taken with `./deploy.sh backup-env`.

## Nothing to administer from the internet

**Chosen:** the Keycloak admin console, RabbitMQ's UI, Eureka, the actuators and Grafana answer 404 from outside. Health
is watched by `verify.sh` and a GitHub Actions uptime check every 15 minutes.

**Why:** every admin page on the internet is something to protect, patch and log into. An operator who needs one can
reach it through SSH; a visitor never needs one.
