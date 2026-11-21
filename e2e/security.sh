#!/usr/bin/env bash
# Security checks of a running Assay stack: the shared demo personas can't be changed or locked out, nothing but the
# app's way in is reachable from outside the host, and the production compose publishes only the edge.
#
# Usage: e2e/security.sh [gateway-url] [keycloak-url]     (defaults: http://localhost:9191 http://localhost:7080)
#        Against the production compose both are its edge: APP_ORIGIN=http://localhost:8080 e2e/security.sh \
#        http://localhost:8080 http://localhost:8080
# Env:   APP_ORIGIN           the origin the SPA client may redirect to (default http://localhost:5173, the dev server)
#        KEYCLOAK_CONTAINER   default: the running container of the compose service keycloak-server (of the project
#                             COMPOSE_PROJECT_NAME, if set)
#        KEYCLOAK_ADMIN_USER / KEYCLOAK_ADMIN_PASSWORD   the master-realm admin for kcadm.sh (default: the container's
#                             bootstrap admin, from its environment)
#        DEMO_PASSWORD        default assay-demo
# Needs: bash, curl, python3, docker (on the stack's host). Runs every check; exits non-zero if any failed.
set -uo pipefail

GW="${1:-http://localhost:9191}"
KC="${2:-http://localhost:7080}"
APP="${APP_ORIGIN:-http://localhost:5173}"
PW="${DEMO_PASSWORD:-assay-demo}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT
pass=0
failn=0

ok()  { pass=$((pass + 1)); printf '  ok   %s\n' "$1"; }
bad() { failn=$((failn + 1)); printf '  FAIL %s\n' "$1"; }
port_of() { python3 -c 'import sys, urllib.parse; u = urllib.parse.urlsplit(sys.argv[1]); print(u.port or (443 if u.scheme == "https" else 80))' "$1"; }

C="${KEYCLOAK_CONTAINER:-$(docker ps -q --filter label=com.docker.compose.service=keycloak-server ${COMPOSE_PROJECT_NAME:+--filter "label=com.docker.compose.project=$COMPOSE_PROJECT_NAME"} | head -n 1)}"
[ -n "$C" ] || { echo "security: no running keycloak-server container (set KEYCLOAK_CONTAINER)" >&2; exit 2; }
PROJECT="$(docker inspect "$C" --format '{{index .Config.Labels "com.docker.compose.project"}}')"
envof() { docker exec "$C" printenv "$1" 2>/dev/null || true; }
ADMIN_USER="${KEYCLOAK_ADMIN_USER:-$(envof KC_BOOTSTRAP_ADMIN_USERNAME)}"
ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD:-$(envof KC_BOOTSTRAP_ADMIN_PASSWORD)}"
# kcadm.sh keeps its session in a file; /tmp is the writable place in the read-only production container.
kc() { docker exec "$C" /opt/keycloak/bin/kcadm.sh "$@" --config /tmp/kcadm.config; }

echo "Assay security checks against $GW (Keycloak $KC, container $PROJECT/$(docker inspect "$C" --format '{{.Name}}' | tr -d /))"
if ! kc config credentials --server http://localhost:8080 --realm master --user "${ADMIN_USER:-admin}" \
  --password "${ADMIN_PASSWORD:-admin}" >/dev/null 2>&1; then
  echo "security: kcadm.sh can't sign in to the master realm (set KEYCLOAK_ADMIN_USER / KEYCLOAK_ADMIN_PASSWORD)" >&2
  exit 2
fi

echo "== personas can't change their password or set up 2FA"
redirect="$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1] + "/", safe=""))' "$APP")"
for action in UPDATE_PASSWORD CONFIGURE_TOTP webauthn-register UPDATE_PROFILE delete_account; do
  rm -f "$T/c"
  auth="$KC/realms/assay/protocol/openid-connect/auth?client_id=assay-spa&response_type=code&scope=openid"
  auth="$auth&redirect_uri=$redirect&code_challenge_method=S256&code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
  auth="$auth&kc_action=$action"
  form="$(curl -s -c "$T/c" "$auth" | python3 -c '
import html, re, sys
m = re.search(r"<form[^>]*id=\"kc-form-login\"[^>]*action=\"([^\"]+)\"", sys.stdin.read())
print(html.unescape(m.group(1)) if m else "")')"
  if [ -z "$form" ]; then bad "kc_action=$action: no sign-in form"; continue; fi
  form="$KC/realms/${form#*/realms/}"   # the form names Keycloak's public hostname; post to the URL we were given
  after="$(curl -s -o "$T/a" -w '%{http_code} %{redirect_url}' -b "$T/c" -c "$T/c" \
    --data-urlencode username=nour.khoury --data-urlencode "password=$PW" "$form")"
  if [[ "$after" == "302 $APP/"* ]] && ! grep -q -E 'password-new|totp|webauthn' "$T/a"; then
    ok "kc_action=$action goes straight back to the app"
  else
    bad "kc_action=$action: $after"
  fi
