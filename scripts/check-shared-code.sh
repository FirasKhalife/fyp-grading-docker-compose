#!/usr/bin/env bash
# The services are self-contained repositories, so a few files are copied between them instead of published as a
# library: the shared plumbing under common/ (demo-session scoping, security, problem details), the lint and build
# files, and the payload fixtures under src/test/resources/contracts. This script checks the copies are identical.
#
# Usage: scripts/check-shared-code.sh [workspace]   (default: the folder holding this repo and the service repos)
# Exits non-zero and lists every difference.
set -uo pipefail

WS="${1:-$(cd "$(dirname "$0")/../.." && pwd)}"
SERVICES=(admin-service evaluation-service rubric-service notification-service)
SPRING=("${SERVICES[@]}" api-gateway config-server registry-server)
status=0

normalise() { sed -E 's/com\.fypgrading\.[a-z]+service/com.fypgrading.SERVICE/g' "$1"; }

same() { # label, files...
  local label="$1"; shift
  local first="$1"; shift
  for other in "$@"; do
    if ! diff -q <(normalise "$first") <(normalise "$other") > /dev/null; then
      echo "DIFFERENT  $label: ${first#"$WS"/} vs ${other#"$WS"/}"
      status=1
    fi
  done
}

# 1. Files every Spring repo shares.
for f in checkstyle.xml .gitattributes Dockerfile .dockerignore; do
  files=(); for r in "${SPRING[@]}"; do files+=("$WS/fyp-grading-$r/$f"); done
  same "$f" "${files[@]}"
done

# 2. The common/ package of the domain services (jpa/ only where the service uses JPA).
ref="$WS/fyp-grading-admin-service/src/main/java/com/fypgrading/adminservice/common"
while IFS= read -r rel; do
  files=()
  for r in "${SERVICES[@]}"; do
    pkg="${r/-/}"
    candidate="$WS/fyp-grading-$r/src/main/java/com/fypgrading/$pkg/common/$rel"
    [ -f "$candidate" ] && files+=("$candidate")
  done
  same "common/$rel" "${files[@]}"
done < <(cd "$ref" && find . -name '*.java' | sed 's#^\./##' | sort)

# 3. Payload fixtures and their test helper: every repo that has a fixture has the same one.
declare -A seen
for r in "${SERVICES[@]}"; do
  dir="$WS/fyp-grading-$r/src/test/resources/contracts"
  [ -d "$dir" ] || continue
  for f in "$dir"/*.json; do
    name="$(basename "$f")"
    if [ -n "${seen[$name]:-}" ]; then same "contracts/$name" "${seen[$name]}" "$f"; else seen[$name]="$f"; fi
  done
done
helpers=(); for r in "${SERVICES[@]}"; do
  h="$WS/fyp-grading-$r/src/test/java/com/fypgrading/${r/-/}/contracts/Contracts.java"
  [ -f "$h" ] && helpers+=("$h")
done
same "contracts/Contracts.java" "${helpers[@]}"

if [ "$status" = 0 ]; then echo "Shared code, build files and payload fixtures are identical across the repos."; fi
exit "$status"
