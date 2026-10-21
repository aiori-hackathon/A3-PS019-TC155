

# Privexis: Personal-Data Discovery and Privacy Evidence Inventory

Team Infynex | AIORI Hackathon 3 | PS-019 (Cybersecurity)

Privexis scans **synthetic** CSV and SQLite data, finds candidate personal-data
fields across five classes (name, email, phone, government ID, date of birth),
links each to its declared purpose and retention metadata, and flags what is missing.

> **Scope:** the output is technical evidence for human review. Privexis makes no
> legal or compliance determination and never decides a lawful basis.


## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/Mac: source .venv/bin/activate
pip install -e .
pip install -r requirements.txt
python scripts/generate_data.py   # synthetic data + answer key (seeded, reproducible)
privexis scan                     # or: python -m privexis scan
pytest -q
```

## How it works

1. **Connectors** read CSV and SQLite (read-only) through one interface.
2. **Sampler** draws a bounded, deterministic reservoir sample per column.
3. **Rule engine** (`config/rules.yaml`) fuses column-name hints, regex patterns and
   strict validators (Verhoeff for Aadhaar-style numbers, PAN format, email syntax,
   date plausibility) into a confidence score.
4. **Linker** joins candidate fields to `config/metadata.yaml` and flags
   `NO_METADATA_ENTRY`, `MISSING_PURPOSE`, `MISSING_RETENTION`.
5. **Evaluator** compares findings with `data/labels.csv` and reports per-class
   precision and recall.

## Outputs (`reports/`)

| File | Contents |
|---|---|
| `inventory.json` / `inventory.csv` | Candidate fields with evidence, purpose, retention, gaps |
| `gap_report.md` | Fields with missing metadata, plus orphaned declared metadata |
| `metrics.json` | Per-class TP / FP / FN, precision, recall, F1 |

## Evaluation (synthetic set, 22 labelled columns)

| Class | Precision | Recall |
|---|---|---|
| NAME | 1.0 | 0.75 |
| EMAIL | 1.0 | 0.75 |
| PHONE | 0.75 | 1.0 |
| GOVT_ID | 1.0 | 1.0 |
| DOB | 0.667 | 1.0 |

The set deliberately includes hard cases (a non-birth date column, a non-phone
10-digit column, a mostly-junk column holding some emails, single-word names), so
these numbers demonstrate the evaluation method. They are not a claim of real-world
accuracy. The unit of evaluation is the column, not the individual value.

## Limitations

- Date and 10-digit checks cannot know a column's meaning (`created_at`, `emp_code`).
- `05/06/1990` is ambiguous between DMY and MDY.
- Email validation is a practical subset of RFC 5322.
- Columns with a low share of PII values fall below the threshold.
- Synthetic data only.

## Configuration

Edit `config/rules.yaml` to change hints, patterns, weights and the threshold.
Edit `config/metadata.yaml` to declare purpose, retention and owner per field.