# Hosting: where everything lives

[← summary](README.md)

| Piece | Where | Cost |
|---|---|---|
| Source code | GitHub, public repositories under `FirasKhalife` | free |
| CI | GitHub Actions, on GitHub's runners | free for public repositories |
| Images | GitHub Container Registry, `ghcr.io/firaskhalife/fyp-grading-*`, public packages | free for public packages |
| The server | One Netcup VPS 1000 G12.5 (4 vCPU, 8 GB RAM, 128 GB SSD), Debian 13, in a Netcup data centre in Europe | about €14/month on a monthly term (less on a 12- or 24-month one) |
| DNS, TLS, the tunnel | Cloudflare, free plan, zone `firaskhalife.dev` | free |
| The domain | `firaskhalife.dev`, registered at Name.com | the yearly renewal |
| The portfolio | `firaskhalife.dev` itself, on Vercel; it links to the demo | free tier |

## The server

Everything runs on one machine with Docker Compose: the seven Spring services, Keycloak, four Postgres databases,
MongoDB, RabbitMQ, Redis, the nginx edge and cloudflared (17 containers). Measured on the live server after the first
deploy: **3.6 GB of 8 GB used**, the largest container being Keycloak at about 520 MB. The compose file gives every
container a memory limit (5.3 GB in total), so one misbehaving service can't take the others down.

What the server is set up with (by Ansible, from `fyp-grading-iac/live`):

- **Users:** a `deploy` user that signs in by SSH key only, with sudo. Root can't sign in over SSH, and passwords
  are refused.
- **Firewall:** ufw lets in port 22 only, rate-limited; fail2ban bans addresses that keep failing.
- **Updates:** Debian security updates install themselves, with a reboot at 04:30 when one is needed. Docker is set
  to `live-restore`, so the containers keep running through a Docker restart.
- **The app:** a clone of this repository in `/opt/assay`, and its `docker-compose/prod/compose.yml` run as the
  project `assay`. Only the edge is published, on `127.0.0.1:8080`, which only cloudflared uses.
- **Two timers:** `assay-update` (new images, every 30 minutes) and `assay-keycloak-reset` (the personas, nightly).

There is no data to back up: each visitor works on a private copy of the demo data that is rebuilt from the seed,
and all copies are deleted at midnight. The server can be rebuilt from git in about 15 minutes. Its one irreplaceable
file is its own `.env` (the generated passwords), and even that can be recreated along with fresh databases.

## Cloudflare

The domain's DNS is on Cloudflare (moved from Vercel's DNS on 20 Nov 2026; the portfolio stays hosted on Vercel).
For the demo, Cloudflare provides:

- **The tunnel.** cloudflared on the server keeps an outbound connection to Cloudflare; requests for
  `assay.firaskhalife.dev` come back through it to the edge. The server's address is never in DNS, and nothing on
  the internet can open a connection to the app directly.
- **TLS** with a Cloudflare certificate, HTTPS only (HTTP redirects), TLS 1.2 minimum, and HSTS on the demo's
  hostname.
- **A rate limit** on Keycloak's token endpoint: 20 requests per 10 seconds per IP, then a 10-second block. The free
  plan allows one such rule, so the finer limits are in the API gateway (see [delivery.md](delivery.md#rate-limits)).
- **The managed WAF rules** of the free plan, and the Browser Integrity Check, which turns away some default client
  user agents. Scripts that call the live site send their own `User-Agent` for that reason.

All of this is code (OpenTofu, `fyp-grading-iac/live/tofu`), not dashboard clicks. The portfolio's own DNS records
are DNS-only: Vercel serves them with its own certificates.

## The images

Eleven public packages on GHCR, one per image: the seven services, the frontend (which is also the edge), and from
this repository the Keycloak image (realm, theme, hardening) and slimmed Postgres and MongoDB images. Each is tagged
`latest` and with the short commit SHA it was built from, so any release can be pinned. Third-party images
(RabbitMQ, Redis, cloudflared) come from Docker Hub, pinned by digest.

The packages are public, so pulling them needs no login: not on the server, not for anyone running
`./run-demo.sh` on their own machine.
