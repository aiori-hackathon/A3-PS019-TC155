"""Strict validators: the 'is this really an X?' layer of the detection pipeline."""
import re

# --- Verhoeff checksum (used by Aadhaar) -----------------------------------
# Three lookup tables: D = multiplication table of the dihedral group D5,
# P = a position-based permutation, INV = the inverse of each element in D.
_D = [
    [0,1,2,3,4,5,6,7,8,9], [1,2,3,4,0,6,7,8,9,5], [2,3,4,0,1,7,8,9,5,6],
    [3,4,0,1,2,8,9,5,6,7], [4,0,1,2,3,9,5,6,7,8], [5,9,8,7,6,0,4,3,2,1],
    [6,5,9,8,7,1,0,4,3,2], [7,6,5,9,8,2,1,0,4,3], [8,7,6,5,9,3,2,1,0,4],
    [9,8,7,6,5,4,3,2,1,0],
]
_P = [
    [0,1,2,3,4,5,6,7,8,9], [1,5,7,6,2,8,3,0,9,4], [5,8,0,3,7,9,6,1,4,2],
    [8,9,1,6,0,4,3,5,2,7], [9,4,5,3,1,2,6,8,7,0], [4,2,8,6,5,7,3,9,0,1],
    [2,7,9,3,8,0,6,4,1,5], [7,0,4,6,9,1,3,2,5,8],
]
_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]


def verhoeff_validate(number: str) -> bool:
    """True if the full number (including its check digit) is valid."""
    if not number.isdigit():
        return False
    c = 0
    for i, ch in enumerate(reversed(number)):
        c = _D[c][_P[i % 8][int(ch)]]
    return c == 0


def verhoeff_check_digit(body: str) -> str:
    """Compute the check digit to append to `body`."""
    c = 0
    for i, ch in enumerate(reversed(body)):
        c = _D[c][_P[(i + 1) % 8][int(ch)]]
    return str(_INV[c])


# --- Aadhaar-style number ---------------------------------------------------
def is_aadhaar_like(value: str) -> bool:
    v = value.replace(" ", "").replace("-", "")
    return len(v) == 12 and v[0] in "23456789" and verhoeff_validate(v)


# --- PAN ---------------------------------------------------------------------
_PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


def is_pan(value: str) -> bool:
    return bool(_PAN_RE.match(value.strip().upper()))


# --- Email (practical subset of RFC 5322 addr-spec) --------------------------
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)+$")


def is_email(value: str) -> bool:
    return bool(_EMAIL_RE.match(value.strip()))