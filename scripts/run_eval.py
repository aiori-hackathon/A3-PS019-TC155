import json
from pathlib import Path

from privexis.engine import load_config, scan_path
from privexis.evaluator import evaluate, load_labels

rules, scoring = load_config()
findings = []
for p in sorted(Path("data").iterdir()):
    if p.suffix in (".csv", ".sqlite") and p.name != "labels.csv":
        findings += scan_path(p, rules, scoring)

result = evaluate(findings, load_labels())

print(f"{'class':9} {'TP':>3} {'FP':>3} {'FN':>3} {'precision':>10} {'recall':>8} {'F1':>6}")
for cls, m in result["per_class"].items():
    print(f"{cls:9} {m['tp']:>3} {m['fp']:>3} {m['fn']:>3} "
          f"{str(m['precision']):>10} {str(m['recall']):>8} {str(m['f1']):>6}")

print(f"\nErrors ({len(result['errors'])} of {result['columns']} columns):")
for (src, tbl, col), true, pred in result["errors"]:
    print(f"  {src}:{col}  truth={true}  predicted={pred}")

Path("reports").mkdir(exist_ok=True)
Path("reports/metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print("\nSaved reports/metrics.json")