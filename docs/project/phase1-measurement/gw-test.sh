#!/bin/bash
# Run the gateway build like CI: Java 25, and no reachable Redis (port 1 is closed).
cd "/mnt/c/src/0. personal/fyp-grading/fyp-grading-api-gateway" || exit 1
run() {
  docker run --rm --network host -v "$PWD":/src -v "$HOME/.m2":/root/.m2 -w /src maven:3.9-eclipse-temurin-25 \
    mvn -B -ntp -U verify -Dspring.data.redis.port=1 "$@" 2>&1 | grep -E "Tests run:.*Fail|EdgeSecurityTest\.|BUILD" | tail -6
}
echo "== with redis health forced back on (should reproduce the CI failure) =="
run -Dmanagement.health.redis.enabled=true
echo "== with the fix =="
run
