import csv
import json
import re
import sqlite3
from pathlib import Path

from .config import SAMPLE_ROWS

CLASSES = {
    "C1": "Personal identity",
    "C2": "Contact information",
    "C3": "Government identifiers",
    "C4": "Financial information",
    "C5": "Location / address",
}
NOT_PERSONAL_DATA = "not personal data"
CLASS_DESCRIPTIONS = {
    "C1": "Name, date of birth, gender, and age",
    "C2": "Email address and phone number",
    "C3": "Aadhaar, PAN, passport, voter ID, and driving licence numbers",
    "C4": "Bank account, IFSC, card number, and UPI ID",
    "C5": "Postal address, PIN code, and geographic coordinates",
}
RULE_VERSION = "privexis-rules/2.0"
PATTERNS = {
    "C1": re.compile(r"\b(name|full.?name|first.?name|given.?name|last.?name|family.?name|surname|person.?name|individual.?name|legal.?name|preferred.?name|date.?of.?birth|birth.?date|birthdate|dob|gender|age)\b", re.I),
    "C2": re.compile(r"\b(email|e.?mail(?:.?address)?|contact.?email|phone|telephone|mobile|sms.?number|mobile.?number|phone.?number|contact.?number)\b", re.I),
    "C3": re.compile(r"\b(aadhaar|aadhar|pan(?:.?number|.?id)?|passport(?:.?number|.?no|.?id)?|voter.?id|voter.?identity|voter.?card|electoral.?id|driving.?licen[cs]e|driver.?licen[cs]e|dl.?number|licen[cs]e.?number)\b", re.I),
    "C4": re.compile(r"\b(bank.?account(?:.?number|.?no)?|(?:savings|current|beneficiary).?account.?number|account.?number|account.?no|bank.?acc.?no|ifsc(?:.?code)?|routing.?ifsc|card.?number|credit.?card|debit.?card|payment.?card|upi(?:.?id|.?address)?|vpa|virtual.?payment.?address)\b", re.I),
    "C5": re.compile(r"\b(postal.?address|residential.?address|home.?address|street.?address|mailing.?address|billing.?address|delivery.?address|address(?:.?line.?[12])?|pin.?code|pincode|postal.?code|zip.?code|geo.?coordinates|gps.?coordinates|coordinates|latitude|longitude|geolocation|geo.?latitude|geo.?longitude|location)\b", re.I),
}
VALUE_PATTERNS = {
    "C2": re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$"),
    "C3": re.compile(r"^(?:\d{4}[ -]?){2}\d{4}$|^[A-Z]{5}\d{4}[A-Z]$|^[A-Z][0-9]{7}$", re.I),
    "C4": re.compile(r"^(?:[A-Z]{4}0[A-Z0-9]{6}|[A-Z0-9._-]+@[A-Z0-9.-]+)$", re.I),
    "C5": re.compile(r"^-?\d{1,3}(?:\.\d+)?\s*[,/]\s*-?\d{1,3}(?:\.\d+)?$"),
}
METADATA_FIELD = re.compile(
    r"(?:account_age_days|address_format_code|ifsc_reference_doc|upi_feature_enabled|"
    r"latitude_unit_label|longitude_unit_label|user_name_rule|birth_date_format|"
    r"gender_field_enabled|name_sort_order|mobile_app_version|email_domain_rule|"
    r"phone_length_limit|address_parser_version|account_age|field_enabled|"
    r"(?:email|phone|mobile)_?(?:opt_?in|opt_?out|verified|valid|enabled|flag|rule|domain|length)|"
    r"(?:address|birth_?date|gender|latitude|longitude|ifsc|upi)_?(?:format|template|unit|label|rule|policy|parser|resolution|reference|doc|enabled)|"
    r"(?:postal|card|voter|license)_?(?:template|layout|export|batch|version))",
    re.I,
)

