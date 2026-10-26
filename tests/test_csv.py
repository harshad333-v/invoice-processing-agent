from app.schemas import Invoice
from app.exports.csv_export import invoice_to_csv

def test_csv_has_header_and_invoice_number():
    invoice = Invoice(vendor_name="Vendor", invoice_number="INV-1", total="10")
    output = invoice_to_csv(invoice)
    assert "invoice_number" in output and "INV-1" in output
