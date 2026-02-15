# Deployment (Docker + Caddy + MinIO)

## Production: phc.alshifalab.pk

The app is deployed at **https://phc.alshifalab.pk**. The host Caddy config at **/home/munaim/srv/proxy/caddy/Caddyfile** routes:

- **phc.alshifalab.pk** → `127.0.0.1:8016` (API, admin, static, media, and frontend)
- **api.phc.alshifalab.pk** → `127.0.0.1:8016`

The internal stack listens on `127.0.0.1:8016`; trusted origins (ALLOWED_HOSTS, CORS, CSRF) are set so the frontend at phc.alshifalab.pk can access the backend. See root `.env.example` and `docker-compose.yml` defaults.

## Main deployment (repo root)

From the repo root (ensure `.env` exists; copy from `.env.example` if needed):

- **Full deployment (first-time or clean):** `DEPLOY_CLEAN=1 ./scripts/deploy_full.sh` — tears down stack (and volumes if `DEPLOY_CLEAN=1`), builds images, starts stack, runs migrations, creates MinIO buckets (evidence, exports), seeds roles and superadmin (admin / admin123), imports PHC standards (121 controls), recomputes control statuses, then runs verification. Use for a complete setup with no steps left behind.
- **Full stack (existing DB):** `docker compose up -d` (or `./scripts/dev.sh` for first-time build + migrations + superadmin)
- **Redeploy frontend only (dev):** `./scripts/front.sh` — stop frontend/proxy, rebuild frontend from fresh codebase, redeploy
- **Redeploy backend only (dev):** `./scripts/back.sh` — stop backend/compliance_cron/proxy, rebuild backend from fresh codebase, redeploy, migrate, create/verify superadmin (admin / admin123)
- **Full redeploy (dev):** `./scripts/both.sh` — stop app services, rebuild frontend and backend from fresh codebase, redeploy, migrate, create/verify superadmin (admin / admin123)
- **Bring up stack:** `./scripts/dev.sh` — starts all services; use `./scripts/dev.sh --build` to build images first; runs migrations and `seed_roles_and_admin` for superadmin
- **Verify deployment:** `./scripts/verify_deployment.sh` — checks Caddy /health, backend /api/v1/health, frontend root, and login with admin/admin123. Default base URL: `http://127.0.0.1:8016`. For production: `BASE_URL=https://phc.alshifalab.pk ./scripts/verify_deployment.sh` or `./scripts/verify_deployment.sh https://phc.alshifalab.pk`

Superadmin is created/verified after each backend or full deploy: **admin** / **admin123** (override via `DEFAULT_ADMIN_USERNAME` / `DEFAULT_ADMIN_PASSWORD`).

The main `docker-compose.yml` at repo root builds `./backend` and `./frontend`; internal Caddyfile is at `./infra/Caddyfile`. The stack binds to **127.0.0.1:8016**; host Caddy forwards phc.alshifalab.pk to that port.

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
