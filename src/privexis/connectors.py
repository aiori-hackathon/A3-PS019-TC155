"""Connectors: read CSV and SQLite through one common interface.
Both yield Table objects whose rows are a lazy iterator (no giant lists in memory)."""
import csv
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass
class Table:
    source: str            # file name, e.g. "onboarding.csv"
    name: str              # table name; "-" for CSV files
    columns: list          # column names, in order
    rows: Iterator         # iterator of row tuples/lists


def _csv_rows(path: Path) -> Iterator:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader, None)          # skip the header row
        yield from reader


def _csv_tables(path: Path) -> Iterator[Table]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        header = next(csv.reader(f), [])
    yield Table(path.name, "-", header, _csv_rows(path))


def _sqlite_tables(path: Path) -> Iterator[Table]:
    # mode=ro opens the database READ-ONLY: a scanner must never modify what it inspects.
    con = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        names = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        for t in names:
            # Table names can't be passed as ? parameters (only values can),
            # so we quote the identifier ourselves.
            safe = t.replace('"', '""')
            cur = con.execute(f'SELECT * FROM "{safe}"')
            cols = [d[0] for d in cur.description]
            yield Table(path.name, t, cols, iter(cur))
    finally:
        con.close()


def iter_tables(path) -> Iterator[Table]:
    """The one entry point. Picks the connector from the file extension."""
    path = Path(path)
    ext = path.suffix.lower()
    if ext == ".csv":
        return _csv_tables(path)
    if ext in (".sqlite", ".db", ".sqlite3"):
        return _sqlite_tables(path)
    raise ValueError(f"Unsupported source type: {path.name}")