#!/usr/bin/env bash
# Redeploy backend only: stop, rebuild from fresh codebase, redeploy, migrate, ensure superadmin.
# Use when only backend code was edited.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[back] Stopping backend, compliance_cron, and proxy..."
docker compose stop backend compliance_cron caddy 2>/dev/null || true

echo "[back] Rebuilding backend from fresh codebase..."
docker compose build --no-cache backend

echo "[back] Starting backend, compliance_cron, and Caddy..."
docker compose up -d backend compliance_cron caddy

echo "[back] Waiting for backend to be healthy..."
for i in {1..30}; do
  if docker compose exec -T backend python -c "from urllib.request import urlopen; urlopen('http://localhost:8000/api/v1/health')" 2>/dev/null; then
    break
  fi
  sleep 2
done

echo "[back] Running migrations..."
docker compose exec -T backend python manage.py migrate --noinput

echo "[back] Creating/verifying superadmin (admin / admin123)..."
docker compose exec -T backend python manage.py seed_roles_and_admin

echo "[back] Done. API at http://127.0.0.1:8016/api/v1"
