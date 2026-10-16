from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional

from config import SOURCE_FILE
from pipeline.models import RetailRecord, ValidationError

SOURCE_ENCODING = "cp1252"

@dataclass(slots=True)
class RejectedRow:
    line_number: int
    raw: dict[str, str]
    reason: str

@dataclass(slots=True)
class ExtractResult:
    records: list[RetailRecord]
    rejected: list[RejectedRow]

    @property
    def total(self) -> int:
        return len(self.records) + len(self.rejected)

    @property
    def valid_count(self) -> int:
        return len(self.records)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected)

def iter_raw_rows(path: Path, encoding: str = SOURCE_ENCODING) -> Iterator[tuple[int, dict[str, str]]]:
    if not path.exists():
        raise FileNotFoundError(f"Source file not found: {path}")
    with path.open("r", newline="", encoding=encoding) as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"Source file has no header: {path}")
        for line_number, row in enumerate(reader, start=2):
            yield line_number, row

def extract_row(line_number: int, row: dict[str, str]) -> RetailRecord:
    return RetailRecord.from_row(row)

def extract(
    path: Optional[Path] = None,
    encoding: str = SOURCE_ENCODING,
) -> ExtractResult:
    source = Path(path) if path is not None else SOURCE_FILE
    records: list[RetailRecord] = []
    rejected: list[RejectedRow] = []

    for line_number, row in iter_raw_rows(source, encoding=encoding):
        try:
            records.append(extract_row(line_number, row))
        except ValidationError as error:
            rejected.append(
                RejectedRow(line_number=line_number, raw=row, reason=str(error))
            )

    return ExtractResult(records=records, rejected=rejected)

def extract_iter(
    path: Optional[Path] = None,
    encoding: str = SOURCE_ENCODING,
) -> Iterator[RetailRecord | RejectedRow]:
    source = Path(path) if path is not None else SOURCE_FILE
    for line_number, row in iter_raw_rows(source, encoding=encoding):
        try:
            yield extract_row(line_number, row)
        except ValidationError as error:
            yield RejectedRow(line_number=line_number, raw=row, reason=str(error))
