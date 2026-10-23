# Privexis: Personal-Data Discovery and Privacy Evidence Inventory

Team Infynex | AIORI Hackathon 3 | PS-019 (Cybersecurity)

**Live demo:** https://a3-ps019-tc155-aiori.streamlit.app/  

Privexis scans **synthetic** CSV and SQLite data, finds candidate personal-data
fields across five classes (name, email, phone, government ID, date of birth),
links each to its declared purpose and retention metadata, checks it against a
configurable evidence checklist, and flags what is missing.
Use it from the command line or from the web app.

> **Scope:** the output is technical evidence for human review. Privexis makes no
> legal or compliance determination, never decides a lawful basis, and does not
> infer how data flows between systems.

**New here?**  The whole flow in 20 lines is in [PSEUDOCODE.md](PSEUDOCODE.md).

## PS-019 requirements and where to find them

| Requirement | Where |
|---|---|
| Support CSV and one SQL database | `src/privexis/connectors.py` (CSV, SQLite read-only) |
| Identify 5 predefined data classes | `config/rules.yaml` |
| Small manually labelled test set | `data/labels.csv`, written by hand (see [docs/LABELLING.md](docs/LABELLING.md)) |
| Detect candidate fields with configurable rules | `config/rules.yaml`, `src/privexis/engine.py` |
| Link fields to purpose and retention metadata | `config/metadata.yaml`, `src/privexis/linker.py` |
| Configurable evidence checklist | `config/checklist.yaml` |
| Flag missing purpose or retention (and other evidence) | `reports/gap_report.md`, `reports/inventory.csv` |
| Per-class precision and recall | `reports/metrics.json`, `src/privexis/evaluator.py` |
| Technical evidence kept separate from legal interpretation | disclaimer in every report; status says "Candidate", never "compliant" |
| No lawful-basis decision, no data-flow inference | nothing in the code attempts either |
| Prototype demo with pseudocode | [PSEUDOCODE.md](PSEUDOCODE.md) |

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/Mac: source .venv/bin/activate
pip install -e .
pip install -r requirements-dev.txt
python scripts/generate_data.py   # rebuilds the synthetic data files (seeded, reproducible)
privexis scan                     # command line: or  python -m privexis scan
streamlit run app.py              # web app: opens in your browser
pytest -q
```

## How it works

1. **Connectors** read CSV and SQLite (read-only) through one interface.
2. **Sampler** draws a bounded, deterministic reservoir sample per column.
3. **Rule engine** (`config/rules.yaml`) fuses column-name hints, value patterns and
   strict validators (Verhoeff for Aadhaar-style numbers, PAN format, email syntax,
   date plausibility) into a confidence score. Negative hints rule a class out
   (a column called `created_at` is not a birth date).
4. **Linker** joins candidate fields to `config/metadata.yaml` and checks each one against
   the **evidence checklist** (`config/checklist.yaml`). A missing *required* item is an
   evidence gap, for example `MISSING_PURPOSE`, `MISSING_RETENTION`, `MISSING_OWNER`.
5. **Evaluator** compares findings with `data/labels.csv` and reports per-class
   precision and recall.

Columns that were **not** flagged but scored between the review floor and the threshold
are listed under **needs review**, so a person can decide.

The command line (`cli.py`) and the web app (`app.py`) both call the same
`pipeline.py`, so they always give the same results.

## The evidence checklist

`config/checklist.yaml` lists the evidence a reviewer expects for every candidate field:

| Item | Source | Default |
|---|---|---|
| Declared purpose | metadata | required |
| Retention period | metadata | required |
| Data owner | metadata | required |
| Column name matches a known hint | scanner | advisory |
| Sampled values pass the class checks | scanner | advisory (required for government IDs) |

Edit the file to change what counts as a gap. No code change is needed.

## Review status wording

| Status | Meaning |
|---|---|
| `Candidate: checklist complete` | Every required checklist item is present. This is **not** a human verification. |
| `EVIDENCE GAP FLAG` | At least one required checklist item is missing. |

Every row is a *candidate* for human review. Nothing is called verified, compliant or lawful.

## The web app

`streamlit run app.py` opens an interface where you can:

- scan the built-in demo data and see precision and recall change as you move the threshold
- **upload your own CSV or SQLite files** (and an optional metadata file) and get an inventory
- see one evidence tag per flagged column: class, confidence against the threshold,
  masked sample values, declared purpose / retention / owner, checklist marks and gaps
- see a **Needs a closer look** list of columns that were not flagged but had some evidence
- download `inventory.csv`, `inventory.json` and `gap_report.md`

The web app is an optional extra on top of the scanner. Use **synthetic or test data only**.
Uploaded files are read in a temporary folder that is deleted right after the scan, nothing
is saved, and sample values are masked on screen.

## Outputs (`reports/`)

| File | Contents |
|---|---|
| `inventory.json` / `inventory.csv` | Candidate fields with evidence, purpose, retention, owner, checklist and gaps |
| `gap_report.md` | Checklist table, fields with gaps, needs-review list, orphaned declared metadata |
| `metrics.json` | Per-class TP / FP / FN, precision, recall, F1 |

## Evaluation (synthetic set, 22 hand-labelled columns)

| Class | Precision before | Precision after | Recall |
|---|---|---|---|
| NAME | 1.0 | 1.0 | 0.75 |
| EMAIL | 1.0 | 1.0 | 0.75 |
| PHONE | 0.75 | 1.0 | 1.0 |
| GOVT_ID | 1.0 | 1.0 | 1.0 |
| DOB | 0.667 | 1.0 | 1.0 |

The set deliberately includes hard cases: a non-birth date column, a non-phone 10-digit
column, a mostly-junk column holding some emails, and single-word names. "Before" is the
first run. "After" adds `negative_hints` to `rules.yaml`, which removed the two false alarms
(`created_at`, `emp_code`). The two misses (`comments`, `holder`) remain.

**Read the "after" column carefully:** the negative hints were written after seeing these
errors, on the same 22 columns, so it is not an unbiased estimate of accuracy on new data.
These numbers demonstrate the evaluation method and that errors can be fixed through
configuration. They are not a claim of real-world accuracy. The unit of evaluation is the
column, not the individual value. The labels were written by hand by the team that also
designed the data, so they are not independent (see [docs/LABELLING.md](docs/LABELLING.md)).

## Limitations and future work

- A date column whose name is not covered by a negative hint can still be flagged as DOB.
- `05/06/1990` is ambiguous between DMY and MDY.
- Email validation is a practical subset of RFC 5322.
- Columns with a low share of PII values fall below the threshold (they appear under needs review).
- Name detection is a pattern, not a language model. **spaCy NER / Microsoft Presidio** are
  cited in our proposal as the idea we build on; using them for name detection is **future work** and is not implemented.
- Accuracy is measured on synthetic data only, and only for the demo set (uploads have no answer key).

## Configuration

- `config/rules.yaml`: hints, negative hints, patterns, weights, threshold, review floor.
- `config/checklist.yaml`: required and advisory evidence items, with per-class overrides.
- `config/metadata.yaml`: declared purpose, retention and owner per field.

To use your own metadata in the web app, upload a CSV with the columns
`source, table, column, purpose, retention, owner` (the app offers a template).

## Deploying the web app

Streamlit Community Cloud: connect the GitHub repo, choose branch `main`, set the main
file to `app.py`. `requirements.txt` lists what the app needs and
`.streamlit/config.toml` holds the theme and the 25 MB upload limit.