RULES_CATALOG = [
    {"id": "c1_identity_v2", "name": "Personal identity fields", "data_class": "C1", "class_name": CLASSES["C1"], "pattern": PATTERNS["C1"].pattern, "format_validator": "Field-name and bounded-sample context", "confidence": "medium", "enabled": True, "version": RULE_VERSION, "description": CLASS_DESCRIPTIONS["C1"]},
    {"id": "c2_contact_v2", "name": "Contact information fields", "data_class": "C2", "class_name": CLASSES["C2"], "pattern": PATTERNS["C2"].pattern, "format_validator": "Email syntax; phone values require a phone-related field name", "confidence": "medium", "enabled": True, "version": RULE_VERSION, "description": CLASS_DESCRIPTIONS["C2"]},
    {"id": "c3_government_v2", "name": "Government identifier fields", "data_class": "C3", "class_name": CLASSES["C3"], "pattern": PATTERNS["C3"].pattern, "format_validator": "Common identifier shapes with matching field context", "confidence": "medium", "enabled": True, "version": RULE_VERSION, "description": CLASS_DESCRIPTIONS["C3"]},
    {"id": "c4_financial_v2", "name": "Financial information fields", "data_class": "C4", "class_name": CLASSES["C4"], "pattern": PATTERNS["C4"].pattern, "format_validator": "IFSC and UPI syntax with matching field context", "confidence": "medium", "enabled": True, "version": RULE_VERSION, "description": CLASS_DESCRIPTIONS["C4"]},
    {"id": "c5_location_v2", "name": "Location and address fields", "data_class": "C5", "class_name": CLASSES["C5"], "pattern": PATTERNS["C5"].pattern, "format_validator": "Coordinate pairs with matching field context", "confidence": "medium", "enabled": True, "version": RULE_VERSION, "description": CLASS_DESCRIPTIONS["C5"]},
]


def classify(column: str, values: list[str], enabled_classes: set[str] | list[str] | None = None) -> list[dict]:
    normalized = re.sub(r"[_-]+", " ", column.strip())
    if METADATA_FIELD.search(column.strip().replace("-", "_")):
        return []
    if re.search(r"\b(email|e mail|upi|vpa)\b", normalized, re.I):
        normalized = re.sub(r"\baddress\b", "", normalized, flags=re.I)
    # Generic "name" occurs on product and organization schemas; those are not
    # person-name fields unless the header explicitly says person or individual.
    if re.search(r"\b(name|full name)\b", normalized, re.I) and re.search(r"\b(product|company|organization|business|campaign|file|table|column|category)\b", normalized, re.I):
        normalized = re.sub(r"\b(name|full name)\b", "", normalized, flags=re.I)
    if re.search(r"\b(email|e mail|phone|telephone|mobile)\b", normalized, re.I) and re.search(r"\b(opt in|opt out|consent|subscription|verified|valid|enabled|flag)\b", normalized, re.I):
        normalized = re.sub(r"\b(email|e mail|phone|telephone|mobile)\b", "", normalized, flags=re.I)

    found = []
    nonempty = [value.strip() for value in values if value and value.strip()]
    government_identifier = bool(re.search(r"\b(aadhaar|aadhar|passport|voter|electoral)\b", normalized, re.I))
    payment_address = bool(re.search(r"\b(upi|vpa|virtual payment)\b", normalized, re.I))
    enabled = set(enabled_classes) if enabled_classes is not None else set(CLASSES)
    for code, pattern in PATTERNS.items():
        if code not in enabled:
            continue
        name_match = bool(pattern.search(normalized)) and not (code == "C4" and government_identifier) and not (code == "C5" and payment_address)
        value_pattern = VALUE_PATTERNS.get(code)
        value_match = bool(name_match and value_pattern and nonempty and sum(bool(value_pattern.search(value)) for value in nonempty) / len(nonempty) >= 0.6)
        if name_match:
            reason = "Field name matches the configured class rule"
            confidence = "high" if value_match else "medium"
            found.append({
                "data_class": code,
                "confidence": confidence,
                "rule_id": f"{code.lower()}_field_v2",
                "evidence": f"{reason}; inspected {len(values)} bounded sample value(s), raw values are not retained.",
            })
    return found


