import re

GSTIN_PATTERN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")

def validate_gstin(value: str) -> list[str]:
    value = (value or "").strip().upper()
    if not value:
        return ["GSTIN is missing"]
    if not GSTIN_PATTERN.fullmatch(value):
        return ["GSTIN format is invalid"]
    # Format validation only; official checksum verification should be added before production.
    return []
