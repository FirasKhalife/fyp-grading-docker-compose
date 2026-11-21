# Runbook: deploying and operating Assay

[← summary](README.md)

The full step-by-step guide, from an empty account to a running server, is
[`fyp-grading-iac/live/README.md`](https://github.com/FirasKhalife/fyp-grading-iac/blob/master/live/README.md). This
page is the operator's view: what you need, where things are, and the commands you will actually use.

## What you need

| | |
|---|---|
| A Linux shell | WSL Ubuntu on Windows works; macOS or Linux too. Everything runs from `fyp-grading-iac/live` |
| The tools | `./tools.sh` installs pinned, checksum-verified copies into `~/.local/bin`, without sudo: OpenTofu 1.13, ansible-core 2.22 and its collections, ansible-lint, ShellCheck |
| For the browser checks | Node 20+ and the frontend's dependencies with Playwright's Chromium |
| Access | The SSH key and the Cloudflare credentials below. Nothing else: GitHub needs no secret for any of this |

## Where the secrets are

No secret is in any repository, in GitHub's settings, or in a CI variable. Each lives in exactly one place:

| Secret | Lives in | Made by | If it's lost |
|---|---|---|---|
| Cloudflare API token, account ID, OpenTofu state passphrase | the operator's machine: `~/.config/assay/cloudflare.env` (readable by the owner only) | the operator, once | Make a new token in the Cloudflare dashboard. The passphrase can't be recovered: keep a copy in a password manager |
| OpenTofu state (it contains the tunnel's secret) | `fyp-grading-iac/live/tofu/terraform.tfstate` on the operator's machine, git-ignored and **encrypted** with the passphrase | `./tofu.sh apply` | Import the tunnel and DNS record again, or delete them and apply ([troubleshooting](https://github.com/FirasKhalife/fyp-grading-iac/blob/master/live/README.md#troubleshooting)) |
| The server's address | `fyp-grading-iac/live/ansible/inventory.yml`, git-ignored | the operator | It's in Netcup's control panel |
| SSH key | the operator's machine: `~/.ssh/assay_netcup` | the operator | Add a new key through Netcup's console (or reinstall and run the deploy again) |
| Database, RabbitMQ, Redis and Keycloak-admin passwords | **only on the server**: `/opt/assay/fyp-grading-docker-compose/docker-compose/prod/.env` (root only) | the first `./deploy.sh`, randomly, on the server | `./deploy.sh` makes new ones along with fresh databases. `./deploy.sh backup-env` keeps an encrypted copy |
| The tunnel token | on the server, in that same `.env` | read from the state by `./deploy.sh`, without printing it | `./deploy.sh` writes it again |
| Root's password | the owner's password manager | Netcup | For Netcup's emergency console only: SSH ignores passwords |
| The demo password `assay-demo` | public, on purpose | | The demo accounts can't change anything outside the visitor's own copy |

The scripts read these files; they never print them. `tofu.sh` refuses to run if its credentials file is readable
by anyone but its owner.

## The commands

From `fyp-grading-iac/live`:

| Command | When | What it does |
|---|---|---|
| `./tofu.sh plan` then `./tofu.sh apply` | Cloudflare changes | Shows, then applies the tunnel, DNS record, rate limit, HSTS and TLS settings |
| `./deploy.sh bootstrap` | once, on a freshly installed server | Signs in as root and creates the `deploy` user |
| `./deploy.sh` | after changing the server setup or the production compose; any time | Hardening, Docker, the stack, Keycloak, the timers. Changes only what differs |
| `./deploy.sh site --check --diff` | before a risky change | A dry run: what would change |
| `./deploy.sh backup-env` | now and then | An encrypted copy of the server's `.env` |
| `./verify.sh` | after a deploy | The six live checks ([delivery.md](delivery.md#checks-after-a-deploy)) |
| `./check.sh` | before committing | The offline checks CI also runs |

On the server, signed in as `deploy` (rarely needed):

| Command | What |
|---|---|
| `sudo assay-compose ps` | The containers and their health (`assay-compose` is `docker compose` for the project, from anywhere) |
| `sudo assay-compose logs -f --tail 100 api-gateway` | One service's logs |
| `sudo assay-compose restart admin-service` | Restart one service (picks up `fyp-grading-config` changes) |
| `sudo assay-update` | Look for new images now instead of waiting for the timer |
| `cat /var/lib/assay-update/last-result`, `journalctl -u assay-update` | What the last update did |
| `sudo assay-keycloak-reset` | Put the realm settings and personas back |
| `systemctl list-timers 'assay-*'` | When the timers run next |
| `sudo docker logs assay-admin-service-1 \| grep 'Midnight purge'` | One line per night: every demo copy deleted |

## First deploy, in short

1. Order the server and install Debian 13 with the SSH public key as root's key.
2. Create the Cloudflare API token (permissions in the guide) and the credentials file.
3. `./tools.sh`, then `./tofu.sh init`, `./tofu.sh plan`, `./tofu.sh apply`.
4. Put the server's address in `ansible/inventory.yml`, then `./deploy.sh bootstrap` and `./deploy.sh` (about 10
   minutes, mostly the first image downloads).
5. `./verify.sh`.

## Day to day

- **A code change:** merge it. It's live within 40 minutes. To check: `./verify.sh`, or `last-result` on the server.
- **A change that didn't go live:** `journalctl -u assay-update` on the server. A rolled-back image is listed in
  `/var/lib/assay-update/failed-images`; once the fix is merged, the next image is a new one and is tried normally.
- **Freeze a version:** set `assay_image_tag` to a commit's short SHA in `ansible/group_vars/assay.yml` and run
  `./deploy.sh`. Set it back to `latest` to follow `master` again.
- **The demo reset:** the visitor copies are deleted at midnight Paris time by admin-service; at 00:05 the timer puts
  the personas back. A visitor can also reset their own copy at any time from the app.
- **Monitoring:** the uptime workflow emails on failure. Grafana, Prometheus and Loki can run on the server but are
  never exposed; there are no admin pages on the internet.

## Troubleshooting

| Symptom | Look at |
|---|---|
| The site shows Cloudflare error 530 / 1033 | The tunnel is down: `sudo assay-compose ps cloudflared`. If the tunnel was deleted at Cloudflare, `./tofu.sh apply` then `./deploy.sh` |
| The site loads but sign-in fails | `sudo assay-compose logs keycloak-server`; `sudo assay-keycloak-reset` |
| One screen fails, the others work | That service's logs; `last-result` (was it just updated, or rolled back?) |
| Can't SSH in | ufw rate-limits new connections: wait a minute. Locked out for good: Netcup's console with root's password |
| A script gets Cloudflare error 1010 | The Browser Integrity Check refused its user agent: send a `User-Agent` header |

More in the [guide's troubleshooting](https://github.com/FirasKhalife/fyp-grading-iac/blob/master/live/README.md#troubleshooting).
