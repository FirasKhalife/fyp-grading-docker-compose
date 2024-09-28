# Stage 1
FROM quay.io/keycloak/keycloak:latest as builder

WORKDIR /opt/keycloak

# for demonstration purposes only, make sure to use proper certificates in production instead
RUN keytool -genkeypair -storepass password -storetype PKCS12 -keyalg RSA -keysize 2048 -dname "CN=server" -alias server -ext "SAN:c=DNS:localhost,IP:127.0.0.1" -keystore conf/server.keystore
RUN /opt/keycloak/bin/kc.sh build

# Stage 2
FROM quay.io/keycloak/keycloak:latest
COPY --from=builder /opt/keycloak/ /opt/keycloak/

# TODO: when import ready, add "--import-realm"
ENTRYPOINT ["/opt/keycloak/bin/kc.sh", "start"]