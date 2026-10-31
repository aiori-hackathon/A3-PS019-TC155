import csv
import json
import sqlite3
from pathlib import Path

from backend.app.scanner import CLASSES, NOT_PERSONAL_DATA, classify, evaluate_cases, load_ground_truth, scan_source
from backend.data.generate_synthetic_datasets import DATA_DIR


def test_csv_duplicate_headers_and_detection(tmp_path):
    source = tmp_path / "members.csv"
    source.write_text("email,email,age,order_id\na@example.invalid,b@example.invalid,31,202610310001\n", encoding="utf-8")
    findings, rows, columns = scan_source("csv", source)
    assert rows == 1 and columns == 4
    assert {finding["column_name"] for finding in findings} == {"email (1)", "email (2)", "age"}
    assert all("a@example.invalid" not in finding["evidence"] for finding in findings)


def test_sqlite_scanning_and_source_is_read_only(tmp_path):
    source = tmp_path / "source.sqlite3"
    con = sqlite3.connect(source)
    con.execute("CREATE TABLE customers(email TEXT, age INTEGER, order_id TEXT)")
    con.execute("INSERT INTO customers VALUES('demo@example.invalid',31,'202610310001')")
    con.commit(); con.close()
    original = source.read_bytes()
    findings, rows, columns = scan_source("sqlite", source)
    assert rows == 1 and columns == 3
    assert {finding["data_class"] for finding in findings} == {"C1", "C2"}
    assert source.read_bytes() == original


def test_reproducible_ground_truth_covers_classes_and_negative_lookalikes():
    cases = load_ground_truth()
    labels = [label for _, _, label in cases]
    assert len(cases) == 175
    assert all(labels.count(code) == 25 for code in CLASSES)
    assert labels.count(NOT_PERSONAL_DATA) == 50
    results = evaluate_cases(cases)
    assert {row["class_code"] for row in results["classes"]} == set(CLASSES)
    assert [(row["tp"], row["fp"], row["fn"]) for row in results["classes"]] == [(25, 2, 0), (25, 4, 0), (25, 3, 0), (25, 2, 0), (25, 3, 0)]
    assert all(row["precision"] < 1 and row["recall"] == 1 for row in results["classes"])
    assert results["macro"] == {"precision": 0.8999, "recall": 1.0, "f1": 0.9472}
    assert results["confusion_matrix"][NOT_PERSONAL_DATA][NOT_PERSONAL_DATA] == 36


def test_lookalikes_are_not_personal_data():
    for name in ("order_id", "ticket_number", "email_opt_in", "phone_verified", "product_name", "postal_template_id"):
        assert classify(name, ["202610310001"]) == []


def test_all_ten_synthetic_fixtures_scan_as_expected():
    manifest = json.loads((DATA_DIR / "demo_files" / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest) == 10
    for fixture in manifest:
        path = DATA_DIR / "demo_files" / fixture["filename"]
        before = path.read_bytes() if fixture["kind"] == "sqlite" else None
        findings, rows, columns = scan_source(fixture["kind"], path, sample_rows=20)
        classes = {finding["data_class"] for finding in findings}
        assert fixture["class_code"] in classes, fixture
        assert rows == 20 and columns == 11
        assert len(findings) >= 8
        if before is not None:
            assert path.read_bytes() == before
