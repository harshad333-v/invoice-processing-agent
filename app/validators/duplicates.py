from app.schemas import Invoice

def duplicate_key(invoice: Invoice) -> tuple[str, str, str, str]:
    return (invoice.vendor_name.strip().casefold(), invoice.invoice_number.strip().casefold(), str(invoice.invoice_date or ""), str(invoice.total))

def is_duplicate(invoice: Invoice, existing_keys: set[tuple[str, str, str, str]]) -> bool:
    return duplicate_key(invoice) in existing_keys
