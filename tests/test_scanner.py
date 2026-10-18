import json

from sentry.audit import verify_audit_log
from sentry.cli import main
from sentry.scanner import scan_csv


def test_scan_csv_returns_masked_findings_and_verifies_audit(tmp_path):
    source = tmp_path / "synthetic_records.csv"
    source.write_text(
        "contact_email,pan_number,date_of_birth\n"
        "person.one@example.com,ABCPD1234E,2004-02-29\n",
        encoding="utf-8",
    )
    audit_path = tmp_path / "audit.jsonl"

    result = scan_csv(source, audit_path=audit_path)

    assert result.rows_scanned == 1
    assert {finding.pii_type for finding in result.findings} == {"EMAIL", "PAN", "DOB"}
    serialized = json.dumps([finding.model_dump() for finding in result.findings])
    for raw in ("person.one@example.com", "ABCPD1234E", "2004-02-29"):
        assert raw not in serialized
    verification = verify_audit_log(audit_path)
    assert verification.valid
    assert verification.records_checked == 2
    audit_text = audit_path.read_text(encoding="utf-8")
    for raw in ("person.one@example.com", "ABCPD1234E", "2004-02-29"):
        assert raw not in audit_text


def test_cli_scan_writes_masked_json_only(tmp_path):
    source = tmp_path / "synthetic_records.csv"
    source.write_text(
        "contact_email\nperson.one@example.com\n",
        encoding="utf-8",
    )
    out_path = tmp_path / "findings.json"
    audit_path = tmp_path / "audit.jsonl"

    exit_code = main(["scan", str(source), "--out", str(out_path), "--audit", str(audit_path)])

    assert exit_code == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["finding_count"] == 1
    assert "person.one@example.com" not in out_path.read_text(encoding="utf-8")
    assert "p***@example.com" in out_path.read_text(encoding="utf-8")


def test_cli_evaluate_sample_labels(tmp_path):
    root = __import__("pathlib").Path(__file__).resolve().parents[1]
    csv_path = root / "sample_data" / "demo_records.csv"
    labels_path = root / "sample_data" / "demo_labels.csv"
    out_path = tmp_path / "evaluation.json"
    audit_path = tmp_path / "eval.audit.jsonl"

    exit_code = main([
        "evaluate", str(csv_path), str(labels_path),
        "--out", str(out_path), "--audit", str(audit_path),
    ])

    assert exit_code == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    evaluation = payload["evaluation"]
    assert evaluation["labelled_items"] == 40
    assert evaluation["micro"]["true_positive"] == 3
    assert evaluation["micro"]["false_positive"] == 0
    assert evaluation["micro"]["false_negative"] == 0
    assert evaluation["unlabelled_predictions"] == 0
