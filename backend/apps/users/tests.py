from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from rest_framework.test import APIClient

from apps.standards.models import Control, StandardPack
from apps.evidence.models import EvidenceItem

User = get_user_model()
CANONICAL_ROLES = ('ADMIN', 'MANAGER', 'AUDITOR', 'DATA_ENTRY', 'VIEWER')


def _assign_role(user, role_name: str):
    group, _ = Group.objects.get_or_create(name=role_name)
    user.groups.add(group)


class AuthAndRBACTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        for role in CANONICAL_ROLES:
            Group.objects.get_or_create(name=role)

        self.pack = StandardPack.objects.create(
            authority_code='PHC',
            name='PHC Lab Licensing Checklist',
            version='1.0',
            status='draft',
            checksum='rbac-test-checksum',
        )
        self.control = Control.objects.create(
            standard_pack=self.pack,
            control_code='PHC-ROM-001',
            section='Records',
            standard='Test',
            indicator='Test',
            sort_order=1,
            active=True,
        )

    def test_login_returns_tokens_and_roles(self):
        admin = User.objects.create_user(username='admin', password='admin12345')
        _assign_role(admin, 'ADMIN')

        response = self.client.post(
            '/api/v1/auth/login',
            {'username': 'admin', 'password': 'admin12345'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('access', data)
        self.assertIn('refresh', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['username'], 'admin')
        self.assertIn('ADMIN', data['user']['roles'])
        self.assertIsInstance(data['user']['roles'], list)

    def test_unauthorized_request_to_controls_returns_401(self):
        response = self.client.get('/api/v1/controls/')
        self.assertEqual(response.status_code, 401)

    def test_viewer_can_read_controls_but_not_create_evidence(self):
        viewer = User.objects.create_user(username='viewer', password='viewer123')
        _assign_role(viewer, 'VIEWER')
        self.client.force_authenticate(user=viewer)

        controls_resp = self.client.get('/api/v1/controls/')
        self.assertEqual(controls_resp.status_code, 200)

        payload = {
            'title': 'Test Evidence',
            'category': 'certificate',
            'event_date': '2024-01-15',
        }
        create_resp = self.client.post('/api/v1/evidence-items', payload, format='json')
        self.assertEqual(create_resp.status_code, 403)

    def test_data_entry_can_create_evidence_but_not_verify(self):
        data_entry = User.objects.create_user(username='dataentry', password='dataentry123')
        _assign_role(data_entry, 'DATA_ENTRY')
        self.client.force_authenticate(user=data_entry)

        payload = {
            'title': 'Test Evidence',
            'category': 'certificate',
            'event_date': '2024-01-15',
        }
        create_resp = self.client.post('/api/v1/evidence-items', payload, format='json')
        self.assertEqual(create_resp.status_code, 201)

        verify_resp = self.client.post(
            f'/api/v1/controls/{self.control.id}/verify',
            {'remarks': 'OK'},
            format='json',
        )
        self.assertEqual(verify_resp.status_code, 403)

    def test_manager_can_verify_and_export(self):
        from unittest.mock import patch

        manager = User.objects.create_user(username='manager', password='manager123')
        _assign_role(manager, 'MANAGER')
        self.client.force_authenticate(user=manager)

        verify_resp = self.client.post(
            f'/api/v1/controls/{self.control.id}/verify',
            {'remarks': 'OK'},
            format='json',
        )
        self.assertIn(verify_resp.status_code, [200, 201])

        with patch('apps.compliance.views.get_s3_client') as mock_s3:
            mock_client = type('DummyS3', (), {
                'head_bucket': lambda *a, **k: None,
                'create_bucket': lambda *a, **k: None,
                'upload_fileobj': lambda *a, **k: None,
            })()
            mock_s3.return_value = mock_client
            export_resp = self.client.post(
                f'/api/v1/exports/control/{self.control.id}',
                {},
                format='json',
            )
        self.assertEqual(export_resp.status_code, 201)

    def test_admin_can_create_users_and_assign_roles(self):
        admin = User.objects.create_user(username='admin', password='admin12345')
        _assign_role(admin, 'ADMIN')
        self.client.force_authenticate(user=admin)

        create_resp = self.client.post(
            '/api/v1/users',
            {
                'username': 'newuser',
                'password': 'newuser123',
                'first_name': 'New',
                'last_name': 'User',
                'roles': ['VIEWER', 'DATA_ENTRY'],
            },
            format='json',
        )
        self.assertEqual(create_resp.status_code, 201)
        data = create_resp.json()
        self.assertEqual(data['username'], 'newuser')
        self.assertIn('VIEWER', data['roles'])
        self.assertIn('DATA_ENTRY', data['roles'])

    def test_health_remains_public(self):
        response = self.client.get('/api/v1/health')
        self.assertEqual(response.status_code, 200)
