"""One reusable pipeline, shared by the command line and the web app.

    files -> sample every column -> score it -> link metadata -> (report)
"""
import csv
import io
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from privexis.engine import score_column
from privexis.linker import link, orphaned_metadata
from privexis.sampler import sample_path

SOURCE_SUFFIXES = {".csv", ".sqlite", ".sqlite3", ".db"}
METADATA_COLUMNS = ("source", "table", "column", "purpose", "retention", "owner")


@dataclass
class PipelineResult:
    findings: list                 # every scanned column, including class "NONE"
    rows: list                     # candidate personal-data fields + linked metadata
    orphans: list                  # declared metadata that matches no candidate field
    samples: dict = field(default_factory=dict)   # (source, table, column) -> sampled values


def find_sources(data_dir) -> list:
    """CSV / SQLite files in a folder (the answer-key file labels.csv is skipped)."""
    return [p for p in sorted(Path(data_dir).iterdir())
            if p.suffix.lower() in SOURCE_SUFFIXES and p.name != "labels.csv"]


def run_pipeline(paths, rules, scoring, metadata, k: int = 50) -> PipelineResult:
    findings, samples = [], {}
    for path in paths:
        for s in sample_path(path, k=k):
            samples[(s.source, s.table, s.column)] = s.values
            findings.append(score_column(s, rules, scoring))
    return PipelineResult(findings,
                          link(findings, metadata),
                          orphaned_metadata(findings, metadata),
                          samples)


def parse_metadata(raw: bytes, filename: str) -> dict:
    """Read declared metadata from an uploaded file.

    YAML: same layout as config/metadata.yaml.
    CSV:  columns source, table, column, purpose, retention, owner
          (source = file name; table = SQLite table, or empty for a CSV file).
    Returns {"source:table:column": {"purpose":..., "retention":..., "owner":...}}.
    """
    text = raw.decode("utf-8-sig")
    if filename.lower().endswith((".yaml", ".yml")):
        data = yaml.safe_load(text) or {}
        if not isinstance(data, dict) or not isinstance(data.get("fields", {}), dict):
            raise ValueError("A metadata YAML file needs a top-level 'fields:' mapping.")
        return data.get("fields", {})

    reader = csv.DictReader(io.StringIO(text))
    missing = [c for c in ("source", "column") if c not in (reader.fieldnames or [])]
    if missing:
        raise ValueError("A metadata CSV needs these columns: "
                         + ", ".join(METADATA_COLUMNS) + f" (missing: {', '.join(missing)}).")
    out = {}
    for r in reader:
        source, column = (r.get("source") or "").strip(), (r.get("column") or "").strip()
        if not source or not column:
            continue
        table = (r.get("table") or "").strip() or "-"
        out[f"{source}:{table}:{column}"] = {
            k: (r.get(k) or "").strip() for k in ("purpose", "retention", "owner")}
    return out


def metadata_template_csv() -> str:
    """A starter file people can download, fill in and upload."""
    return ("source,table,column,purpose,retention,owner\n"
            "customers.csv,,email,Service communication,Account closure + 1 year,Support team\n")
