from decimal import Decimal
from app.schemas import Invoice, ValidationIssue
from .gstin import validate_gstin

CENT = Decimal("0.01")
def validate_invoice(invoice: Invoice, tolerance: Decimal = Decimal("1.00")) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    def add(code: str, msg: str, severity: str = "error"):
        issues.append(ValidationIssue(code=code, message=msg, severity=severity))
    if not invoice.vendor_name.strip(): add("missing_vendor", "Vendor name is missing")
    if not invoice.invoice_number.strip(): add("missing_invoice_number", "Invoice number is missing")
    for msg in validate_gstin(invoice.gstin): add("gstin", msg)
    if invoice.invoice_date is None: add("missing_date", "Invoice date is missing", "warning")
    if min(invoice.taxable_value, invoice.cgst, invoice.sgst, invoice.igst, invoice.total) < 0:
        add("negative_amount", "One or more monetary values are negative")
    calculated = invoice.taxable_value + invoice.cgst + invoice.sgst + invoice.igst
    if abs(calculated - invoice.total) > tolerance:
        add("tax_total_mismatch", f"Taxable value plus taxes ({calculated}) differs from total ({invoice.total})")
    if invoice.line_items:
        item_sum = sum((item.amount for item in invoice.line_items), Decimal("0"))
        if abs(item_sum - invoice.taxable_value) > tolerance:
            add("line_items_mismatch", f"Line-item sum ({item_sum}) differs from taxable value ({invoice.taxable_value})")
    if invoice.cgst and invoice.igst: add("mixed_tax_types", "CGST and IGST are both non-zero; verify invoice tax treatment")
    if invoice.sgst and invoice.igst: add("mixed_tax_types", "SGST and IGST are both non-zero; verify invoice tax treatment")
    return issues
