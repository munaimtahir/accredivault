# Domain Model (MVP)

## StandardPack
- authority_code (PHC)
- name
- version
- status: draft → published → archived
- checksum, published_at, source_file_name

## Control (immutable after publish)
- control_code (e.g., PHC-ROM-001)
- section, standard, indicator, sort_order

## EvidenceItem
- title, category, subtype, notes
- event_date (what date it represents)
- valid_from, valid_until (expiry evidence)

## EvidenceFile
- bucket, object_key, filename, content_type, sha256, size_bytes

## ControlEvidenceLink
- control ↔ evidence many-to-many

## EvidenceRule (per control)
- rule_type: ONE_TIME / ROLLING_WINDOW / EXPIRY / COUNT_IN_WINDOW
- window_days, min_items
- frequency (optional)
- requires_verification
- acceptable_categories/subtypes

## Verification
- control_id, status VERIFIED/REJECTED, verified_by, verified_at, remarks

## ControlStatus (computed; optionally cached)
- computed_status: NOT_STARTED / IN_PROGRESS / READY / OVERDUE / VERIFIED
- last_evidence_date, next_due_date

## AuditEvent (append-only)
- actor, action, entity_type, entity_id, before/after JSON, created_at

## ExportJob
- job_type: CONTROL_PDF / SECTION_PACK / FULL_PACK
- filters JSON, status, output location, errors
