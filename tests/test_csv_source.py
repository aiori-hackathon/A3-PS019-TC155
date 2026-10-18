import pytest

from sentry.config import ScannerConfig
from sentry.connectors.csv_source import CSVSourceError, iter_csv_rows


def test_csv_rows_are_read_in_record_order(tmp_path):
    source = tmp_path / "synthetic.csv"
    source.write_text("name,email\nExample,person@example.com\n", encoding="utf-8")

    records = list(iter_csv_rows(source))
    assert len(records) == 1
    assert records[0].source_file == "synthetic.csv"
    assert records[0].row_number == 2
    assert records[0].values["name"] == "Example"


def test_duplicate_headers_are_rejected(tmp_path):
    source = tmp_path / "duplicate.csv"
    source.write_text("email,Email\na@example.com,b@example.com\n", encoding="utf-8")
    with pytest.raises(CSVSourceError, match="duplicate column"):
        list(iter_csv_rows(source))


def test_file_size_limit_is_enforced(tmp_path):
    source = tmp_path / "large.csv"
    source.write_text("name\nExample\n", encoding="utf-8")
    with pytest.raises(CSVSourceError, match="maximum file size"):
        list(iter_csv_rows(source, config=ScannerConfig(max_file_bytes=1)))
