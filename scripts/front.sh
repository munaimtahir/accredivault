#!/usr/bin/env bash
# Redeploy frontend only: stop, rebuild from fresh codebase, redeploy.
# Use when only frontend code was edited.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "[front] Stopping frontend and proxy..."
docker compose stop frontend caddy 2>/dev/null || true

echo "[front] Rebuilding frontend from fresh codebase..."
docker compose build --no-cache frontend

echo "[front] Starting frontend and Caddy..."
docker compose up -d frontend caddy

echo "[front] Done. App at http://127.0.0.1:8016"
