#!/usr/bin/env bash
# Runs the whole Assay demo on this machine from the published images. Only this repository is needed: nothing is
# cloned or built.
#
#   ./run-demo.sh            start it (the first run downloads the images and creates docker-compose/prod/.env)
#   ./run-demo.sh update     download newer images and restart with them
#   ./run-demo.sh status     list the containers and their health
#   ./run-demo.sh logs       follow the logs
#   ./run-demo.sh stop       stop it, keeping the data
#   ./run-demo.sh reset      stop it and delete all its data (the next start is a fresh install)
#
# EDGE_PORT=9000 ./run-demo.sh serves it on another port (default 8080). ASSAY_TAG=<short sha> pins a release.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROD="$ROOT/docker-compose/prod"
ENV_FILE="$PROD/.env"

die() { echo "run-demo: $*" >&2; exit 1; }

command -v docker >/dev/null 2>&1 || die "Docker is not installed. Install Docker Desktop (or Docker Engine) first."
docker compose version >/dev/null 2>&1 || die "Docker Compose v2 is needed ('docker compose', not 'docker-compose')."
docker info >/dev/null 2>&1 || die "Docker is installed but not running. Start Docker and try again."

compose() { docker compose --project-directory "$PROD" -f "$PROD/compose.yml" "$@"; }

# 32 random letters and digits.
random_secret() {
  LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 32 || true
}

# The first run writes a local .env next to compose.yml: random passwords that never leave this machine, and the
# local address as the public URL. It is git-ignored. Delete it (after `reset`) to start over with new passwords.
create_env() {
  local port="${EDGE_PORT:-8080}"
  sed \
    -e "s|^PUBLIC_URL=.*|PUBLIC_URL=http://localhost:${port}|" \
    -e "s|^DB_PASSWORD=$|DB_PASSWORD=$(random_secret)|" \
    -e "s|^RABBITMQ_PASSWORD=$|RABBITMQ_PASSWORD=$(random_secret)|" \
    -e "s|^REDIS_PASSWORD=$|REDIS_PASSWORD=$(random_secret)|" \
    -e "s|^KEYCLOAK_ADMIN_PASSWORD=$|KEYCLOAK_ADMIN_PASSWORD=$(random_secret)|" \
    -e "s|^# EDGE_PORT=.*|EDGE_PORT=${port}|" \
    "$PROD/.env.example" >"$ENV_FILE"
  chmod 600 "$ENV_FILE"
  echo "Created docker-compose/prod/.env with new random passwords (local only, git-ignored)."
}

env_value() { sed -n "s|^$1=||p" "$ENV_FILE" | tail -n 1; }

case "${1:-start}" in
  start | up)
    [ -f "$ENV_FILE" ] || create_env
    url="$(env_value PUBLIC_URL)"
    echo "Starting 16 containers and waiting until all of them are healthy. The first run downloads about 3 GB"
    echo "of images, so give it a few minutes..."
    if ! compose up -d --wait --wait-timeout 600 --pull missing --quiet-pull; then
      compose ps --format 'table {{.Service}}\t{{.Status}}' >&2 || true
      die "It didn't start. If the images failed to download with 'denied' or 'unauthorized', they aren't public
yet. Otherwise see './run-demo.sh logs'. Docker needs about 6 GB of memory (Docker Desktop: Settings > Resources),
and the config server needs internet access to read its settings from GitHub."
    fi
    cat <<EOF

Assay is running: ${url}

Pick a role on the landing page and you're in. No sign-up: every persona's password is "assay-demo".
  ./run-demo.sh stop     stop it (your data is kept)
  ./run-demo.sh reset    delete everything and start fresh next time
EOF
    ;;
  update)
    compose pull --quiet
    compose up -d --wait --wait-timeout 600
    echo "Updated to the latest images."
    ;;
  status | ps)
    compose ps --format 'table {{.Service}}\t{{.Status}}'
    ;;
  logs)
    compose logs -f --tail 100
    ;;
  stop | down)
    compose down
    ;;
  reset)
    compose down --volumes
    echo "All demo data is deleted. './run-demo.sh' starts a fresh install (docker-compose/prod/.env is kept)."
    ;;
  *)
    sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit 2
    ;;
esac
