import hashlib
import os
import re
import uuid
import boto3
from django.conf import settings


def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL', None),
        aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
        aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
        region_name=getattr(settings, 'AWS_S3_REGION_NAME', None),
        verify=getattr(settings, 'AWS_S3_VERIFY', True),
    )


def sanitize_filename(filename: str) -> str:
    base = os.path.basename(filename or '')
    if not base:
        return 'file'
    sanitized = re.sub(r'[^A-Za-z0-9._-]+', '_', base).strip('._')
    return sanitized or 'file'


def build_object_key(evidence_item_id, filename: str) -> str:
    safe_name = sanitize_filename(filename)
    return f"evidence/{evidence_item_id}/{str(uuid.uuid4())}_{safe_name}"


def compute_sha256(uploaded_file) -> str:
    hasher = hashlib.sha256()
    for chunk in uploaded_file.chunks():
        hasher.update(chunk)
    return hasher.hexdigest()
