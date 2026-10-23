from privexis.engine import load_config, score_column
from privexis.sampler import ColumnSample
from privexis.validators import verhoeff_check_digit

RULES, SCORING = load_config()   # run pytest from the repo root so this path resolves


def col(name, values):
    return ColumnSample("t.csv", "-", name, values, len(values))


def test_renamed_email_column_still_found():
    f = score_column(col("contact", ["a@x.com", "b.c@y.org"]), RULES, SCORING)
    assert f.cls == "EMAIL"


def test_failed_checksum_is_not_govt_id():
    body = "23456789012"
    bad = str((int(verhoeff_check_digit(body)) + 1) % 10)
    f = score_column(col("ref_no", [body + bad] * 5), RULES, SCORING)
    assert f.cls == "NONE"


def test_valid_aadhaar_found_without_name_hint():
    body = "23456789012"
    f = score_column(col("xyz", [body + verhoeff_check_digit(body)] * 5), RULES, SCORING)
    assert f.cls == "GOVT_ID"


def test_name_hint_alone_is_not_enough():
    f = score_column(col("file_name", ["report.pdf", "data.csv"]), RULES, SCORING)
    assert f.cls == "NONE"

def test_negative_hint_rules_out_a_date_of_birth():
    f = score_column(col("created_at", ["1990-05-17"] * 5), RULES, SCORING)
    assert f.cls == "NONE" and "negative hint 'created'" in f.evidence


def test_negative_hint_rules_out_a_phone_number():
    f = score_column(col("emp_code", ["9876543210"] * 5), RULES, SCORING)
    assert f.cls == "NONE"


def test_real_birth_date_column_is_still_found():
    f = score_column(col("birth_date", ["1990-05-17"] * 5), RULES, SCORING)
    assert f.cls == "DOB"


def test_evidence_names_the_checks_that_ran():
    f = score_column(col("mobile", ["9876543210"] * 5), RULES, SCORING)
    assert "10-digit mobile pattern" in f.evidence
