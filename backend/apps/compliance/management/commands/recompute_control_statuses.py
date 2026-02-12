from collections import Counter

from django.core.management.base import BaseCommand, CommandError

from apps.compliance.engine import recompute_and_persist
from apps.standards.models import StandardPack


class Command(BaseCommand):
    help = 'Recompute ControlStatusCache for controls in a standard pack.'

    def add_arguments(self, parser):
        parser.add_argument('--pack-version', type=str)
        parser.add_argument('--latest', action='store_true')

    def handle(self, *args, **options):
        pack_version = options.get('pack_version')
        latest = options.get('latest')

        if bool(pack_version) == bool(latest):
            raise CommandError('Use exactly one of --pack-version <str> OR --latest')

        if latest:
            pack = StandardPack.objects.order_by('-created_at').first()
            if not pack:
                raise CommandError('No standard packs found')
        else:
            pack = StandardPack.objects.filter(version=pack_version).order_by('-created_at').first()
            if not pack:
                raise CommandError(f'No standard pack found for version={pack_version}')

        controls = pack.controls.all()
        if not controls.exists():
            self.stdout.write(self.style.WARNING('No controls found for selected pack'))
            return

        counts = Counter()
        total = 0
        for control in controls:
            cache = recompute_and_persist(control)
            counts[cache.computed_status] += 1
            total += 1

        self.stdout.write(self.style.SUCCESS(f'Recomputed statuses for {total} controls in pack {pack.version}'))
        for status_name in ['NOT_STARTED', 'IN_PROGRESS', 'READY', 'VERIFIED', 'OVERDUE']:
            self.stdout.write(f'{status_name}: {counts.get(status_name, 0)}')
