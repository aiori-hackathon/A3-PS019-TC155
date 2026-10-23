import sqlite3

import pytest

from privexis.engine import load_config
from privexis.linker import load_checklist
from privexis.pipeline import metadata_template_csv, parse_metadata, run_pipeline

RULES, SCORING = load_config()   # run pytest from the repo root so these paths resolve
CHECKLIST = load_checklist()


def test_parse_metadata_csv():
    raw = b"source,table,column,purpose,retention,owner\nt.csv,,email,Support,1 year,Ops\n"
    meta = parse_metadata(raw, "m.csv")
    assert meta["t.csv:-:email"] == {"purpose": "Support", "retention": "1 year", "owner": "Ops"}


def test_parse_metadata_csv_with_sqlite_table():
    raw = b"source,table,column,purpose\ndb.sqlite,people,name,Billing\n"
    assert "db.sqlite:people:name" in parse_metadata(raw, "m.csv")


def test_parse_metadata_yaml():
    raw = b'fields:\n  "t.csv:-:email":\n    purpose: Support\n'
    assert parse_metadata(raw, "m.yaml")["t.csv:-:email"]["purpose"] == "Support"


def test_parse_metadata_rejects_wrong_csv_columns():
    with pytest.raises(ValueError):
        parse_metadata(b"foo,bar\n1,2\n", "m.csv")


def test_template_is_valid_metadata():
    meta = parse_metadata(metadata_template_csv().encode(), "m.csv")
    assert "customers.csv:-:email" in meta


def test_pipeline_finds_renamed_columns_and_keeps_samples(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("Email ID,notes\na@x.com,hello\nb@y.org,ok\n", encoding="utf-8")
    res = run_pipeline([p], RULES, SCORING, {}, CHECKLIST)
    assert [r.cls for r in res.rows] == ["EMAIL"]
    assert "NO_METADATA_ENTRY" in res.rows[0].gaps
    assert res.samples[("t.csv", "-", "Email ID")] == ["a@x.com", "b@y.org"]


def test_pipeline_links_uploaded_metadata(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("email\na@x.com\n", encoding="utf-8")
    meta = {"t.csv:-:email": {"purpose": "p", "retention": "r", "owner": "o"}}
    assert run_pipeline([p], RULES, SCORING, meta, CHECKLIST).rows[0].gaps == []


def test_pipeline_reads_sqlite(tmp_path):
    db = tmp_path / "t.sqlite"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE people (mobile TEXT)")
    con.executemany("INSERT INTO people VALUES (?)", [("9876543210",), ("8123456789",)])
    con.commit()
    con.close()
    res = run_pipeline([db], RULES, SCORING, {}, CHECKLIST)
    assert res.rows[0].cls == "PHONE" and res.rows[0].table == "people"


def test_partial_evidence_goes_to_the_review_list(tmp_path):
    p = tmp_path / "t.csv"
    rows = ["a@x.com"] * 3 + ["call back"] * 7          # 30% emails: below threshold, above floor
    p.write_text("notes\n" + "\n".join(rows) + "\n", encoding="utf-8")
    res = run_pipeline([p], RULES, SCORING, {}, CHECKLIST)
    assert res.rows == []
    assert [f.column for f in res.review] == ["notes"]


def test_columns_with_no_evidence_are_not_listed_for_review(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("city\nPune\nJaipur\n", encoding="utf-8")
    assert run_pipeline([p], RULES, SCORING, {}, CHECKLIST).review == []


def test_scan_labelled_scores_a_folder_against_its_labels():
    from privexis.pipeline import scan_labelled
    findings, metrics = scan_labelled("data/holdout", "data/holdout/labels.csv", RULES, SCORING)
    assert metrics["columns"] == len(findings) == 21
    assert set(metrics["per_class"]) == {"NAME", "EMAIL", "PHONE", "GOVT_ID", "DOB"}
