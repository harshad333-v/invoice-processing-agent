from xml.etree.ElementTree import Element, SubElement, tostring
from app.schemas import Invoice

def invoice_to_tally_xml(invoice: Invoice) -> str:
    root = Element("ENVELOPE")
    body = SubElement(root, "BODY")
    data = SubElement(body, "INVOICE")
    for key, value in [("VENDOR", invoice.vendor_name), ("INVOICE_NUMBER", invoice.invoice_number), ("DATE", str(invoice.invoice_date or "")), ("TOTAL", str(invoice.total))]:
        SubElement(data, key).text = value
    return '<?xml version="1.0" encoding="UTF-8"?>' + tostring(root, encoding="unicode")
