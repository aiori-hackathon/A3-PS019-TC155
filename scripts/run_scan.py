from pathlib import Path
from privexis.engine import load_config, scan_path

rules, scoring = load_config()
for p in sorted(Path("data").iterdir()):
    if p.suffix in (".csv", ".sqlite") and p.name != "labels.csv":
        for f in scan_path(p, rules, scoring):
            print(f"{f.source:15} {f.column:14} {f.cls:8} {f.confidence:4}  {f.evidence}")