import json

import pytest
from pydantic import ValidationError

from sentry.audit import AuditIntegrityError, AuditLog, fingerprint_source, verify_audit_log


def test_audit_log_appends_and_verifies_chain(tmp_path):
    path = tmp_path / "audit" / "sentry.audit.jsonl"
    log = AuditLog(path)

    log.append(event_type="scan_started", actor="reviewer-01", scan_id="scan-001")
    log.append(
        event_type="finding_reviewed",
        actor="reviewer-01",
        scan_id="scan-001",
        pii_type="EMAIL",
        rule_id="EMAIL_RFC5322_V1",
        row_number=2,
        column_name="contact_email",
        masked_evidence="j***@example.com",
        decision="confirmed_pii",
        reason_code="confirmed_by_reviewer",
    )

    report = verify_audit_log(path)
    assert report.valid is True
    assert report.records_checked == 2
    contents = path.read_text(encoding="utf-8")
    assert "jane.doe@example.com" not in contents
    assert '"raw_value"' not in contents


def test_audit_rejects_unmasked_evidence_and_raw_fields(tmp_path):
    log = AuditLog(tmp_path / "audit.jsonl")
    with pytest.raises(ValidationError):
        log.append(
            event_type="finding_reviewed",
            pii_type="EMAIL",
            masked_evidence="jane.doe@example.com",
        )
    with pytest.raises(ValidationError):
        log.append(event_type="scan_started", raw_value="example secret")
    assert not (tmp_path / "audit.jsonl").exists()


def test_audit_detects_tampering_and_refuses_future_appends(tmp_path):
    path = tmp_path / "audit.jsonl"
    log = AuditLog(path)
    log.append(event_type="scan_started", actor="reviewer-01", scan_id="scan-001")

    record = json.loads(path.read_text(encoding="utf-8").strip())
    record["payload"]["actor"] = "rewritten-actor"
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    report = verify_audit_log(path)
    assert not report.valid
    with pytest.raises(AuditIntegrityError):
        log.append(event_type="scan_completed", scan_id="scan-001")


def test_fingerprint_source_is_repeatable_and_keyable():
    assert fingerprint_source("synthetic.csv") == fingerprint_source("synthetic.csv")
    assert fingerprint_source("synthetic.csv", key="demo-secret") != fingerprint_source(
        "synthetic.csv", key="different-secret"
    )
