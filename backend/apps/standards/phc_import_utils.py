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
    normalize_key("Client Services"): "CLI",
    normalize_key("Laboratory Services"): "LAB",
    normalize_key("Personnel"): "PER",
    normalize_key("Quality Management"): "QMS",
    normalize_key("Record Keeping"): "RRS",
    normalize_key("Room & Building"): "RMB",
    normalize_key("Safety & Biosafety"): "BSB",
    normalize_key("Waste Management"): "WMS",
}


def resolve_section_code(section_value, warn=None):
    section_display = normalize_whitespace(section_value)
    key = section_display.casefold()

    if key in SECTION_CODE_MAP:
        return SECTION_CODE_MAP[key]

    raise ValueError(f"Unknown section: '{section_display}'")


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
