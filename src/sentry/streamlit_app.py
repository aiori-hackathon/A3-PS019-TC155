"""Local Streamlit review UI for Sentry. Never renders or exports raw cell values."""

from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from sentry.audit import AuditIntegrityError, AuditLog, verify_audit_log
from sentry.config import ScannerConfig
from sentry.metadata import (
    ColumnMetadata,
    MetadataConfigError,
    metadata_coverage_rows,
    metadata_for_column,
    parse_column_metadata_csv,
)
from sentry.scanner import scan_csv


AUDIT_PATH = Path("outputs/streamlit.audit.jsonl")
MAX_METADATA_BYTES = 1_000_000

st.set_page_config(page_title="Sentry | PII Review", page_icon="🛡️", layout="wide")
st.title("Sentry — PII Governance Review")
st.caption(
    "Deterministic PII detection with masked evidence, purpose/retention context, and an audit trail. "
    "This tool reports technical signals; it does not make legal determinations."
)

with st.sidebar:
    st.header("Privacy and controls")
    st.write("Source rows are processed locally. The uploaded CSV is written to a temporary file for scanning and then removed.")
    st.write("The app stores masked findings and audit events, not raw cell values.")
    reviewer = st.text_input("Reviewer / actor label", value="reviewer", max_chars=128)
    st.caption("Use an approved internal label; avoid entering unnecessary personal information.")

source_upload = st.file_uploader("1. Choose a CSV dataset", type=["csv"], key="source_upload")
metadata_upload = st.file_uploader(
    "2. Choose the purpose/retention metadata CSV (optional)",
    type=["csv"],
    key="metadata_upload",
    help="Required headers: column_name, business_purpose, retention_period. Optional: data_owner, review_status.",
)
st.caption("Smoke-test files are in sample_data/: demo_records.csv and demo_column_metadata.csv.")

metadata_map: dict[str, ColumnMetadata] = {}
metadata_error: str | None = None
if metadata_upload is not None:
    try:
        metadata_bytes = metadata_upload.getvalue()
        if len(metadata_bytes) > MAX_METADATA_BYTES:
            raise MetadataConfigError("Metadata CSV exceeds the 1 MB limit.")
        metadata_text = metadata_bytes.decode("utf-8-sig")
        metadata_map = parse_column_metadata_csv(metadata_text)
        st.success(f"Loaded {len(metadata_map)} column metadata mapping(s).")
    except (UnicodeError, MetadataConfigError) as exc:
        metadata_error = str(exc)
        st.error(f"Metadata not loaded: {metadata_error}")


def _safe_upload_name(name: str) -> str:
    # Normalize both slash types because uploaded filenames may originate on Windows.
    cleaned = name.replace("\\", "/").rsplit("/", 1)[-1].strip()
    return cleaned if cleaned and cleaned.casefold().endswith(".csv") else "uploaded_source.csv"


def _read_header(path: Path, config: ScannerConfig) -> list[str]:
    """Read only the header for coverage reporting; never render row contents."""
    try:
        with path.open("r", encoding=config.encoding, newline="") as handle:
            reader = csv.reader(handle, strict=True)
            header = next(reader, None)
    except (OSError, UnicodeError, csv.Error):
        raise ValueError("CSV header could not be read. Check file structure and encoding.") from None
    if header is None:
        raise ValueError("CSV is empty and has no header row.")
    columns = [name.strip() for name in header]
    normalized = [name.casefold() for name in columns]
    if not columns or any(not name for name in columns) or len(normalized) != len(set(normalized)):
        raise ValueError("CSV header is blank or contains duplicate column names.")
    return columns


if "sentry_scan" not in st.session_state:
    st.session_state["sentry_scan"] = None
if "sentry_reviews" not in st.session_state:
    st.session_state["sentry_reviews"] = {}

