# fyp-grading-docker-compose

Runs **Assay**, the final-year-project grading platform, on one machine:

- seven Spring services
- Keycloak with the demo realm
- Postgres, MongoDB, RabbitMQ and Redis
- optional Prometheus, Grafana and Loki

How the pieces fit together, and how a grade flows through them: [docs/architecture.md](docs/architecture.md).

## Try it in one command

You need Docker with Compose v2, about 6 GB of memory for Docker, and an internet connection. Only this repository
is needed:

```bash
git clone https://github.com/FirasKhalife/fyp-grading-docker-compose.git
cd fyp-grading-docker-compose
./run-demo.sh
```

Then open http://localhost:8080 and pick a role. The first run downloads about 3 GB of images, then starts 16
containers and waits until every one is healthy (a few minutes). It also creates `docker-compose/prod/.env` with
random local passwords (git-ignored). On Windows, run it from WSL or Git Bash.

| Command | What it does |
|---|---|
| `./run-demo.sh` | Start the demo, or bring it back up |
| `./run-demo.sh status` | List the containers and their health |
| `./run-demo.sh logs` | Follow the logs |
| `./run-demo.sh update` | Download newer images and restart with them |
| `./run-demo.sh stop` | Stop it and keep the data |
| `./run-demo.sh reset` | Stop it and delete all its data |

`EDGE_PORT=9000 ./run-demo.sh` uses another port on the first run, and `ASSAY_TAG=<short sha>` pins a release. It
runs the same hardened production compose as the live demo (`docker-compose/prod/`), from the images CI publishes
to `ghcr.io/firaskhalife/`.

## Layout

