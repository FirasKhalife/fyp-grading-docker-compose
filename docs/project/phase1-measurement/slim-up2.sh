#!/bin/bash
# Same as slim-up.sh but EXTRA_FILES is relative (the workspace path has a space, which word-splits).
SP="$(cd "$(dirname "$0")" && pwd)"
export EXTRA_FILES="../../phase1-measurement/slim.yml"
export JAVA_OPTS="-XX:+UseSerialGC -XX:TieredStopAtLevel=1 -Xmx144m -Xss512k -XX:MaxMetaspaceSize=180m -XX:ReservedCodeCacheSize=48m -XX:MaxDirectMemorySize=32m -XX:+ExitOnOutOfMemoryError"
SVC="admin-db mongodb rabbitmq redis registry-server config-server keycloak-server admin-service evaluation-service notification-service rubric-service api-gateway frontend"
T0=$(date +%s)
bash "$SP/dc.sh" up -d --no-build --wait --wait-timeout 600 $SVC > /tmp/up.log 2>&1; rc=$?
echo "slim up rc=$rc in $(( $(date +%s)-T0 ))s"; tail -5 /tmp/up.log
docker ps -a --filter label=com.docker.compose.project=fyp-grading --format '{{.Names}}\t{{.Status}}' | sort
