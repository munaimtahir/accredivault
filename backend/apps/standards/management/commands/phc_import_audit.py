import csv
from collections import Counter
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from apps.standards.phc_import_utils import (
    normalize_whitespace,
    normalize_key,
    is_repeated_header_row,
)


class Command(BaseCommand):
    help = 'Audit PHC checklist CSV file for import readiness'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            required=True,
            help='Path to CSV file'
        )

    def handle(self, *args, **options):
        csv_path = options['path']

        # Resolve path
        if not csv_path.startswith('/'):
            csv_path = Path(__file__).resolve().parent.parent.parent.parent.parent / csv_path
        else:
            csv_path = Path(csv_path)

        if not csv_path.exists():
            raise CommandError(f"CSV file not found: {csv_path}")

        self.stdout.write(f"Reading CSV from: {csv_path}")

        with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                raise CommandError("CSV file is missing headers.")

            # Normalize header names (case and whitespace insensitive)
            fieldnames = reader.fieldnames
            header_map = {}
            for field in fieldnames:
                normalized = normalize_key(field)
                if 'section' in normalized:
                    header_map['section'] = field
                elif 'standard' in normalized:
                    header_map['standard'] = field
                elif 'indicator' in normalized:
                    header_map['indicator'] = field

            if not all(k in header_map for k in ['section', 'standard', 'indicator']):
                raise CommandError(
                    f"CSV must have columns: Section, Standard, Indicator. Found: {fieldnames}"
                )

            raw_rows = 0
            non_empty_rows = 0
            section_counts = Counter()
            duplicate_counter = Counter()
            suspicious_rows = []

            for idx, row in enumerate(reader, start=1):
                raw_rows += 1
                section = normalize_whitespace(row.get(header_map['section'], ''))
                standard = normalize_whitespace(row.get(header_map['standard'], ''))
                indicator = normalize_whitespace(row.get(header_map['indicator'], ''))

                reasons = []
                if is_repeated_header_row(section, standard, indicator):
                    reasons.append("repeated header row")
                if not indicator:
                    reasons.append("blank indicator")
                if not (section or standard or indicator):
                    reasons.append("blank row")
                if indicator and not section:
                    reasons.append("missing section")
                if indicator and not standard:
                    reasons.append("missing standard")

                if reasons and len(suspicious_rows) < 10:
                    suspicious_rows.append({
                        'row': idx,
                        'reasons': ", ".join(reasons),
                        'section': section,
                        'standard': standard,
                        'indicator': indicator,
                    })

                if indicator:
                    non_empty_rows += 1
                    section_counts[section or "(blank)"] += 1
                    key = (normalize_key(section), normalize_key(standard), normalize_key(indicator))
                    duplicate_counter[key] += 1

            duplicate_rows = sum(count - 1 for count in duplicate_counter.values() if count > 1)
            unique_non_empty = non_empty_rows - duplicate_rows

            self.stdout.write(f"Total raw rows: {raw_rows}")
            self.stdout.write(f"Total non-empty rows (indicator present): {non_empty_rows}")
            self.stdout.write(f"Unique non-empty rows: {unique_non_empty}")
            self.stdout.write(f"Exact duplicate triples (Section, Standard, Indicator): {duplicate_rows}")
            self.stdout.write("Count by Section:")
            for section_name in sorted(section_counts.keys()):
                self.stdout.write(f"  {section_name}: {section_counts[section_name]}")

            self.stdout.write("Suspicious rows (first 10):")
            if not suspicious_rows:
                self.stdout.write("  None")
            else:
                for row in suspicious_rows:
                    self.stdout.write(
                        f"  Row {row['row']}: {row['reasons']} | "
                        f"Section='{row['section']}' Standard='{row['standard']}' Indicator='{row['indicator']}'"
                    )
