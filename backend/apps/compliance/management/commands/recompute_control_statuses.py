from collections import Counter
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.compliance.engine import compute_control_status, recompute_and_persist
from apps.standards.models import StandardPack


class Command(BaseCommand):
    help = 'Recompute ControlStatusCache for controls in a standard pack.'

    def add_arguments(self, parser):
        parser.add_argument('--pack-version', type=str)
        parser.add_argument('--latest', action='store_true')
        parser.add_argument('--only-overdue', action='store_true')
        parser.add_argument('--only-near-due', type=int)
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--ignore-overdue', action='store_true')

    def handle(self, *args, **options):
        pack_version = options.get('pack_version')
        latest = options.get('latest')
        only_overdue = options.get('only_overdue')
        only_near_due = options.get('only_near_due')
        dry_run = options.get('dry_run')
        ignore_overdue = options.get('ignore_overdue')

        if bool(pack_version) == bool(latest):
            raise CommandError('Use exactly one of --pack-version <str> OR --latest')
        if only_overdue and only_near_due is not None:
            raise CommandError('Use either --only-overdue or --only-near-due, not both')
        if only_near_due is not None and only_near_due < 0:
            raise CommandError('--only-near-due must be >= 0')

        if latest:
            pack = StandardPack.objects.order_by('-created_at').first()
            if not pack:
                raise CommandError('No standard packs found')
        else:
            pack = StandardPack.objects.filter(version=pack_version).order_by('-created_at').first()
            if not pack:
                raise CommandError(f'No standard pack found for version={pack_version}')

        controls = list(pack.controls.select_related('status_cache').order_by('sort_order'))
        if not controls:
            self.stdout.write(self.style.WARNING('No controls found for selected pack'))
            return

        today = timezone.localdate()
        near_due_window_days = only_near_due if only_near_due is not None else 14
        near_due_cutoff = today + timedelta(days=near_due_window_days)

        counts = Counter()
        total = 0
        overdue_found = False

        for control in controls:
            computed = compute_control_status(control)
            due_date = computed.get('next_due_date')
            is_near_due = bool(
                due_date is not None
                and today <= due_date <= near_due_cutoff
                and computed['computed_status'] != 'OVERDUE'
            )

            if only_overdue and computed['computed_status'] != 'OVERDUE':
                continue
            if only_near_due is not None and not is_near_due:
                continue

            if dry_run:
                status_name = computed['computed_status']
            else:
                cache = recompute_and_persist(control, computed=computed)
                status_name = cache.computed_status

            counts[status_name] += 1
            if is_near_due:
                counts['NEAR_DUE'] += 1
            if status_name == 'OVERDUE':
                overdue_found = True
            total += 1

        mode_text = 'dry-run ' if dry_run else ''
        self.stdout.write(self.style.SUCCESS(f'Recomputed {mode_text}statuses for {total} controls in pack {pack.version}'))
        self.stdout.write(f'total: {total}')
        for status_name in ['NOT_STARTED', 'IN_PROGRESS', 'READY', 'VERIFIED', 'OVERDUE', 'NEAR_DUE']:
            self.stdout.write(f'{status_name}: {counts.get(status_name, 0)}')

        if overdue_found and not ignore_overdue:
            raise SystemExit(1)
