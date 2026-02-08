# Security

Roles:
- Owner/Admin: all
- Compliance Manager: rules, verify, exports
- Staff: upload/link evidence, view controls
- Verifier: verify/reject, view evidence
- Auditor: read-only, download exports

Evidence access:
- Signed URLs (time-limited)
- No direct MinIO credentials exposed

Audit:
- Append-only AuditEvent for all sensitive actions
