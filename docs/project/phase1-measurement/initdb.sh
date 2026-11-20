#!/bin/bash
set -e
for db in notification-db rubric-db keycloak-db; do
  psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE \"$db\" OWNER \"$POSTGRES_USER\";"
done
