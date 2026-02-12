#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
INFRA_DIR="$ROOT_DIR/infra"
API_BASE="http://127.0.0.1:8016/api/v1"

cd "$INFRA_DIR"

echo "==================================="
echo "AccrediVault Prompt 2 Verification"
echo "==================================="

echo "[1/7] Ensuring services are up..."
docker compose up -d --build

echo "[2/7] Applying migrations..."
docker compose exec -T backend python manage.py migrate --noinput

CONTROL_COUNT=$(docker compose exec -T backend python manage.py shell << 'PY'
from apps.standards.models import Control
print(Control.objects.count())
PY
)
CONTROL_COUNT=$(echo "$CONTROL_COUNT" | tr -d '\r\n ')
if [ "$CONTROL_COUNT" = "0" ]; then
  echo "[3/7] No controls found. Importing PHC checklist..."
  docker compose exec -T backend python manage.py import_phc_csv \
    --path apps/standards/seed_data/phc/Final_PHC_list.csv \
    --pack-version 1.0 \
    --publish
else
  echo "[3/7] Controls already present ($CONTROL_COUNT)."
fi

echo "[4/7] Recomputing statuses for latest pack..."
docker compose exec -T backend python manage.py recompute_control_statuses --latest

CONTROL_ID=$(docker compose exec -T backend python manage.py shell << 'PY'
from apps.standards.models import Control
c = Control.objects.order_by('id').first()
print(c.id if c else '')
PY
)
CONTROL_ID=$(echo "$CONTROL_ID" | tr -d '\r\n ')
if [ -z "$CONTROL_ID" ]; then
  echo "No control found. Import standards first (e.g. import_phc_csv)."
  exit 1
fi

echo "Using control_id=$CONTROL_ID"

echo "[5/7] Creating and linking evidence via API..."
TODAY=$(date -u +%F)
EVIDENCE_PAYLOAD=$(cat <<JSON
{"title":"Prompt2 Verification Evidence","category":"policy","event_date":"$TODAY","notes":"Created by verify_prompt2.sh"}
JSON
)
EVIDENCE_RESP=$(curl -sS -X POST "$API_BASE/evidence-items" -H "Content-Type: application/json" -d "$EVIDENCE_PAYLOAD")
EVIDENCE_ID=$(python3 - <<PY
import json
obj=json.loads('''$EVIDENCE_RESP''')
print(obj.get('id',''))
PY
)
if [ -z "$EVIDENCE_ID" ]; then
  echo "Failed to create evidence item"
  echo "$EVIDENCE_RESP"
  exit 1
fi

LINK_PAYLOAD=$(cat <<JSON
{"evidence_item_id":"$EVIDENCE_ID","note":"prompt2 verification link"}
JSON
)
LINK_RESP=$(curl -sS -X POST "$API_BASE/controls/$CONTROL_ID/link-evidence" -H "Content-Type: application/json" -d "$LINK_PAYLOAD")
python3 - <<PY
import json
obj=json.loads('''$LINK_RESP''')
assert obj.get('id'), 'Link creation failed'
print('Link created:', obj['id'])
PY

echo "[6/7] Checking computed control status endpoint..."
STATUS_RESP=$(curl -sS "$API_BASE/controls/$CONTROL_ID/status")
python3 - <<PY
import json
obj=json.loads('''$STATUS_RESP''')
assert obj.get('computed_status') in {'NOT_STARTED','IN_PROGRESS','READY','VERIFIED','OVERDUE'}, f"Unexpected status payload: {obj}"
print('Computed status:', obj['computed_status'])
PY

echo "[7/7] Generating export and validating download URL..."
EXPORT_RESP=$(curl -sS -X POST "$API_BASE/exports/control/$CONTROL_ID" -H "Content-Type: application/json" -d '{}')
JOB_ID=$(python3 - <<PY
import json
obj=json.loads('''$EXPORT_RESP''')
job=obj.get('job',{})
assert job.get('status')=='COMPLETED', f"Export not completed: {obj}"
assert obj.get('download',{}).get('url'), f"Missing download URL: {obj}"
print(job.get('id',''))
PY
)
JOB_ID=$(echo "$JOB_ID" | tr -d '\r\n ')

DOWNLOAD_RESP=$(curl -sS "$API_BASE/exports/$JOB_ID/download")
python3 - <<PY
import json
obj=json.loads('''$DOWNLOAD_RESP''')
assert obj.get('url'), f"Missing presigned URL: {obj}"
assert obj.get('expires_in')==600, f"Unexpected expires_in: {obj}"
print('Download endpoint OK')
PY

echo "==================================="
echo "Prompt 2 verification passed"
echo "==================================="
