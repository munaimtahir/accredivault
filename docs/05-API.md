# API (v1)

Base: /api/v1

Auth
- POST /auth/login
- POST /auth/refresh
- POST /auth/logout

Standard Packs
- GET /standard-packs
- POST /standard-packs/import (CSV upload)
- POST /standard-packs/{id}/publish

Controls
- GET /controls?section=&status=&q=
- GET /controls/{id}
- GET /controls/{id}/timeline

Evidence
- POST /evidence-items
- POST /evidence-items/{id}/files
- GET /evidence-items?category=&from=&to=
- POST /controls/{id}/link-evidence
- DELETE /controls/{id}/unlink-evidence/{link_id}

Rules
- GET /controls/{id}/rule
- PUT /controls/{id}/rule
- POST /controls/rules/bulk

Verification
- POST /controls/{id}/verify

Status
- GET /status/summary
- POST /status/recompute

Exports
- POST /exports
- GET /exports
- GET /exports/{id}
- GET /exports/{id}/download

Audit
- GET /audit?entity_type=&entity_id=
