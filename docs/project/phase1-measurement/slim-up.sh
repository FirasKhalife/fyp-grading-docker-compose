#!/bin/bash
SP="$(cd "$(dirname "$0")" && pwd)"
bash "$SP/dc.sh" down --remove-orphans > /tmp/down.log 2>&1; echo "down rc=$?"
export EXTRA_FILES="$SP/slim.yml"
export JAVA_OPTS="-XX:+UseSerialGC -XX:TieredStopAtLevel=1 -Xss256k -XX:ReservedCodeCacheSize=48m -XX:MaxMetaspaceSize=128m -Xmx160m -XX:+ExitOnOutOfMemoryError"
SVC="admin-db mongodb rabbitmq redis registry-server config-server keycloak-server admin-service evaluation-service notification-service rubric-service api-gateway frontend"
T0=$(date +%s)
bash "$SP/dc.sh" up -d --no-build --wait --wait-timeout 600 $SVC > /tmp/up.log 2>&1; rc=$?
echo "slim up rc=$rc cold boot (all healthy) in $(( $(date +%s)-T0 ))s"
grep -vE "obsolete|JAVA_OPTS" /tmp/up.log | grep -iE "error|unhealthy|fail" | head
docker ps -a --filter label=com.docker.compose.project=fyp-grading --format '{{.Names}}\t{{.Status}}' | sort
