"""End-to-end CSV scanning orchestration for Sentry.

Raw cell values are passed directly from the CSV connector into the rule engine
and are never placed in ScanResult, JSON output, or audit events.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from sentry.audit import AuditIntegrityError, AuditLog, fingerprint_source, verify_audit_log
from sentry.config import ScannerConfig
from sentry.connectors.csv_source import iter_csv_rows
from sentry.models import Finding
from sentry.rules import scan_row


@dataclass(frozen=True, slots=True)
class ScanResult:
    """Safe scan result; it has no field for raw input rows or cell values."""

    scan_id: str
    source_file: str
    rows_scanned: int
    findings: tuple[Finding, ...]
    audit_path: str
    audit_records_checked: int
    audit_final_hash: str


def scan_csv(
    csv_path: str | Path,
    *,
    audit_path: str | Path = "outputs/sentry.audit.jsonl",
    config: ScannerConfig | None = None,
    actor: str = "system",
) -> ScanResult:
    """Scan one CSV, append scan events, and verify the resulting audit chain.

    The audit records use a fingerprint of the resolved source identifier, not
    the source path itself. This is correlation metadata, not anonymization;
    use a keyed HMAC at the fingerprinting boundary if that is required by the
    deployment's threat model.
    """
    source_path = Path(csv_path)
    cfg = config or ScannerConfig()
    scan_id = uuid4().hex
    source_file = source_path.name
    source_fingerprint = fingerprint_source(str(source_path.resolve()))
    audit = AuditLog(audit_path)

    # If source reading fails after this event, the log remains valid but has a
    # start without a completion event, making the incomplete run visible.
    audit.append(
        event_type="scan_started",
        actor=actor,
        scan_id=scan_id,
        source_fingerprint=source_fingerprint,
    )

    findings: list[Finding] = []
    rows_scanned = 0
    for record in iter_csv_rows(source_path, config=cfg):
        rows_scanned += 1
        findings.extend(
            scan_row(
                record.values,
                source_file=record.source_file,
                row_number=record.row_number,
                config=cfg,
            )
        )

    audit.append(
        event_type="scan_completed",
        actor=actor,
        scan_id=scan_id,
        source_fingerprint=source_fingerprint,
    )
    verification = verify_audit_log(audit_path)
    if not verification.valid:
        raise AuditIntegrityError("Audit integrity verification failed after the scan.")

    return ScanResult(
        scan_id=scan_id,
        source_file=source_file,
        rows_scanned=rows_scanned,
        findings=tuple(findings),
        audit_path=str(Path(audit_path)),
        audit_records_checked=verification.records_checked,
        audit_final_hash=verification.final_hash,
    )
