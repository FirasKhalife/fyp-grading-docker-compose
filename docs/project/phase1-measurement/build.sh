#!/bin/bash
SP="$(dirname "$0")"; R="/mnt/c/src/0. personal/fyp-grading"
sed 's/\$\$JAVA_OPTS/$JAVA_OPTS/' "$SP/Dockerfile.spring" > /tmp/Dockerfile.spring
declare -A tag=([registry-server]=registry-server [config-server]=config-server [api-gateway]=api-gateway [admin-service]=admin-service [evaluation-service]=evaluation-service [notification-service]=notification-service [rubric-service]=rubric-service)
pids=()
for s in "${!tag[@]}"; do
  ( docker build -q --network host -f /tmp/Dockerfile.spring -t ${tag[$s]}:1.0 "$R/fyp-grading-$s" > /tmp/b-$s.log 2>&1; echo "$s rc=$?" ) &
done
( docker build -q --network host -t frontend:1.0 "$R/fyp-grading-frontend" > /tmp/b-frontend.log 2>&1; echo "frontend rc=$?" ) &
( docker build -q --network host -t keycloak-server "$R/fyp-grading-docker-compose/docker-compose/config/keycloak" > /tmp/b-kc.log 2>&1; echo "keycloak rc=$?" ) &
wait
docker images --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep -E ':1.0|keycloak-server'
