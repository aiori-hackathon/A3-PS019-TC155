"""Write the evidence inventory (JSON + CSV) and a human-readable gap report."""
import csv
import json
from dataclasses import asdict
from pathlib import Path

DISCLAIMER = ("TECHNICAL EVIDENCE ONLY. This report lists candidate personal-data "
              "fields and whether declared purpose/retention metadata exists. It makes "
              "no legal or compliance determination. Lawful basis and adequacy of "
              "purpose or retention are for a human reviewer to decide.")


def write_inventory(rows, out_dir="reports"):
    out = Path(out_dir)
    out.mkdir(exist_ok=True)
    data = [asdict(r) for r in rows]

    (out / "inventory.json").write_text(
        json.dumps({"disclaimer": DISCLAIMER, "fields": data}, indent=2),
        encoding="utf-8")

    with open(out / "inventory.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source", "table", "column", "class", "confidence", "purpose",
                    "retention", "owner", "gaps", "review_status", "evidence"])
        for r in rows:
            w.writerow([r.source, r.table, r.column, r.cls, r.confidence, r.purpose,
                        r.retention, r.owner, "|".join(r.gaps), r.review_status,
                        r.evidence])


def write_gap_report(rows, orphans, out_dir="reports"):
    gaps = [r for r in rows if r.gaps]
    lines = ["# Evidence Gap Report", "", f"> {DISCLAIMER}", "",
             f"- Candidate personal-data fields: **{len(rows)}**",
             f"- Fields with at least one metadata gap: **{len(gaps)}**",
             f"- Fields fully linked: **{len(rows) - len(gaps)}**", "",
             "## Fields with gaps", "",
             "| Source | Table | Column | Class | Gaps |",
             "|---|---|---|---|---|"]
    for r in gaps:
        lines.append(f"| {r.source} | {r.table} | {r.column} | {r.cls} | "
                     f"{', '.join(r.gaps)} |")
    lines += ["", "## Declared metadata with no matching candidate field", ""]
    lines += [f"- `{o}`" for o in orphans] or ["- none"]
    Path(out_dir, "gap_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")