"""Generate synthetic CSV + SQLite data and the ground-truth label file.
Everything here is FAKE. A fixed seed makes the output reproducible."""
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


labels = []  # (source, table, column, true_class)


def label(source, table, col, cls):
    labels.append((source, table, col, cls))


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

for col, cls in [("customer_name", "NAME"), ("national_id", "GOVT_ID"),
                 ("email_addr", "EMAIL"), ("mobile", "PHONE"), ("dob", "DOB"),
                 ("city", "NONE"), ("ref_no", "NONE")]:
    label("onboarding.csv", "-", col, cls)

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

for col, cls in [("tmp_mail", "EMAIL"), ("tmp_id", "GOVT_ID"),
                 ("tmp_ph", "PHONE"), ("misc_code", "NONE")]:
    label("temp_dump.csv", "-", col, cls)

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

for col, cls in [("user_id", "NONE"), ("usr_contact", "PHONE"),
                 ("full_name", "NAME"), ("birth_date", "DOB"),
                 ("contact_email", "EMAIL"), ("order_no", "NONE")]:
    label("users.sqlite", "acc", col, cls)

# ---------- ground truth ----------
with open(OUT / "labels.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["source", "table", "column", "true_class"])
    w.writerows(labels)

print(f"Done. {len(labels)} labelled columns written to {OUT}/")