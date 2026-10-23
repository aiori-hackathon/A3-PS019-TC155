"""Write the evidence inventory (JSON + CSV) and a human-readable gap report."""
import csv
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

DISCLAIMER = ("TECHNICAL EVIDENCE ONLY. This report lists candidate personal-data "
              "fields and whether the evidence on the configured checklist is present. "
              "It makes no legal or compliance determination. Lawful basis and the "
              "adequacy of any purpose or retention period are for a human reviewer to decide.")


def cell(check) -> str:
    """How one checklist item is shown: yes / NO (required, missing) / no (advisory, missing)."""
    if check["present"]:
        return "yes"
    return "**NO**" if check["required"] else "no"


def _checklist_text(r) -> str:
    return "|".join(f"{c['item']}:{cell(c).strip('*')}" for c in r.checklist)


def write_inventory(rows, out_dir="reports"):
    out = Path(out_dir)
    out.mkdir(exist_ok=True)

    (out / "inventory.json").write_text(
        json.dumps({"disclaimer": DISCLAIMER, "fields": [asdict(r) for r in rows]}, indent=2),
        encoding="utf-8")

    with open(out / "inventory.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source", "table", "column", "class", "confidence", "purpose",
                    "retention", "owner", "checklist", "gaps", "review_status", "evidence"])
        for r in rows:
            w.writerow([r.source, r.table, r.column, r.cls, r.confidence, r.purpose,
                        r.retention, r.owner, _checklist_text(r), "|".join(r.gaps),
                        r.review_status, r.evidence])


def write_gap_report(rows, orphans, out_dir="reports", review=None):
    review = review or []
    gaps = [r for r in rows if r.gaps]
    items = []                                           # checklist items, in checklist order
    for r in rows:
        for c in r.checklist:
            if c["item"] not in [i["item"] for i in items]:
                items.append(c)
    by_value_only = [r for r in rows
                     if any(c["item"] == "name_hint" and not c["present"] for c in r.checklist)]

    lines = ["# Evidence Gap Report", "", f"> {DISCLAIMER}", "",
             f"- Candidate personal-data fields: **{len(rows)}**",
             f"- Fields with at least one required evidence item missing: **{len(gaps)}**",
             f"- Fields with a complete checklist: **{len(rows) - len(gaps)}**",
             f"- Flagged by values alone (no column-name hint): **{len(by_value_only)}**",
             f"- Columns not flagged but worth a human look: **{len(review)}**", "",
             "## Evidence checklist", "",
             "`yes` = evidence present. `**NO**` = required item missing (an evidence gap). "
             "`no` = advisory item missing (shown for the reviewer, not counted as a gap).", "",
             "| Source | Column | Class | " + " | ".join(i["label"] for i in items) + " |",
             "|---|---|---|" + "---|" * len(items)]
    for r in rows:
        by_item = {c["item"]: c for c in r.checklist}
        cells = [cell(by_item[i["item"]]) if i["item"] in by_item else "n/a" for i in items]
        lines.append(f"| {r.source} | {r.column} | {r.cls} | " + " | ".join(cells) + " |")

    lines += ["", "## Fields with gaps", ""]
    if gaps:
        lines += ["| Source | Table | Column | Class | Gaps |", "|---|---|---|---|---|"]
        lines += [f"| {r.source} | {r.table} | {r.column} | {r.cls} | {', '.join(r.gaps)} |"
                  for r in gaps]
        tally = Counter(g for r in gaps for g in r.gaps)
        lines += ["", "Missing most often: " + ", ".join(
            f"`{g}` ({n})" for g, n in tally.most_common())]
    else:
        lines.append("- none")

    lines += ["", "## Needs human review (not flagged, but some evidence)", "",
              "These columns scored below the detection threshold but above the review floor. "
              "They are listed so a person can decide, not because the scanner thinks they are personal data.", ""]
    lines += [f"- `{f.source}` / `{f.column}`: {f.evidence}" for f in review] or ["- none"]

    lines += ["", "## Declared metadata with no matching candidate field", ""]
    lines += [f"- `{o}`" for o in orphans] or ["- none"]
    Path(out_dir, "gap_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
