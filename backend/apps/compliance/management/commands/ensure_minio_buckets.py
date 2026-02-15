"""Create MinIO buckets (evidence, exports) if they do not exist."""
from django.conf import settings
from django.core.management.base import BaseCommand

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    boto3 = None
    ClientError = Exception


class Command(BaseCommand):
    help = 'Ensure MinIO buckets (evidence, exports) exist; create if missing.'

    def handle(self, *args, **options):
        if not getattr(settings, 'USE_S3', False):
            self.stdout.write('USE_S3 is False; skipping bucket creation.')
            return

        if boto3 is None:
            self.stderr.write('boto3 not installed; cannot create buckets.')
            return

        endpoint = getattr(settings, 'AWS_S3_ENDPOINT_URL', None)
        if not endpoint:
            self.stderr.write('AWS_S3_ENDPOINT_URL not set.')
            return

        buckets = [
            getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'evidence'),
            getattr(settings, 'MINIO_BUCKET_EXPORTS', 'exports'),
        ]
        buckets = list(dict.fromkeys(buckets))  # unique, order preserved

        client = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', ''),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''),
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1'),
        )

        for name in buckets:
            try:
                client.head_bucket(Bucket=name)
                self.stdout.write(self.style.SUCCESS(f'Bucket "{name}" already exists.'))
            except ClientError as e:
                if e.response.get('Error', {}).get('Code') in ('404', 'NoSuchBucket'):
                    try:
                        client.create_bucket(Bucket=name)
                        self.stdout.write(self.style.SUCCESS(f'Created bucket "{name}".'))
                    except ClientError as err:
                        self.stderr.write(f'Failed to create bucket "{name}": {err}')
                else:
                    self.stderr.write(f'Error checking bucket "{name}": {e}')
