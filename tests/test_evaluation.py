from decimal import Decimal
import pytest
from evaluation.evaluate import evaluate, field_match


def test_numeric_field_uses_configured_tolerance():
    assert field_match("total", "10.005", "10.00", Decimal("0.01"))
    assert not field_match("total", "10.02", "10.00", Decimal("0.01"))


def test_evaluation_reports_per_field_and_micro_accuracy():
    pred = [{"vendor_name": "Vendor", "total": "10"}]
    truth = [{"vendor_name": "vendor", "total": "10.02"}]
    report = evaluate(pred, truth, Decimal("0.01"))
    assert report["records"] == 1
    assert report["fields"]["vendor_name"]["accuracy"] == 1
    assert report["fields"]["total"]["accuracy"] == 0
    assert 0 <= report["micro_field_accuracy"] <= 1


def test_evaluation_rejects_mismatched_row_counts():
    with pytest.raises(ValueError, match="Row count mismatch"):
        evaluate([{}], [])
