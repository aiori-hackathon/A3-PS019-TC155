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