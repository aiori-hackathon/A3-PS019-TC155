from pathlib import Path
from privexis.sampler import sample_path

for p in sorted(Path("data").iterdir()):
    if p.suffix in (".csv", ".sqlite") and p.name != "labels.csv":
        for c in sample_path(p, k=3):
            print(f"{c.source:16} {c.table:5} {c.column:14} {c.non_empty:3} rows  {c.values}")