"""Command-line interface for safe CSV scans and labelled evaluation."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Sequence

from sentry.audit import AuditIntegrityError
from sentry.config import ScannerConfig
from sentry.connectors.csv_source import CSVSourceError
from sentry.evaluator import evaluate_findings, load_labels_csv
from sentry.scanner import ScanResult, scan_csv


def _write_json(path: str | Path, payload: dict[str, object]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".tmp")
    try:
        temporary.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink(missing_ok=True)


def _validate_distinct_paths(paths: Sequence[str | Path]) -> None:
    resolved = [Path(path).resolve() for path in paths]
    if len(set(resolved)) != len(resolved):
        raise ValueError("Input, output, labels and audit paths must all be different.")


def _scan_payload(result: ScanResult) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "scan_id": result.scan_id,
        "source_file": result.source_file,
        "rows_scanned": result.rows_scanned,
        "finding_count": len(result.findings),
        "findings": [finding.model_dump(mode="json") for finding in result.findings],
        "audit": {
            "path": result.audit_path,
            "verified": True,
            "records_checked": result.audit_records_checked,
            "final_hash": result.audit_final_hash,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sentry",
        description="Scan CSV data for PII and emit masked findings only.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Scan a CSV and write masked findings")
    scan_parser.add_argument("csv_path", help="Path to a CSV source")
    scan_parser.add_argument("--out", default="outputs/findings.json", help="Safe JSON findings output")
    scan_parser.add_argument("--audit", default="outputs/sentry.audit.jsonl", help="Hash-chained audit log")
    scan_parser.add_argument("--max-rows", type=int, default=None, help="Optional positive row limit for development")

    eval_parser = subparsers.add_parser("evaluate", help="Scan a CSV and evaluate against hand labels")
    eval_parser.add_argument("csv_path", help="Path to the same CSV named in the label file")
    eval_parser.add_argument("labels_path", help="CSV with source_file,row_number,column_name,pii_type,is_pii")
    eval_parser.add_argument("--out", default="outputs/evaluation_report.json", help="Evaluation report JSON output")
    eval_parser.add_argument("--audit", default="outputs/sentry-evaluation.audit.jsonl", help="Hash-chained audit log")
    eval_parser.add_argument("--max-rows", type=int, default=None, help="Optional positive row limit for development")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.max_rows is not None and args.max_rows <= 0:
            raise ValueError("--max-rows must be a positive integer.")

        paths: list[str | Path] = [args.csv_path, args.out, args.audit]
        if args.command == "evaluate":
            paths.append(args.labels_path)
        _validate_distinct_paths(paths)

        config = ScannerConfig(max_rows=args.max_rows)
        result = scan_csv(args.csv_path, audit_path=args.audit, config=config)

        if args.command == "scan":
            payload = _scan_payload(result)
            _write_json(args.out, payload)
            print(
                f"Scan complete: {result.rows_scanned} rows, {len(result.findings)} findings. "
                f"Audit verified ({result.audit_records_checked} records)."
            )
            print(f"Masked findings JSON: {Path(args.out)}")
            print(f"Audit log: {Path(args.audit)}")
            return 0

        labels = load_labels_csv(args.labels_path)
        report = evaluate_findings(result.findings, labels)
        payload = {
            "schema_version": "1.0",
            "scan_id": result.scan_id,
            "source_file": result.source_file,
            "rows_scanned": result.rows_scanned,
            "evaluation": report.model_dump(mode="json"),
            "note": (
                "Metrics are cell/type-level and apply only to the supplied labelled coverage. "
                "Review unlabelled_predictions before interpreting precision or recall."
            ),
        }
        _write_json(args.out, payload)
        micro = report.micro
        print(
            "Evaluation complete: "
            f"precision={micro.precision:.3f}, recall={micro.recall:.3f}, F1={micro.f1:.3f}; "
            f"unlabelled predictions={report.unlabelled_predictions}."
        )
        print(f"Evaluation report JSON: {Path(args.out)}")
        print(f"Audit log: {Path(args.audit)}")
        return 0

    except (CSVSourceError, AuditIntegrityError, OSError, ValueError) as exc:
        # Print the exception class only. Validation exceptions can include
        # input excerpts; those should not leak into terminal logs.
        print(
            f"Sentry operation failed ({type(exc).__name__}). "
            "Details are withheld to avoid exposing source data; check file structure and audit integrity.",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
