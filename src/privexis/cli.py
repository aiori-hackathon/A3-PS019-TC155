"""Command-line entry point: one command runs the whole pipeline."""
import argparse
import json
from pathlib import Path

from privexis.engine import load_config
from privexis.evaluator import evaluate, load_labels
from privexis.linker import load_checklist, load_metadata
from privexis.pipeline import find_sources, run_pipeline
from privexis.report import write_gap_report, write_inventory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="privexis",
        description="Personal-data discovery and privacy evidence inventory "
                    "(technical evidence only, no legal determinations).")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="scan, link metadata, report gaps, evaluate")
    scan.add_argument("--data", default="data", help="folder with CSV/SQLite files")
    scan.add_argument("--config", default="config",
                      help="folder with rules.yaml, checklist.yaml and metadata.yaml")
    scan.add_argument("--labels", default="data/labels.csv",
                      help="hand-labelled ground truth (evaluation is skipped if absent)")
    scan.add_argument("--out", default="reports", help="output folder")
    scan.add_argument("--sample-size", type=int, default=50,
                      help="max values sampled per column")
    return parser


def run_scan(args) -> int:
    config = Path(args.config)
    rules, scoring = load_config(config / "rules.yaml")
    metadata = load_metadata(config / "metadata.yaml")
    checklist = load_checklist(config / "checklist.yaml")

    result = run_pipeline(find_sources(args.data), rules, scoring, metadata, checklist,
                          k=args.sample_size)
    findings, rows, orphans = result.findings, result.rows, result.orphans
    write_inventory(rows, args.out)
    write_gap_report(rows, orphans, args.out, result.review)

    gaps = [r for r in rows if r.gaps]
    print(f"Scanned {len(findings)} columns -> {len(rows)} candidate personal-data "
          f"fields, {len(gaps)} with evidence gaps, {len(result.review)} need review")

    labels_path = Path(args.labels)
    if labels_path.exists():
        try:
            result = evaluate(findings, load_labels(labels_path))
        except ValueError as e:
            print(f"Evaluation skipped: {e}")
        else:
            (Path(args.out) / "metrics.json").write_text(
                json.dumps(result, indent=2), encoding="utf-8")
            print("\nclass      precision   recall")
            for cls, m in result["per_class"].items():
                print(f"{cls:9} {str(m['precision']):>10} {str(m['recall']):>8}")
    else:
        print("No labels file found: evaluation skipped.")

    print(f"\nReports written to {args.out}/ (inventory.json, inventory.csv, "
          f"gap_report.md, metrics.json)")
    print("Reminder: this is technical evidence for human review, not a legal determination.")
    return 0


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "scan":
        return run_scan(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())