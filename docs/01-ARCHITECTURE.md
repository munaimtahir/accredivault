# Architecture (Single Deployment)

## Topology
- frontend (React/Vite) served via Caddy (static) or Nginx
- backend (Django/DRF) behind Caddy reverse proxy
- postgres (data)
- minio (evidence objects)
- optional: redis + celery worker (export jobs + reminders)

## Docker Compose services
- db: Postgres 16 + volume
- minio: MinIO server + volume
- backend: Django app
- frontend: optional build container; static output served by Caddy
- caddy: TLS + reverse proxy routing to backend and serving frontend static
- optional: redis, worker

## Routing through Caddy (required)
Caddy terminates HTTPS and routes:
- `/api/*` → backend container
- `/admin/*` → backend container
- `/` → frontend static build

This keeps backend bound to internal network and exposes only Caddy publicly.

## SaaS upgrade path later (not implemented now)
- Add tenant table
- Add tenant_id FK to domain tables
- Enforce row-level isolation
- Convert buckets/prefix by tenant
