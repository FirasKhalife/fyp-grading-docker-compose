# fyp-grading-docker-compose

Runs **Assay**, the final-year-project grading platform, on one machine:

- seven Spring services
- Keycloak with the demo realm
- Postgres, MongoDB, RabbitMQ and Redis
- optional Prometheus, Grafana and Loki

How the pieces fit together, and how a grade flows through them: [docs/architecture.md](docs/architecture.md).

## Layout

| Path | What |
|---|---|
| `docker-compose.sh` | Runs `docker compose` with every `docker-compose/docker-compose.*.yml` file |
| `docker-compose/.env` | Non-secret settings (service names, URLs). Passwords here are local defaults only; real ones come from the environment |
| `docker-compose/config/keycloak/` | The Keycloak image, and `import/assay-realm.json`: realm `assay`, roles `ADMIN` / `REVIEWER` / `STUDENT`, the eight demo personas, and the public `assay-spa` client |
| `docker-compose/config/keycloak/themes/assay/` | The Assay login theme: Keycloak's sign-in, error and sign-out pages in the app's look, light and dark, with self-hosted IBM Plex fonts ([below](#the-login-theme)) |
| `seed/` | The generator of the demo data each service loads into a visitor's private copy ([seed/README.md](seed/README.md)) |
| `e2e/smoke.sh` | End-to-end smoke test of a running stack, through the gateway with real tokens |
| `docs/` | Architecture |

The service repositories are expected next to this one (`../fyp-grading-admin-service`, and so on).

## Run

```bash
./docker-compose.sh up -d --build
```

| URL | What |
|---|---|
| http://localhost:9191 | The API gateway (`/api/**`, `/swagger-ui.html`) |
| http://localhost:7080 | Keycloak (realm `assay`) |

The config server serves the local `../fyp-grading-config` checkout (`native` profile). Set
`CONFIG_SERVER_PROFILE=git` to read `GIT_REPO_URI` instead.

## Demo personas

All of them share the password `assay-demo`. It's published on purpose: the accounts can't change anything outside
the visitor's own demo copy.

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
- the seed generator's own checks

A manual and weekly job also checks out every service repo and runs `check-shared-code.sh`. It also confirms that
the committed seeds are exactly what the generator produces.
