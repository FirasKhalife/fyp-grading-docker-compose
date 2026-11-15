#!/usr/bin/env bash
# End-to-end smoke test of a running Assay stack, through the gateway with real Keycloak tokens.
# It walks the demo's key moment: Jane (jury) finishes and submits the Team Beta final report, the coordinator
# sees the team grade become final live (SSE) and releases it, the student view stays scoped, and a reset
# brings the copy back to the seed.
#
# Usage: e2e/smoke.sh [gateway-url] [keycloak-url]     (defaults: http://localhost:9191 http://localhost:7080)
# Needs: bash, curl, python3. Exits non-zero on the first failed check.
set -euo pipefail

GW="${1:-http://localhost:9191}"
KC="${2:-http://localhost:7080}"
PASSWORD="${DEMO_PASSWORD:-assay-demo}"   # the public demo personas' password (see README)
SESSION="$(python3 -c 'import uuid; print(uuid.uuid4())')"
pass=0

ok()   { pass=$((pass + 1)); printf '  ok   %s\n' "$1"; }
fail() { printf '  FAIL %s\n' "$1" >&2; exit 1; }
json() { python3 -c "import json,sys; d=json.load(sys.stdin); print($1)"; }

token() {
  curl -sf "$KC/realms/assay/protocol/openid-connect/token" \
    -d grant_type=password -d client_id=assay-spa -d "username=$1" -d "password=$PASSWORD" | json 'd["access_token"]'
}

# call <token> <method> <path> [json-body]  -> prints the body; $(status) is its HTTP status
call() {
  curl -s -o /tmp/assay-smoke-body -w '%{http_code}' -X "$2" "$GW$3" \
    -H "Authorization: Bearer $1" -H "X-Demo-Session: $SESSION" -H 'Content-Type: application/json' \
    ${4:+--data "$4"} > /tmp/assay-smoke-status
  cat /tmp/assay-smoke-body
}
status() { cat /tmp/assay-smoke-status; }

echo "Assay smoke test against $GW (demo session $SESSION)"

# Right after a start, the gateway needs a few seconds to learn where the services are.
for i in $(seq 1 30); do
  curl -sf -o /dev/null "$GW/api/demo/personas" && break
  sleep 2
done
personas="$(curl -sf "$GW/api/demo/personas")"
[ "$(echo "$personas" | json 'len(d)')" = 4 ] && ok "four personas, public" || fail "personas"

JANE="$(token jane.smith)"; RANIA="$(token rania.haddad)"; NOUR="$(token nour.khoury)"
ok "persona sign-in through Keycloak (realm assay)"

call "$JANE" PUT /api/demo/session > /dev/null
[ "$(status)" = 201 ] && ok "demo copy created (201)" || fail "demo copy: $(status) $(cat /tmp/assay-smoke-body)"
call "$RANIA" PUT /api/demo/session > /dev/null
[ "$(status)" = 200 ] && ok "switching persona keeps the same copy (200)" || fail "second PUT: $(status)"

beta="$(call "$RANIA" GET /api/overview | json '[t["team"]["id"] for t in d["teams"] if t["team"]["name"]=="Beta"][0]')"
state="$(call "$RANIA" GET /api/overview | json '[t for t in d["teams"] if t["team"]["name"]=="Beta"][0]["cells"][3]["state"]')"
[ "$state" = WAITING ] && ok "Beta final report: 2 of 3 submitted" || fail "Beta FR state $state"

draft="$(call "$JANE" GET "/api/my-evaluations/$beta/FINAL_REPORT")"
[ "$(echo "$draft" | json 'd["status"]')" = DRAFT ] && ok "Jane's Beta final report draft ($(echo "$draft" | json 'd["scoredCount"]') of 13 scored)" || fail "draft"
form="$(echo "$draft" | json 'json.dumps({"criteria":[{"criterionId":c["criterionId"],"level":c["level"] if c["level"] is not None else 3,"comment":c["comment"]} for c in d["criteria"]],"overallComment":"Solid report; fix the privacy constraint."})')"

# Listen to the coordinator's live stream while Jane submits.
curl -sN --max-time 25 "$GW/api/notifications/stream" -H "Authorization: Bearer $RANIA" \
  -H "X-Demo-Session: $SESSION" > /tmp/assay-smoke-sse &
