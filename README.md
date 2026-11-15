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
| Student | `nour.khoury` | STUDENT |
| Other faculty | `john.doe`, `michael.johnson`, `emily.clark`, `lea.mansour` | REVIEWER |

The web app signs a persona in with one click: it uses the password grant on `assay-spa`. "Sign in with email" uses
the authorization code flow with PKCE.

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
