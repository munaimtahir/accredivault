#!/usr/bin/env bash
# Verify deployment: Caddy routing (frontend + backend public access) and login with admin/admin123.
set -euo pipefail
BASE="${1:-http://127.0.0.1:8016}"
API="${BASE}/api/v1"

echo "[verify] Checking Caddy proxy health..."
curl -sf "${BASE}/health" >/dev/null && echo "  OK /health" || { echo "  FAIL /health"; exit 1; }

echo "[verify] Checking backend API health..."
curl -sf "${API}/health" >/dev/null && echo "  OK ${API}/health" || { echo "  FAIL ${API}/health"; exit 1; }

echo "[verify] Checking frontend (root)..."
code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}/")
if [ "$code" = "200" ]; then
  echo "  OK ${BASE}/ (200)"
else
  echo "  FAIL ${BASE}/ (got $code)"
  exit 1
fi

echo "[verify] Checking login with admin / admin123..."
resp=$(curl -sf -X POST "${API}/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}')
if echo "$resp" | grep -q '"access"'; then
  echo "  OK login returned access token"
else
  echo "  FAIL login response: $resp"
  exit 1
fi

echo "[verify] All checks passed. Frontend and backend are reachable; admin/admin123 works."
