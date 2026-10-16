from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

from config import CLEANED_FILE, REJECTED_FILE, SUMMARY_FILE
from pipeline.extract import ExtractResult, RejectedRow
from pipeline.models import RetailRecord
from pipeline.transform import (
    MonthlySales,
    TransformResult,
    monthly_summary,
)


CLEANED_COLUMNS = [
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
    "TotalPrice",
]

REJECTED_COLUMNS = [
    "LineNumber",
    "Reason",
    "InvoiceNo",
    "StockCode",
    "Description",
    "Quantity",
    "InvoiceDate",
    "UnitPrice",
    "CustomerID",
    "Country",
]


@dataclass(slots=True)
class LoadReport:
    cleaned_file: Path
    rejected_file: Path
    summary_file: Path
    cleaned_rows: int
    rejected_rows: int
    summary_rows: int


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_cleaned(
    records: Iterable[RetailRecord],
    path: Path = CLEANED_FILE,
    encoding: str = "utf-8",
) -> int:
    _ensure_parent(path)
    count = 0
    with path.open("w", newline="", encoding=encoding) as handle:
        writer = csv.DictWriter(handle, fieldnames=CLEANED_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow(record.to_row())
            count += 1
    return count


def write_rejected(
    rows: Sequence[RejectedRow],
    path: Path = REJECTED_FILE,
    encoding: str = "utf-8",
) -> int:
    _ensure_parent(path)
    with path.open("w", newline="", encoding=encoding) as handle:
        writer = csv.DictWriter(handle, fieldnames=REJECTED_COLUMNS)
        writer.writeheader()
        for rejected in rows:
            raw = rejected.raw
            writer.writerow(
                {
                    "LineNumber": rejected.line_number,
                    "Reason": rejected.reason,
                    "InvoiceNo": raw.get("InvoiceNo", ""),
                    "StockCode": raw.get("StockCode", ""),
                    "Description": raw.get("Description", ""),
                    "Quantity": raw.get("Quantity", ""),
                    "InvoiceDate": raw.get("InvoiceDate", ""),
                    "UnitPrice": raw.get("UnitPrice", ""),
                    "CustomerID": raw.get("CustomerID", ""),
                    "Country": raw.get("Country", ""),
                }
            )
    return len(rows)


def write_summary(
    monthly: Sequence[MonthlySales],
    path: Path = SUMMARY_FILE,
) -> int:
    _ensure_parent(path)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(
            [asdict(row) for row in monthly],
            handle,
            ensure_ascii=False,
            indent=2,
        )
    return len(monthly)


def load(
    extract_result: ExtractResult,
    transform_result: TransformResult,
    cleaned_path: Path = CLEANED_FILE,
    rejected_path: Path = REJECTED_FILE,
    summary_path: Path = SUMMARY_FILE,
) -> LoadReport:
    records = [*transform_result.sales, *transform_result.returns]
    cleaned_rows = write_cleaned(records, path=cleaned_path)
    rejected_rows = write_rejected(extract_result.rejected, path=rejected_path)
    summary_rows = write_summary(
        monthly_summary(transform_result.sales), path=summary_path
    )

    return LoadReport(
        cleaned_file=cleaned_path,
        rejected_file=rejected_path,
        summary_file=summary_path,
        cleaned_rows=cleaned_rows,
        rejected_rows=rejected_rows,
        summary_rows=summary_rows,
    )
