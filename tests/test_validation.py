from decimal import Decimal
from app.schemas import Invoice, LineItem
from app.validators.run import validate_invoice

def base_invoice(**kwargs):
    data = dict(vendor_name="Example Vendor", gstin="27ABCDE1234F1Z5", invoice_number="INV-001", invoice_date="2026-01-01", taxable_value="100", cgst="9", sgst="9", igst="0", total="118", line_items=[{"description":"Item","quantity":"1","unit_price":"100","amount":"100"}])
    data.update(kwargs)
    return Invoice.model_validate(data)

def test_valid_totals_pass():
    assert not [i for i in validate_invoice(base_invoice()) if i.code == "tax_total_mismatch"]

def test_bad_total_is_flagged():
    assert any(i.code == "tax_total_mismatch" for i in validate_invoice(base_invoice(total="999")))

def test_missing_gstin_flagged():
    assert any(i.code == "gstin" for i in validate_invoice(base_invoice(gstin="")))
