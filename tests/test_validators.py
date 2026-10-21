from privexis.validators import (
    verhoeff_validate, verhoeff_check_digit, is_aadhaar_like, is_pan, is_email,
)


def test_verhoeff_known_example():
    # Classic textbook example: 236 -> check digit 3
    assert verhoeff_check_digit("236") == "3"
    assert verhoeff_validate("2363")
    assert not verhoeff_validate("2364")      # single-digit error caught
    assert not verhoeff_validate("2336")      # wrong digits


def test_aadhaar_roundtrip():
    body = "23456789012"
    num = body + verhoeff_check_digit(body)
    assert is_aadhaar_like(num)
    assert not is_aadhaar_like("123456789012")  # starts with 1


def test_pan():
    assert is_pan("ABCDE1234F")
    assert not is_pan("ABCD12345F")


def test_email():
    assert is_email("asha.k@example.com")
    assert not is_email("asha@@example")
    assert not is_email("not-an-email")