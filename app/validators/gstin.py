import re

GSTIN_PATTERN = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
BASE36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _expected_check_digit(first_14: str) -> str:
    """Compute GSTIN's base-36 check digit using alternating factors 2 and 1."""
    total = 0
    factor = 2
    for char in reversed(first_14):
        product = BASE36.index(char) * factor
        total += product // 36 + product % 36
        factor = 1 if factor == 2 else 2
    return BASE36[(36 - total % 36) % 36]


def validate_gstin(value: str) -> list[str]:
    value = (value or "").strip().upper()
    if not value:
        return ["GSTIN is missing"]
    if not GSTIN_PATTERN.fullmatch(value):
        return ["GSTIN format is invalid"]
    if _expected_check_digit(value[:14]) != value[14]:
        return ["GSTIN checksum is invalid"]
    return []
