from app.validators.gstin import validate_gstin


def test_valid_gstin_checksum():
    assert validate_gstin("27ABCDE1234F1Z0") == []


def test_invalid_gstin_checksum_is_rejected():
    assert validate_gstin("27ABCDE1234F1Z5") == ["GSTIN checksum is invalid"]


def test_invalid_gstin_format_is_rejected():
    assert validate_gstin("not-a-gstin") == ["GSTIN format is invalid"]


def test_missing_gstin_is_rejected():
    assert validate_gstin("") == ["GSTIN is missing"]
