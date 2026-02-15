#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INFRA_DIR="$ROOT_DIR/infra"
API_BASE="http://127.0.0.1:8016/api/v1"

cd "$INFRA_DIR"

PASS() { echo "PASS: $*"; }
FAIL() { echo "FAIL: $*"; exit 1; }

echo "========================================="
echo "AccrediVault Prompt 3 (Auth + RBAC)"
echo "========================================="

echo "[1/9] Starting services..."
docker compose up -d --build 2>/dev/null || true
sleep 5

echo "[2/9] Applying migrations..."
docker compose exec -T backend python manage.py migrate --noinput

# Ensure controls exist for RBAC tests
CONTROL_COUNT=$(docker compose exec -T backend python manage.py shell -c "
from apps.standards.models import Control
print(Control.objects.count())
" 2>/dev/null | tr -d '\r\n ' || echo "0")
if [ "${CONTROL_COUNT:-0}" = "0" ]; then
  echo "Importing PHC controls..."
  docker compose exec -T backend python manage.py import_phc_csv \
    --path apps/standards/seed_data/phc/Final_PHC_list.csv \
    --pack-version 1.0 \
    --publish 2>/dev/null || true
fi

echo "[3/9] Seeding roles and admin user..."
docker compose exec -T backend python manage.py seed_roles_and_admin

echo "[4/9] Login to obtain access token..."
TMP_LOGIN=$(mktemp)
curl -sS -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin12345"}' > "$TMP_LOGIN"

ACCESS=$(python3 -c "import json,sys; d=json.load(open('$TMP_LOGIN')); print(d.get('access',''))" 2>/dev/null || true)
rm -f "$TMP_LOGIN"

if [ -z "$ACCESS" ]; then
  FAIL "Could not obtain access token from login"
fi
PASS "Login successful, token obtained"

echo "[5/9] Calling protected endpoint with token..."
CONTROLS_RESP=$(curl -sS -w "\n%{http_code}" "$API_BASE/controls/" -H "Authorization: Bearer $ACCESS")
HTTP_CODE=$(echo "$CONTROLS_RESP" | tail -n1)
BODY=$(echo "$CONTROLS_RESP" | sed '$d')
[ "$HTTP_CODE" = "200" ] || FAIL "GET /controls/ returned $HTTP_CODE (expected 200)"
PASS "GET /controls/ with token returns 200"

echo "[6/9] Creating VIEWER user via admin token..."
TMP_VIEWER=$(mktemp)
curl -sS -w "\n%{http_code}" -X POST "$API_BASE/users" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"username":"viewer_test","password":"viewer12345","roles":["VIEWER"]}' > "$TMP_VIEWER"
VIEWER_HTTP=$(tail -n1 "$TMP_VIEWER")
[ "$VIEWER_HTTP" = "201" ] || FAIL "Create VIEWER user returned $VIEWER_HTTP"
rm -f "$TMP_VIEWER"

TMP_LV=$(mktemp)
curl -sS -X POST "$API_BASE/auth/login" -H "Content-Type: application/json" \
  -d '{"username":"viewer_test","password":"viewer12345"}' > "$TMP_LV"
ACCESS_VIEWER=$(python3 -c "import json; print(json.load(open('$TMP_LV')).get('access',''))")
rm -f "$TMP_LV"

VIEWER_CONTROLS=$(curl -sS -w "\n%{http_code}" "$API_BASE/controls/" -H "Authorization: Bearer $ACCESS_VIEWER")
[ "$(echo "$VIEWER_CONTROLS" | tail -n1)" = "200" ] || FAIL "VIEWER GET /controls/ should return 200"

