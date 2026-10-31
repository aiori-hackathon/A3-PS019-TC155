"""Generate reproducible, fully synthetic scan fixtures and evaluation labels."""

import csv
import json
import random
import sqlite3
from pathlib import Path

SEED = 20261031
DATA_DIR = Path(__file__).resolve().parent
FIXTURE_DIR = DATA_DIR / "demo_files"
CLASSES = {
    "C1": ("Personal identity", "personal_identity"),
    "C2": ("Contact information", "contact_information"),
    "C3": ("Government identifiers", "government_identifiers"),
    "C4": ("Financial information", "financial_information"),
    "C5": ("Location / address", "location_address"),
}

POSITIVE_FIELDS = {
    "C1": [
        "name", "full_name", "first_name", "given_name", "last_name", "family_name", "surname", "person_name", "individual_name", "legal_name",
        "preferred_name", "date_of_birth", "birth_date", "birthdate", "dob", "gender", "age", "reported_age", "person_age", "gender_identity",
        "child_name", "guardian_name", "dependent_name", "employee_name", "patient_name",
    ],
    "C2": [
        "email", "email_address", "e_mail_address", "primary_email", "secondary_email", "contact_email", "work_email", "phone", "phone_number", "telephone",
        "mobile", "mobile_number", "contact_number", "contact_phone", "primary_phone", "alternate_phone", "home_phone", "work_phone", "sms_number",
        "alternate_contact_number", "customer_email", "member_phone", "emergency_phone", "email_address_1", "phone_contact",
    ],
    "C3": [
        "aadhaar", "aadhaar_number", "aadhar_number", "aadhaar_id", "pan", "pan_number", "pan_id", "passport", "passport_number", "passport_id",
        "voter_id", "voter_id_number", "voter_identity_number", "voter_card_number", "driving_license", "driving_license_number", "driving_licence_number",
        "driver_license_number", "driver_licence_no", "dl_number", "electoral_id", "passport_no", "voter_card_id", "license_number", "aadhaar_card_number",
    ],
    "C4": [
        "bank_account", "bank_account_number", "account_number", "bank_acc_no", "savings_account_number", "current_account_number", "ifsc", "ifsc_code",
        "routing_ifsc", "card_number", "credit_card_number", "debit_card_number", "payment_card_number", "upi_id", "vpa", "upi_address",
        "virtual_payment_address", "bank_account_no", "account_no", "beneficiary_account_number", "credit_card", "debit_card", "primary_upi_id",
        "card_number_primary", "beneficiary_account_number",
    ],
    "C5": [
        "address", "postal_address", "residential_address", "home_address", "street_address", "mailing_address", "address_line_1", "address_line_2",
        "pin_code", "pincode", "postal_code", "zip_code", "geo_coordinates", "coordinates", "gps_coordinates", "latitude", "longitude",
        "geo_latitude", "geo_longitude", "location_coordinates", "geo_coordinates", "delivery_address", "billing_address", "location_address", "pin_code",
    ],
}

LOOKALIKE_NEGATIVES = [
    ("order_id", "202610310001"), ("order_number", "000000000000"), ("shipment_id", "9876543210"), ("tracking_number", "123456789012"),
    ("ticket_number", "ABCDE1234F"), ("product_code", "AAAAA0000A"), ("warehouse_code", "0000 0000 0000"), ("transaction_reference", "0000000000000000"),
    ("batch_id", "ABCD0123456"), ("line_item_id", "123-456-7890"), ("sequence_number", "000001234567"), ("inventory_code", "123456789012"),
    ("record_version", "2026-10-31"), ("event_count", "42"), ("product_name", "Synthetic Widget"), ("company_name", "Example Systems"),
    ("email_opt_in", "true"), ("phone_verified", "false"), ("consent_status", "not recorded"), ("subscriber_flag", "0"),
    ("account_age_days", "365"), ("processing_duration", "30"), ("retry_count", "5"), ("request_id", "0000000000000000001"),
    ("postal_template_id", "000000"), ("address_format_code", "A1B2"), ("card_layout_version", "0000"), ("panels_per_page", "12"),
    ("voter_export_batch", "202610"), ("license_plate_template", "SYN-0001"), ("ifsc_reference_doc", "DOC-1234"), ("upi_feature_enabled", "true"),
    ("geo_grid_resolution", "0.001"), ("latitude_unit_label", "degrees"), ("longitude_unit_label", "degrees"), ("map_tile_id", "000000123"),
    ("customer_count", "27"), ("user_name_rule", "lowercase"), ("data_owner_team", "Example Ops"), ("middle_initial_policy", "optional"),
    ("birth_date_format", "YYYY-MM-DD"), ("gender_field_enabled", "false"), ("name_sort_order", "family-first"), ("mobile_app_version", "1.2.3"),
    ("email_domain_rule", "example.invalid"), ("phone_length_limit", "15"), ("payment_attempt_count", "2"), ("address_parser_version", "v2"),
]


