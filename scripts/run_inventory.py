from pathlib import Path

from privexis.engine import load_config, scan_path
from privexis.linker import link, load_metadata, orphaned_metadata
from privexis.report import write_gap_report, write_inventory

rules, scoring = load_config()
findings = []
for p in sorted(Path("data").iterdir()):
    if p.suffix in (".csv", ".sqlite") and p.name != "labels.csv":
        findings += scan_path(p, rules, scoring)

metadata = load_metadata()
rows = link(findings, metadata)
orphans = orphaned_metadata(findings, metadata)

write_inventory(rows)
write_gap_report(rows, orphans)

gaps = [r for r in rows if r.gaps]
print(f"{len(rows)} candidate fields, {len(gaps)} with gaps")
for r in gaps:
    print(f"  {r.source}:{r.column:14} {r.cls:8} {', '.join(r.gaps)}")
print("Wrote reports/inventory.json, inventory.csv, gap_report.md")