if st.button("Scan uploaded CSV", type="primary", disabled=source_upload is None or bool(metadata_error)):
    config = ScannerConfig()
    uploaded_bytes = source_upload.getvalue() if source_upload is not None else b""
    if len(uploaded_bytes) > config.max_file_bytes:
        st.error(f"CSV exceeds the configured {config.max_file_bytes // (1024 * 1024)} MB limit.")
    elif not reviewer.strip():
        st.error("Enter a non-empty reviewer / actor label before scanning.")
    else:
        try:
            safe_name = _safe_upload_name(source_upload.name)
            with st.spinner("Scanning locally; raw cell values will not be displayed..."):
                with tempfile.TemporaryDirectory(prefix="sentry_scan_") as temporary_dir:
                    source_path = Path(temporary_dir) / safe_name
                    source_path.write_bytes(uploaded_bytes)
                    columns = _read_header(source_path, config)
                    audit_path = Path(AUDIT_PATH)
                    result = scan_csv(
                        source_path,
                        audit_path=audit_path,
                        config=config,
                        actor=reviewer.strip(),
                    )
                    verification = verify_audit_log(audit_path)
                    if not verification.valid:
                        raise AuditIntegrityError("Audit integrity verification failed.")

                    # Store only the schema-approved Finding fields and run metadata in session state.
                    safe_findings = [finding.model_dump(mode="json") for finding in result.findings]
                    st.session_state["sentry_scan"] = {
                        "scan_id": result.scan_id,
                        "source_file": safe_name,
                        "rows_scanned": result.rows_scanned,
                        "columns": columns,
                        "findings": safe_findings,
                        "audit_path": str(audit_path),
                        "audit_records_checked": verification.records_checked,
                        "audit_final_hash": verification.final_hash,
                    }
                    st.session_state["sentry_reviews"] = {}
            st.success("Scan completed. The temporary source file has been removed.")
        except Exception as exc:
            # Do not display exception messages or tracebacks that could include input fragments.
            st.error(
                f"Scan failed ({type(exc).__name__}). Check CSV structure, file size, and audit-log integrity. "
                "Input values are intentionally omitted from diagnostics."
            )

scan: dict[str, Any] | None = st.session_state.get("sentry_scan")
reviews: dict[str, dict[str, str]] = st.session_state["sentry_reviews"]