def synthetic_rows(code: str, rng: random.Random) -> tuple[list[str], list[list[str]]]:
    fields = POSITIVE_FIELDS[code][:]
    rng.shuffle(fields)
    fields = fields[:8]
    negatives = ["order_id", "product_name", "event_count"]
    headers = fields + negatives
    rows = []
    for index in range(1, 21):
        values = []
        for field in fields:
            if field in {"name", "full_name", "first_name", "given_name", "last_name", "family_name", "surname", "person_name", "individual_name", "legal_name", "preferred_name", "child_name", "guardian_name", "dependent_name", "employee_name", "patient_name"}:
                value = f"Synthetic Person {index:03d}"
            elif field in {"date_of_birth", "birth_date", "birthdate", "dob"}:
                value = f"2000-{(index % 12) + 1:02d}-{(index % 27) + 1:02d}"
            elif field in {"gender", "gender_identity"}:
                value = "synthetic-unspecified"
            elif field in {"age", "reported_age", "person_age"}:
                value = str(18 + index)
            elif "email" in field:
                value = f"person{index:03d}@example.invalid"
            elif any(term in field for term in ("phone", "mobile", "telephone", "sms", "contact_number")):
                value = f"000000{index:04d}"
            elif any(term in field for term in ("aadhaar", "aadhar")):
                value = f"00000000{index:04d}"
            elif "pan" in field:
                value = f"AAAAA{index:04d}A"
            elif "passport" in field:
                value = f"T{index:07d}"
            elif any(term in field for term in ("voter", "electoral")):
                value = f"TESTVOTER{index:04d}"
            elif any(term in field for term in ("licen", "dl_number")):
                value = f"TEST-DL-{index:05d}"
            elif "ifsc" in field:
                value = f"TEST0ABCD{index:02d}"
            elif "upi" in field or field == "vpa" or "virtual_payment" in field:
                value = f"synthetic{index:03d}@upi.invalid"
            elif any(term in field for term in ("card", "account", "acc_no")):
                value = f"0000000000{index:04d}"
            elif "pin" in field or "postal_code" in field or "zip_code" in field:
                value = f"000{index:03d}"
            elif any(term in field for term in ("coordinate", "latitude", "longitude", "location")):
                value = f"{index / 1000:.3f},{index / 2000:.3f}"
            else:
                value = f"{index} Synthetic Lane"
            values.append(value)
        rows.append(values + [f"ORD-{2026}{index:06d}", "Synthetic Product", str(index)])
    return headers, rows


def write_fixtures(rng: random.Random) -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = []
    for code, (label, slug) in CLASSES.items():
        headers, rows = synthetic_rows(code, rng)
        csv_name = f"{slug}.csv"
        csv_path = FIXTURE_DIR / csv_name
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)
            writer.writerows(rows)
        manifest.append({"id": f"{slug}-csv", "name": f"{label} · CSV", "class_code": code, "class_name": label, "kind": "csv", "filename": csv_name, "description": f"Synthetic {label.lower()} fields and look-alike negative columns."})

        sql_name = f"{slug}.sqlite3"
        sql_path = FIXTURE_DIR / sql_name
        sql_path.unlink(missing_ok=True)
        connection = sqlite3.connect(sql_path)
        declarations = ", ".join(f'"{name}" TEXT' for name in headers)
        connection.execute(f'CREATE TABLE synthetic_records ({declarations})')
        placeholders = ",".join("?" for _ in headers)
        safe_headers = ", ".join(f'"{name}"' for name in headers)
        connection.executemany(f'INSERT INTO synthetic_records ({safe_headers}) VALUES ({placeholders})', rows)
        connection.commit()
        connection.close()
        manifest.append({"id": f"{slug}-sqlite", "name": f"{label} · SQLite", "class_code": code, "class_name": label, "kind": "sqlite", "filename": sql_name, "description": f"SQLite version of the synthetic {label.lower()} fixture."})
    (FIXTURE_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def write_metadata_template() -> None:
    path = DATA_DIR / "purpose_retention_template.csv"
    rows = [
        ["personal_identity.csv", "synthetic_records", "first_name", "Synthetic testing", "30 days"],
        ["personal_identity.csv", "synthetic_records", "date_of_birth", "", ""],
        ["contact_information.csv", "synthetic_records", "email_address", "Synthetic testing", ""],
        ["government_identifiers.csv", "synthetic_records", "aadhaar_number", "", ""],
        ["financial_information.csv", "synthetic_records", "bank_account_number", "Synthetic testing", "30 days"],
        ["location_address.csv", "synthetic_records", "postal_address", "", "30 days"],
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["source", "table_name", "column_name", "purpose", "retention"])
        writer.writerows(rows)


if __name__ == "__main__":
    generator = random.Random(SEED)
    write_fixtures(generator)
    write_metadata_template()
    print(f"Generated 10 synthetic scan fixtures and the metadata template (seed {SEED}). The independently curated ground_truth.csv was left unchanged.")
