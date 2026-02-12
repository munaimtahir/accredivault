import csv

from django.core.management.base import BaseCommand, CommandError

from apps.compliance.models import EvidenceRule
from apps.standards.models import Control, StandardPack


def _to_bool(value, default=False):
    if value is None or value == '':
        return default
    return str(value).strip().lower() in {'1', 'true', 'yes', 'y'}


def _to_int(value):
    if value is None or str(value).strip() == '':
        return None
    return int(str(value).strip())


def _to_list(value):
    if not value:
        return []
    return [chunk.strip() for chunk in str(value).split('|') if chunk.strip()]


class Command(BaseCommand):
    help = 'Import evidence rules from CSV for a specific pack version.'

    def add_arguments(self, parser):
        parser.add_argument('--path', required=True, type=str)
        parser.add_argument('--pack-version', required=True, type=str)

    def handle(self, *args, **options):
        path = options['path']
        pack_version = options['pack_version']

        pack = StandardPack.objects.filter(version=pack_version).order_by('-created_at').first()
        if not pack:
            raise CommandError(f'Standard pack not found for version={pack_version}')

        created_count = 0

        with open(path, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for row_num, row in enumerate(reader, start=2):
                scope_type = (row.get('scope_type') or '').strip().upper()
                target = (row.get('target') or '').strip()
                rule_type = (row.get('rule_type') or '').strip().upper()

                if scope_type not in {EvidenceRule.SCOPE_CONTROL, EvidenceRule.SCOPE_SECTION}:
                    raise CommandError(f'Invalid scope_type at row {row_num}: {scope_type}')
                if not target:
                    raise CommandError(f'Missing target at row {row_num}')

                control = None
                section_code = None
                if scope_type == EvidenceRule.SCOPE_CONTROL:
                    control = Control.objects.filter(standard_pack=pack, control_code=target).first()
                    if not control:
                        raise CommandError(f'Control not found at row {row_num}: {target}')
                else:
                    section_code = target

                rule = EvidenceRule.objects.create(
                    standard_pack=pack,
                    scope_type=scope_type,
                    control=control,
                    section_code=section_code,
                    rule_type=rule_type,
                    window_days=_to_int(row.get('window_days')),
                    frequency_days=_to_int(row.get('frequency_days')),
                    min_items=_to_int(row.get('min_items')) or 1,
                    requires_verification=_to_bool(row.get('requires_verification'), default=False),
                    acceptable_categories=_to_list(row.get('categories')),
                    acceptable_subtypes=_to_list(row.get('subtypes')),
                    enabled=_to_bool(row.get('enabled'), default=True),
                    notes=row.get('notes') or None,
                )
                created_count += 1
                self.stdout.write(f'Created rule {rule.id} ({rule.scope_type}:{rule.rule_type})')

        self.stdout.write(self.style.SUCCESS(f'Imported {created_count} rules for pack version {pack.version}'))
