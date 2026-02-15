import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()
CANONICAL_ROLES = ('ADMIN', 'MANAGER', 'AUDITOR', 'DATA_ENTRY', 'VIEWER')


class Command(BaseCommand):
    help = 'Ensure canonical roles exist and create default admin user if missing.'

    def handle(self, *args, **options):
        created_groups = []
        for role in CANONICAL_ROLES:
            group, created = Group.objects.get_or_create(name=role)
            if created:
                created_groups.append(role)
                self.stdout.write(self.style.SUCCESS(f'Created group: {role}'))

        if created_groups:
            self.stdout.write(self.style.SUCCESS(f'Groups created: {", ".join(created_groups)}'))
        else:
            self.stdout.write('All canonical groups already exist.')

        username = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
        password = os.getenv('DEFAULT_ADMIN_PASSWORD', 'admin12345')

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {username}'))
        else:
            self.stdout.write(f'Admin user "{username}" already exists.')
