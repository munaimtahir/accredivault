#!/usr/bin/env bash
# Full deployment: tear down, build, bring up stack, migrate, create buckets, seed roles/admin,
# import PHC standards, recompute control statuses, verify. Use for first-time or clean redeploy.
# Optional: DEPLOY_CLEAN=1 to remove volumes (wipes DB and MinIO data). BASE_URL for verify (default http://127.0.0.1:8016; set to https://phc.alshifalab.pk to check public URL).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Optional: clean slate (removes volumes)
if [ "${DEPLOY_CLEAN:-0}" = "1" ]; then
  echo "[deploy] Cleaning existing containers and volumes..."
  docker compose down -v
else
  echo "[deploy] Stopping existing containers..."
  docker compose down
fi

echo "[deploy] Building images (no cache)..."
docker compose build --no-cache frontend backend

echo "[deploy] Starting stack..."
docker compose up -d

echo "[deploy] Waiting for DB and MinIO..."
sleep 5
for i in {1..30}; do
  if docker compose exec -T db pg_isready -U "${DB_USER:-accredvault}" -d "${DB_NAME:-accredvault}" 2>/dev/null; then
    break
  fi
  sleep 2
done

echo "[deploy] Waiting for backend to be healthy..."
for i in {1..60}; do
  if docker compose exec -T backend python -c "from urllib.request import urlopen; urlopen('http://localhost:8000/api/v1/health')" 2>/dev/null; then
    break
  fi
  sleep 2
done

echo "[deploy] Running migrations..."
docker compose exec -T backend python manage.py migrate --noinput

echo "[deploy] Ensuring MinIO buckets (evidence, exports)..."
docker compose exec -T backend python manage.py ensure_minio_buckets

echo "[deploy] Creating/verifying superadmin (admin / admin123)..."
docker compose exec -T backend python manage.py seed_roles_and_admin

echo "[deploy] Importing PHC standards..."
docker compose exec -T backend python manage.py import_phc_csv \
  --path apps/standards/seed_data/phc/Final_PHC_list.csv \
  --pack-version 1.0 \
  --publish

echo "[deploy] Recomputing control statuses..."
docker compose exec -T backend python manage.py recompute_control_statuses --latest

BASE_URL="${BASE_URL:-http://127.0.0.1:8016}"
echo "[deploy] Verifying deployment at ${BASE_URL}..."
"$ROOT/scripts/verify_deployment.sh" "$BASE_URL"

echo "[deploy] Done. App: ${BASE_URL}  Login: admin / admin123"
