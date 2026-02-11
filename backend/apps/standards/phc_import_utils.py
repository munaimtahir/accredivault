import hashlib
import re


_WHITESPACE_RE = re.compile(r"\s+")


def normalize_whitespace(value):
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return _WHITESPACE_RE.sub(" ", value).strip()


def normalize_key(value):
    return normalize_whitespace(value).casefold()


SECTION_CODE_MAP = {
    normalize_key("Responsibilities of Management"): "ROM",
    normalize_key("Quality Assurance"): "QA",
    normalize_key("Human Resource Management"): "HRM",
    normalize_key("Biosafety & Biosecurity"): "BSBS",
    normalize_key("Equipment & Reagents"): "MER",
    normalize_key("Facility Management & Safety"): "FMS",
    normalize_key("Recording & Reporting"): "RRS",
    normalize_key("Access"): "Access",
    normalize_key("Patient Rights & Education"): "PRE",
    normalize_key("Care of Patients"): "COP",
}

SHORT_CODE_MAP = {
    "rom": "ROM",
    "qa": "QA",
    "hrm": "HRM",
    "bsbs": "BSBS",
    "mer": "MER",
    "fms": "FMS",
    "rrs": "RRS",
    "access": "Access",
    "pre": "PRE",
    "cop": "COP",
}


def resolve_section_code(section_value, warn=None):
    section_display = normalize_whitespace(section_value)
    key = section_display.casefold()
    if key in SHORT_CODE_MAP:
        return SHORT_CODE_MAP[key]
    if key in SECTION_CODE_MAP:
        return SECTION_CODE_MAP[key]
    if warn:
        warn(section_display)
    letters_only = re.sub(r"[^A-Za-z]", "", section_display)
    fallback = letters_only[:3].upper()
    return fallback or "UNK"


def is_repeated_header_row(section, standard, indicator):
    return (
        normalize_key(section) == "section"
        and normalize_key(standard) == "standard"
        and normalize_key(indicator) == "indicator"
    )


def compute_normalized_checksum(path):
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
