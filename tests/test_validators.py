from hypothesis import given, settings, strategies as st

from sentry.validators import (
    is_valid_verhoeff,
    mask_aadhaar,
    mask_dob,
    mask_email,
    mask_pan,
    validate_aadhaar,
    validate_dob,
    validate_email_rfc5322,
    validate_pan,
)

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
_INV = (0, 4, 3, 2, 1, 5, 6, 7, 8, 9)


def _append_verhoeff_check_digit(prefix: str) -> str:
    checksum = 0
    for index, digit in enumerate(reversed(prefix)):
        checksum = _D[checksum][_P[(index + 1) % 8][int(digit)]]
    return prefix + str(_INV[checksum])


def test_email_syntax_without_dns_lookup():
    assert validate_email_rfc5322("vaibhav@example.com")
    assert not validate_email_rfc5322("not-an-email")


def test_pan_format():
    assert validate_pan("ABCPD1234E")
    assert validate_pan("abcpd1234e")
    assert not validate_pan("ABCPD123E")


def test_dob_calendar_validation():
    assert validate_dob("29/02/2004")
    assert validate_dob("2004-02-29")
    assert not validate_dob("29/02/2003")
    assert not validate_dob("31/04/2001")


def test_verhoeff_known_example():
    assert is_valid_verhoeff("2363")
    assert not is_valid_verhoeff("2364")


@given(
    first=st.sampled_from(list("23456789")),
    rest=st.text(alphabet="0123456789", min_size=10, max_size=10),
)
@settings(max_examples=80, derandomize=True)
def test_generated_aadhaar_shaped_checksums_are_accepted(first, rest):
    prefix = first + rest
    candidate = _append_verhoeff_check_digit(prefix)
    assert len(candidate) == 12
    assert validate_aadhaar(candidate)
    assert validate_aadhaar(f"{candidate[:4]} {candidate[4:8]} {candidate[8:]}")


def test_maskers_do_not_echo_complete_identifiers():
    email = "vaibhav@example.com"
    pan = "ABCPD1234E"
    dob = "29/02/2004"
    assert mask_email(email) != email and "vaibhav" not in mask_email(email)
    assert mask_pan(pan) != pan and "ABCPD" not in mask_pan(pan)
    assert mask_dob(dob) == "**/**/****"
    assert mask_aadhaar("234567890123") == "XXXX XXXX 0123"
