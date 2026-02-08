# Deployment (Docker + Caddy + MinIO)

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
