from decimal import Decimal, InvalidOperation
from app.schemas import Invoice, ValidationIssue
from .gstin import validate_gstin

CENT = Decimal("0.01")


def validate_invoice(invoice: Invoice, tolerance: Decimal = Decimal("1.00")) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    def add(code: str, msg: str, severity: str = "error", field: str | None = None):
        issues.append(ValidationIssue(code=code, message=msg, severity=severity, field=field))

    if not invoice.vendor_name.strip():
        add("missing_vendor", "Vendor name is missing", field="vendor_name")
    if not invoice.invoice_number.strip():
        add("missing_invoice_number", "Invoice number is missing", field="invoice_number")
    for msg in validate_gstin(invoice.gstin):
        add("gstin", msg, field="gstin")
    if invoice.invoice_date is None:
        add("missing_date", "Invoice date is missing", "warning", "invoice_date")
    if invoice.currency != "INR":
        add("currency_review", f"Currency {invoice.currency!r} requires explicit review", "warning", "currency")

    amounts = {
        "taxable_value": invoice.taxable_value, "cgst": invoice.cgst,
        "sgst": invoice.sgst, "igst": invoice.igst, "total": invoice.total,
    }
    for field, amount in amounts.items():
        if amount < 0:
            add("negative_amount", f"{field} cannot be negative", field=field)
    if invoice.taxable_value < 0 or invoice.total < 0:
        return issues

    calculated = invoice.taxable_value + invoice.cgst + invoice.sgst + invoice.igst
    if abs(calculated - invoice.total) > tolerance:
        add("tax_total_mismatch", f"Taxable value plus taxes ({calculated}) differs from total ({invoice.total})", field="total")

    for index, item in enumerate(invoice.line_items):
        if item.quantity < 0 or item.unit_price < 0 or item.amount < 0:
            add("negative_line_item", f"Line item {index + 1} has a negative quantity or amount", field="line_items")
        expected = (item.quantity * item.unit_price).quantize(CENT)
        if abs(expected - item.amount) > tolerance:
            add("line_item_arithmetic", f"Line item {index + 1}: quantity × unit price ({expected}) differs from amount ({item.amount})", field="line_items")
    if invoice.line_items:
        item_sum = sum((item.amount for item in invoice.line_items), Decimal("0"))
        if abs(item_sum - invoice.taxable_value) > tolerance:
            add("line_items_mismatch", f"Line-item sum ({item_sum}) differs from taxable value ({invoice.taxable_value})", field="taxable_value")

    if invoice.cgst and invoice.igst:
        add("mixed_tax_types", "CGST and IGST are both non-zero; verify invoice tax treatment", "warning", "igst")
    if invoice.sgst and invoice.igst:
        add("mixed_tax_types", "SGST and IGST are both non-zero; verify invoice tax treatment", "warning", "igst")
    if invoice.cgst != invoice.sgst and invoice.cgst and invoice.sgst:
        add("tax_split_mismatch", "CGST and SGST differ; verify the intra-state tax split", "warning", "cgst")
    if invoice.field_confidence:
        low = sorted(name for name, score in invoice.field_confidence.items() if score < 0.65)
        if low:
            add("low_extraction_confidence", "Low model-reported confidence for: " + ", ".join(low), "warning")
    return issues
