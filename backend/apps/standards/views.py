from rest_framework import viewsets, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Q
from apps.users.permissions import CanReadControls

from .models import Control, StandardPack
from .serializers import ControlSerializer, StandardPackSerializer
import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.db import connection


class ControlViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing and retrieving controls.
    Supports filtering by section and text search.
    """
    queryset = Control.objects.select_related('standard_pack', 'status_cache').filter(active=True)
    serializer_class = ControlSerializer
    permission_classes = [CanReadControls]
    filter_backends = [filters.SearchFilter]
    search_fields = ['control_code', 'section', 'standard', 'indicator']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by section
        section = self.request.query_params.get('section', None)
        if section:
            queryset = queryset.filter(section__icontains=section)
        
        # Text search
        q = self.request.query_params.get('q', None)
        if q:
            queryset = queryset.filter(
                Q(control_code__icontains=q) |
                Q(section__icontains=q) |
                Q(standard__icontains=q) |
                Q(indicator__icontains=q)
            )
        
        return queryset


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint that verifies:
    - Database connectivity
    - MinIO credentials (can list buckets)
    """
    health_status = {
        'status': 'healthy',
        'checks': {
            'database': 'unknown',
            'minio': 'unknown',
        }
    }
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['status'] = 'unhealthy'
        health_status['checks']['database'] = f'error: {str(e)}'
    
    # Check MinIO
    if settings.USE_S3:
        try:
            s3_client = boto3.client(
                's3',
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
                verify=settings.AWS_S3_VERIFY,
            )
            # Try to list buckets
            response = s3_client.list_buckets()
            health_status['checks']['minio'] = 'ok'
            health_status['checks']['minio_buckets'] = [b['Name'] for b in response.get('Buckets', [])]
        except ClientError as e:
            health_status['status'] = 'unhealthy'
            health_status['checks']['minio'] = f'error: {str(e)}'
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['checks']['minio'] = f'error: {str(e)}'
    else:
        health_status['checks']['minio'] = 'disabled'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return Response(health_status, status=status_code)
