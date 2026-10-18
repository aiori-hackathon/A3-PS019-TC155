from __future__ import annotations

import pytest

from sentry.metadata import (
    MetadataConfigError,
    metadata_coverage_rows,
    metadata_for_column,
    parse_column_metadata_csv,
)


def test_parse_metadata_and_case_insensitive_lookup() -> None:
    text = (
        "column_name,business_purpose,retention_period,data_owner,review_status\n"
        "Email,Account contact,180 days,Ops,reviewed\n"
    )
    parsed = parse_column_metadata_csv(text)
    item = metadata_for_column("EMAIL", parsed)
    assert item is not None
    assert item.business_purpose == "Account contact"
    assert item.review_status == "reviewed"


def test_duplicate_case_insensitive_mapping_is_rejected() -> None:
    text = (
        "column_name,business_purpose,retention_period\n"
        "Email,One purpose,30 days\n"
        "email,Another purpose,60 days\n"
    )
    with pytest.raises(MetadataConfigError, match="duplicate"):
        parse_column_metadata_csv(text)


def test_required_headers_are_enforced() -> None:
    with pytest.raises(MetadataConfigError, match="must include"):
        parse_column_metadata_csv("column_name,description\nemail,contact\n")


def test_invalid_review_status_is_rejected_without_echoing_content() -> None:
    secret_like_value = "customer.secret@example.test"
    text = (
        "column_name,business_purpose,retention_period,review_status\n"
        f"email,Account contact,30 days,{secret_like_value}\n"
    )
    with pytest.raises(MetadataConfigError) as error:
        parse_column_metadata_csv(text)
    assert secret_like_value not in str(error.value)


def test_coverage_marks_unmapped_columns() -> None:
    parsed = parse_column_metadata_csv(
        "column_name,business_purpose,retention_period\nemail,Contact,30 days\n"
    )
    coverage = metadata_coverage_rows(["email", "transaction_date"], parsed)
    assert coverage[0]["metadata_status"] == "Draft"
    assert coverage[1]["metadata_status"] == "Missing mapping"
    assert coverage[1]["business_purpose"] == ""
