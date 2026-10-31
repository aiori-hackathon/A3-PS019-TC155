# Privexis

Privexis is a local-first synthetic-data scanner for CSV and SQLite files. It identifies candidate fields in five personal-data classes, supports human review and purpose/retention mapping, and reports reproducible per-class evaluation metrics. Findings are technical candidates, not legal conclusions.

## Start locally

Requirements: Python 3.12+, Node.js 20.9+, and pnpm.

1. Create and activate a Python environment, then install the root `requirements.txt`.
2. Copy `.env.example` to `.env` and set `PRIVEXIS_SECRET_KEY` to a random secret of at least 32 characters.
3. In one terminal run `uvicorn backend.app.main:app --reload --port 8000`.
4. In another terminal run `corepack pnpm install` and `corepack pnpm dev`.
5. Open <http://localhost:3000>. Choose **Get started**, then add a file or use one of the ten synthetic fixtures.

No account or sign-in is required. Each browser creates a random local workspace key and receives an isolated workspace. Clearing browser storage removes the key needed to access that workspace. Uploaded files are stored on the API host until the source is removed. Use synthetic or otherwise authorized data only.

## Scan and review

- Upload UTF-8 CSV with a header row, or SQLite (`.db`, `.sqlite`, `.sqlite3`). SQLite scans open the database read-only.
- The scan page lets you choose a row sample limit from 100 to 5,000. Raw sample values are not stored in findings.
- The findings inventory supports search, class/status/confidence filters, human review, metadata links, and CSV export.
- Purpose and retention declarations live in the metadata page. The included template deliberately has missing values so gap reporting can be exercised.
- The bottom-right Privexis helper answers product and evaluation questions using local guidance; it does not send source data to an external AI provider.

## Personal-data classes

| Code | Class | Examples |
| --- | --- | --- |
| C1 | Personal identity | Name, date of birth, gender, age |
| C2 | Contact information | Email address, phone number |
| C3 | Government identifiers | Aadhaar, PAN, passport, voter ID, driving licence |
| C4 | Financial information | Bank account, IFSC, card number, UPI ID |
| C5 | Location / address | Postal address, PIN code, geographic coordinates |

Fields that match none of the five classes are labelled **not personal data**. Look-alike identifiers and metadata/configuration fields are included as negatives to make precision measurable.

## Reproducible synthetic evaluation

The generator uses fixed seed `20261031` and creates ten scan fixtures: one CSV and one SQLite database for each class, each with 20 synthetic rows and negative look-alike fields. The separate, independently curated label file contains 25 positive examples per class and 50 negative examples.

```powershell
.\.venv\Scripts\python.exe -m backend.data.generate_synthetic_datasets
```

Generated artifacts:

- `backend/data/demo_files/`: five CSV files and five SQLite files plus a manifest.
- `backend/data/ground_truth.csv`: independently curated UTF-8 evaluation labels (`column_name`, JSON `sample_values`, `label`). The fixture generator leaves this file unchanged.
- `backend/data/purpose_retention_template.csv`: per-field purpose and retention examples, with intentional gaps.

SQLite is the local application database and the supported SQL fixture format; there is no external SQL server requirement. The fixed-seed generator and separate labels are committed so fixtures and evaluation can be reproduced independently. The evaluation page and `/api/v1/evaluation` report precision, recall, and F1 separately for all five classes. The Rules page lets each workspace enable or disable class rules for scans.

## Checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q
corepack pnpm typecheck
corepack pnpm lint
corepack pnpm build
```

See `docs/` for API, evaluation, security, and deployment notes.
