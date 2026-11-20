#!/bin/bash
SP="$(cd "$(dirname "$0")" && pwd)"
T0=$(date +%s)
bash "$SP/dc.sh" up -d --no-build "$@" > /tmp/up.log 2>&1; rc=$?
echo "up rc=$rc after $(( $(date +%s)-T0 ))s"
grep -vE "obsolete|JAVA_OPTS" /tmp/up.log | grep -iE "error|unhealthy|fail|dependency" | head -15
docker ps -a --filter label=com.docker.compose.project=fyp-grading --format '{{.Names}}\t{{.Status}}' | sort
