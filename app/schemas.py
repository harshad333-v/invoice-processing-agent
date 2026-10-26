from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict

class LineItem(BaseModel):
    description: str
    quantity: Decimal = Decimal("1")
    unit_price: Decimal = Decimal("0")
    amount: Decimal = Decimal("0")

class Invoice(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vendor_name: str = ""
    gstin: str = ""
    invoice_number: str = ""
    invoice_date: date | None = None
    line_items: list[LineItem] = Field(default_factory=list)
    taxable_value: Decimal = Decimal("0")
    cgst: Decimal = Decimal("0")
    sgst: Decimal = Decimal("0")
    igst: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    currency: str = "INR"

class ValidationIssue(BaseModel):
    code: str
    message: str
    severity: str = "error"
