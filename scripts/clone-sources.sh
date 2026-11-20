#!/usr/bin/env bash
# Clones every Assay repository next to this one, which the development compose (./docker-compose.sh) builds from.
# Repositories that are already there are left alone. To run the demo without the sources, use ./run-demo.sh instead.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PARENT="$(dirname "$ROOT")"
BASE_URL="${ASSAY_GIT_BASE:-https://github.com/FirasKhalife}"

REPOS=(
  fyp-grading-admin-service
  fyp-grading-evaluation-service
  fyp-grading-notification-service
  fyp-grading-rubric-service
  fyp-grading-api-gateway
  fyp-grading-config-server
  fyp-grading-registry-server
  fyp-grading-config
  fyp-grading-frontend
)

for repo in "${REPOS[@]}"; do
  if [ -d "$PARENT/$repo" ]; then
    echo "$repo: already there"
  else
    git clone --quiet "$BASE_URL/$repo.git" "$PARENT/$repo"
    echo "$repo: cloned"
  fi
done
echo "Done. Start the development stack with: ./docker-compose.sh up -d --build"
