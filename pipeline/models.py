from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Optional


DATE_FORMAT = "%d-%m-%Y %H:%M"


class ValidationError(ValueError):
    def __init__(self, field: str, value: Any, reason: str) -> None:
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"{field}={value!r}: {reason}")


@dataclass(slots=True)
class RetailRecord:
    invoice_no: str
    stock_code: str
    description: str
    quantity: int
    invoice_date: datetime
    unit_price: float
    customer_id: Optional[str]
    country: str

    @property
    def is_cancellation(self) -> bool:
        return self.invoice_no.startswith("C")

    @property
    def total_price(self) -> float:
        return self.quantity * self.unit_price

    @property
    def has_customer(self) -> bool:
        return self.customer_id is not None

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "RetailRecord":
        invoice_no = _require_text(row, "InvoiceNo")
        stock_code = _require_text(row, "StockCode")
        description = str(row.get("Description") or "").strip()
        quantity = _parse_int(row, "Quantity")
        invoice_date = _parse_date(row, "InvoiceDate")
        unit_price = _parse_float(row, "UnitPrice")
        customer_id = _parse_customer_id(row)
        country = _require_text(row, "Country")

        return cls(
            invoice_no=invoice_no,
            stock_code=stock_code,
            description=description,
            quantity=quantity,
            invoice_date=invoice_date,
            unit_price=unit_price,
            customer_id=customer_id,
            country=country,
        )

    def to_row(self) -> dict[str, Any]:
        return {
            "InvoiceNo": self.invoice_no,
            "StockCode": self.stock_code,
            "Description": self.description,
            "Quantity": self.quantity,
            "InvoiceDate": self.invoice_date.strftime(DATE_FORMAT),
            "UnitPrice": self.unit_price,
            "CustomerID": self.customer_id if self.customer_id is not None else "",
            "Country": self.country,
            "TotalPrice": round(self.total_price, 2),
        }


def _require_text(row: Mapping[str, Any], field_name: str) -> str:
    value = str(row.get(field_name) or "").strip()
    if not value:
        raise ValidationError(field_name, row.get(field_name), "is required")
    return value


def _parse_int(row: Mapping[str, Any], field_name: str) -> int:
    raw = row.get(field_name)
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        raise ValidationError(field_name, raw, "must be an integer")


def _parse_float(row: Mapping[str, Any], field_name: str) -> float:
    raw = row.get(field_name)
    try:
        return float(str(raw).strip())
    except (TypeError, ValueError):
        raise ValidationError(field_name, raw, "must be a number")


def _parse_date(row: Mapping[str, Any], field_name: str) -> datetime:
    raw = str(row.get(field_name) or "").strip()
    try:
        return datetime.strptime(raw, DATE_FORMAT)
    except ValueError:
        raise ValidationError(field_name, raw, f"must match {DATE_FORMAT}")


def _parse_customer_id(row: Mapping[str, Any]) -> Optional[str]:
    raw = str(row.get("CustomerID") or "").strip()
    if not raw:
        return None
    if raw.endswith(".0"):
        raw = raw[:-2]
    return raw
