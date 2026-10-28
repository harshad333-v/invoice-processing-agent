from app.schemas import Invoice, ValidationIssue
from app.validators.duplicates import invoice_fingerprint, find_duplicate_candidates
from app.agent.risk import score_invoice_risk


def test_fingerprint_is_stable_for_normalized_invoice():
    a = Invoice(vendor_name="Example Vendor", gstin="27ABCDE1234F1Z0",
                invoice_number="INV- 001", invoice_date="2026-01-01", total="118.00")
    b = Invoice(vendor_name="Example Vendor", gstin="27ABCDE1234F1Z0",
                invoice_number="INV-001", invoice_date="2026-01-01", total="118")
    assert invoice_fingerprint(a) == invoice_fingerprint(b)


def test_duplicate_candidate_is_returned():
    invoice = Invoice(vendor_name="Example Vendor", gstin="27ABCDE1234F1Z0",
                      invoice_number="INV-001", invoice_date="2026-01-01", total="118")
    assert len(find_duplicate_candidates(invoice, [invoice])) == 1


def test_risk_score_is_bounded_and_explained():
    invoice = Invoice(total="0")
    issues = [ValidationIssue(code="missing_vendor", message="Missing vendor", severity="error")]
    result = score_invoice_risk(invoice, issues, [{"invoice_number": "INV-1"}])
    assert 0 <= result["score"] <= 100
    assert result["tier"] == "high"
    assert result["is_fraud_probability"] is False
    assert result["reasons"]
