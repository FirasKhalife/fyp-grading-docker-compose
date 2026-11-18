#!/bin/bash
# The development stack: builds every service from the sibling repositories (../fyp-grading-*) and runs it with
# every docker-compose/docker-compose.*.yml file. To just run the demo, use ./run-demo.sh, which needs only this repo.
cd "$(dirname "$0")" || exit 1

case "${1:-}" in
  up | build | create | run | start)
    missing=""
    for repo in admin-service evaluation-service notification-service rubric-service api-gateway config-server \
      registry-server config frontend; do
      [ -d "../fyp-grading-$repo" ] || missing="$missing fyp-grading-$repo"
    done
    if [ -n "$missing" ]; then
      echo "The development stack builds from the sibling repositories, and these are missing next to this one:" >&2
      echo " $missing" >&2
      echo "Clone them with scripts/clone-sources.sh, or run the demo from the published images: ./run-demo.sh" >&2
      exit 1
    fi
    ;;
esac

docker_compose_command="docker compose"

# Append all docker-compose YAML files
for file in docker-compose/docker-compose.*.yml; do
  docker_compose_command="$docker_compose_command -f $file"
done

# Execute with all passed arguments
if [ "$#" -gt 0 ]; then
  docker_compose_command="$docker_compose_command $*"
fi

$docker_compose_command
