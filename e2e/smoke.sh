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
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
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
  curl -s -o $TMP/body -w '%{http_code}' -X "$2" "$GW$3" \
    -H "Authorization: Bearer $1" -H "X-Demo-Session: $SESSION" -H 'Content-Type: application/json' \
    ${4:+--data "$4"} > $TMP/status
  cat $TMP/body
}
status() { cat $TMP/status; }

echo "Assay smoke test against $GW (demo session $SESSION)"

# Right after a start, the gateway needs a few seconds to learn where the services are.
for _ in $(seq 1 30); do
  curl -sf -o /dev/null "$GW/api/demo/personas" && break
  sleep 2
done
personas="$(curl -sf "$GW/api/demo/personas")"
[ "$(echo "$personas" | json 'len(d)')" = 4 ] && ok "four personas, public" || fail "personas"

JANE="$(token jane.smith)"; RANIA="$(token rania.haddad)"; NOUR="$(token nour.khoury)"
ok "persona sign-in through Keycloak (realm assay)"

call "$JANE" PUT /api/demo/session > /dev/null
[ "$(status)" = 201 ] && ok "demo copy created (201)" || fail "demo copy: $(status) $(cat $TMP/body)"
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
  -H "X-Demo-Session: $SESSION" > $TMP/sse &
SSE=$!
sleep 2

submitted="$(call "$JANE" POST "/api/my-evaluations/$beta/FINAL_REPORT/submit" "$form")"
[ "$(status)" = 200 ] && [ "$(echo "$submitted" | json 'd["status"]')" = SUBMITTED ] \
  && ok "Jane submits: locked, score $(echo "$submitted" | json 'd["score"]')" || fail "submit: $(status) $submitted"
call "$JANE" PUT "/api/my-evaluations/$beta/FINAL_REPORT" "$form" > /dev/null
[ "$(status)" = 409 ] && ok "a submitted evaluation can't be changed (409)" || fail "edit after submit: $(status)"

for _ in $(seq 1 20); do
  grade="$(call "$RANIA" GET "/api/teams/$beta" | json 'd["assessments"][3]["grade"]')"
  [ "$grade" != None ] && break
  sleep 1
done
[ "$grade" != None ] && ok "hand-off to admin-service: Beta final report grade is final ($grade)" || fail "no team grade"

for _ in $(seq 1 10); do
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
grep -q "event:activity" $TMP/sse && grep -q "event:notification" $TMP/sse \
  && ok "live: activity and notification arrived over SSE through the gateway" || fail "SSE: $(head -c 300 $TMP/sse)"

released="$(call "$RANIA" POST /api/assessments/FINAL_REPORT/release | json 'len(d["releasedTeamIds"])')"
[ "$released" -ge 1 ] && ok "coordinator releases the final report ($released team(s))" || fail "release"

home="$(call "$NOUR" GET /api/me/team)"
[ "$(echo "$home" | json 'd["team"]["name"]')" = Alpha ] && ok "student home: Nour, Team Alpha, final $(echo "$home" | json 'd["finalGrade"]')" || fail "student home"
call "$NOUR" GET /api/overview > /dev/null
[ "$(status)" = 403 ] && ok "a student can't open the coordinator overview (403)" || fail "student overview: $(status)"
code="$(curl -s -o /dev/null -w '%{http_code}' "$GW/api/overview" -H "X-Demo-Session: $SESSION")"
[ "$code" = 401 ] && ok "no token, no data (401)" || fail "anonymous: $code"
code="$(curl -s -o $TMP/body -w '%{http_code}' "$GW/api/overview" -H "Authorization: Bearer $RANIA")"
[ "$code" = 400 ] && grep -q demo-session-required $TMP/body && ok "no demo session header, 400 demo-session-required"   || fail "missing session header: $code $(cat $TMP/body)"
for path in /internal/grades /admin-service/actuator/env /config/admin-service/default /actuator/env             /actuator/prometheus /admin-service/actuator/prometheus; do
  code="$(curl -s -o /dev/null -w '%{http_code}' "$GW$path" -H "Authorization: Bearer $RANIA")"
  [[ "$code" =~ ^(403|404)$ ]] || fail "$path is reachable ($code)"
