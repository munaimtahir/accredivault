# PHC Lab Licensing Checklist - Seed Data

## Source
This CSV file contains the Primary Healthcare (PHC) Lab Licensing Checklist controls.

## Version Information
- **Pack Version**: 1.0
- **Authority**: PHC (Primary Healthcare)
- **Total Controls**: 118
- **Last Updated**: 2026-02-08

## Structure
The CSV contains three columns:
- **Section**: Major category of the control (e.g., "Room & Building", "Laboratory Services")
- **Standard**: Sub-category or standard area
- **Indicator**: Specific requirement or compliance indicator

## Import Command
```bash
python manage.py import_phc_csv --path apps/standards/seed_data/phc/Final_PHC_list.csv --version 1.0 --publish
```

## Control Code Format
Controls are automatically assigned codes in the format: `PHC-{SECTION_ABBR}-{NNN}`
- Section abbreviation is the first 3 characters of the section name
- NNN is a 3-digit sequential number within that section

Examples:
- PHC-ROO-001 (Room & Building, first control)
- PHC-LAB-001 (Laboratory Services, first control)
- PHC-PER-001 (Personnel, first control)
