# Deployment (Docker + Caddy + MinIO)

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