if scan:
    findings: list[dict[str, Any]] = scan["findings"]
    suppressed_count = sum(
        1 for index in range(len(findings))
        if reviews.get(f"{scan['scan_id']}:{index}", {}).get("decision") == "override_suppress"
    )
    active_findings = [
        finding for index, finding in enumerate(findings)
        if reviews.get(f"{scan['scan_id']}:{index}", {}).get("decision") != "override_suppress"
    ]
    coverage = metadata_coverage_rows(scan["columns"], metadata_map)
    missing_mappings = sum(1 for item in coverage if item["metadata_status"] == "Missing mapping")

    st.divider()
    st.subheader("Scan summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows scanned", scan["rows_scanned"])
    col2.metric("Findings", len(findings))
    col3.metric("Active after scan overrides", len(active_findings))
    col4.metric("Columns missing metadata", missing_mappings)
    st.caption(f"Scan ID: `{scan['scan_id']}` · Source: `{scan['source_file']}`")

    st.subheader("Purpose and retention coverage")
    if not metadata_map:
        st.info("Upload a metadata CSV to link each source column to its stated purpose and retention period.")
    else:
        st.dataframe(pd.DataFrame(coverage), use_container_width=True, hide_index=True)
    st.caption(
        "Metadata is displayed as supplied by the project team. A 'reviewed' flag is not independent proof "
        "of legal or policy compliance. Blank mappings should be resolved by the responsible data owner."
    )

    def _enriched_finding(index: int, finding: dict[str, Any]) -> dict[str, Any]:
        item = metadata_for_column(finding["column_name"], metadata_map)
        review = reviews.get(f"{scan['scan_id']}:{index}", {})
        return {
            "pii_type": finding["pii_type"],
            "masked_evidence": finding["masked_evidence"],
            "source_file": finding["source_file"],
            "row_number": finding["row_number"],
            "column_name": finding["column_name"],
            "rule_id": finding["rule_id"],
            "business_purpose": item.business_purpose if item else "",
            "retention_period": item.retention_period if item else "",
            "metadata_status": item.review_status if item else "Missing mapping",
            "review_action": review.get("action", "Not reviewed"),
            "active_for_this_scan": review.get("decision") != "override_suppress",
        }

    active_table = [
        _enriched_finding(index, finding)
        for index, finding in enumerate(findings)
        if reviews.get(f"{scan['scan_id']}:{index}", {}).get("decision") != "override_suppress"
    ]
    st.subheader("Active findings — masked evidence only")
    if active_table:
        st.dataframe(pd.DataFrame(active_table), use_container_width=True, hide_index=True)
    else:
        st.success("No active findings remain for this scan after recorded overrides.")

    if suppressed_count:
        with st.expander(f"View {suppressed_count} finding(s) suppressed for this scan"):
            st.dataframe(
                pd.DataFrame([
                    _enriched_finding(index, finding)
                    for index, finding in enumerate(findings)
                    if reviews.get(f"{scan['scan_id']}:{index}", {}).get("decision") == "override_suppress"
                ]),
                use_container_width=True,
                hide_index=True,
            )
            st.caption("Suppression is limited to this in-memory scan session; the deterministic engine is unchanged.")

    st.subheader("Manual review and scan-scoped overrides")
    st.caption(
        "Review actions are appended to the hash-chained audit log. Overrides affect only this scan session; "
        "they do not change the rule engine or future scans. No free-text reviewer notes are collected."
    )
    verification = verify_audit_log(scan["audit_path"])
    if verification.valid:
        st.success(f"Audit chain valid · {verification.records_checked} record(s) · final hash {verification.final_hash[:16]}…")
    else:
        st.error("Audit chain verification failed. Review actions are disabled.")

    action_options = {
        "Needs more context": ("finding_reviewed", "needs_review", "insufficient_context"),
        "Confirm as PII": ("finding_reviewed", "confirmed_pii", "confirmed_by_reviewer"),
        "Mark as false positive": ("finding_reviewed", "false_positive", "false_positive"),
        "Override: keep finding active for this scan": ("override_applied", "override_allow", "other"),
        "Override: suppress finding for this scan": ("override_applied", "override_suppress", "rule_exception"),
    }
    if not findings:
        st.info("No findings to review.")
    for index, finding in enumerate(findings):
        finding_id = f"{scan['scan_id']}:{index}"
        current = reviews.get(finding_id)
        title = f"{finding['pii_type']} · row {finding['row_number']} · {finding['column_name']}"
        with st.expander(title, expanded=(current is None)):
            st.write(f"**Masked evidence:** `{finding['masked_evidence']}`")
            st.write(f"**Rule:** `{finding['rule_id']}`")
            mapped = metadata_for_column(finding["column_name"], metadata_map)
            if mapped:
                st.write(f"**Purpose:** {mapped.business_purpose}")
                st.write(f"**Retention period as configured:** {mapped.retention_period}")
                st.write(f"**Metadata status:** {mapped.review_status}")
            else:
                st.warning("No purpose/retention mapping is configured for this column.")
            if current:
                st.info(f"Recorded action: {current['action']} · decision: {current['decision']}")
            if verification.valid and not current:
                with st.form(f"review_form_{index}"):
                    chosen_action = st.selectbox("Review action", list(action_options), key=f"action_{scan['scan_id']}_{index}")
                    submitted = st.form_submit_button("Record review in audit log", use_container_width=True)
                if submitted:
                    event_type, decision, reason_code = action_options[chosen_action]
                    try:
                        AuditLog(scan["audit_path"]).append(
                            event_type=event_type,
                            actor=reviewer.strip() or "reviewer",
                            scan_id=scan["scan_id"],
                            pii_type=finding["pii_type"],
                            rule_id=finding["rule_id"],
                            row_number=finding["row_number"],
                            column_name=finding["column_name"],
                            masked_evidence=finding["masked_evidence"],
                            decision=decision,
                            reason_code=reason_code,
                        )
                        reviews[finding_id] = {
                            "action": chosen_action,
                            "decision": decision,
                            "event_type": event_type,
                            "reason_code": reason_code,
                        }
                        st.session_state["sentry_reviews"] = reviews
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Review could not be recorded ({type(exc).__name__}). No success was assumed.")

    export_findings = [_enriched_finding(index, finding) for index, finding in enumerate(findings)]
    export_payload = {
        "schema_version": "1.0-review",
        "scan_id": scan["scan_id"],
        "source_file": scan["source_file"],
        "rows_scanned": scan["rows_scanned"],
        "findings": export_findings,
        "metadata_coverage": coverage,
        "audit": {
            "path": scan["audit_path"],
            "verified": verification.valid,
            "records_checked": verification.records_checked,
            "final_hash": verification.final_hash,
        },
        "scope_note": "Findings contain masked evidence only. Overrides are scan-session-only and do not alter future scans.",
    }
    st.download_button(
        "Download masked review report (JSON)",
        data=json.dumps(export_payload, ensure_ascii=False, indent=2, sort_keys=True),
        file_name="sentry-masked-review-report.json",
        mime="application/json",
    )

    st.subheader("Audit log")
    st.write(f"Local path: `{scan['audit_path']}`")
    st.write(f"Verified records: {verification.records_checked if verification.valid else 'verification failed'}")
    st.caption("Hash chaining is tamper-evident, not absolute immutability. Export periodic hashes to a separately controlled system for stronger assurance.")
else:
    st.info("Upload a CSV and click Scan uploaded CSV. The included synthetic files are recommended for the first UI smoke test.")
