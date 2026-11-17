#!/usr/bin/env bash
# Applies the Assay realm hardening to a running Keycloak and resets the shared demo personas (review C1, H4).
# --import-realm never updates an existing realm, so run this once after deploying a realm change, and nightly
# (cron) so a visitor who changed a persona's state can't keep it broken for more than a day.
#
# - every required action disabled (no UPDATE_PASSWORD / CONFIGURE_TOTP / webauthn via kc_action),
# - brute-force lockout off (it locks the persona for everyone, and the password is public),
# - the assay-spa client redirects only to ASSAY_SPA_ORIGIN (default http://localhost:5173),
# - personas missing from an older import are created with the export's fixed ids,
# - each persona: password reset to the public demo password, no pending required actions, no OTP or other
#   credential except the password, sessions logged out.
#
# Usage: scripts/keycloak-reset-personas.sh [container]      (default container: keycloak-server)
# Env:   KEYCLOAK_ADMIN_USER / KEYCLOAK_ADMIN_PASSWORD (default admin/admin, the local dev bootstrap admin)
#        DEMO_PASSWORD (default assay-demo)
set -euo pipefail

CONTAINER="${1:-keycloak-server}"
ADMIN_USER="${KEYCLOAK_ADMIN_USER:-admin}"
ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD:-admin}"
DEMO_PASSWORD="${DEMO_PASSWORD:-assay-demo}"
SPA_ORIGIN="${ASSAY_SPA_ORIGIN:-http://localhost:5173}"
REALM=assay
PERSONAS=(rania.haddad jane.smith john.doe michael.johnson emily.clark karim.nassar lea.mansour nour.khoury ahmad.fares)
REALM_FILE="$(cd "$(dirname "$0")" && pwd)/../docker-compose/config/keycloak/import/assay-realm.json"

kc() { docker exec "$CONTAINER" /opt/keycloak/bin/kcadm.sh "$@"; }

kc config credentials --server http://localhost:8080 --realm master --user "$ADMIN_USER" --password "$ADMIN_PASSWORD" >/dev/null

kc update "realms/$REALM" -s bruteForceProtected=false
for alias in $(kc get authentication/required-actions -r "$REALM" --fields alias --format csv --noquotes); do
  kc update "authentication/required-actions/$alias" -r "$REALM" -s enabled=false -s defaultAction=false
done
client_id="$(kc get clients -r "$REALM" -q clientId=assay-spa --fields id --format csv --noquotes)"
kc update "clients/$client_id" -r "$REALM" -s "redirectUris=[\"$SPA_ORIGIN/*\"]" -s 'webOrigins=["+"]'   -s "attributes.\"post.logout.redirect.uris\"=$SPA_ORIGIN/*"
echo "realm $REALM: required actions disabled, brute-force lockout off, assay-spa redirects to $SPA_ORIGIN"

# Personas added to the realm export after this Keycloak was first imported (e.g. ahmad.fares) are created here,
# with the export's fixed ids, which the demo seed uses. Existing users are skipped, not overwritten.
python3 - "$REALM_FILE" "${PERSONAS[@]}" <<'PY' | docker exec -i "$CONTAINER" /opt/keycloak/bin/kcadm.sh create partialImport -r "$REALM" -f - >/dev/null
import json, sys
realm = json.load(open(sys.argv[1]))
users = [u for u in realm["users"] if u["username"] in sys.argv[2:]]
print(json.dumps({"ifResourceExists": "SKIP", "users": users}))
PY

for username in "${PERSONAS[@]}"; do
  id="$(kc get users -r "$REALM" -q "username=$username" -q exact=true --fields id --format csv --noquotes)"
  [ -n "$id" ] || { echo "missing persona: $username" >&2; continue; }
  kc update "users/$id" -r "$REALM" -s 'requiredActions=[]' -s enabled=true
  while IFS=, read -r cred_id cred_type; do
    [ "$cred_type" = password ] || kc delete "users/$id/credentials/$cred_id" -r "$REALM"
  done < <(kc get "users/$id/credentials" -r "$REALM" --fields id,type --format csv --noquotes)
  kc set-password -r "$REALM" --userid "$id" --new-password "$DEMO_PASSWORD"
  kc create "users/$id/logout" -r "$REALM" >/dev/null 2>&1 || true
  echo "reset $username"
done
