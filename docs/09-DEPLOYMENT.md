# Deployment (Docker + Caddy + MinIO)

## Main deployment (repo root)

From the repo root:

- **Full stack:** `docker compose up -d` (or `./scripts/dev.sh` for first-time build + migrations + superadmin)
- **Redeploy frontend only (dev):** `./scripts/front.sh` — stop frontend/proxy, rebuild frontend from fresh codebase, redeploy
- **Redeploy backend only (dev):** `./scripts/back.sh` — stop backend/compliance_cron/proxy, rebuild backend from fresh codebase, redeploy, migrate, create/verify superadmin (admin / admin123)
- **Full redeploy (dev):** `./scripts/both.sh` — stop app services, rebuild frontend and backend from fresh codebase, redeploy, migrate, create/verify superadmin (admin / admin123)
- **Bring up stack:** `./scripts/dev.sh` — starts all services; use `./scripts/dev.sh --build` to build images first; runs migrations and `seed_roles_and_admin` for superadmin
- **Verify deployment:** `./scripts/verify_deployment.sh` — checks Caddy /health, backend /api/v1/health, frontend root, and login with admin/admin123

Superadmin is created/verified after each backend or full deploy: **admin** / **admin123** (override via `DEFAULT_ADMIN_USERNAME` / `DEFAULT_ADMIN_PASSWORD`).

The main `docker-compose.yml` at repo root builds `./backend` and `./frontend`; Caddyfile is at `./infra/Caddyfile`. App is served at **http://127.0.0.1:8016**.

## Host Caddy (optional)

If using a host-level Caddy in front of the internal stack, add:

```
accv.alshifalab.pk {
  reverse_proxy 127.0.0.1:8016
}
```

This forwards traffic to the internal Caddy container (port 8016).

## Services
- Postgres 16
- MinIO
- Django backend
- Caddy reverse proxy
Optional: Redis + worker

## Routing through Caddy
- /api/* and /admin/* → backend
- / → frontend static

## Backups (mandatory)
- Nightly pg_dump
- Nightly MinIO data directory snapshot
- Offsite copy
- Periodic restore drills
