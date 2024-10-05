#!/bin/bash

docker_compose_command="docker-compose"

# Append all docker-compose YAML files
for file in docker-compose/docker-compose.*.yml; do
  docker_compose_command="$docker_compose_command -f $file"
done

# Execute with all passed arguments
if [ "$#" -gt 0 ]; then
  docker_compose_command="$docker_compose_command $*"
fi

$docker_compose_command
