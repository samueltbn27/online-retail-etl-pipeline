from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Iterator, Sequence

from pipeline.models import RetailRecord


@dataclass(slots=True, frozen=True)
class MonthlySales:
    year: int
    month: int
    revenue: float
    quantity: int
    order_count: int
    customer_count: int

    @property
    def period(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"


@dataclass(slots=True, frozen=True)
class CountrySales:
    country: str
    revenue: float
    quantity: int
    order_count: int
    customer_count: int


@dataclass(slots=True)
class TransformResult:
    sales: list[RetailRecord] = field(default_factory=list)
    returns: list[RetailRecord] = field(default_factory=list)
    duplicates_removed: int = 0
    invalid_removed: int = 0

    @property
    def total_revenue(self) -> float:
        return round(sum(record.total_price for record in self.sales), 2)

    @property
    def total_quantity(self) -> int:
        return sum(record.quantity for record in self.sales)

    @property
    def order_count(self) -> int:
        return len({record.invoice_no for record in self.sales})

    @property
    def customer_count(self) -> int:
        return len({record.customer_id for record in self.sales if record.has_customer})


def _dedupe_key(record: RetailRecord) -> tuple:
    return (
        record.invoice_no,
        record.stock_code,
        record.quantity,
        record.invoice_date,
        record.unit_price,
        record.customer_id,
    )


def is_valid_sale(record: RetailRecord) -> bool:
    return (
        not record.is_cancellation
        and record.quantity > 0
        and record.unit_price > 0
    )


def transform(records: Iterable[RetailRecord]) -> TransformResult:
    result = TransformResult()
    seen: set[tuple] = set()

    for record in records:
        key = _dedupe_key(record)
        if key in seen:
            result.duplicates_removed += 1
            continue
        seen.add(key)

        if record.is_cancellation:
            result.returns.append(record)
            continue

        if not is_valid_sale(record):
            result.invalid_removed += 1
            continue

        result.sales.append(record)

    return result


def monthly_summary(records: Sequence[RetailRecord]) -> list[MonthlySales]:
    buckets: dict[tuple[int, int], dict] = {}

    for record in records:
        period = (record.invoice_date.year, record.invoice_date.month)
        bucket = buckets.setdefault(
            period,
            {"revenue": 0.0, "quantity": 0, "orders": set(), "customers": set()},
        )
        bucket["revenue"] += record.total_price
        bucket["quantity"] += record.quantity
        bucket["orders"].add(record.invoice_no)
        if record.has_customer:
            bucket["customers"].add(record.customer_id)

    return [
        MonthlySales(
            year=year,
            month=month,
            revenue=round(data["revenue"], 2),
            quantity=data["quantity"],
            order_count=len(data["orders"]),
            customer_count=len(data["customers"]),
        )
        for (year, month), data in sorted(buckets.items())
    ]


def country_summary(records: Sequence[RetailRecord]) -> list[CountrySales]:
    buckets: dict[str, dict] = {}

    for record in records:
        bucket = buckets.setdefault(
            record.country,
            {"revenue": 0.0, "quantity": 0, "orders": set(), "customers": set()},
        )
        bucket["revenue"] += record.total_price
        bucket["quantity"] += record.quantity
        bucket["orders"].add(record.invoice_no)
        if record.has_customer:
            bucket["customers"].add(record.customer_id)

    rows = [
        CountrySales(
            country=country,
            revenue=round(data["revenue"], 2),
            quantity=data["quantity"],
            order_count=len(data["orders"]),
            customer_count=len(data["customers"]),
        )
        for country, data in buckets.items()
    ]
    return sorted(rows, key=lambda row: row.revenue, reverse=True)