def scan_csv(path: Path, sample_rows: int = SAMPLE_ROWS, enabled_classes: set[str] | list[str] | None = None) -> tuple[list[dict], int, int]:
    findings = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, strict=True)
        try:
            original = next(reader)
        except StopIteration:
            raise ValueError("CSV file is empty or missing a header row.")
        if not original or not any(item.strip() for item in original):
            raise ValueError("CSV file needs at least one non-empty header.")
        cleaned = [(raw.strip() or "unnamed") for raw in original]
        counts: dict[str, int] = {}
        for name in cleaned:
            counts[name] = counts.get(name, 0) + 1
        seen: dict[str, int] = {}
        headers = []
        for name in cleaned:
            seen[name] = seen.get(name, 0) + 1
            headers.append(f"{name} ({seen[name]})" if counts[name] > 1 else name)
        samples: list[list[str]] = [[] for _ in headers]
        rows = 0
        try:
            for row in reader:
                if rows >= sample_rows:
                    break
                rows += 1
                for index, value in enumerate(row[:len(headers)]):
                    if value.strip():
                        samples[index].append(value.strip()[:500])
        except csv.Error:
            raise ValueError("CSV rows could not be parsed; check the delimiter and quoting.")
        for name, values in zip(headers, samples):
            for match in classify(name, values, enabled_classes):
                findings.append({**match, "table_name": "", "column_name": name})
    return findings, rows, len(headers)


def scan_sqlite(path: Path, sample_rows: int = SAMPLE_ROWS, enabled_classes: set[str] | list[str] | None = None) -> tuple[list[dict], int, int]:
    findings, sampled, inspected = [], 0, 0
    uri = path.resolve().as_uri() + "?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=3)
    except sqlite3.Error:
        raise ValueError("Could not open this SQLite database read-only.")
    try:
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
        for (table,) in tables:
            safe_table = table.replace('"', '""')
            columns = conn.execute(f'PRAGMA table_info("{safe_table}")').fetchall()
            for column_index, column in enumerate(columns):
                inspected += 1
                name = column[1]
                safe_column = name.replace('"', '""')
                rows = conn.execute(f'SELECT "{safe_column}" FROM "{safe_table}" LIMIT ?', (sample_rows,)).fetchall()
                if column_index == 0:
                    sampled += len(rows)
                values = [str(row[0])[:500] for row in rows if row[0] is not None]
                for match in classify(name, values, enabled_classes):
                    findings.append({**match, "table_name": table, "column_name": name})
    except sqlite3.Error:
        raise ValueError("The SQLite source schema could not be read safely.")
    finally:
        conn.close()
    return findings, sampled, inspected


def scan_source(kind: str, path: Path, sample_rows: int = SAMPLE_ROWS, enabled_classes: set[str] | list[str] | None = None):
    if kind == "csv":
        return scan_csv(path, sample_rows, enabled_classes)
    return scan_sqlite(path, sample_rows, enabled_classes)


def inspect_schema(kind: str, path: Path):
    if kind == "csv":
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                row = next(csv.reader(handle, strict=True), None)
            if row is None:
                raise ValueError("CSV file is empty.")
            cleaned = [(value.strip() or "unnamed") for value in row]
            counts: dict[str, int] = {}
            for name in cleaned:
                counts[name] = counts.get(name, 0) + 1
            seen: dict[str, int] = {}
            columns = []
            for base in cleaned:
                seen[base] = seen.get(base, 0) + 1
                name = f"{base} ({seen[base]})" if counts[base] > 1 else base
                columns.append({"name": name, "type": "inferred during scan"})
            return [{"table_name": "", "columns": columns}]
        except csv.Error:
            raise ValueError("CSV header could not be parsed.")
    uri = path.resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=3)
    try:
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
        output = []
        for (table,) in tables:
            safe_table = table.replace('"', '""')
            columns = conn.execute(f'PRAGMA table_info("{safe_table}")').fetchall()
            output.append({"table_name": table, "columns": [{"name": column[1], "type": column[2] or "unknown"} for column in columns]})
        return output
    except sqlite3.Error:
        raise ValueError("The SQLite source schema could not be read safely.")
    finally:
        conn.close()


