import hashlib
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from apps.standards.models import StandardPack, Control
from .models import EvidenceItem, EvidenceFile, ControlEvidenceLink

User = get_user_model()


def _assign_role(user, role_name):
    group, _ = Group.objects.get_or_create(name=role_name)
    user.groups.add(group)


class DummyS3Client:
    def __init__(self):
        self.uploads = []
        self.presigned_urls = []

    def upload_fileobj(self, fileobj, bucket, key, ExtraArgs=None):
        self.uploads.append((bucket, key, ExtraArgs))

    def generate_presigned_url(self, *args, **kwargs):
        self.presigned_urls.append((args, kwargs))
        return 'http://example.com/presigned'


class EvidenceAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='tester', password='pass1234')
        _assign_role(self.user, 'DATA_ENTRY')
        self.client.force_authenticate(user=self.user)

        self.pack = StandardPack.objects.create(
            authority_code='PHC',
            name='PHC Lab Licensing Checklist',
            version='1.0',
            status='draft',
            checksum='testchecksum123',
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

    def test_create_evidence_item(self):
        payload = {
            'title': 'Calibration Certificate',
            'category': 'certificate',
            'event_date': '2024-01-15',
            'notes': 'Annual calibration',
        }
        response = self.client.post('/api/v1/evidence-items', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(EvidenceItem.objects.count(), 1)
        self.assertEqual(EvidenceItem.objects.first().title, 'Calibration Certificate')

    @patch('apps.evidence.views.get_s3_client')
    def test_upload_file(self, mock_s3_client):
        evidence = EvidenceItem.objects.create(
            title='Test Evidence',
            category='report',
            event_date='2024-02-01',
            created_by=self.user,
        )
        dummy_s3 = DummyS3Client()
        mock_s3_client.return_value = dummy_s3

        file_content = b'hello'
        upload_file = SimpleUploadedFile('hello.txt', file_content, content_type='text/plain')
        response = self.client.post(
            f'/api/v1/evidence-items/{evidence.id}/files',
            {'file': upload_file},
            format='multipart',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(EvidenceFile.objects.count(), 1)
        evidence_file = EvidenceFile.objects.first()
        expected_sha = hashlib.sha256(file_content).hexdigest()
        self.assertEqual(evidence_file.sha256, expected_sha)
        self.assertEqual(len(dummy_s3.uploads), 1)

    def test_link_to_control_and_timeline(self):
        evidence = EvidenceItem.objects.create(
            title='Policy Document',
            category='policy',
            event_date='2024-03-10',
            created_by=self.user,
        )

        response = self.client.post(
            f'/api/v1/controls/{self.control.id}/link-evidence',
            {'evidence_item_id': str(evidence.id), 'note': 'Relevant to record keeping'},
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ControlEvidenceLink.objects.count(), 1)

        timeline = self.client.get(f'/api/v1/controls/{self.control.id}/timeline')
        self.assertEqual(timeline.status_code, 200)
        data = timeline.json()
        self.assertEqual(data['control']['id'], self.control.id)
        self.assertEqual(len(data['evidence_items']), 1)
        self.assertEqual(data['evidence_items'][0]['evidence_item']['id'], str(evidence.id))

    @patch('apps.evidence.views.get_s3_client')
    def test_download_presigned_url(self, mock_s3_client):
        evidence = EvidenceItem.objects.create(
            title='Manual',
            category='manual',
            event_date='2024-04-01',
            created_by=self.user,
        )
        evidence_file = EvidenceFile.objects.create(
            evidence_item=evidence,
            bucket='evidence',
            object_key='evidence/test/manual.pdf',
            filename='manual.pdf',
            content_type='application/pdf',
            size_bytes=123,
            sha256='abc',
        )
        dummy_s3 = DummyS3Client()
        mock_s3_client.return_value = dummy_s3

        response = self.client.get(f'/api/v1/evidence-files/{evidence_file.id}/download')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['url'], 'http://example.com/presigned')
