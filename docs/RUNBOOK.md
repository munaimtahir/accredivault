# AccrediVault MVP - Deployment & Verification Runbook

This runbook provides step-by-step instructions to deploy and verify the AccrediVault MVP stack.

## Prerequisites

- Docker and Docker Compose installed
- Git repository cloned
- Ports 80 and 443 available on the host

## Deployment Steps

### 1. Navigate to Infrastructure Directory

```bash
cd /path/to/accredivault/infra
```

### 2. Configure Environment (Optional)

Copy and customize the environment file if needed:

```bash
cp .env.example .env
# Edit .env to customize database passwords, secrets, etc.
```

### 3. Build and Start All Services

```bash
docker compose up -d --build
```

This command will:
- Build the backend Django application
- Build the frontend React application
- Start PostgreSQL database
- Start MinIO object storage
- Start Caddy reverse proxy

**Expected Output:**
```
[+] Building ...
[+] Running 5/5
 ✔ Container infra-db-1       Started
 ✔ Container infra-minio-1    Started
 ✔ Container infra-backend-1  Started
 ✔ Container infra-frontend-1 Started
 ✔ Container infra-caddy-1    Started
```

### 4. Wait for Services to Initialize

Wait 30-60 seconds for all services to fully start. Check service status:

```bash
docker compose ps
```

All services should show "Up" status.

### 5. Run Database Migrations

```bash
docker compose exec backend python manage.py migrate
```

**Expected Output:**
```
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
  Applying standards.0001_initial... OK
  Applying audit.0001_initial... OK
```

### 6. Create Superuser

```bash
docker compose exec backend python manage.py createsuperuser
```

Follow the prompts to create an admin account:
- Username: admin (or your choice)
- Email: admin@example.com
- Password: (choose a secure password)

### 7. Import PHC Checklist

```bash
docker compose exec backend python manage.py import_phc_csv \
  --path apps/standards/seed_data/phc/Final_PHC_list.csv \
  --pack-version 1.0 \
  --publish
```

**Expected Output:**
```
Reading CSV from: /app/apps/standards/seed_data/phc/Final_PHC_list.csv
File checksum: <sha256_hash>
Parsed 121 controls from CSV
Created StandardPack: PHC PHC Lab Licensing Checklist v1.0 (draft)
Created 121 controls
Published pack: PHC PHC Lab Licensing Checklist v1.0 (published)
Successfully imported PHC checklist version 1.0
```

### 8. Create MinIO Buckets (Optional)

Access MinIO console to create required buckets:

```bash
# MinIO is accessible at http://localhost:9001 (if ports are exposed)
# Or use the backend health check which will create buckets automatically
```

## Verification Steps

### 1. Verify Backend Health Check

```bash
curl http://localhost/api/v1/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "minio": "ok",
    "minio_buckets": ["evidence", "exports"]
  }
}
```

### 2. Verify Admin Interface

Open your browser and navigate to:

```
http://localhost/admin
```

1. Login with the superuser credentials created in step 6
2. Verify you can see:
   - Standard Packs (should show 1 pack: PHC v1.0, status: published)
   - Controls (should show 121 controls)
   - Audit Events
3. Click on Standard Packs → PHC Lab Licensing Checklist v1.0
4. Verify the pack details and associated controls

### 3. Verify API Endpoint

Test the controls API endpoint:

```bash
curl http://localhost/api/v1/controls/ | jq
```

**Expected Response:**
- Should return a JSON object with a `results` array
- Array should contain 118 control objects
- Each control should have: id, control_code, section, indicator, sort_order, active, status

Count the controls:
```bash
curl -s http://localhost/api/v1/controls/ | jq '.results | length'
```

Should return: `100` (due to pagination)

Get total count:
```bash
curl -s http://localhost/api/v1/controls/ | jq '.count'
```

Should return: `118`

### 4. Test API Filtering

Filter by section:
```bash
curl "http://localhost/api/v1/controls/?section=Room" | jq '.count'
```

Search query:
```bash
curl "http://localhost/api/v1/controls/?q=safety" | jq '.count'
```

### 5. Verify Frontend Application

Open your browser and navigate to:

```
http://localhost/
```

1. You should see the AccrediVault frontend
2. Click the "Controls" button in the navigation
3. Verify the controls table displays with 118 total controls
4. Test the section filter dropdown (should show all section names)
5. Test the search functionality
6. Click "Login (Placeholder)" to see the login page

