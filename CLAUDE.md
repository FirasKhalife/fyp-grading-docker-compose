# Notes for Claude Code sessions

This repository runs Assay, live at https://assay.firaskhalife.dev. The deployment itself (one VPS behind a
Cloudflare Tunnel, Ansible and OpenTofu) is in [`fyp-grading-iac/live/`](https://github.com/FirasKhalife/fyp-grading-iac/tree/master/live);
its README is the full guide. A local session on the owner's machine also gets a private runbook with the machine
details; this file is the part that is safe to publish.

## How a change reaches production

| What changed | How it goes live |
|---|---|
| Any service, the gateway, the frontend, the Keycloak image (`docker-compose/config/keycloak/`: theme, realm), config server, registry | Merge to `master`. That repo's CI publishes `ghcr.io/firaskhalife/fyp-grading-*:latest`, and a timer on the server pulls it within about 30 minutes, recreates only that service, and rolls back if it doesn't become healthy. Nothing to run |
| `fyp-grading-config` (branch `main`) | Read when a service starts: needs a restart of that service on the server |
| `docker-compose/prod/*` here (compose.yml, edge.nginx.conf, .env.example), `scripts/keycloak-reset-personas.sh`, digest bumps of the datastore images | Not automatic: a local session runs `./deploy.sh` in `fyp-grading-iac/live` |
| `fyp-grading-iac/live` (Ansible, OpenTofu) | A local session runs `./deploy.sh` or `./tofu.sh apply` |

A cloud session has no key to the server and no Cloudflare token, so it can't run those. If a change needs one,
say so in the report. Realm changes in `assay-realm.json` reach an existing Keycloak through
`scripts/keycloak-reset-personas.sh` (run after every Keycloak update and nightly), not through the import.

## Rules

- The repositories are public: never commit a secret, a server address or a hostname. The demo password
  `assay-demo` is public on purpose.
- Check a change against the production compose before merging: `./run-demo.sh`, then the commands in
  [README.md](README.md#smoke-test-and-checks). CI runs the same on every pull request.
- Requests to the live site from scripts need their own `User-Agent`: Cloudflare refuses some default ones
  (Python-urllib's gets error 1010).