done
enabled="$(kc get authentication/required-actions -r assay --fields alias,enabled --format csv --noquotes | awk -F, '$2=="true"{print $1}')"
[ -z "$enabled" ] && ok "every required action is disabled" || bad "required actions still enabled: $enabled"
for u in rania.haddad jane.smith karim.nassar nour.khoury; do
  id="$(kc get users -r assay -q "username=$u" -q exact=true --fields id --format csv --noquotes)"
  types="$(kc get "users/$id/credentials" -r assay --fields type --format csv --noquotes | sort -u | tr '\n' ' ')"
  ra="$(kc get "users/$id" -r assay --fields requiredActions --format csv --noquotes)"
  if [ "$types" = "password " ] && { [ -z "$ra" ] || [ "$ra" = "[]" ]; }; then
    ok "$u: password only, no pending actions"
  else
    bad "$u: credentials [$types] actions [$ra]"
  fi
done
tok="$(curl -s "$KC/realms/assay/protocol/openid-connect/token" -d grant_type=password -d client_id=assay-spa \
  -d username=karim.nassar -d "password=$PW" | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')"
code="$(curl -s -o /dev/null -w '%{http_code}' -X POST "$KC/realms/assay/account/credentials/password" \
  -H "Authorization: Bearer $tok" -H 'Content-Type: application/json' \
  -d "{\"currentPassword\":\"$PW\",\"newPassword\":\"x\",\"confirmation\":\"x\"}")"
[ "$code" != 200 ] && [ "$code" != 204 ] && ok "account API refuses a password change with the app token ($code)" \
  || bad "account API password change answered $code"

echo "== brute force can't lock a persona out"
for i in $(seq 1 20); do
  curl -s -o /dev/null "$KC/realms/assay/protocol/openid-connect/token" -d grant_type=password -d client_id=assay-spa \
    -d username=karim.nassar -d "password=wrong-$i"
done
code="$(curl -s -o /dev/null -w '%{http_code}' "$KC/realms/assay/protocol/openid-connect/token" -d grant_type=password \
  -d client_id=assay-spa -d username=karim.nassar -d "password=$PW")"
[ "$code" = 200 ] && ok "20 wrong passwords, then the right one still signs in" || bad "after 20 wrong passwords: $code"
bf="$(kc get realms/assay --fields bruteForceProtected --format csv --noquotes)"
[ "$bf" = false ] && ok "realm brute-force lockout is off" || bad "bruteForceProtected=$bf"
uid="$(kc get users -r assay -q username=karim.nassar -q exact=true --fields id --format csv --noquotes)"
# On failure, print what Keycloak answered: the first nightly run failed here once with no clue why.
attack="$(kc get "attack-detection/brute-force/users/$uid" -r assay 2>&1)"
grep -Eq '"disabled" *: *false' <<<"$attack" && ok "Karim isn't temporarily disabled" \
  || bad "Karim is flagged by brute-force detection (user id '$uid'): $(tr -s ' \n' ' ' <<<"$attack" | cut -c1-300)"

echo "== datastores, consoles and the app aren't reachable from outside the host"
ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
[ -n "$ip" ] || { bad "no network address found"; ip=0.0.0.0; }
gw_port="$(port_of "$GW")"
kc_port="$(port_of "$KC")"
timeout 3 bash -c "exec 3<>/dev/tcp/127.0.0.1/$gw_port" 2>/dev/null \
  && ok "control: the way in answers on 127.0.0.1:$gw_port" || bad "control: nothing on 127.0.0.1:$gw_port"
# The databases, RabbitMQ (and its console), Redis, Keycloak, MinIO, the Spring Cloud servers, and the URLs given.
for p in $(printf '%s\n' 5432 27017 5672 15672 6379 7080 8080 9000 9191 8761 8071 80 "$gw_port" "$kc_port" | sort -un); do
  if timeout 3 bash -c "exec 3<>/dev/tcp/$ip/$p" 2>/dev/null; then bad "port $p open on $ip"; else ok "port $p closed on the network address $ip"; fi
done
wide="$(docker ps --filter "label=com.docker.compose.project=$PROJECT" --format '{{.Names}} {{.Ports}}' | grep -E '0\.0\.0\.0|\[::\]' || true)"
[ -z "$wide" ] && ok "no $PROJECT container publishes on 0.0.0.0 or ::" || bad "published widely: $wide"

prod="$ROOT/docker-compose/prod"
sed 's/=$/=placeholder/' "$prod/.env.example" > "$T/prod.env"
pub="$(docker compose --project-directory "$prod" -f "$prod/compose.yml" --env-file "$T/prod.env" --profile tunnel \
  config --format json 2>"$T/err" | python3 -c '
import json, sys
s = json.load(sys.stdin)["services"]
print(" ".join(n + ":" + str(p.get("host_ip")) + ":" + str(p.get("published")) for n, v in s.items() for p in v.get("ports", [])), "|", len(s), "services")')"
[[ "$pub" =~ ^edge:127\.0\.0\.1:[0-9]+\ \|\ [1-9][0-9]*\ services$ ]] \
  && ok "the production compose publishes only the edge, on 127.0.0.1 ($pub)" || bad "production compose: $pub $(head -c 300 "$T/err")"

for path in /admin/ /admin/master/console/ /realms/master/ /actuator/env /eureka/apps /admin-service/actuator/env /internal/grades; do
  c="$(curl -s -o /dev/null -w '%{http_code}' "$GW$path")"
  [[ "$c" =~ ^(401|403|404)$ ]] && ok "$path isn't served on the way in ($c)" || bad "$GW$path answers $c"
done

echo "$pass passed, $failn failed"
[ "$failn" = 0 ]