VIEWER_EVIDENCE=$(curl -sS -w "\n%{http_code}" -X POST "$API_BASE/evidence-items" \
  -H "Authorization: Bearer $ACCESS_VIEWER" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","category":"policy","event_date":"2024-01-01"}')
[ "$(echo "$VIEWER_EVIDENCE" | tail -n1)" = "403" ] || FAIL "VIEWER POST /evidence-items/ should return 403"
PASS "VIEWER: can read controls, cannot create evidence (403)"

echo "[7/9] Creating DATA_ENTRY user..."
curl -sS -X POST "$API_BASE/users" -H "Authorization: Bearer $ACCESS" -H "Content-Type: application/json" \
  -d '{"username":"dataentry_test","password":"de12345678","roles":["DATA_ENTRY"]}' >/dev/null

LOGIN_DE=$(curl -sS -X POST "$API_BASE/auth/login" -H "Content-Type: application/json" \
  -d '{"username":"dataentry_test","password":"de12345678"}')
ACCESS_DE=$(echo "$LOGIN_DE" | python3 -c "import json,sys; print(json.load(sys.stdin).get('access',''))")

CONTROL_ID=$(docker compose exec -T backend python manage.py shell -c "
from apps.standards.models import Control
c=Control.objects.first()
print(c.id if c else '')
" 2>/dev/null | tr -d '\r\n ')
[ -n "$CONTROL_ID" ] || CONTROL_ID=1

EVID_DE=$(curl -sS -X POST "$API_BASE/evidence-items" -H "Authorization: Bearer $ACCESS_DE" \
  -H "Content-Type: application/json" \
  -d '{"title":"DE Test","category":"policy","event_date":"2024-01-01"}')
EVID_ID=$(echo "$EVID_DE" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('id',''))")
[ -n "$EVID_ID" ] || FAIL "DATA_ENTRY should create evidence"

VERIFY_DE=$(curl -sS -w "\n%{http_code}" -X POST "$API_BASE/controls/$CONTROL_ID/verify" \
  -H "Authorization: Bearer $ACCESS_DE" -H "Content-Type: application/json" -d '{"remarks":"ok"}')
[ "$(echo "$VERIFY_DE" | tail -n1)" = "403" ] || FAIL "DATA_ENTRY POST /verify should return 403"
PASS "DATA_ENTRY: can create evidence, cannot verify (403)"

echo "[8/9] Creating MANAGER user..."
curl -sS -X POST "$API_BASE/users" -H "Authorization: Bearer $ACCESS" -H "Content-Type: application/json" \
  -d '{"username":"manager_test","password":"manager1234","roles":["MANAGER"]}' >/dev/null

LOGIN_MGR=$(curl -sS -X POST "$API_BASE/auth/login" -H "Content-Type: application/json" \
  -d '{"username":"manager_test","password":"manager1234"}')
ACCESS_MGR=$(echo "$LOGIN_MGR" | python3 -c "import json,sys; print(json.load(sys.stdin).get('access',''))")

VERIFY_MGR=$(curl -sS -w "\n%{http_code}" -X POST "$API_BASE/controls/$CONTROL_ID/verify" \
  -H "Authorization: Bearer $ACCESS_MGR" -H "Content-Type: application/json" -d '{"remarks":"verified"}')
[ "$(echo "$VERIFY_MGR" | tail -n1)" = "201" ] || [ "$(echo "$VERIFY_MGR" | tail -n1)" = "200" ] || FAIL "MANAGER verify should return 200/201"

EXPORT_MGR=$(curl -sS -w "\n%{http_code}" -X POST "$API_BASE/exports/control/$CONTROL_ID" \
  -H "Authorization: Bearer $ACCESS_MGR" -H "Content-Type: application/json" -d '{}')
[ "$(echo "$EXPORT_MGR" | tail -n1)" = "201" ] || [ "$(echo "$EXPORT_MGR" | tail -n1)" = "200" ] || FAIL "MANAGER export should return 200/201"
PASS "MANAGER: can verify and export"

echo "[9/9] Health endpoint remains public (AllowAny)..."
HEALTH_CODE=$(curl -sS -o /dev/null -w "%{http_code}" "$API_BASE/health")
[ "$HEALTH_CODE" = "200" ] || FAIL "GET /health without auth should return 200"
PASS "Health endpoint accessible without auth"

echo ""
echo "========================================="
echo "Prompt 3 verification PASSED"
echo "========================================="
exit 0
