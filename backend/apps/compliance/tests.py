import io
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.compliance.models import ControlStatusCache, ControlVerification, EvidenceRule, ExportJob
from apps.evidence.models import EvidenceItem
from apps.standards.models import Control, StandardPack

User = get_user_model()


class DummyS3Client:
    def __init__(self):
        self.uploads = []
        self.buckets = set()

    def head_bucket(self, Bucket):
        if Bucket not in self.buckets:
            raise Exception('NoSuchBucket')

    def create_bucket(self, Bucket):
        self.buckets.add(Bucket)

    def upload_fileobj(self, fileobj, bucket, key, ExtraArgs=None):
        payload = fileobj.read()
        self.buckets.add(bucket)
        self.uploads.append((bucket, key, ExtraArgs, payload))

    def generate_presigned_url(self, *args, **kwargs):
        return 'http://example.com/presigned-download'


class ComplianceEngineAndApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='compliance_tester', password='pass1234')
        self.client.force_authenticate(user=self.user)

        self.pack = StandardPack.objects.create(
            authority_code='PHC',
            name='PHC Lab Licensing Checklist',
            version='1.0',
            status='draft',
            checksum='compliance-tests-checksum',
        )
        self.control = Control.objects.create(
            standard_pack=self.pack,
            control_code='PHC-ROM-001',
            section='Records',
            standard='Maintain records',
            indicator='Records are maintained',
            sort_order=1,
            active=True,
        )

    def _create_and_link_evidence(self, event_date, valid_until=None):
        evidence = EvidenceItem.objects.create(
            title='Evidence',
            category='policy',
            event_date=event_date,
            valid_until=valid_until,
            created_by=self.user,
        )
        response = self.client.post(
            f'/api/v1/controls/{self.control.id}/link-evidence',
            {'evidence_item_id': str(evidence.id)},
            format='json',
        )
        self.assertIn(response.status_code, [200, 201])
        return evidence

    def test_status_transitions_no_evidence_and_evidence_without_rules(self):
        status_response = self.client.get(f'/api/v1/controls/{self.control.id}/status')
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()['computed_status'], 'NOT_STARTED')

        self._create_and_link_evidence(event_date=timezone.localdate())
        status_response = self.client.get(f'/api/v1/controls/{self.control.id}/status')
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()['computed_status'], 'IN_PROGRESS')

    def test_frequency_rule_overdue_and_ready(self):
        EvidenceRule.objects.create(
            standard_pack=self.pack,
            scope_type=EvidenceRule.SCOPE_CONTROL,
            control=self.control,
            rule_type=EvidenceRule.RULE_FREQUENCY,
            frequency_days=30,
            min_items=1,
            enabled=True,
        )

        self._create_and_link_evidence(event_date=timezone.localdate() - timedelta(days=45))
        status_response = self.client.get(f'/api/v1/controls/{self.control.id}/status')
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()['computed_status'], 'OVERDUE')

        self._create_and_link_evidence(event_date=timezone.localdate() - timedelta(days=5))
        status_response = self.client.get(f'/api/v1/controls/{self.control.id}/status')
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()['computed_status'], 'READY')

    def test_verification_freshness(self):
        EvidenceRule.objects.create(
            standard_pack=self.pack,
            scope_type=EvidenceRule.SCOPE_CONTROL,
            control=self.control,
            rule_type=EvidenceRule.RULE_ONE_TIME,
            min_items=1,
            requires_verification=True,
            enabled=True,
        )

        self._create_and_link_evidence(event_date=timezone.localdate())

        status_before = self.client.get(f'/api/v1/controls/{self.control.id}/status')
        self.assertEqual(status_before.status_code, 200)
        self.assertEqual(status_before.json()['computed_status'], 'READY')

        verify_response = self.client.post(f'/api/v1/controls/{self.control.id}/verify', {'remarks': 'Looks good'}, format='json')
        self.assertEqual(verify_response.status_code, 201)
        self.assertEqual(verify_response.json()['status_cache']['computed_status'], 'VERIFIED')

        self._create_and_link_evidence(event_date=timezone.localdate())
        stale_status = self.client.get(f'/api/v1/controls/{self.control.id}/status')
        self.assertEqual(stale_status.status_code, 200)
        self.assertEqual(stale_status.json()['computed_status'], 'READY')

    @patch('apps.compliance.views.get_s3_client')
    def test_export_creation_and_download(self, mock_s3_client):
        dummy_s3 = DummyS3Client()
        mock_s3_client.return_value = dummy_s3

        self._create_and_link_evidence(event_date=timezone.localdate())

        export_response = self.client.post(f'/api/v1/exports/control/{self.control.id}', {}, format='json')
        self.assertEqual(export_response.status_code, 201)
        payload = export_response.json()
        self.assertEqual(payload['job']['status'], 'COMPLETED')
        self.assertTrue(payload['job']['sha256'])
        self.assertEqual(payload['download']['url'], 'http://example.com/presigned-download')
        self.assertEqual(len(dummy_s3.uploads), 1)

        job = ExportJob.objects.get(pk=payload['job']['id'])
        self.assertEqual(job.status, ExportJob.STATUS_COMPLETED)
        self.assertIsNotNone(job.sha256)

        dl_response = self.client.get(f'/api/v1/exports/{job.id}/download')
        self.assertEqual(dl_response.status_code, 200)
        self.assertEqual(dl_response.json()['url'], 'http://example.com/presigned-download')
