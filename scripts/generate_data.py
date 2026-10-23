"""Generate the synthetic CSV + SQLite files. Everything here is FAKE.
A fixed seed makes the output reproducible.

This script does NOT write data/labels.csv. The answer key is labelled by hand
(see docs/LABELLING.md), so it is independent of the code that makes the data."""
import csv
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

from privexis.validators import verhoeff_check_digit

random.seed(42)
N = 60
OUT = Path("data")
OUT.mkdir(exist_ok=True)

FIRST = ["Asha", "Rohan", "Meera", "Vikram", "Priya", "Arjun", "Sneha", "Kabir", "Isha", "Nikhil"]
LAST = ["Sharma", "Verma", "Iyer", "Khan", "Gupta", "Reddy", "Singh", "Das", "Nair", "Joshi"]
CITIES = ["Bareilly", "Pune", "Chennai", "Kolkata", "Jaipur"]
DIGITS = "0123456789"
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def name():
    return f"{random.choice(FIRST)} {random.choice(LAST)}"


def email(n):
    first, last = n.lower().split()
    return f"{first}.{last}{random.randint(1, 99)}@example.com"


def phone():
    return random.choice("6789") + "".join(random.choices(DIGITS, k=9))


def aadhaar():
    body = random.choice("23456789") + "".join(random.choices(DIGITS, k=10))
    return body + verhoeff_check_digit(body)


def pan():
    return ("".join(random.choices(LETTERS, k=5))
            + "".join(random.choices(DIGITS, k=4))
            + random.choice(LETTERS))


def random_dob():
    return date(1960, 1, 1) + timedelta(days=random.randint(0, 17000))


# ---- DECOYS: look like PII but are NOT. They test precision. ----
def decoy_12_digit():
    """12 digits whose Verhoeff check FAILS."""
    body = random.choice("23456789") + "".join(random.choices(DIGITS, k=10))
    good = verhoeff_check_digit(body)
    bad = str((int(good) + 1) % 10)
    return body + bad


def decoy_10_digit():
    """10 digits starting 1-5: not a valid mobile number."""
    return random.choice("12345") + "".join(random.choices(DIGITS, k=9))


# ---------- onboarding.csv ----------
rows = []
for i in range(N):
    n = name()
    rows.append({
        "customer_name": n,
        "national_id": aadhaar(),
        "email_addr": email(n),
        "mobile": phone(),
        "dob": random_dob().isoformat(),          # ISO: 1990-05-17
        "city": random.choice(CITIES),
        "ref_no": decoy_12_digit(),
    })
with open(OUT / "onboarding.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)


# ---------- temp_dump.csv (undocumented leftovers) ----------
rows = []
for i in range(N):
    n = name()
    rows.append({"tmp_mail": email(n), "tmp_id": pan(),
                 "tmp_ph": "+91" + phone(), "misc_code": decoy_10_digit()})
with open(OUT / "temp_dump.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)


# ---------- users.sqlite ----------
db = OUT / "users.sqlite"
if db.exists():
    db.unlink()
con = sqlite3.connect(db)
con.execute("""CREATE TABLE acc (
    user_id INTEGER PRIMARY KEY, usr_contact TEXT, full_name TEXT,
    birth_date TEXT, contact_email TEXT, order_no TEXT)""")
for i in range(N):
    n = name()
    d = random_dob()
    con.execute("INSERT INTO acc VALUES (?,?,?,?,?,?)",
                (i + 1, phone(), n, d.strftime("%d/%m/%Y"),  # DMY: 17/05/1990
                 email(n), decoy_10_digit()))
con.commit()
con.close()


# ---------- hard_cases.csv (columns that fool simple rules) ----------
rows = []
for i in range(N):
    n = name()
    rows.append({
        "created_at": random_dob().isoformat(),    # date, but NOT a birth date
        "emp_code": phone(),                        # 10 digits, but NOT a phone
        "comments": email(n) if i % 4 == 0 else random.choice(
            ["call back", "ok", "pending", "see notes"]),   # 25% emails, rest junk
        "holder": random.choice(FIRST),             # first names only
        "contact_person": n,                        # a name under a 'contact' header
    })
with open(OUT / "hard_cases.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)

print(f"Done. Synthetic data written to {OUT}/")
print("Note: data/labels.csv is the hand-written answer key. This script does not touch it.")