| Path | What |
|---|---|
| `run-demo.sh` | Runs the demo from the published images ([above](#try-it-in-one-command)) |
| `docker-compose.sh` | Development: runs `docker compose` with every `docker-compose/docker-compose.*.yml` file, building from the sibling repositories |
| `scripts/clone-sources.sh` | Clones the sibling repositories the development stack builds from |
| `docker-compose/.env` | Non-secret settings (service names, URLs). Passwords here are local defaults only; real ones come from the environment |
| `docker-compose/config/keycloak/` | The Keycloak image, and `import/assay-realm.json`: realm `assay`, roles `ADMIN` / `REVIEWER` / `STUDENT`, the eight demo personas, and the public `assay-spa` client |
| `docker-compose/config/keycloak/themes/assay/` | The Assay login theme: Keycloak's sign-in, error and sign-out pages in the app's look, light and dark, with self-hosted IBM Plex fonts ([below](#the-login-theme)) |
| `seed/` | The generator of the demo data each service loads into a visitor's private copy ([seed/README.md](seed/README.md)) |
| `e2e/smoke.sh` | End-to-end smoke test of a running stack, through the gateway with real tokens |
| `docker-compose/prod/` | Production: a standalone compose for one 8 GB host that pulls the published images, with memory limits, health checks, one edge (`edge.nginx.conf`) and secrets from a git-ignored `.env` ([docs/deploy-hardening.md](docs/deploy-hardening.md)) |
| `docs/` | Architecture, and running it in production |

## Develop: build from source

The development stack builds every service from the repositories next to this one (`../fyp-grading-admin-service`,
and so on). `scripts/clone-sources.sh` clones the missing ones. `run-demo.sh` needs none of them.

```bash
scripts/clone-sources.sh
./docker-compose.sh up -d --build
```

| URL | What |
|---|---|
| http://localhost:9191 | The API gateway (`/api/**`, `/swagger-ui.html`) |
| http://localhost:7080 | Keycloak (realm `assay`) |

For production on a server, see [docs/deploy-hardening.md](docs/deploy-hardening.md): `cd docker-compose/prod`,
copy `.env.example` to `.env` and fill it in, then `docker compose up -d --wait`. Everything is then on one origin,
`http://localhost:8080` on the host.

The config server serves the local `../fyp-grading-config` checkout (`native` profile). Set
`CONFIG_SERVER_PROFILE=git` to read `GIT_REPO_URI` instead.

## Demo personas

All of them share the password `assay-demo`. It's published on purpose: the accounts can't change anything outside
the visitor's own demo copy.

Keycloak's account console and account API are switched off in the image (`KC_FEATURES_DISABLED=account,account-api`),
and every required action is off in the realm. So nobody can change a persona's password, 2FA or profile, and
`/realms/assay/account` shows the Assay error page. The smoke test checks both.

| Persona | Username | Roles |
|---|---|---|
| Coordinator | `rania.haddad` | ADMIN, REVIEWER |
| Jury member | `jane.smith` | REVIEWER |
| Advisor | `karim.nassar` | REVIEWER |
| Student, Team Alpha (every result released) | `nour.khoury` | STUDENT |
| Student, Team Beta (waiting on results) | `ahmad.fares` | STUDENT |
| Other faculty | `john.doe`, `michael.johnson`, `emily.clark`, `lea.mansour` | REVIEWER |

The web app signs a persona in with one click: it uses the password grant on `assay-spa`. "Sign in with email" uses
the authorization code flow with PKCE.

A realm import never updates an existing realm. On a Keycloak imported before a persona was added, run
`scripts/keycloak-reset-personas.sh` once: it creates the missing personas with their fixed ids.

## The login theme

"Sign in with email" and the sign-out confirmation show Keycloak's own pages. The `assay` theme makes them look like
the app: the "Private demo" strip, the wordmark, one card, the Assay colours in light and dark (from the visitor's
system setting), 44 px targets and a 375 px layout.

- It's a plain FreeMarker theme on Keycloak's `base` theme. It overrides the layout (`template.ftl`), the login,
  error, info, page-expired and sign-out pages, and the English copy (`messages/messages_en.properties`). Every other page
  still uses Keycloak's template with the theme's CSS classes.
- The fonts are IBM Plex Sans and Mono (SIL Open Font License, `resources/fonts/OFL.txt`). The pages load nothing
  from outside Keycloak.
- The image copies it to `/opt/keycloak/themes/assay`, and the realm export sets `loginTheme: assay`. On a realm
  imported before that, `scripts/keycloak-reset-personas.sh` sets it.
- "Back to Assay" and the wordmark link to `ASSAY_SPA_ORIGIN` (default `http://localhost:5173`), so the link works
  even on pages where Keycloak has no client to link back to.
- After a Keycloak upgrade, compare the six overridden `.ftl` files with the new `base/login` ones. Each says which
  Keycloak version it follows.

## Smoke test

```bash
e2e/smoke.sh                                   # gateway http://localhost:9191, Keycloak http://localhost:7080
```

The script walks the demo's key moment:

1. Persona sign-in, and the creation of a private demo copy.
2. Jane finishes and submits the Team Beta final report, and can't change it afterwards.
3. RabbitMQ aggregates the team grade. The coordinator and the jury get notifications, and the feed and the live
   SSE stream show it.
4. The coordinator releases the final report.
5. Scoping holds:
   - the student's view is scoped to their team
   - anonymous and internal paths are closed
   - another visitor sees nothing of this copy
6. A reset brings the copy back to the seed.

## Shared code and CI

Each service is a self-contained repository, so a few files are copied between them instead of published as a
library:

- the `common/` package (demo-session scoping, security, problem details)
- `checkstyle.xml`, the `Dockerfile`, `.gitattributes`
- the JSON fixtures of the payloads services exchange (`src/test/resources/contracts`)

`scripts/check-shared-code.sh` checks that every copy is identical. Each service's `PayloadContractsTest` checks
that it writes exactly a fixture's fields and can read the fixtures it consumes.

GitHub Actions (`.github/workflows/ci.yml`) runs on every pull request:

- ShellCheck on the scripts
- validation of the compose files and the Keycloak realm
- the production compose: every service has a memory limit, a health check and log rotation, only the edge
  publishes a port, and the limits fit the 8 GB host
- the seed generator's own checks
- the Keycloak image build. From `master`, CI also pushes it to `ghcr.io/firaskhalife/fyp-grading-keycloak`
  (`latest` and the short commit SHA)

A manual and weekly job also checks out every service repo and runs `check-shared-code.sh`. It also confirms that
the committed seeds are exactly what the generator produces.
