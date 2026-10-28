from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, ConfigDict, field_validator


class LineItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str = ""
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
    # Evidence is a short source quotation/page hint, not a guarantee of correctness.
    field_evidence: dict[str, str] = Field(default_factory=dict)
    # Model-reported scores are uncalibrated; use only as review hints.
    field_confidence: dict[str, float] = Field(default_factory=dict)

    @field_validator("field_confidence")
    @classmethod
    def confidence_in_unit_interval(cls, value: dict[str, float]) -> dict[str, float]:
        if any(score < 0 or score > 1 for score in value.values()):
            raise ValueError("Field confidence values must be between 0 and 1")
        return value


class ValidationIssue(BaseModel):
    code: str
    message: str
    severity: str = "error"
    field: str | None = None
    model_config = ConfigDict(extra="forbid")


class AuditEvent(BaseModel):
    action: str
    actor: str = "system"
    details: dict[str, Any] = Field(default_factory=dict)
