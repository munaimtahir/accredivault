# AccrediVault — PHC Lab Licensing Evidence Platform

[![Status](https://img.shields.io/badge/Status-MVP_Complete-success)]()
[![Python](https://img.shields.io/badge/Python-3.12-blue)]()
[![Django](https://img.shields.io/badge/Django-5.0-green)]()
[![React](https://img.shields.io/badge/React-18-blue)]()
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)]()

**AccrediVault** is an enterprise-grade evidence management platform for PHC (Primary Healthcare) Lab Licensing compliance. It provides a complete solution for tracking, managing, and verifying compliance evidence against regulatory standards.

## ✨ Features (MVP - Prompt 0)

### ✅ Standards Management
- Import checklist controls from CSV files
- 121 PHC Lab Licensing controls organized by sections
- Immutable published standards (cannot edit after publish)
- Version control with checksum-based idempotency
- Automatic control code generation (PHC-{SECTION}-{NNN})

### ✅ API & Admin Interface
- RESTful API with filtering and search
- Django admin interface for standards management
- Health check endpoint (DB + MinIO connectivity)
- CORS-enabled for frontend integration

### ✅ Frontend Application
- React + TypeScript + Vite
- Controls listing with section filtering
- Text search across controls
- Responsive design
- Login placeholder (auth in Prompt 1)

### ✅ Infrastructure
- Docker Compose deployment
- PostgreSQL 16 database
- MinIO S3-compatible object storage
- Caddy reverse proxy with automatic HTTPS
- Internal networking (only Caddy exposed)

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Git
- Ports 80 and 443 available

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/munaimtahir/accredivault.git
   cd accredivault/infra
   ```

2. **Start all services**
   ```bash
   docker compose up -d --build
   ```

3. **Run database migrations**
   ```bash
   docker compose exec backend python manage.py migrate
   ```

4. **Create admin user**
   ```bash
   docker compose exec backend python manage.py createsuperuser
   ```

5. **Import PHC checklist**
   ```bash
   docker compose exec backend python manage.py import_phc_csv \
     --path apps/standards/seed_data/phc/Final_PHC_list.csv \
     --pack-version 1.0 \
     --publish
   ```

6. **Verify deployment**
   ```bash
   ../scripts/verify_mvp.sh
   ```

### Access the Application

- **Frontend**: https://localhost/
- **Admin Panel**: https://localhost/admin/ (use credentials from step 4)
- **API**: https://localhost/api/v1/controls/
- **Health Check**: https://localhost/api/v1/health

> **Note**: Use `-k` flag with curl for self-signed certificate: `curl -k https://localhost/api/v1/health`

## 📚 Documentation

- **[RUNBOOK.md](docs/RUNBOOK.md)** - Complete deployment and verification guide
- **[MVP_IMPLEMENTATION_SUMMARY.md](docs/MVP_IMPLEMENTATION_SUMMARY.md)** - Technical implementation details
- **[TODO_CHECKLIST.md](docs/TODO_CHECKLIST.md)** - Roadmap and future features
- **[01-ARCHITECTURE.md](docs/01-ARCHITECTURE.md)** - System architecture overview
- **[02-DOMAIN-MODEL.md](docs/02-DOMAIN-MODEL.md)** - Data models and relationships

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Caddy (Reverse Proxy)                │
│                   Ports: 80, 443 (HTTPS)                │
└───────┬─────────────────────────────────────┬───────────┘
        │                                     │
        │ /api/*, /admin/*                   │ /
        │                                     │
┌───────▼─────────────────┐         ┌────────▼─────────────┐
│   Django Backend        │         │  React Frontend      │
│   (Python 3.12)         │         │  (TypeScript)        │
│   - REST API            │         │  - Controls UI       │
│   - Admin Interface     │         │  - Login Page        │
│   - Standards Import    │         │  - Search & Filter   │
└───────┬─────────┬───────┘         └──────────────────────┘
        │         │
        │         │
┌───────▼─────────┐ ┌────▼─────────────────┐
│  PostgreSQL 16  │ │  MinIO (S3)          │
│  - Standards    │ │  - Evidence Files    │
│  - Controls     │ │  - Exports           │
│  - Audit Logs   │ │  (Future)            │
└─────────────────┘ └──────────────────────┘
```

## 🛠️ Technology Stack

### Backend
- **Python 3.12** - Modern Python with latest features
- **Django 5.0** - Web framework
- **Django REST Framework 3.14** - API development
- **PostgreSQL 16** - Primary database
- **django-storages + boto3** - MinIO/S3 integration
- **ReportLab** - PDF generation (Prompt 2)

### Frontend
- **React 18** - UI framework
- **TypeScript 5** - Type-safe JavaScript
- **Vite** - Fast build tool
- **CSS3** - Styling (no frameworks in MVP)

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **Caddy 2** - Reverse proxy with automatic HTTPS
- **MinIO** - S3-compatible object storage
- **PostgreSQL 16** - Database server

## 📊 Current Status

**Prompt 0 (MVP Scaffold): ✅ COMPLETE**

All verification tests passing:
- ✅ All services running
- ✅ Health checks passing
- ✅ API serving 121 controls
- ✅ Frontend accessible
- ✅ Admin interface accessible
- ✅ Database records correct
- ✅ Immutability enforced

Run `./scripts/verify_mvp.sh` to verify your deployment.

## 🗂️ Project Structure

```
accredivault/
├── backend/                  # Django backend
│   ├── apps/
│   │   ├── standards/       # Standards & controls management
│   │   ├── audit/           # Audit logging
│   │   └── users/           # User management
│   ├── config/              # Django settings
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile
├── frontend/                 # React frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── api.ts          # API client
│   │   └── App.tsx         # Main application
│   ├── package.json
│   └── Dockerfile
├── infra/                    # Infrastructure
│   ├── docker-compose.yml   # Service definitions
│   ├── Caddyfile           # Reverse proxy config
│   └── .env.example        # Environment template
├── docs/                     # Documentation
│   ├── RUNBOOK.md
│   ├── MVP_IMPLEMENTATION_SUMMARY.md
│   └── TODO_CHECKLIST.md
└── scripts/                  # Utility scripts
    └── verify_mvp.sh        # Automated verification
```

## 🔜 Roadmap

### Prompt 1 - Evidence Management (Next)
- Evidence upload to MinIO
- Link evidence to controls
- Evidence timeline and history
- File type validation
- Evidence CRUD operations

### Prompt 2 - Rules & PDF Export
- Evidence rules engine
- Control status computation
- PDF export with ReportLab
- Background job processing
- Export history

### Prompt 3 - Auth, Audit, Polish
- JWT authentication
- Role-based permissions
- Complete audit logging
- Dashboard UI
- Production hardening

### Prompt 4 - SaaS & Multi-tenancy (Optional)
- Multi-tenant architecture
- Tenant isolation
- Subscription plans
- Billing integration

See [TODO_CHECKLIST.md](docs/TODO_CHECKLIST.md) for detailed feature list.

## 🧪 Testing

### Automated Verification
```bash
./scripts/verify_mvp.sh
```

### Manual Testing
```bash
# Health check
curl -k https://localhost/api/v1/health

# List controls
curl -k https://localhost/api/v1/controls/

# Filter by section
curl -k "https://localhost/api/v1/controls/?section=Personnel"

# Search
curl -k "https://localhost/api/v1/controls/?q=safety"
```

## 🔒 Security

- HTTPS enforced via Caddy (automatic certificate management)
- Internal service networking (backend/frontend not exposed)
- Environment-based secrets management
- CORS configuration
- SQL injection protection via Django ORM
- XSS protection via React

**Production Notes:**
- Change default passwords in `.env`
- Generate secure `SECRET_KEY`
- Set `DEBUG=False`
- Configure `ALLOWED_HOSTS`
- Use strong database passwords
- Enable audit logging

## 📝 License

This project is proprietary software. All rights reserved.

## 👥 Contributors

- munaimtahir - Initial implementation

## 🤝 Support

For issues, questions, or contributions:
1. Check existing documentation in `/docs`
2. Review [RUNBOOK.md](docs/RUNBOOK.md) for troubleshooting
3. Open an issue on GitHub

## 🎯 Design Philosophy

AccrediVault is built with the following principles:

1. **Single Deployment First** - Optimized for one organization, with clear SaaS upgrade path
2. **Enterprise-Grade** - Production-ready architecture from day one
3. **Compliance-Focused** - Built specifically for PHC lab licensing standards
4. **Immutability** - Published standards cannot be modified (audit trail)
5. **Self-Hosted** - Complete control over data and infrastructure
6. **Open Architecture** - Clean separation of concerns, extensible design

---

**Built for PHC Lab Licensing Compliance** | **Enterprise-Ready** | **Self-Hosted**
