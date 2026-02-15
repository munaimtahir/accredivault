from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.compliance.models import ComplianceAlert, ControlNote, ControlVerification, EvidenceRule, ExportJob
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
        Group.objects.get_or_create(name='MANAGER')
        self.user.groups.add(Group.objects.get(name='MANAGER'))
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

    def _create_and_link_evidence(self, control, event_date, valid_until=None):
        evidence = EvidenceItem.objects.create(
            title='Evidence',
            category='policy',
            event_date=event_date,
            valid_until=valid_until,
            created_by=self.user,
        )
        response = self.client.post(
            f'/api/v1/controls/{control.id}/link-evidence',
            {'evidence_item_id': str(evidence.id)},
            format='json',
        )
        self.assertIn(response.status_code, [200, 201])
        return evidence

    def _assign_role(self, user, role_name):
        group, _ = Group.objects.get_or_create(name=role_name)
        user.groups.add(group)

    def test_status_transitions_no_evidence_and_evidence_without_rules(self):
        status_response = self.client.get(f'/api/v1/controls/{self.control.id}/status')
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()['computed_status'], 'NOT_STARTED')

        self._create_and_link_evidence(control=self.control, event_date=timezone.localdate())
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

        self._create_and_link_evidence(control=self.control, event_date=timezone.localdate() - timedelta(days=45))
        status_response = self.client.get(f'/api/v1/controls/{self.control.id}/status')
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()['computed_status'], 'OVERDUE')

        self._create_and_link_evidence(control=self.control, event_date=timezone.localdate() - timedelta(days=5))
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

        self._create_and_link_evidence(control=self.control, event_date=timezone.localdate())

        status_before = self.client.get(f'/api/v1/controls/{self.control.id}/status')
        self.assertEqual(status_before.status_code, 200)
        self.assertEqual(status_before.json()['computed_status'], 'READY')

        verify_response = self.client.post(f'/api/v1/controls/{self.control.id}/verify', {'remarks': 'Looks good'}, format='json')
        self.assertEqual(verify_response.status_code, 201)
        self.assertEqual(verify_response.json()['status_cache']['computed_status'], 'VERIFIED')

        self._create_and_link_evidence(control=self.control, event_date=timezone.localdate())
        stale_status = self.client.get(f'/api/v1/controls/{self.control.id}/status')
        self.assertEqual(stale_status.status_code, 200)
        self.assertEqual(stale_status.json()['computed_status'], 'READY')

    @patch('apps.compliance.views.get_s3_client')
    def test_export_creation_and_download(self, mock_s3_client):
        dummy_s3 = DummyS3Client()
        mock_s3_client.return_value = dummy_s3

        self._create_and_link_evidence(control=self.control, event_date=timezone.localdate())

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

    def test_scheduled_recompute_flags_overdue_correctly(self):
        EvidenceRule.objects.create(
            standard_pack=self.pack,
            scope_type=EvidenceRule.SCOPE_CONTROL,
            control=self.control,
            rule_type=EvidenceRule.RULE_FREQUENCY,
            frequency_days=7,
            min_items=1,
            enabled=True,
        )
        self._create_and_link_evidence(control=self.control, event_date=timezone.localdate() - timedelta(days=30))

        with self.assertRaises(SystemExit) as exc:
            call_command('recompute_control_statuses', '--pack-version', self.pack.version)
        self.assertEqual(exc.exception.code, 1)

    def test_dashboard_summary_counts_match_status_cache(self):
        self._assign_role(self.user, 'AUDITOR')

        control2 = Control.objects.create(
            standard_pack=self.pack,
            control_code='PHC-ROM-002',
            section='Records',
            standard='Maintain register',
            indicator='Register present',
            sort_order=2,
            active=True,
        )

        EvidenceRule.objects.create(
            standard_pack=self.pack,
            scope_type=EvidenceRule.SCOPE_SECTION,
            section_code='ROM',
            rule_type=EvidenceRule.RULE_FREQUENCY,
            frequency_days=30,
            min_items=1,
            enabled=True,
        )
        self._create_and_link_evidence(control=self.control, event_date=timezone.localdate() - timedelta(days=3))
        self._create_and_link_evidence(control=control2, event_date=timezone.localdate() - timedelta(days=40))

        self.client.get(f'/api/v1/controls/{self.control.id}/status')
        self.client.get(f'/api/v1/controls/{control2.id}/status')

        response = self.client.get('/api/v1/dashboard/summary')
        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload['pack_version'], self.pack.version)
        self.assertEqual(payload['totals']['total_controls'], 2)
        self.assertEqual(payload['totals']['READY'], 1)
        self.assertEqual(payload['totals']['OVERDUE'], 1)

    @patch('apps.compliance.views.get_s3_client')
    def test_section_export_creates_valid_export_job(self, mock_s3_client):
        dummy_s3 = DummyS3Client()
        mock_s3_client.return_value = dummy_s3

        self._create_and_link_evidence(control=self.control, event_date=timezone.localdate())
        response = self.client.post('/api/v1/exports/section/ROM', {}, format='json')
        self.assertEqual(response.status_code, 201)

        payload = response.json()
        self.assertEqual(payload['job']['job_type'], ExportJob.JOB_SECTION_PACK)
        self.assertEqual(payload['job']['status'], ExportJob.STATUS_COMPLETED)
        self.assertIn('/sections/ROM/', payload['job']['object_key'])

    @patch('apps.compliance.views.get_s3_client')
    def test_full_export_creates_valid_export_job(self, mock_s3_client):
        dummy_s3 = DummyS3Client()
        mock_s3_client.return_value = dummy_s3

        self._create_and_link_evidence(control=self.control, event_date=timezone.localdate())
        response = self.client.post('/api/v1/exports/full', {}, format='json')
        self.assertEqual(response.status_code, 201)

        payload = response.json()
        self.assertEqual(payload['job']['job_type'], ExportJob.JOB_FULL_PACK)
        self.assertEqual(payload['job']['status'], ExportJob.STATUS_COMPLETED)
        self.assertIn('/full/', payload['job']['object_key'])

    def test_control_note_crud(self):
        manager = User.objects.create_user(username='manager1', password='pass1234')
        self._assign_role(manager, 'MANAGER')

        viewer = User.objects.create_user(username='viewer1', password='pass1234')
        self.client.force_authenticate(user=manager)

        create_response = self.client.post(
            f'/api/v1/controls/{self.control.id}/notes',
            {'note_type': 'INSPECTION', 'text': 'Initial inspection note'},
            format='json',
        )
        self.assertEqual(create_response.status_code, 201)
        note_id = create_response.json()['id']

        self.client.force_authenticate(user=viewer)
        list_response = self.client.get(f'/api/v1/controls/{self.control.id}/notes')
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)

        self.client.force_authenticate(user=manager)
        patch_response = self.client.patch(
            f'/api/v1/controls/{self.control.id}/notes/{note_id}',
            {'resolved': True},
            format='json',
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertTrue(patch_response.json()['resolved'])

        delete_response = self.client.delete(f'/api/v1/controls/{self.control.id}/notes/{note_id}')
        self.assertEqual(delete_response.status_code, 204)
        self.assertEqual(ControlNote.objects.count(), 0)

    def test_compliance_alert_auto_create_and_clear(self):
        EvidenceRule.objects.create(
            standard_pack=self.pack,
            scope_type=EvidenceRule.SCOPE_CONTROL,
            control=self.control,
            rule_type=EvidenceRule.RULE_FREQUENCY,
            frequency_days=15,
            min_items=1,
            enabled=True,
        )

        self._create_and_link_evidence(control=self.control, event_date=timezone.localdate() - timedelta(days=50))
        status_response = self.client.get(f'/api/v1/controls/{self.control.id}/status')
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()['computed_status'], 'OVERDUE')

        overdue_alert = ComplianceAlert.objects.filter(control=self.control, alert_type='OVERDUE', cleared_at__isnull=True).first()
        self.assertIsNotNone(overdue_alert)

        self._create_and_link_evidence(control=self.control, event_date=timezone.localdate())
        status_response = self.client.get(f'/api/v1/controls/{self.control.id}/status')
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()['computed_status'], 'READY')

        overdue_alert.refresh_from_db()
        self.assertIsNotNone(overdue_alert.cleared_at)

        self._assign_role(self.user, 'AUDITOR')
        alerts_response = self.client.get('/api/v1/alerts')
        self.assertEqual(alerts_response.status_code, 200)
