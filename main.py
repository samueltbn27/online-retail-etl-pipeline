from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from config import (
    CLEANED_FILE,
    REJECTED_FILE,
    SOURCE_FILE,
    SUMMARY_FILE,
)
from pipeline.extract import extract
from pipeline.load import LoadReport, load
from pipeline.transform import TransformResult, country_summary, monthly_summary, transform


@dataclass(slots=True)
class PipelineReport:
    source_file: Path
    load_report: LoadReport
    transform_result: TransformResult


def run(
    source_file: Optional[Path] = None,
    cleaned_file: Optional[Path] = None,
    rejected_file: Optional[Path] = None,
    summary_file: Optional[Path] = None,
    verbose: bool = True,
) -> PipelineReport:
    source = Path(source_file) if source_file is not None else SOURCE_FILE

    if verbose:
        _print_header("EXTRACT")
    extract_result = extract(source)
    if verbose:
        print(f"  Source        : {source}")
        print(f"  Total rows    : {extract_result.total:,}")
        print(f"  Valid rows    : {extract_result.valid_count:,}")
        print(f"  Rejected rows : {extract_result.rejected_count:,}")

    if verbose:
        _print_header("TRANSFORM")
    transform_result = transform(extract_result.records)
    if verbose:
        print(f"  Sales rows         : {len(transform_result.sales):,}")
        print(f"  Returns rows       : {len(transform_result.returns):,}")
        print(f"  Duplicates removed : {transform_result.duplicates_removed:,}")
        print(f"  Invalid removed    : {transform_result.invalid_removed:,}")
        print(f"  Total revenue      : {transform_result.total_revenue:,.2f}")
        print(f"  Unique orders      : {transform_result.order_count:,}")
        print(f"  Unique customers   : {transform_result.customer_count:,}")

    if verbose:
        _print_header("LOAD")
    load_report = load(
        extract_result,
        transform_result,
        cleaned_path=Path(cleaned_file) if cleaned_file else CLEANED_FILE,
        rejected_path=Path(rejected_file) if rejected_file else REJECTED_FILE,
        summary_path=Path(summary_file) if summary_file else SUMMARY_FILE,
    )
    if verbose:
        print(f"  Cleaned  -> {load_report.cleaned_file} ({load_report.cleaned_rows:,} rows)")
        print(f"  Rejected -> {load_report.rejected_file} ({load_report.rejected_rows:,} rows)")
        print(f"  Summary  -> {load_report.summary_file} ({load_report.summary_rows:,} rows)")

    if verbose:
        _print_summary(transform_result)

    return PipelineReport(
        source_file=source,
        load_report=load_report,
        transform_result=transform_result,
    )


def _print_summary(transform_result: TransformResult) -> None:
    _print_header("TOP 5 COUNTRIES BY REVENUE")
    for row in country_summary(transform_result.sales)[:5]:
        print(f"  {row.country:<22} {row.revenue:>14,.2f}  ({row.order_count:,} orders)")

    _print_header("MONTHLY SUMMARY")
    for row in monthly_summary(transform_result.sales):
        print(
            f"  {row.period}  revenue={row.revenue:>13,.2f}  "
            f"qty={row.quantity:>9,}  orders={row.order_count:>6,}"
        )


def _print_header(title: str) -> None:
    print()
    print(f"=== {title} " + "=" * (56 - len(title)))


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ETL pipeline for the Online Retail dataset.",
    )
    parser.add_argument("--source", type=Path, default=SOURCE_FILE, help="Raw input CSV.")
    parser.add_argument("--cleaned", type=Path, default=CLEANED_FILE, help="Cleaned output CSV.")
    parser.add_argument("--rejected", type=Path, default=REJECTED_FILE, help="Rejected rows output CSV.")
    parser.add_argument("--summary", type=Path, default=SUMMARY_FILE, help="Monthly summary output JSON.")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress progress output.")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)

    try:
        run(
            source_file=args.source,
            cleaned_file=args.cleaned,
            rejected_file=args.rejected,
            summary_file=args.summary,
            verbose=not args.quiet,
        )
    except FileNotFoundError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if not args.quiet:
        print()
        print("Pipeline finished successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