def _normalize_label(label: str | None) -> str:
    value = (label or "").strip()
    if value.upper() in CLASSES:
        return value.upper()
    if value.lower() in {"", "none", "not personal data", "not_personal_data", "negative"}:
        return NOT_PERSONAL_DATA
    return NOT_PERSONAL_DATA


def evaluate_cases(cases: list[tuple[str, list[str], str | None]]) -> dict:
    per_class = []
    total_tp = total_fp = total_fn = 0
    labels = list(CLASSES) + [NOT_PERSONAL_DATA]
    confusion = {actual: {predicted: 0 for predicted in labels} for actual in labels}

    for code, name in CLASSES.items():
        tp = fp = fn = 0
        for column, values, label in cases:
            predicted = code in {item["data_class"] for item in classify(column, values)}
            actual = _normalize_label(label) == code
            if predicted and actual:
                tp += 1
            elif predicted and not actual:
                fp += 1
            elif actual:
                fn += 1
        precision = tp / (tp + fp) if tp + fp else None
        recall = tp / (tp + fn) if tp + fn else None
        f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and precision + recall else None
        total_tp += tp
        total_fp += fp
        total_fn += fn
        per_class.append({"class_code": code, "class_name": name, "tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1})

    for column, values, label in cases:
        actual = _normalize_label(label)
        predicted_classes = [item["data_class"] for item in classify(column, values)]
        predicted = predicted_classes[0] if predicted_classes else NOT_PERSONAL_DATA
        confusion[actual][predicted] += 1

    valid_precision = [row["precision"] for row in per_class if row["precision"] is not None]
    valid_recall = [row["recall"] for row in per_class if row["recall"] is not None]
    valid_f1 = [row["f1"] for row in per_class if row["f1"] is not None]
    macro_precision = sum(valid_precision) / len(valid_precision) if valid_precision else 0.0
    macro_recall = sum(valid_recall) / len(valid_recall) if valid_recall else 0.0
    macro_f1 = sum(valid_f1) / len(valid_f1) if valid_f1 else 0.0
    micro_precision = total_tp / (total_tp + total_fp) if total_tp + total_fp else 0.0
    micro_recall = total_tp / (total_tp + total_fn) if total_tp + total_fn else 0.0
    micro_f1 = 2 * micro_precision * micro_recall / (micro_precision + micro_recall) if micro_precision + micro_recall else 0.0
    return {
        "classes": per_class,
        "macro": {"precision": round(macro_precision, 4), "recall": round(macro_recall, 4), "f1": round(macro_f1, 4)},
        "micro": {"precision": round(micro_precision, 4), "recall": round(micro_recall, 4), "f1": round(micro_f1, 4)},
        "confusion_matrix": confusion,
        "sample_count": len(cases),
        "not_personal_data_label": NOT_PERSONAL_DATA,
    }


def load_ground_truth() -> list[tuple[str, list[str], str | None]]:
    path = Path(__file__).resolve().parents[1] / "data" / "ground_truth.csv"
    cases = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"column_name", "sample_values", "label"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("Ground-truth file must contain column_name, sample_values, and label headers.")
        for row in reader:
            if not row.get("column_name"):
                continue
            try:
                values = json.loads(row.get("sample_values") or "[]")
            except json.JSONDecodeError as exc:
                raise ValueError("Ground-truth sample_values must contain JSON arrays.") from exc
            cases.append((row["column_name"], [str(value) for value in values], row.get("label")))
    return cases


def evaluate() -> list[dict]:
    return evaluate_cases(load_ground_truth())["classes"]
