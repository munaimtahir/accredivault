#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [ "${1:-}" = "--build" ] || [ "${1:-}" = "-b" ]; then
  echo "[dev] Building all images..."
  docker compose build
fi
echo "[dev] Starting stack..."
docker compose up -d
echo "[dev] Running migrations..."
sleep 10
docker compose exec -T backend python manage.py migrate --noinput 2>/dev/null || true
echo "[dev] Creating/verifying superadmin (admin / admin123)..."
docker compose exec -T backend python manage.py seed_roles_and_admin 2>/dev/null || true
echo "[dev] Done. App at http://127.0.0.1:8016 (login: admin / admin123)"
