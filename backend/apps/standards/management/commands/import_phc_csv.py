import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.standards.models import StandardPack, Control
from apps.standards.phc_import_utils import (
    normalize_whitespace,
    normalize_key,
    resolve_section_code,
    is_repeated_header_row,
    compute_normalized_checksum,
)


class Command(BaseCommand):
    help = 'Import PHC checklist from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            required=True,
            help='Path to CSV file'
        )
        parser.add_argument(
            '--pack-version',
            type=str,
            required=True,
            help='Version number (e.g., 1.0)',
            dest='version'
        )
        parser.add_argument(
            '--new-version',
            type=str,
            required=False,
            help='Explicit new version to use if checksum differs (e.g., 1.0+rev1)',
            dest='new_version'
        )
        parser.add_argument(
            '--publish',
            action='store_true',
            help='Publish the pack immediately after import'
        )
        parser.add_argument(
            '--force-new-version',
            type=str,
            required=False,
            help='Force a new version string (e.g., 1.0+codes1) to re-import despite existing pack.',
            dest='force_new_version'
        )

    def handle(self, *args, **options):
        csv_path = options['path']
        version = options['version']
        publish = options['publish']
        force_new_version = options.get('force_new_version')
        
        # Resolve path
        if not csv_path.startswith('/'):
            # Relative to manage.py location
            csv_path = Path(__file__).resolve().parent.parent.parent.parent.parent / csv_path
        else:
            csv_path = Path(csv_path)
        
        if not csv_path.exists():
            raise CommandError(f"CSV file not found: {csv_path}")
        
        self.stdout.write(f"Reading CSV from: {csv_path}")
        
        # Compute checksum (normalized line endings)
        checksum = compute_normalized_checksum(csv_path)
        
        self.stdout.write(f"File checksum: {checksum}")
        
        # Check for existing pack with same checksum
        existing_by_checksum = StandardPack.objects.filter(checksum=checksum).first()
        if existing_by_checksum:
            if not force_new_version:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Pack already imported: {existing_by_checksum} (checksum match). No action taken."
                    )
                )
                return
            self.stdout.write(f"Checksum match, but forcing new version: {force_new_version}")
        
        # Check for existing pack with same authority+version
        existing_by_version = StandardPack.objects.filter(
            authority_code='PHC',
            version=version
        ).first()
        
        if existing_by_version or existing_by_checksum:
            if not force_new_version:
                raise CommandError(
                    f"Pack with version {version} already exists. "
                    f"Use --force-new-version <version> to re-import as a new version."
                )
            
            # Check if the forced version already exists
            if StandardPack.objects.filter(authority_code='PHC', version=force_new_version).exists():
                 raise CommandError(
                    f"Pack with version {force_new_version} already exists. Choose a different version."
                )
            version = force_new_version
            self.stdout.write(f"Using new version: {version}")
        
        # Parse CSV
        controls_data = []
        section_counters = {}
        seen_keys = set()
        duplicates_removed = 0
        non_empty_rows = 0

        with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
            # Read first line to detect headers
            reader = csv.DictReader(f)
            
            # Normalize header names (case and whitespace insensitive)
            fieldnames = reader.fieldnames
            if not fieldnames:
                raise CommandError("CSV file is missing headers.")
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
            
            for row in reader:
                section = normalize_whitespace(row.get(header_map['section'], ''))
                standard = normalize_whitespace(row.get(header_map['standard'], ''))
                indicator = normalize_whitespace(row.get(header_map['indicator'], ''))
                
                # Skip repeated header rows or blank indicators
                if is_repeated_header_row(section, standard, indicator):
                    continue
                if not indicator:
                    continue

                non_empty_rows += 1
                key = (normalize_key(section), normalize_key(standard), normalize_key(indicator))
                if key in seen_keys:
                    duplicates_removed += 1
                    continue
                seen_keys.add(key)
                
                # Generate control code
                section_code = resolve_section_code(section)
                if section_code not in section_counters:
                    section_counters[section_code] = 0
                
                section_counters[section_code] += 1
                control_code = f"PHC-{section_code}-{section_counters[section_code]:03d}"
                
                controls_data.append({
                    'control_code': control_code,
                    'section': section,
                    'standard': standard,
                    'indicator': indicator,
                    'sort_order': len(controls_data) + 1,
                })
        
        if not controls_data:
            raise CommandError("No valid control data found in CSV")
        
        self.stdout.write(f"Parsed {len(controls_data)} controls from CSV")
        self.stdout.write(f"Non-empty rows (indicator present): {non_empty_rows}")
        if duplicates_removed:
            self.stdout.write(
                self.style.WARNING(f"Removed {duplicates_removed} duplicate row(s) based on Section/Standard/Indicator.")
            )
        
        # Create pack and controls in transaction
        try:
            with transaction.atomic():
                # Create StandardPack
                pack = StandardPack.objects.create(
                    authority_code='PHC',
                    name='PHC Lab Licensing Checklist',
                    version=version,
                    status='draft',
                    checksum=checksum if not force_new_version else f"{checksum[:50]}-{version}",
                    source_file_name=csv_path.name,
                )
                
                self.stdout.write(f"Created StandardPack: {pack}")
                
                # Create Controls
                controls = []
                for data in controls_data:
                    control = Control(
                        standard_pack=pack,
                        **data
                    )
                    controls.append(control)
                
                Control.objects.bulk_create(controls)
                self.stdout.write(f"Created {len(controls)} controls")

                # Summary output
                section_summary = {}
                for control in controls_data:
                    section_code = control['control_code'].split('-')[1]
                    section_summary.setdefault(section_code, []).append(control['control_code'])
                self.stdout.write("Counts by section code:")
                for section_code in sorted(section_summary.keys()):
                    count = len(section_summary[section_code])
                    samples = ", ".join(section_summary[section_code][:3])
                    self.stdout.write(f"  {section_code}: {count} (sample: {samples})")
                
                # Publish if requested
                if publish:
                    pack.publish()
                    self.stdout.write(self.style.SUCCESS(f"Published pack: {pack}"))
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully imported PHC checklist version {version}"
                    )
                )
        
        except Exception as e:
            raise CommandError(f"Failed to import: {e}")
