#!/bin/bash
# Probe gateway endpoints (optionally with TOKEN env) for the Phase 2 UI audit.
H=(); [ -n "$TOKEN" ] && H=(-H "Authorization: Bearer $TOKEN")
for p in "$@"; do echo "== $p"; curl -s "${H[@]}" -w ' [%{http_code}]' "localhost:9191/api/$p" | head -c ${MAX:-800}; echo; done
