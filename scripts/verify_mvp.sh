#!/bin/bash
# AccrediVault MVP Verification Script

set -e

echo "==================================="
echo "AccrediVault MVP Verification"
echo "==================================="
echo ""

cd "$(dirname "$0")/../infra"

# Check if services are running
echo "✓ Checking services status..."
docker compose ps | grep -q "Up" && echo "  Services are running" || { echo "  ✗ Services not running"; exit 1; }

# Check health endpoint
echo "✓ Checking health endpoint..."
HEALTH=$(curl -k -s https://localhost/api/v1/health)
echo "$HEALTH" | grep -q "healthy" && echo "  Health check passed" || { echo "  ✗ Health check failed"; exit 1; }

# Check database connectivity
echo "$HEALTH" | grep -q '"database":"ok"' && echo "  Database OK" || { echo "  ✗ Database check failed"; exit 1; }

# Check MinIO connectivity
echo "$HEALTH" | grep -q '"minio":"ok"' && echo "  MinIO OK" || { echo "  ✗ MinIO check failed"; exit 1; }

# Check controls API
echo "✓ Checking controls API..."
CONTROLS=$(curl -k -s https://localhost/api/v1/controls/)
CONTROL_COUNT=$(echo "$CONTROLS" | grep -o '"count":[0-9]*' | grep -o '[0-9]*')
if [ "$CONTROL_COUNT" -eq 121 ]; then
    echo "  Found $CONTROL_COUNT controls ✓"
else
    echo "  ✗ Expected 121 controls, found $CONTROL_COUNT"
    exit 1
fi

# Check first control
echo "$CONTROLS" | grep -q "PHC-ROO-001" && echo "  First control code verified (PHC-ROO-001)" || { echo "  ✗ Control code not found"; exit 1; }

# Check API filtering
echo "✓ Checking API filtering..."
FILTERED=$(curl -k -s 'https://localhost/api/v1/controls/?section=Personnel')
echo "$FILTERED" | grep -q "Personnel" && echo "  Section filter works" || { echo "  ✗ Section filter failed"; exit 1; }

# Check search
SEARCH=$(curl -k -s 'https://localhost/api/v1/controls/?q=safety')
echo "$SEARCH" | grep -q "safety" && echo "  Search filter works" || { echo "  ✗ Search filter failed"; exit 1; }

# Check frontend is serving
echo "✓ Checking frontend..."
FRONTEND=$(curl -k -s https://localhost/)
echo "$FRONTEND" | grep -q "root" && echo "  Frontend is serving" || { echo "  ✗ Frontend not serving"; exit 1; }

# Check admin interface
echo "✓ Checking admin interface..."
ADMIN=$(curl -k -L -s https://localhost/admin/)
echo "$ADMIN" | grep -q "Django\|Log in" && echo "  Admin interface accessible" || { echo "  ✗ Admin not accessible"; exit 1; }

# Check database records
echo "✓ Checking database records..."
PACK_COUNT=$(docker compose exec -T backend python manage.py shell << 'EOF'
from apps.standards.models import StandardPack
print(StandardPack.objects.count())
EOF
)
PACK_COUNT=$(echo "$PACK_COUNT" | tr -d '\r')
[ "$PACK_COUNT" -eq 1 ] && echo "  StandardPack count: $PACK_COUNT ✓" || { echo "  ✗ Expected 1 pack, found $PACK_COUNT"; exit 1; }

DB_CONTROL_COUNT=$(docker compose exec -T backend python manage.py shell << 'EOF'
from apps.standards.models import Control
print(Control.objects.count())
EOF
)
DB_CONTROL_COUNT=$(echo "$DB_CONTROL_COUNT" | tr -d '\r')
[ "$DB_CONTROL_COUNT" -eq 121 ] && echo "  Control count: $DB_CONTROL_COUNT ✓" || { echo "  ✗ Expected 121 controls, found $DB_CONTROL_COUNT"; exit 1; }

# Check immutability
echo "✓ Testing immutability enforcement..."
IMMUTABLE_TEST=$(docker compose exec -T backend python manage.py shell << 'EOF' 2>&1 || true
from apps.standards.models import Control
from django.core.exceptions import ValidationError
control = Control.objects.first()
if control.standard_pack.status == 'published':
    try:
        control.section = "Modified Section"
        control.save()
        print("FAIL: Immutability not enforced")
    except ValidationError:
        print("PASS: Immutability enforced")
else:
    print("SKIP: Pack not published")
EOF
)
echo "$IMMUTABLE_TEST" | grep -q "PASS" && echo "  Immutability enforced ✓" || { echo "  ✗ Immutability test failed"; exit 1; }

echo ""
echo "==================================="
echo "✅ All Verification Tests Passed!"
echo "==================================="
echo ""
echo "Summary:"
echo "  - All services running"
echo "  - Health checks passing"
echo "  - API serving 121 controls"
echo "  - Frontend accessible"
echo "  - Admin interface accessible"
echo "  - Database records correct"
echo "  - Immutability enforced"
echo ""
echo "Access URLs (use -k flag for curl due to self-signed cert):"
echo "  - Frontend:  https://localhost/"
echo "  - Admin:     https://localhost/admin/"
echo "  - API:       https://localhost/api/v1/controls/"
echo "  - Health:    https://localhost/api/v1/health"
echo ""
