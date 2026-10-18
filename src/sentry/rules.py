"""Deterministic PII candidate extraction and rule evaluation."""

from __future__ import annotations

import re
from collections.abc import Mapping

from sentry.config import ScannerConfig
from sentry.models import Finding
from sentry.validators import (
    DOB_DATE_PATTERN,
    mask_evidence,
    validate_aadhaar,
    validate_dob,
    validate_email_rfc5322,
    validate_pan,
)

EMAIL_CANDIDATE_RE = re.compile(
    r"(?<![A-Z0-9.!#$%&'*+/=?^_`{|}~-])"
    r"[A-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Z0-9!#$%&'*+/=?^_`{|}~-]+)*"
    r"@"
    r"[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?"
    r"(?:\.[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?)+"
    r"(?![A-Z0-9.-])",
    re.IGNORECASE,
)
AADHAAR_CANDIDATE_RE = re.compile(r"(?<![0-9])(?:[0-9][ -]?){11}[0-9](?![0-9])")
PAN_CANDIDATE_RE = re.compile(r"(?<![A-Z0-9])[A-Z]{3}[ABCFGHLJPT][A-Z][0-9]{4}[A-Z](?![A-Z0-9])", re.I)
DOB_CANDIDATE_RE = re.compile(DOB_DATE_PATTERN)
DOB_LABELLED_RE = re.compile(
    rf"\b(?:d\.?\s*o\.?\s*b\.?|date\s+of\s+birth|birth\s+date)\b"
    rf"\s*(?:[:=#-]\s*)?(?P<date>{DOB_DATE_PATTERN})",
    re.IGNORECASE,
)


def _column_is_dob(column_name: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", " ", column_name.casefold()).strip()
    tokens = normalized.split()
    return (
        "dob" in tokens
        or "birthdate" in tokens
        or "date of birth" in normalized
        or "birth date" in normalized
    )


def _finding(
    *,
    rule_id: str,
    pii_type: str,
    source_file: str,
    row_number: int,
    column_name: str,
    candidate: str,
) -> Finding:
    # The matched candidate is consumed only for masking and is never attached
    # to the returned Finding object.
    return Finding(
        rule_id=rule_id,
        pii_type=pii_type,  # type: ignore[arg-type]
        source_file=source_file,
        row_number=row_number,
        column_name=column_name,
        masked_evidence=mask_evidence(pii_type, candidate),
    )


def scan_row(
    values: Mapping[str, str | None],
    *,
    source_file: str,
    row_number: int,
    config: ScannerConfig | None = None,
) -> list[Finding]:
    """Scan one CSV row and return masked findings only.

    Raw cell values are used transiently in memory for candidate validation;
    callers must not log or serialize `values`. Returned findings contain no
    raw matched values.
    """
    cfg = config or ScannerConfig()
    findings: list[Finding] = []

    for column_name, raw_value in values.items():
        if not isinstance(raw_value, str) or not raw_value:
            continue

        for match in EMAIL_CANDIDATE_RE.finditer(raw_value):
            candidate = match.group(0)
            if validate_email_rfc5322(candidate):
                findings.append(
                    _finding(
                        rule_id="EMAIL_RFC5322_V1",
                        pii_type="EMAIL",
                        source_file=source_file,
                        row_number=row_number,
                        column_name=column_name,
                        candidate=candidate,
                    )
                )

        for match in AADHAAR_CANDIDATE_RE.finditer(raw_value):
            candidate = match.group(0)
            if validate_aadhaar(candidate):
                findings.append(
                    _finding(
                        rule_id="AADHAAR_VERHOEFF_V1",
                        pii_type="AADHAAR",
                        source_file=source_file,
                        row_number=row_number,
                        column_name=column_name,
                        candidate=candidate,
                    )
                )

        for match in PAN_CANDIDATE_RE.finditer(raw_value):
            candidate = match.group(0)
            if validate_pan(candidate):
                findings.append(
                    _finding(
                        rule_id="PAN_REGEX_V1",
                        pii_type="PAN",
                        source_file=source_file,
                        row_number=row_number,
                        column_name=column_name,
                        candidate=candidate,
                    )
                )

        if _column_is_dob(column_name):
            date_matches = DOB_CANDIDATE_RE.finditer(raw_value)
        elif cfg.require_dob_context:
            # When there is no DOB-like header, require an explicit nearby label
            # so ordinary event/transaction dates are not automatically called DOB.
            date_matches = (m for m in DOB_LABELLED_RE.finditer(raw_value))
        else:
            date_matches = DOB_CANDIDATE_RE.finditer(raw_value)

        for match in date_matches:
            candidate = match.groupdict().get("date") or match.group(0)
            if validate_dob(candidate):
                findings.append(
                    _finding(
                        rule_id="DOB_REGEX_CONTEXT_V1",
                        pii_type="DOB",
                        source_file=source_file,
                        row_number=row_number,
                        column_name=column_name,
                        candidate=candidate,
                    )
                )

    # Stable ordering makes evaluations and test output reproducible.
    return sorted(
        findings,
        key=lambda item: (item.column_name, item.row_number, item.pii_type, item.rule_id, item.masked_evidence),
    )
