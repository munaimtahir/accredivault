#!/usr/bin/env bash
# Full redeploy: stop app services, rebuild frontend and backend from fresh codebase, redeploy, migrate, ensure superadmin.
# Use for complete redeployment when both frontend and backend (or infra) changed.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[both] Stopping frontend, backend, compliance_cron, and proxy..."
docker compose stop frontend backend compliance_cron caddy 2>/dev/null || true

echo "[both] Rebuilding frontend and backend from fresh codebase..."
docker compose build --no-cache frontend backend

echo "[both] Starting app stack (frontend, backend, compliance_cron, Caddy)..."
docker compose up -d frontend backend compliance_cron caddy

echo "[both] Waiting for backend to be healthy..."
for i in {1..30}; do
  if docker compose exec -T backend python -c "from urllib.request import urlopen; urlopen('http://localhost:8000/api/v1/health')" 2>/dev/null; then
    break
  fi
  sleep 2
done

echo "[both] Running migrations..."
docker compose exec -T backend python manage.py migrate --noinput

echo "[both] Creating/verifying superadmin (admin / admin123)..."
docker compose exec -T backend python manage.py seed_roles_and_admin

echo "[both] Done. App at http://127.0.0.1:8016 (frontend) and http://127.0.0.1:8016/api/v1 (API)"
echo "[both] Login: admin / admin123"