## Troubleshooting

### Services Not Starting

Check logs for specific service:
```bash
docker compose logs backend
docker compose logs frontend
docker compose logs caddy
```

### Database Connection Issues

```bash
docker compose logs db
docker compose exec backend python manage.py dbshell
```

### Import Command Fails

Check if CSV file exists:
```bash
docker compose exec backend ls -la apps/standards/seed_data/phc/
```

Re-run with verbose output:
```bash
docker compose exec backend python manage.py import_phc_csv \
  --path apps/standards/seed_data/phc/Final_PHC_list.csv \
  --pack-version 1.0 \
  --publish --verbosity 2
```

### Caddy Routing Issues

Check Caddy logs:
```bash
docker compose logs caddy
```

Test direct backend access:
```bash
docker compose exec backend curl http://localhost:8000/api/v1/health
```

### Frontend Not Loading

Check if frontend is running:
```bash
docker compose logs frontend
```

Access frontend directly:
```bash
docker compose exec frontend curl http://localhost:5173
```

## Stopping and Restarting

Stop all services:
```bash
docker compose down
```

Stop and remove all data (⚠️ WARNING: This deletes all data):
```bash
docker compose down -v
```

Restart services:
```bash
docker compose up -d
```

## Production Deployment Notes

For production deployment:

1. **Update Caddyfile**: Replace `localhost` with your domain and add TLS email
2. **Set Environment Variables**: Update `.env` with secure passwords and secrets
3. **Set DEBUG=False**: In backend environment variables
4. **Configure ALLOWED_HOSTS**: Set to your domain(s)
5. **Use Proper Secrets**: Generate strong SECRET_KEY for Django
6. **Backup Strategy**: Implement regular backups of PostgreSQL and MinIO data
7. **SSL Certificates**: Caddy will automatically provision Let's Encrypt certificates
8. **Monitoring**: Set up logging and monitoring for all services

## Success Criteria

✅ All 5 containers running (db, minio, backend, frontend, caddy)
✅ Health check returns "healthy" status
✅ Admin interface accessible via Caddy at /admin
✅ API returns 121 controls at /api/v1/controls
✅ Frontend displays controls table
✅ PHC checklist imported and published
✅ Immutability enforced (cannot edit published controls in admin)

## Evidence MVP (Prompt 1) Operations

### 1. Create Evidence
You can create evidence items directly from the Control Detail view in the frontend, or via API.

**API Example:**
```bash
# Create Evidence Item
curl -X POST http://localhost/api/v1/evidence-items \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Calibration Certificate 2024",
    "category": "certificate",
    "event_date": "2024-02-11",
    "notes": "Annual calibration for centrifuge"
  }'

# Upload File to Evidence Item (returns file_id)
curl -X POST http://localhost/api/v1/evidence-items/<evidence_item_id>/files \
  -F "files=@/path/to/your/file.pdf"

# Link Evidence to Control
curl -X POST http://localhost/api/v1/controls/<control_id>/link-evidence \
  -H "Content-Type: application/json" \
  -d '{
    "evidence_item_id": "<evidence_item_id>",
    "note": "Specifically addresses calibration requirements"
  }'
```

### 2. Verify MinIO Bucket
The application expects a bucket named `evidence` (configurable via `MINIO_BUCKET_EVIDENCE`).

**Verify via Health Check:**
```bash
curl http://localhost/api/v1/health
```
Expect `"minio_buckets": ["evidence", ...]`.

**Manual Creation (if needed):**
Access MinIO Console at `http://localhost:9001` (login with `minioadmin` / `minioadmin_change_me`) and create a bucket named `evidence`.

**Verify Files in MinIO:**
```bash
# Exec into minio container and list files
docker compose exec minio ls -R /data/evidence
```

### 3. Verify Timeline
```bash
curl http://localhost/api/v1/controls/<control_id>/timeline | jq
```
Expected response includes `control` information and a list of `evidence_items` (which are Link objects).

### 4. Test Download
```bash
curl http://localhost/api/v1/evidence-files/<file_id>/download
```
Returns a presigned URL valid for 10 minutes.

## Next Steps (Prompt 2)

The following features will be implemented in Prompt 2:
- [ ] EvidenceRule system (automated status checks)
- [ ] Control Status engine (calculating status from linked evidence)
- [ ] Status rollups (Section -> Standard Pack)
- [ ] Dashboard with progress visualization
- [ ] Automated evidence expiration alerts
