#!/bin/bash
# Light "clicking": N visitor containers (distinct IPs -> own rate-limit bucket), each ~1 API GET/s
# through the gateway, a frontend fetch per cycle, and a Keycloak login every ~20 s.
D=${1:-180}; N=${2:-4}
for v in $(seq 1 $N); do
docker run -d --rm --name loadgen-$v --network fyp-grading --entrypoint sh curlimages/curl -c "
P='/api/teams/ /api/reviewers/ /api/evaluations/ /api/rubrics/ /api/notifications/ /api/admin/teams/grades /api/rubrics/FINAL_REPORT'
end=\$((\$(date +%s)+$D)); i=0
while [ \$(date +%s) -lt \$end ]; do
  for p in \$P; do
    curl -s -o /dev/null -w '%{http_code}\n' -m 10 http://api-gateway:9191\$p >> /tmp/codes
    curl -s -o /dev/null -m 5 http://frontend/
    i=\$((i+1)); [ \$((i%20)) -eq 0 ] && curl -s -o /dev/null -w 'kc%{http_code}\n' -m 10 -d client_id=admin-cli -d username=admin -d password=admin -d grant_type=password http://keycloak-server:8080/realms/master/protocol/openid-connect/token >> /tmp/codes
    sleep 1.1
  done
done
sort /tmp/codes | uniq -c | tr '\n' ' '; sleep 600" > /dev/null
done
echo "started $N visitors for ${D}s"
