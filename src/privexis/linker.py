"""Link discovered fields to declared metadata and score each one against the evidence checklist.

The checklist (config/checklist.yaml) says which evidence items a reviewer expects.
This module records TECHNICAL facts only (is the evidence present?). It never judges
whether a purpose or a retention period is legally adequate."""
from dataclasses import dataclass

import yaml

# Detection items are computed from the scanner's own finding. Metadata items are looked up
# in the declared metadata. Both kinds are listed in config/checklist.yaml.
DETECTION_CHECKS = {
    "name_hint": lambda f, spec: f.name_score > 0,
    "value_check": lambda f, spec: f.value_score >= spec.get("min_pass_rate", 0.8),
}
STATUS_COMPLETE = "Candidate: checklist complete"
STATUS_GAP = "EVIDENCE GAP FLAG"


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
    checklist: list       # one dict per checklist item: item, label, kind, required, present
    review_status: str


def load_metadata(path="config/metadata.yaml") -> dict:
    with open(path, encoding="utf-8") as f:
        return (yaml.safe_load(f) or {}).get("fields", {})


def load_checklist(path="config/checklist.yaml") -> dict:
    """Read and validate the evidence checklist."""
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    items = raw.get("items") or {}
    for name, spec in items.items():
        kind = spec.get("kind")
        if kind not in ("metadata", "detection"):
            raise ValueError(f"Checklist item '{name}': kind must be 'metadata' or 'detection'.")
        if kind == "detection" and name not in DETECTION_CHECKS:
            raise ValueError(f"Checklist item '{name}': unknown detection check. "
                             f"Known: {', '.join(DETECTION_CHECKS)}.")
    checklist = {"items": items,
                 "required": raw.get("required") or [],
                 "advisory": raw.get("advisory") or [],
                 "overrides": raw.get("overrides") or {}}
    lists = [checklist["required"], checklist["advisory"]]
    for over in checklist["overrides"].values():
        lists += [over.get("required", []), over.get("advisory", [])]
    for lst in lists:
        for name in lst:
            if name not in items:
                raise ValueError(f"Checklist refers to '{name}', which is not defined under items.")
    return checklist


def _lists_for(checklist: dict, cls: str):
    over = checklist["overrides"].get(cls, {})
    required = over.get("required", checklist["required"])
    advisory = [i for i in over.get("advisory", checklist["advisory"]) if i not in required]
    return required, advisory


def _clean(value) -> str:
    return str(value).strip() if value is not None else ""


def link(findings, metadata, checklist) -> list:
    rows = []
    for f in findings:
        if f.cls == "NONE":
            continue                          # only candidate personal-data fields
        entry = metadata.get(f"{f.source}:{f.table}:{f.column}") or {}
        required, advisory = _lists_for(checklist, f.cls)

        checks = []
        for item, spec in checklist["items"].items():      # fixed order: same in every row
            if item not in required and item not in advisory:
                continue
            if spec["kind"] == "metadata":
                present = bool(_clean(entry.get(item)))
            else:
                present = bool(DETECTION_CHECKS[item](f, spec))
            checks.append({"item": item, "label": spec.get("label", item),
                           "kind": spec["kind"], "required": item in required,
                           "present": present})

        gaps = []
        needs_metadata = any(c["kind"] == "metadata" and c["required"] for c in checks)
        if needs_metadata and not entry:
            gaps.append("NO_METADATA_ENTRY")
        gaps += [f"MISSING_{c['item'].upper()}" for c in checks
                 if c["required"] and not c["present"]]

        rows.append(InventoryRow(
            f.source, f.table, f.column, f.cls, f.confidence, f.evidence,
            _clean(entry.get("purpose")), _clean(entry.get("retention")),
            _clean(entry.get("owner")), gaps, checks,
            STATUS_GAP if gaps else STATUS_COMPLETE,
        ))
    return rows


def orphaned_metadata(findings, metadata) -> list:
    """Declared fields that the scanner did NOT flag: stale metadata, or a missed detection."""
    flagged = {f"{f.source}:{f.table}:{f.column}" for f in findings if f.cls != "NONE"}
    return sorted(set(metadata) - flagged)
