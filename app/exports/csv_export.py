import csv, io
from app.schemas import Invoice

def invoice_to_csv(invoice: Invoice) -> str:
    stream = io.StringIO()
    fields = ["vendor_name","gstin","invoice_number","invoice_date","taxable_value","cgst","sgst","igst","total","currency"]
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    row = invoice.model_dump(mode="json")
    row.pop("line_items", None)
    writer.writerow({key: row.get(key, "") for key in fields})
    return stream.getvalue()
