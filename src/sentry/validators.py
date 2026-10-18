"""Deterministic validators and safe evidence masking functions."""

from __future__ import annotations

import re
from datetime import date, datetime

from email_validator import EmailNotValidError, validate_email

# Verhoeff multiplication table.
_D = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 2, 3, 4, 0, 6, 7, 8, 9, 5),
    (2, 3, 4, 0, 1, 7, 8, 9, 5, 6),
    (3, 4, 0, 1, 2, 8, 9, 5, 6, 7),
    (4, 0, 1, 2, 3, 9, 5, 6, 7, 8),
    (5, 9, 8, 7, 6, 0, 4, 3, 2, 1),
    (6, 5, 9, 8, 7, 1, 0, 4, 3, 2),
    (7, 6, 5, 9, 8, 2, 1, 0, 4, 3),
    (8, 7, 6, 5, 9, 3, 2, 1, 0, 4),
    (9, 8, 7, 6, 5, 4, 3, 2, 1, 0),
)

# Verhoeff permutation table.
_P = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 5, 7, 6, 2, 8, 3, 0, 9, 4),
    (5, 8, 0, 3, 7, 9, 6, 1, 4, 2),
    (8, 9, 1, 6, 0, 4, 3, 5, 2, 7),
    (9, 4, 5, 3, 1, 2, 6, 8, 7, 0),
    (4, 2, 8, 6, 5, 7, 3, 9, 0, 1),
    (2, 7, 9, 3, 8, 0, 6, 4, 1, 5),
    (7, 0, 4, 6, 9, 1, 3, 2, 5, 8),
)

_PAN_RE = re.compile(r"[A-Z]{3}[ABCFGHLJPT][A-Z][0-9]{4}[A-Z]\Z")
_DMY_RE = re.compile(
    r"(?:0?[1-9]|[12][0-9]|3[01])(?P<sep>[./-])"
    r"(?:0?[1-9]|1[0-2])(?P=sep)(?:19|20)[0-9]{2}\Z"
)
_ISO_RE = re.compile(
    r"(?:19|20)[0-9]{2}-(?:0[1-9]|1[0-2])-"
    r"(?:0[1-9]|[12][0-9]|3[01])\Z"
)

# Shared by rules.py when searching a cell for date candidates.
DOB_DATE_PATTERN = (
    r"(?:(?:0?[1-9]|[12][0-9]|3[01])[./-](?:0?[1-9]|1[0-2])[./-](?:19|20)[0-9]{2}"
    r"|(?:19|20)[0-9]{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01]))"
)


def is_valid_verhoeff(number: str) -> bool:
    """Return whether an ASCII digit string passes the Verhoeff checksum."""
    if not number or re.fullmatch(r"[0-9]+", number) is None:
        return False

    checksum = 0
    for index, digit in enumerate(reversed(number)):
        checksum = _D[checksum][_P[index % 8][int(digit)]]
    return checksum == 0


def validate_aadhaar(value: str) -> bool:
    """Validate Aadhaar-like candidates by shape, leading digit and Verhoeff.

    This is a format/checksum check only. It does not establish that a number
    was issued to a person or that it belongs to any particular individual.
    """
    if not isinstance(value, str):
        return False
    normalized = re.sub(r"[\s-]", "", value.strip())
    if re.fullmatch(r"[2-9][0-9]{11}", normalized) is None:
        return False
    return is_valid_verhoeff(normalized)


def validate_email_rfc5322(value: str) -> bool:
    """Check email syntax without DNS lookups or deliverability checks."""
    if not isinstance(value, str) or not value:
        return False
    try:
        validate_email(
            value.strip(),
            check_deliverability=False,
            allow_smtputf8=False,
        )
    except (EmailNotValidError, TypeError, ValueError):
        return False
    return True


def validate_pan(value: str) -> bool:
    """Validate the standard 10-character Indian PAN shape."""
    if not isinstance(value, str):
        return False
    return _PAN_RE.fullmatch(value.strip().upper()) is not None


def validate_dob(value: str) -> bool:
    """Validate a date string in DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY or ISO form.

    Calendar validity is checked. Whether a date is actually a person's DOB is
    inferred separately from its column name or an adjacent DOB label.
    """
    if not isinstance(value, str):
        return False
    candidate = value.strip()
    if _DMY_RE.fullmatch(candidate):
        formats = ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y")
    elif _ISO_RE.fullmatch(candidate):
        formats = ("%Y-%m-%d",)
    else:
        return False

    for fmt in formats:
        try:
            parsed = datetime.strptime(candidate, fmt).date()
            return date(1900, 1, 1) <= parsed <= date(2099, 12, 31)
        except ValueError:
            continue
    return False


def mask_email(value: str) -> str:
    """Mask the local part; retain the domain as contextual evidence."""
    local, separator, domain = value.rpartition("@")
    if not separator or not local or not domain:
        return "[masked email]"
    masked_local = local[0] + "***" if len(local) > 1 else "*"
    return f"{masked_local}@{domain}"


def mask_aadhaar(value: str) -> str:
    """Mask all but the final four digits of an Aadhaar candidate."""
    digits = re.sub(r"[\s-]", "", value)
    if len(digits) != 12 or not digits.isascii() or not digits.isdigit():
        return "XXXX XXXX XXXX"
    return f"XXXX XXXX {digits[-4:]}"


def mask_pan(value: str) -> str:
    """Mask PAN letters while retaining the four middle digits as evidence."""
    candidate = value.strip().upper()
    if len(candidate) != 10:
        return "XXXXXXXXXX"
    return f"XXXXX{candidate[5:9]}X"


def mask_dob(_value: str) -> str:
    """Never expose date components in review evidence."""
    return "**/**/****"


def mask_evidence(pii_type: str, value: str) -> str:
    """Dispatch to the one-way, display-only masking helper."""
    maskers = {
        "EMAIL": mask_email,
        "AADHAAR": mask_aadhaar,
        "PAN": mask_pan,
        "DOB": mask_dob,
    }
    try:
        return maskers[pii_type](value)
    except KeyError as exc:
        raise ValueError("Unsupported PII type for masking.") from exc
