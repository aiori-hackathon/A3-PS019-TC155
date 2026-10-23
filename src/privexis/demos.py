"""'Try to fool it' cases: columns whose NAME says one thing and whose VALUES say another.

All values are synthetic and generated here with a fixed seed. No file is read or written.
The comparison scanner is deliberately simple: it only looks at the column name, using the
same hint words as config/rules.yaml. It stands for any tool that never opens the values."""
import random
from dataclasses import dataclass

from privexis.engine import matched_hint, score_column
from privexis.sampler import ColumnSample
from privexis.validators import verhoeff_check_digit

MAX_VALUES = 50          # same sample size the real scanner uses by default


@dataclass
class Case:
    title: str
    column: str
    values: list
    truth: str           # the class a careful human would give: NAME, EMAIL, ... or NONE
    story: str           # one sentence: why this is a good test


def _aadhaar(rng, valid: bool = True) -> str:
    body = str(rng.randint(2, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(10))
    digit = verhoeff_check_digit(body)
    if not valid:
        digit = str((int(digit) + 1) % 10)
    n = body + digit
    return f"{n[:4]} {n[4:8]} {n[8:]}"


def build_cases() -> list:
    rng = random.Random(7)
    phones = [str(rng.randint(6, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(9))
              for _ in range(30)]
    emails = [f"user{rng.randint(10, 99)}.{i}@example.org" for i in range(30)]
    dobs = [f"19{rng.randint(60, 99)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
            for _ in range(30)]
    created = [f"202{rng.randint(0, 5)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
               for _ in range(30)]
    codes = [str(rng.randint(10 ** 9, 10 ** 10 - 1)) for _ in range(30)]
    return [
        Case("Aadhaar numbers under a dull name", "ref_no",
             [_aadhaar(rng) for _ in range(30)], "GOVT_ID",
             "Nothing in the name says ID. Only the checksum on the values gives it away."),
        Case("Phone numbers under a meaningless name", "x1", phones, "PHONE",
             "A name-only tool sees 'x1' and learns nothing."),
        Case("Emails under a meaningless name", "col_a", emails, "EMAIL",
             "The values are emails even though the header is not."),
        Case("Birth dates under a vague name", "col_d", dobs, "DOB",
             "Plausible birth dates, but the header gives no hint."),
        Case("Name says Aadhaar, values are not", "aadhaar",
             [_aadhaar(rng, valid=False) for _ in range(30)], "NONE",
             "12 digits that FAIL the Verhoeff checksum: not Aadhaar numbers. "
             "It is listed for review, not flagged."),
        Case("Record dates, not birth dates", "created_at", created, "NONE",
             "Valid dates, but a negative hint rules out DOB for a column called 'created'."),
        Case("An employee code shaped like a phone number", "emp_code", codes, "NONE",
             "Ten digits, but an employee code, not a phone number."),
    ]


def name_only_guess(column: str, rules) -> str:
    """What a scanner that never opens the values would say about this column."""
    for rule in rules:
        if matched_hint(column, rule.name_hints):
            return rule.cls
    return "NONE"


def probe(column: str, values: list, rules, scoring):
    """Run the real scoring on a column the visitor describes. Returns a Finding."""
    clean = [str(v).strip() for v in values if str(v).strip()][:MAX_VALUES]
    sample = ColumnSample(source="your input", table="-", column=column.strip() or "column",
                          values=clean, non_empty=len(clean))
    return score_column(sample, rules, scoring)
