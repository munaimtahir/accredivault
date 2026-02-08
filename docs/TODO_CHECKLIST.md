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

## Prompt 1 (Evidence Management) - 🔜 NEXT

### Backend Models
- [ ] EvidenceItem model
  - [ ] title, category, subtype, notes
  - [ ] event_date, valid_from, valid_until
  - [ ] created_by, created_at
- [ ] EvidenceFile model
  - [ ] bucket, object_key, filename
  - [ ] content_type, sha256, size_bytes
  - [ ] uploaded_by, uploaded_at
- [ ] ControlEvidenceLink model
  - [ ] control FK, evidence FK
  - [ ] linked_by, linked_at

### Backend Features
- [ ] File upload to MinIO
- [ ] File download from MinIO
- [ ] Evidence CRUD endpoints
- [ ] Link evidence to controls
- [ ] Unlink evidence from controls
- [ ] Evidence timeline/history view
- [ ] File type validation (PDF, images, documents)
- [ ] File size limits
- [ ] SHA256 checksum generation
- [ ] Evidence search and filtering

### Frontend Features
- [ ] Evidence upload form
- [ ] File drag-and-drop
- [ ] Evidence list view
- [ ] Evidence detail view
- [ ] Link evidence to control
- [ ] Evidence preview/download
- [ ] Evidence timeline
- [ ] Upload progress indicator
- [ ] File type icons

### Admin Interface
- [ ] Register EvidenceItem
- [ ] Register EvidenceFile
- [ ] Register ControlEvidenceLink
- [ ] Read-only fields for checksums
- [ ] Filter by category, date ranges

### Testing
- [ ] Evidence upload/download tests
- [ ] MinIO integration tests
- [ ] Evidence linking tests
- [ ] File validation tests
- [ ] API endpoint tests

---

## Prompt 2 (Evidence Rules & PDF Export) - 📅 FUTURE

### Evidence Rules Engine
- [ ] EvidenceRule model
  - [ ] rule_type (ONE_TIME, ROLLING_WINDOW, EXPIRY, COUNT_IN_WINDOW)
  - [ ] window_days, min_items
  - [ ] frequency, requires_verification
  - [ ] acceptable_categories/subtypes
- [ ] Rule evaluation engine
- [ ] Compute control status based on rules
- [ ] Status: NOT_STARTED, IN_PROGRESS, READY, OVERDUE, VERIFIED

### PDF Export (ReportLab)
- [ ] ExportJob model
  - [ ] job_type (CONTROL_PDF, SECTION_PACK, FULL_PACK)
  - [ ] filters JSON, status, output location
- [ ] Single control PDF export
- [ ] Section pack PDF export
- [ ] Full pack PDF export
- [ ] PDF generation with ReportLab
- [ ] Background job processing (Celery + Redis)
- [ ] Export history and download

### Verification
- [ ] Verification model
  - [ ] control_id, status (VERIFIED/REJECTED)
  - [ ] verified_by, verified_at, remarks
- [ ] Verification workflow
- [ ] Verification history

### ControlStatus (Computed/Cached)
- [ ] ControlStatus model or computed property
  - [ ] computed_status
  - [ ] last_evidence_date
  - [ ] next_due_date
- [ ] Status recomputation triggers
- [ ] Caching strategy

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
✅ Prompt 0 (MVP Scaffold) is **COMPLETE** and all verification tests are **PASSING**.

The system is ready for Prompt 1: Evidence management implementation.

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
