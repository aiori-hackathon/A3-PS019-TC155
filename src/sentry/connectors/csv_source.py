"""CSV input connector with structural checks and privacy-safe errors."""

from __future__ import annotations

import csv
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from sentry.config import ScannerConfig


class CSVSourceError(ValueError):
    """A CSV could not be read safely; messages intentionally omit cell data."""


@dataclass(frozen=True, slots=True)
class CSVRecord:
    """One in-memory source row.

    `values` contains raw input for the scanner and must never be logged,
    rendered in the UI, or serialized into scan results.
    `row_number` is the logical CSV record number (header is row 1).
    """

    source_file: str
    row_number: int
    values: dict[str, str]


def iter_csv_rows(
    path: str | Path,
    *,
    config: ScannerConfig | None = None,
) -> Iterator[CSVRecord]:
    """Yield CSV records while checking file size, headers and row shape."""
    cfg = config or ScannerConfig()
    csv_path = Path(path)

    try:
        if not csv_path.exists() or not csv_path.is_file():
            raise CSVSourceError("CSV source does not exist or is not a regular file.")
        if csv_path.stat().st_size > cfg.max_file_bytes:
            raise CSVSourceError("CSV exceeds the configured maximum file size.")

        with csv_path.open("r", encoding=cfg.encoding, newline="") as handle:
            reader = csv.reader(handle, strict=True)
            raw_header = next(reader, None)
            if raw_header is None:
                raise CSVSourceError("CSV is empty and has no header row.")

            header = [name.strip() for name in raw_header]
            if not header or any(not name for name in header):
                raise CSVSourceError("CSV header contains an empty column name.")
            normalized = [name.casefold() for name in header]
            if len(normalized) != len(set(normalized)):
                raise CSVSourceError("CSV header contains duplicate column names.")

            yielded = 0
            for record_number, row in enumerate(reader, start=2):
                if not row or all(not cell.strip() for cell in row):
                    continue
                if len(row) != len(header):
                    raise CSVSourceError(
                        f"Malformed CSV record {record_number}: expected {len(header)} columns, got {len(row)}."
                    )
                yield CSVRecord(
                    source_file=csv_path.name,
                    row_number=record_number,
                    values=dict(zip(header, row, strict=True)),
                )
                yielded += 1
                if cfg.max_rows is not None and yielded >= cfg.max_rows:
                    break

    except CSVSourceError:
        raise
    except (OSError, UnicodeError, csv.Error) as exc:
        # Do not include the exception string: some library errors can contain
        # snippets from the offending input. Keep diagnostics intentionally generic.
        raise CSVSourceError("CSV could not be read. Check the encoding and CSV structure.") from None
