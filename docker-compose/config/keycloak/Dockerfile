# Keycloak with the Assay realm (personas, roles, the SPA client) imported on first start.
# The base is pinned by digest; Dependabot proposes updates.
FROM quay.io/keycloak/keycloak:26.8.2@sha256:c68e286cacd87b942ac1939a0a1481461109d6acd3a57dc496969a319a76bbf0 AS builder
ENV KC_DB=postgres KC_HEALTH_ENABLED=true KC_METRICS_ENABLED=true
# No account console or account REST API: the demo accounts are shared, so nobody may edit them. /realms/*/account
# then answers with the theme's "page not found" error page.
ENV KC_FEATURES_DISABLED=account,account-api
RUN /opt/keycloak/bin/kc.sh build

FROM quay.io/keycloak/keycloak:26.8.2@sha256:c68e286cacd87b942ac1939a0a1481461109d6acd3a57dc496969a319a76bbf0
COPY --from=builder /opt/keycloak/ /opt/keycloak/
COPY import/ /opt/keycloak/data/import/
# The Assay login theme (realm setting loginTheme=assay). Themes are read at start, so no rebuild step is needed.
COPY themes/ /opt/keycloak/themes/
# --import-realm skips a realm that already exists, so restarts keep their state.
ENTRYPOINT ["/opt/keycloak/bin/kc.sh", "start", "--optimized", "--import-realm"]
