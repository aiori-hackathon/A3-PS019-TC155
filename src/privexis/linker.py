"""Link discovered fields to declared purpose/retention metadata and flag gaps.
This module records TECHNICAL facts (is metadata present?). It never judges
whether a purpose or retention period is legally adequate."""
from dataclasses import dataclass

import yaml


@dataclass
class InventoryRow:
    source: str
    table: str
    column: str
    cls: str
    confidence: float
    evidence: str
    purpose: str
    retention: str
    owner: str
    gaps: list            # e.g. ["MISSING_PURPOSE", "MISSING_RETENTION"]
    review_status: str


def load_metadata(path="config/metadata.yaml") -> dict:
    with open(path, encoding="utf-8") as f:
        return (yaml.safe_load(f) or {}).get("fields", {})


def _clean(value) -> str:
    return str(value).strip() if value is not None else ""


def link(findings, metadata) -> list:
    rows = []
    for f in findings:
        if f.cls == "NONE":
            continue                          # only candidate personal-data fields
        entry = metadata.get(f"{f.source}:{f.table}:{f.column}") or {}
        purpose = _clean(entry.get("purpose"))
        retention = _clean(entry.get("retention"))
        owner = _clean(entry.get("owner"))

        gaps = []
        if not entry:
            gaps.append("NO_METADATA_ENTRY")
        if not purpose:
            gaps.append("MISSING_PURPOSE")
        if not retention:
            gaps.append("MISSING_RETENTION")

        rows.append(InventoryRow(
            f.source, f.table, f.column, f.cls, f.confidence, f.evidence,
            purpose, retention, owner, gaps,
            "EVIDENCE GAP FLAG" if gaps else "Candidate - metadata linked",
        ))
    return rows


def orphaned_metadata(findings, metadata) -> list:
    """Declared fields that the scanner did NOT flag: stale metadata, or a missed detection."""
    flagged = {f"{f.source}:{f.table}:{f.column}" for f in findings if f.cls != "NONE"}
    return sorted(set(metadata) - flagged)