done
ok "internal endpoints, actuator, metrics and config server aren't routed"

other="$(python3 -c 'import uuid; print(uuid.uuid4())')"
code="$(curl -s -o $TMP/body -w '%{http_code}' "$GW/api/overview" -H "Authorization: Bearer $RANIA" -H "X-Demo-Session: $other")"
[ "$code" = 404 ] && grep -q demo-session-not-found $TMP/body   && ok "a session with no demo copy gets 404 demo-session-not-found" || fail "unknown session: $code $(cat $TMP/body)"

# Review M6: a reset hands out a new copy id; the old one is answered with 404.
old="$SESSION"
fresh="$(call "$RANIA" POST /api/demo/session/reset | json 'd["id"]')"
[ "$(status)" = 200 ] && [ "$fresh" != "$old" ] && ok "reset my demo: a new copy id" || fail "reset: $(status) $fresh"
SESSION="$fresh"
state="$(call "$RANIA" GET /api/overview | json '[t for t in d["teams"] if t["team"]["name"]=="Beta"][0]["cells"][3]["state"]')"
[ "$state" = WAITING ] && ok "after reset, Beta's final report is back to 2 of 3" || fail "after reset: $state"
code="$(curl -s -o /dev/null -w '%{http_code}' "$GW/api/overview" -H "Authorization: Bearer $RANIA" -H "X-Demo-Session: $old")"
[ "$code" = 404 ] && ok "the old copy id is gone (404)" || fail "old session after reset: $code"

# Review H3: too many requests from one address get 429 with Retry-After (the bucket refills in a few seconds).
seq 1 90 | xargs -P 30 -I{} curl -s -o /dev/null -D - "$GW/api/demo/personas" > $TMP/burst
grep -q '^HTTP/[0-9.]* 429' $TMP/burst && grep -qi '^retry-after: [0-9]' $TMP/burst   && ok "rate limit: 429 with Retry-After" || fail "no 429 in a burst of 90 requests"

# Review C1: a visitor must not be able to trigger an application-initiated action (here: change the shared
# persona's password) by adding kc_action to the sign-in URL. Signing in must go straight back to the app.
auth="$KC/realms/assay/protocol/openid-connect/auth?client_id=assay-spa&response_type=code&scope=openid"
auth="$auth&redirect_uri=http%3A%2F%2Flocalhost%3A5173%2F&code_challenge_method=S256"
auth="$auth&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&kc_action=UPDATE_PASSWORD"
form="$(curl -s -c "$TMP/kc-cookies" "$auth" | python3 -c '
import html, re, sys
m = re.search(r"<form[^>]*id=\"kc-form-login\"[^>]*action=\"([^\"]+)\"", sys.stdin.read())
print(html.unescape(m.group(1)) if m else "")')"
form="$KC/realms/${form#*/realms/}"   # the form names Keycloak's public hostname; post to the URL we were given
[ -n "$form" ] || fail "Keycloak login form not found"
after="$(curl -s -o "$TMP/kc-after" -w '%{http_code} %{redirect_url}' -b "$TMP/kc-cookies" -c "$TMP/kc-cookies"   --data-urlencode "username=jane.smith" --data-urlencode "password=$PASSWORD" "$form")"
if grep -q 'password-new' "$TMP/kc-after"; then fail "kc_action=UPDATE_PASSWORD shows the change-password form"; fi
[[ "$after" == 302\ http://localhost:5173/* ]] && ok "personas can't be changed through kc_action (straight back to the app)"   || fail "unexpected answer to the kc_action sign-in: $after"

echo "All $pass checks passed."
