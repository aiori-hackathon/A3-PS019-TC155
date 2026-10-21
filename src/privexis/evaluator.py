"""Compare scanner findings with the hand-labelled ground truth."""
import csv

CLASSES = ["NAME", "EMAIL", "PHONE", "GOVT_ID", "DOB"]


def load_labels(path="data/labels.csv") -> dict:
    with open(path, newline="", encoding="utf-8") as f:
        return {(r["source"], r["table"], r["column"]): r["true_class"]
                for r in csv.DictReader(f)}


def _ratio(num, den):
    return round(num / den, 3) if den else None     # None = undefined, not 0


def evaluate(findings, truth) -> dict:
    predicted = {(f.source, f.table, f.column): f.cls for f in findings}
    if set(predicted) != set(truth):
        raise ValueError("Scanned columns and labelled columns do not match. "
                         "Re-run generate_data.py and check the labels.")

    per_class = {}
    for cls in CLASSES:
        tp = sum(1 for k, t in truth.items() if t == cls and predicted[k] == cls)
        fp = sum(1 for k, t in truth.items() if t != cls and predicted[k] == cls)
        fn = sum(1 for k, t in truth.items() if t == cls and predicted[k] != cls)
        p, r = _ratio(tp, tp + fp), _ratio(tp, tp + fn)
        f1 = round(2 * p * r / (p + r), 3) if p and r else None
        per_class[cls] = {"tp": tp, "fp": fp, "fn": fn,
                          "precision": p, "recall": r, "f1": f1}

    errors = [(k, truth[k], predicted[k]) for k in sorted(truth)
              if truth[k] != predicted[k]]
    return {"per_class": per_class, "errors": errors, "columns": len(truth)}