SSE=$!
sleep 2

submitted="$(call "$JANE" POST "/api/my-evaluations/$beta/FINAL_REPORT/submit" "$form")"
[ "$(status)" = 200 ] && [ "$(echo "$submitted" | json 'd["status"]')" = SUBMITTED ] \
  && ok "Jane submits: locked, score $(echo "$submitted" | json 'd["score"]')" || fail "submit: $(status) $submitted"
call "$JANE" PUT "/api/my-evaluations/$beta/FINAL_REPORT" "$form" > /dev/null
[ "$(status)" = 409 ] && ok "a submitted evaluation can't be changed (409)" || fail "edit after submit: $(status)"

for i in $(seq 1 20); do
  grade="$(call "$RANIA" GET "/api/teams/$beta" | json 'd["assessments"][3]["grade"]')"
  [ "$grade" != None ] && break
  sleep 1
done
[ "$grade" != None ] && ok "RabbitMQ aggregation: Beta final report grade is final ($grade)" || fail "no team grade"

for i in $(seq 1 10); do
  call "$RANIA" GET /api/notifications | grep -q "Final report for Team Beta is final" && break
  sleep 1
done
call "$RANIA" GET /api/notifications | grep -q "Final report for Team Beta is final" \
  && ok "coordinator notified (personal notification)" || fail "no notification"
call "$JANE" GET /api/notifications | grep -q "Final report for Team Beta is final" \
  && ok "jury member on the team notified" || fail "jury not notified"
call "$RANIA" GET /api/activity | grep -q "submitted the Final report for Team Beta" \
  && ok "activity feed shows the submission" || fail "no activity"

wait "$SSE" || true
grep -q "event:activity" /tmp/assay-smoke-sse && grep -q "event:notification" /tmp/assay-smoke-sse \
  && ok "live: activity and notification arrived over SSE through the gateway" || fail "SSE: $(head -c 300 /tmp/assay-smoke-sse)"

released="$(call "$RANIA" POST /api/assessments/FINAL_REPORT/release | json 'len(d["releasedTeamIds"])')"
[ "$released" -ge 1 ] && ok "coordinator releases the final report ($released team(s))" || fail "release"

home="$(call "$NOUR" GET /api/me/team)"
[ "$(echo "$home" | json 'd["team"]["name"]')" = Alpha ] && ok "student home: Nour, Team Alpha, final $(echo "$home" | json 'd["finalGrade"]')" || fail "student home"
call "$NOUR" GET /api/overview > /dev/null
[ "$(status)" = 403 ] && ok "a student can't open the coordinator overview (403)" || fail "student overview: $(status)"
code="$(curl -s -o /dev/null -w '%{http_code}' "$GW/api/overview" -H "X-Demo-Session: $SESSION")"
[ "$code" = 401 ] && ok "no token, no data (401)" || fail "anonymous: $code"
for path in /internal/grades /admin-service/actuator/env /config/admin-service/default /actuator/env; do
  code="$(curl -s -o /dev/null -w '%{http_code}' "$GW$path" -H "Authorization: Bearer $RANIA")"
  [[ "$code" =~ ^(403|404)$ ]] || fail "$path is reachable ($code)"
done
ok "internal endpoints, actuator and config server aren't routed"

other="$(python3 -c 'import uuid; print(uuid.uuid4())')"
code="$(curl -s -o /tmp/assay-smoke-body -w '%{http_code}' "$GW/api/overview" -H "Authorization: Bearer $RANIA" -H "X-Demo-Session: $other")"
[ "$(json 'len(d["teams"])' < /tmp/assay-smoke-body)" = 0 ] && ok "another visitor's session sees none of this copy" || fail "isolation"

call "$RANIA" POST /api/demo/session/reset > /dev/null
[ "$(status)" = 200 ] && ok "reset my demo" || fail "reset: $(status)"
state="$(call "$RANIA" GET /api/overview | json '[t for t in d["teams"] if t["team"]["name"]=="Beta"][0]["cells"][3]["state"]')"
[ "$state" = WAITING ] && ok "after reset, Beta's final report is back to 2 of 3" || fail "after reset: $state"

echo "All $pass checks passed."
