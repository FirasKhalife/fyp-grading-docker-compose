#!/bin/bash
# Wrapper: all repo compose files + measurement override. Fixes .env bugs via shell env.
SP="$(cd "$(dirname "$0")" && pwd)"
cd "/mnt/c/src/0. personal/fyp-grading/fyp-grading-docker-compose/docker-compose"
export REGISTRY_SERVER_URL=http://registry-server:8761/eureka/ RUBRIC_SERVICE_NAME=rubric-service DOCKER_BUILDKIT=1 COMPOSE_BAKE=false
args=(); for f in docker-compose.*.yml; do args+=(-f "$f"); done
for f in ${EXTRA_FILES:-}; do args+=(-f "$f"); done
exec docker compose "${args[@]}" -f "$SP/override.yml" "$@"
