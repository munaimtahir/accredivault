import csv
import hashlib
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.standards.models import StandardPack, Control


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
            '--publish',
            action='store_true',
            help='Publish the pack immediately after import'
        )
        parser.add_argument(
            '--force-new-version',
            action='store_true',
            help='Force import as new version even if checksum differs'
        )

    def handle(self, *args, **options):
        csv_path = options['path']
        version = options['version']
        publish = options['publish']
        force_new_version = options['force_new_version']
        
        # Resolve path
        if not csv_path.startswith('/'):
            # Relative to manage.py location
            csv_path = Path(__file__).resolve().parent.parent.parent.parent.parent / csv_path
        else:
            csv_path = Path(csv_path)
        
        if not csv_path.exists():
            raise CommandError(f"CSV file not found: {csv_path}")
        
        self.stdout.write(f"Reading CSV from: {csv_path}")
        
        # Compute checksum
        with open(csv_path, 'rb') as f:
            file_content = f.read()
            checksum = hashlib.sha256(file_content).hexdigest()
        
        self.stdout.write(f"File checksum: {checksum}")
        
        # Check for existing pack with same checksum
        existing_by_checksum = StandardPack.objects.filter(checksum=checksum).first()
        if existing_by_checksum:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Pack already imported: {existing_by_checksum} (checksum match). No action taken."
                )
            )
            return
        
        # Check for existing pack with same authority+version
        existing_by_version = StandardPack.objects.filter(
            authority_code='PHC',
            version=version
        ).first()
        
        if existing_by_version:
            if not force_new_version:
                raise CommandError(
                    f"Pack with version {version} already exists but with different checksum. "
                    f"Use --force-new-version to import as {version}+rev1 or choose a different version."
                )
            else:
                # Auto-increment revision
                base_version = version
                revision = 1
                while StandardPack.objects.filter(
                    authority_code='PHC',
                    version=f"{base_version}+rev{revision}"
                ).exists():
                    revision += 1
                version = f"{base_version}+rev{revision}"
                self.stdout.write(f"Using new version: {version}")
        
        # Parse CSV
        controls_data = []
        section_counters = {}
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            # Read first line to detect headers
            reader = csv.DictReader(f)
            
            # Normalize header names (case and whitespace insensitive)
            fieldnames = reader.fieldnames
            header_map = {}
            for field in fieldnames:
                normalized = field.strip().lower()
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
            
            sort_order = 1
            for row in reader:
                section = row[header_map['section']].strip()
                standard = row[header_map['standard']].strip()
                indicator = row[header_map['indicator']].strip()
                
                # Skip empty rows
                if not section or not indicator:
                    continue
                
                # Generate control code
                if section not in section_counters:
                    section_counters[section] = 0
                
                section_counters[section] += 1
                # Create section abbreviation (first 3 chars uppercase, or full if short)
                section_abbr = section[:3].upper().replace(' ', '')
                control_code = f"PHC-{section_abbr}-{section_counters[section]:03d}"
                
                controls_data.append({
                    'control_code': control_code,
                    'section': section,
                    'standard': standard,
                    'indicator': indicator,
                    'sort_order': sort_order,
                })
                sort_order += 1
        
        if not controls_data:
            raise CommandError("No valid control data found in CSV")
        
        self.stdout.write(f"Parsed {len(controls_data)} controls from CSV")
        
        # Create pack and controls in transaction
        try:
            with transaction.atomic():
                # Create StandardPack
                pack = StandardPack.objects.create(
                    authority_code='PHC',
                    name='PHC Lab Licensing Checklist',
                    version=version,
                    status='draft',
                    checksum=checksum,
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
