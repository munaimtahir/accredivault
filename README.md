# AccrediVault — Enterprise Blueprint Pack (Single Deployment)

This repository contains the complete **enterprise-level blueprint** for **AccrediVault** (PHC-first evidence platform),
designed for **single deployment (one organization per install)** with a clean upgrade path to SaaS later.

## Locked decisions
- **Single deployment** now (one lab / one organization per install)
- **Evidence storage:** MinIO (S3-compatible), self-hosted
- **PDF engine:** ReportLab (print-perfect, inspector-ready)
- **Reverse proxy:** **Caddy** (route traffic to Docker services, TLS/HTTPS)

## Contents
- `docs/` — full blueprint pack (architecture, data model, APIs, exports, security, deployment, tests, roadmap, AI-bridge schema)
- `infra/` — Docker Compose skeleton + Caddyfile example + env examples

## Next step
Use the blueprint to implement the MVP:
1) Import PHC CSV as a StandardPack (draft → publish)
2) Evidence + Rules engine → computed status
3) Print/Export engine (Control PDF, Section Pack, Full Pack)
4) Verification + Audit trail
