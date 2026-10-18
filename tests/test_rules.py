import json

from sentry.config import ScannerConfig
from sentry.rules import scan_row
from sentry.validators import validate_dob


def test_scan_row_returns_masked_findings_only():
    row = {
        "email": "contact jane.doe@example.com",
        "pan_number": "ABCPD1234E",
        "Date of Birth": "2004-02-29",
        "comment": "order date 2024-01-15",
    }
    findings = scan_row(row, source_file="synthetic.csv", row_number=2)

    assert {f.pii_type for f in findings} == {"EMAIL", "PAN", "DOB"}
    serialized = json.dumps([finding.model_dump() for finding in findings])
    for raw in ("jane.doe@example.com", "ABCPD1234E", "2004-02-29"):
        assert raw not in serialized
    assert "**/**/****" in serialized
    assert all("raw_value" not in type(finding).model_fields for finding in findings)


def test_date_in_generic_column_is_not_dob_by_default():
    findings = scan_row(
        {"event_date": "2024-01-15"},
        source_file="synthetic.csv",
        row_number=2,
    )
    assert not [f for f in findings if f.pii_type == "DOB"]


def test_labelled_dob_detected_even_without_dob_header():
    findings = scan_row(
        {"notes": "DOB: 15/01/2004; next visit 15/02/2024"},
        source_file="synthetic.csv",
        row_number=2,
    )
    dates = [f for f in findings if f.pii_type == "DOB"]
    assert len(dates) == 1
    assert dates[0].masked_evidence == "**/**/****"


def test_config_validation():
    config = ScannerConfig(max_rows=10, require_dob_context=True)
    assert config.max_rows == 10
