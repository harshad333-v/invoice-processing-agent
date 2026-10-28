import hashlib
import re
from decimal import Decimal
from app.schemas import Invoice


def _normal(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").casefold())


def invoice_fingerprint(invoice: Invoice) -> str:
    """Stable fingerprint; candidate signal only, not proof of fraud."""
    parts = [_normal(invoice.gstin), _normal(invoice.vendor_name), _normal(invoice.invoice_number),
             str(Decimal(invoice.total).quantize(Decimal("0.01"))),
             invoice.invoice_date.isoformat() if invoice.invoice_date else ""]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def find_duplicate_candidates(invoice: Invoice, prior_invoices: list[Invoice]) -> list[dict]:
    current = invoice_fingerprint(invoice)
    return [{"invoice_number": prior.invoice_number, "vendor_name": prior.vendor_name,
             "total": str(prior.total),
             "reason": "matching vendor, GSTIN, invoice number, date and total"}
            for prior in prior_invoices if invoice_fingerprint(prior) == current]
