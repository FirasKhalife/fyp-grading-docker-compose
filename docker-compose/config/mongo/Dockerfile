# MongoDB for the production compose: the official image without gosu, js-yaml and the database tools.
#
# - gosu: the entrypoint runs it only when the container starts as root, to drop to the mongodb user. The production
#   compose starts it as mongodb (uid 999) with no capabilities, so it never runs (27 HIGH/CRITICAL findings in its
#   old Go runtime, in every tag).
# - /opt/js-yaml and /js-yaml.js (3 findings): the entrypoint loads it only to read a --config YAML file, and Assay
#   passes its settings on the command line.
# - The database tools (bsondump, mongodump, mongorestore, mongoexport, ...; 16 findings in their Go runtime and
#   x/net): nothing in the stack runs them. A backup can use a stock mongo image on the same network.
# mongosh stays: the entrypoint creates the root user with it on the first start, and the health check pings with it.
#
# Built, scanned, signed and pushed by CI (job "Images") as ghcr.io/firaskhalife/fyp-grading-mongo:<this version>.
# Dependabot bumps the base within MongoDB 7.0: a new major version needs a feature-compatibility upgrade first.
FROM mongo:7.0.48@sha256:884c055bff8b7144ca44830d01826facd3083b33c4dea44b94a1476c62de3c32

RUN rm -f /usr/local/bin/gosu /js-yaml.js \
 && rm -rf /opt/js-yaml \
 && dpkg --purge --force-depends mongodb-database-tools mongodb-org-database-tools-extra mongodb-org-tools \
 && rm -rf /var/log/* /tmp/*

USER 999:999
