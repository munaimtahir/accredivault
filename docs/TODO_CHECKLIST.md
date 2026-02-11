# AccrediVault - TODO Checklist

## Prompt 0 (MVP Scaffold) - ✅ COMPLETED

### Backend
- [x] Django 5 project setup with Python 3.12
- [x] Apps: standards, users, audit
- [x] StandardPack model with immutability
- [x] Control model with immutability
- [x] import_phc_csv management command
- [x] Django admin for StandardPack and Control
- [x] REST API endpoint for controls (GET /api/v1/controls)
- [x] Health check endpoint
- [x] django-storages + boto3 MinIO configuration
- [x] 121 PHC controls imported successfully

### Frontend
- [x] React + TypeScript + Vite setup
- [x] Login placeholder page
- [x] Controls listing page with filters
- [x] API integration
- [x] Environment configuration

### Infrastructure
- [x] Docker Compose with all services
- [x] PostgreSQL 16
- [x] MinIO object storage
- [x] Caddy reverse proxy with HTTPS
- [x] Internal networking (only Caddy exposed)
- [x] Production Caddyfile template

### Documentation
- [x] RUNBOOK.md
- [x] MVP_IMPLEMENTATION_SUMMARY.md
- [x] Seed data README
- [x] Automated verification script

### Testing
- [x] All services running
- [x] API returning 121 controls
- [x] Frontend accessible
- [x] Admin accessible
- [x] Health checks passing
- [x] Immutability enforced

---

## Prompt 1 (Evidence Management) - ✅ COMPLETED

### Backend Models
- [x] EvidenceItem model
  - [x] title, category, subtype, notes
  - [x] event_date, valid_from, valid_until
  - [x] created_by, created_at
- [x] EvidenceFile model
  - [x] bucket, object_key, filename
  - [x] content_type, sha256, size_bytes
  - [x] uploaded_at
- [x] ControlEvidenceLink model
  - [x] control FK, evidence item FK
  - [x] linked_by, linked_at

### Backend Features
- [x] File upload to MinIO
- [x] Signed file download from MinIO (10 min expires)
- [x] Evidence creation endpoint
- [x] Link evidence to controls
- [x] Unlink evidence from controls
- [x] Evidence timeline/history view
- [x] SHA256 checksum generation during upload
- [x] Audit Event logging for all evidence actions

### Frontend Features
- [x] Premium Control Detail view (integrated in dashboard)
- [x] Evidence upload form with multi-file support
- [x] Evidence timeline with file list
- [x] File download functionality via presigned URLs
- [x] Responsive layout with glassmorphism touches
- [x] Modern typography and Inter font integration
- [x] Empty state handling for timeline

### Admin Interface
- [x] Register EvidenceItem, EvidenceFile, ControlEvidenceLink
- [x] Basic filters and search for evidence
- [x] Audit log viewing

### Testing
- [x] Evidence lifecycle tests (create, upload, link, timeline)
- [x] Signed download URL verification
- [x] All 4 evidence backend tests passing
- [x] Verified re-import with strict codes (1.0+codes1)

---

## Prompt 2 (Evidence Rules & PDF Export) - ✅ COMPLETED

### Evidence Rules Engine
- [x] EvidenceRule model
  - [x] rule_type (ONE_TIME, FREQUENCY, ROLLING_WINDOW, EXPIRY, COUNT_IN_WINDOW)
  - [x] window_days, min_items
  - [x] frequency, requires_verification
  - [x] acceptable_categories/subtypes
- [x] Rule evaluation engine
- [x] Compute control status based on rules
- [x] Status: NOT_STARTED, IN_PROGRESS, READY, OVERDUE, VERIFIED

### PDF Export (ReportLab)
- [x] ExportJob model
  - [x] job_type (CONTROL_PDF, SECTION_PACK, FULL_PACK)
  - [x] filters JSON, status, output location
- [x] Single control PDF export
- [ ] Section pack PDF export
- [ ] Full pack PDF export
- [x] PDF generation with ReportLab
- [x] Synchronous processing (no Celery/Redis in Prompt 2)
- [x] Export history and download

### Verification
- [x] Verification model
  - [x] control_id, status (VERIFIED/REJECTED)
  - [x] verified_by, verified_at, remarks
- [x] Verification workflow
- [x] Verification history

### ControlStatus (Computed/Cached)
- [x] ControlStatusCache model
  - [x] computed_status
  - [x] last_evidence_date
  - [x] next_due_date
- [x] Status recomputation triggers
- [x] Caching strategy

---

## Prompt 3 (Auth, Audit, Polish) - 📅 FUTURE

### Authentication & Authorization
- [ ] JWT token authentication
- [ ] User registration
- [ ] Login/logout endpoints
- [ ] Role-based permissions
- [ ] Password reset
- [ ] Frontend auth state management

### Audit Logging
- [ ] Audit log creation on all changes
- [ ] Actor capture (user + IP + user agent)
- [ ] Before/after JSON snapshots
- [ ] Audit log API endpoints
- [ ] Audit log viewing in admin
- [ ] Audit log filtering and search

### UI Polish
- [ ] Dashboard with summary stats
- [ ] Control detail page
- [ ] Section overview pages
- [ ] Progress indicators
- [ ] Responsive design improvements
- [ ] Error handling and user feedback
- [ ] Loading states
- [ ] Toast notifications

### Production Readiness
- [ ] Environment-based configuration
- [ ] Production SECRET_KEY generation
- [ ] ALLOWED_HOSTS configuration
- [ ] DEBUG=False in production
- [ ] Proper logging configuration
- [ ] Error monitoring (Sentry)
- [ ] Performance optimization
- [ ] Database indexing review

---

## Prompt 4 (SaaS & Multi-tenancy) - 📅 OPTIONAL

### Multi-tenancy
- [ ] Tenant model
- [ ] tenant_id FK on all domain tables
- [ ] Row-level security
- [ ] Tenant isolation
- [ ] Per-tenant MinIO buckets/prefixes
- [ ] Tenant registration
- [ ] Tenant admin panel

### SaaS Features
- [ ] Subscription plans
- [ ] Usage limits
- [ ] Billing integration
- [ ] Tenant analytics
- [ ] White-labeling options

---

## Quality Assurance (Ongoing)

### Code Quality
- [ ] Unit tests (backend)
- [ ] Integration tests (backend)
- [ ] E2E tests (frontend)
- [ ] Code coverage > 80%
- [ ] Linting (flake8, pylint)
- [ ] Type checking (mypy)
- [ ] Frontend linting (ESLint)
- [ ] Security scanning

### Documentation
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Architecture diagrams
- [ ] Deployment guide
- [ ] User manual
- [ ] Developer guide
- [ ] Changelog

### Performance
- [ ] Database query optimization
- [ ] API response time monitoring
- [ ] Frontend bundle size optimization
- [ ] Lazy loading
- [ ] Caching strategy
- [ ] CDN for static assets

---

## Notes

### Current Status
✅ Prompt 0 (MVP Scaffold) is **COMPLETE**.  
✅ Prompt 1 (Evidence management) is **COMPLETE**.  
✅ Prompt 2 (Rules, verification, and control PDF export) is **COMPLETE**.

### Key Achievements
- Full stack deployment working
- 121 PHC controls imported
- Immutability enforced
- API functional
- Frontend operational
- Admin interface accessible
- Health checks passing
- Automated verification in place

### Technical Debt
- None identified in Prompt 0 scope
- Static files committed (will be added to .gitignore)
- Production settings need hardening (planned for Prompt 3)

### Known Issues
- None blocking - MVP is fully functional
- Self-signed cert for localhost (expected for dev)
