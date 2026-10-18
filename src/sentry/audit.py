"""Append-only, hash-chained audit records without raw PII fields.

This is tamper-evident, not a storage system with absolute immutability: a user
who can rewrite the entire file can recompute the chain. For stronger assurance,
export periodic chain hashes to a separately controlled system.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from sentry.models import PIIType

ZERO_HASH = "0" * 64

AuditEventType = Literal[
    "scan_started",
    "scan_completed",
    "finding_reviewed",
    "override_applied",
]
AuditDecision = Literal[
    "confirmed_pii",
    "false_positive",
    "needs_review",
    "override_allow",
    "override_suppress",
]
AuditReason = Literal[
    "confirmed_by_reviewer",
    "false_positive",
    "insufficient_context",
    "rule_exception",
    "other",
]

_MASK_PATTERNS: dict[str, re.Pattern[str]] = {
    "EMAIL": re.compile(r"^(?:[^@*\s]\*{3}|\*)@[A-Za-z0-9.-]+$"),
    "AADHAAR": re.compile(r"^XXXX XXXX [0-9]{4}$"),
    "PAN": re.compile(r"^XXXXX[0-9]{4}X$"),
    "DOB": re.compile(r"^\*\*/\*\*/\*\*\*\*$"),
}


class AuditPayload(BaseModel):
    """Allow-listed audit payload. Unknown fields (including raw_value) fail closed."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    sequence: int = Field(ge=1)
    timestamp_utc: str = Field(min_length=20, max_length=40)
    event_type: AuditEventType
    actor: str = Field(default="system", min_length=1, max_length=128)
    scan_id: str | None = Field(default=None, max_length=64)
    source_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    pii_type: PIIType | None = None
    rule_id: str | None = Field(default=None, max_length=128)
    row_number: int | None = Field(default=None, ge=2)
    column_name: str | None = Field(default=None, min_length=1, max_length=256)
    masked_evidence: str | None = Field(default=None, max_length=512)
    decision: AuditDecision | None = None
    reason_code: AuditReason | None = None

    @model_validator(mode="after")
    def evidence_must_be_masked(self) -> "AuditPayload":
        if self.masked_evidence is not None:
            if self.pii_type is None:
                raise ValueError("masked_evidence requires pii_type")
            pattern = _MASK_PATTERNS[self.pii_type]
            if pattern.fullmatch(self.masked_evidence) is None:
                raise ValueError("masked_evidence does not match the expected masked format")
        return self


@dataclass(frozen=True, slots=True)
class AuditVerification:
    valid: bool
    records_checked: int
    final_hash: str
    error: str | None = None
    bad_line: int | None = None


class AuditIntegrityError(RuntimeError):
    """Raised when the existing chain is invalid or the append is unsafe."""


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _record_hash(payload: dict[str, object], previous_hash: str) -> str:
    body = {"payload": payload, "prev_hash": previous_hash}
    return hashlib.sha256(_canonical_json(body).encode("utf-8")).hexdigest()


def fingerprint_source(source_identifier: str, *, key: str | bytes | None = None) -> str:
    """Return a stable source fingerprint without storing the source identifier.

    A keyed HMAC is preferable when a secret key can be managed securely. If no
    key is supplied, plain SHA-256 provides correlation, not anonymization.
    """
    source_bytes = source_identifier.encode("utf-8")
    if key is None:
        return hashlib.sha256(source_bytes).hexdigest()
    key_bytes = key.encode("utf-8") if isinstance(key, str) else key
    if not key_bytes:
        raise ValueError("key must not be empty")
    return hmac.new(key_bytes, source_bytes, hashlib.sha256).hexdigest()


def verify_audit_log(path: str | Path) -> AuditVerification:
    """Verify line order, payload schema, previous links, and event hashes."""
    audit_path = Path(path)
    if not audit_path.exists():
        return AuditVerification(True, 0, ZERO_HASH)

    previous_hash = ZERO_HASH
    checked = 0
    try:
        with audit_path.open("r", encoding="utf-8", newline="") as handle:
            for line_number, line in enumerate(handle, start=1):
                try:
                    record = json.loads(line)
                    if not isinstance(record, dict) or set(record) != {"payload", "prev_hash", "hash"}:
                        raise ValueError
                    payload = record["payload"]
                    previous_link = record["prev_hash"]
                    event_hash = record["hash"]
                    if not isinstance(payload, dict) or not isinstance(previous_link, str) or not isinstance(event_hash, str):
                        raise ValueError
                    validated = AuditPayload.model_validate(payload)
                    if validated.sequence != checked + 1:
                        raise ValueError
                    if previous_link != previous_hash:
                        return AuditVerification(
                            False, checked, previous_hash, "previous-hash link mismatch", line_number
                        )
                    expected = _record_hash(payload, previous_link)
                    if not hmac.compare_digest(event_hash, expected):
                        return AuditVerification(False, checked, previous_hash, "record hash mismatch", line_number)
                    previous_hash = event_hash
                    checked += 1
                except Exception:
                    return AuditVerification(False, checked, previous_hash, "invalid record or payload", line_number)
    except OSError:
        return AuditVerification(False, checked, previous_hash, "audit log could not be read")

    return AuditVerification(True, checked, previous_hash)


class AuditLog:
    """Single-writer JSONL audit log. Each append is flushed to disk and chained."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, **fields: object) -> dict[str, object]:
        """Append a typed event; unknown/unmasked payload fields are rejected."""
        reserved = {"sequence", "timestamp_utc", "prev_hash", "hash", "payload"}
        if reserved.intersection(fields):
            raise ValueError("sequence, timestamp, and chain fields are managed by AuditLog")

        self.path.parent.mkdir(parents=True, exist_ok=True)
        state = verify_audit_log(self.path)
        if not state.valid:
            raise AuditIntegrityError(
                "Existing audit log failed integrity verification; no record was appended."
            )

        payload_fields: dict[str, object] = {
            **fields,
            "sequence": state.records_checked + 1,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
        }
        payload = AuditPayload.model_validate(payload_fields).model_dump(mode="json", exclude_none=True)
        previous_hash = state.final_hash
        event_hash = _record_hash(payload, previous_hash)
        record: dict[str, object] = {
            "payload": payload,
            "prev_hash": previous_hash,
            "hash": event_hash,
        }

        # One process should own a given audit file at a time. The chain detects
        # corruption but this implementation does not provide a cross-process lock.
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(_canonical_json(record) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return record
