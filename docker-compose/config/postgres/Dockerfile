# Postgres for the production compose: the official image without gosu.
#
# The entrypoint runs gosu (and its su-exec link) only when the container starts as root, to drop to the postgres
# user. The production compose starts it as postgres (uid 70) with no capabilities, so gosu never runs, but Trivy
# reports about 27 HIGH/CRITICAL findings in the old Go runtime it is built with, in every tag. Nothing else changes:
# same binaries, same entrypoint, same environment variables.
#
# Built, scanned, signed and pushed by CI (job "Images") as ghcr.io/firaskhalife/fyp-grading-postgres:<this version>.
# Dependabot bumps the base within Postgres 16: a new major version needs a dump and restore of the data volumes.
FROM postgres:16.16-alpine3.24@sha256:81e77a4833487b8132fe4b00bedd39dc3f74b8641e387f19312a48f7de218c2e

# apk upgrade: Alpine's security fixes that came out after the pinned base was built (libxml2 2.13.9-r3,
# CVE-2026-86144, was the first). Patch releases within Alpine 3.24 only, so the binaries stay the same version.
RUN apk upgrade --no-cache \
 && rm -f /usr/local/bin/gosu /usr/local/bin/su-exec

USER 70:70
