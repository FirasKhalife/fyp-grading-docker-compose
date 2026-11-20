sed 's#mvn -q -B clean package -DskipTests#mvn -q -B clean package org.springframework.boot:spring-boot-maven-plugin:3.1.5:repackage -DskipTests#' /tmp/Dockerfile.spring > /tmp/Dockerfile.gw
cd "/mnt/c/src/0. personal/fyp-grading/fyp-grading-api-gateway" && docker build -q --network host -f /tmp/Dockerfile.gw -t api-gateway:1.0 . && echo built
bash "$(dirname "$0")/up.sh" | head -1
sleep 75
docker inspect api-gateway --format 'status={{.State.Status}} health={{.State.Health.Status}}'
for p in /api/rubrics/ /api/teams/ /api/reviewers/ /api/evaluations/ /api/notifications/; do curl -s -o /dev/null -w "$p %{http_code}\n" -m 10 localhost:9191$p; done
