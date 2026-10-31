<p align="center">
  <img src="public/brand/privexis-mark.png" alt="Privexis mark" width="150" />
</p>

<h1 align="center">Privexis</h1>

<p align="center"><strong>Detect. Decrypt. Defend.</strong><br />Personal-data discovery and privacy evidence for structured datasets.</p>

<p align="center">
  <a href="https://privexis.vercel.app/"><img alt="Open live demo" src="https://img.shields.io/badge/🚀%20OPEN%20LIVE%20DEMO-Launch%20Privexis-00A896?style=for-the-badge&logo=vercel&logoColor=white" /></a>
  <a href="https://github.com/aiori-hackathon/A3-PS019-TC155/blob/main/docs/API.md"><img alt="Open API guide" src="https://img.shields.io/badge/⚡%20API%20GUIDE-Explore%20endpoints-6554C0?style=for-the-badge&logo=fastapi&logoColor=white" /></a>
  <a href="https://youtu.be/s2ewHvCSnIo"><img alt="Watch the team introduction" src="https://img.shields.io/badge/🎬%20MEET%20THE%20TEAM-Watch%20video-FF4B6E?style=for-the-badge&logo=youtube&logoColor=white" /></a>
</p>

<p align="center">
  <img alt="Python and FastAPI" src="https://img.shields.io/badge/Python-FastAPI-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img alt="TypeScript and Next.js" src="https://img.shields.io/badge/TypeScript-Next.js-3178C6?style=for-the-badge&logo=typescript&logoColor=white" />
  <img alt="PostgreSQL and SQLite" src="https://img.shields.io/badge/PostgreSQL%20%2B%20SQLite-Storage-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" />
  <img alt="Vercel and Render" src="https://img.shields.io/badge/Vercel%20%2B%20Render-Live%20Hosting-111111?style=for-the-badge&logo=render&logoColor=white" />
</p>

Privexis scans **synthetic CSV and SQLite datasets** for candidate personal-data fields, maps them to declared purpose and retention metadata, and creates an evidence inventory for human review. It reports precision and recall against a committed, manually labelled evaluation set. It does not make legal compliance or lawful-basis decisions.

## Hackathon materials

The original challenge brief and planning files are kept together in [`assets/hackathon/`](assets/hackathon/README.md) and linked here for quick access from the repository home page.

<p>
  <a href="assets/hackathon/Privexis.pdf"><img alt="Open hackathon problem statement" src="https://img.shields.io/badge/📄%20PROBLEM%20STATEMENT-Open%20PDF-FF8A3D?style=for-the-badge&logo=adobeacrobatreader&logoColor=white" /></a>
  <a href="assets/hackathon/Proposed-structure-hackathon.pdf"><img alt="Open proposed project structure" src="https://img.shields.io/badge/🧭%20PROPOSED%20STRUCTURE-Open%20PDF-7B61FF?style=for-the-badge&logo=readthedocs&logoColor=white" /></a>
  <a href="assets/hackathon/Video%20Introduction.txt"><img alt="Open team introduction link" src="https://img.shields.io/badge/🎥%20TEAM%20INTRO-Open%20video%20link-ED4264?style=for-the-badge&logo=youtube&logoColor=white" /></a>
</p>

| Material | What's inside |
| --- | --- |
| [Problem statement](assets/hackathon/Privexis.pdf) | PS-019 requirements and expected outcomes |
| [Proposed structure](assets/hackathon/Proposed-structure-hackathon.pdf) | Initial project planning document |
| [Team introduction](assets/hackathon/Video%20Introduction.txt) | Link to the team's introduction video |

## Try the working demo

<p>
  <a href="https://privexis.vercel.app/"><img alt="Launch Privexis" src="https://img.shields.io/badge/▶%20Launch%20Privexis%20Demo-Visit%20the%20live%20app-11a9a3?style=for-the-badge" /></a>
  <a href="https://privexis-api.onrender.com/api/v1/health/ready"><img alt="Check API status" src="https://img.shields.io/badge/API%20STATUS-Ready-2f9e44?style=for-the-badge" /></a>
</p>

The first API request after a quiet period may take about a minute while Render’s free service wakes. The demo is for synthetic data; do not upload real personal information.

### What to try

1. Open the live app and choose **Get started**.
2. Open **Data Sources** and add a sample CSV or SQLite file, or upload one of the ten included fixtures.
3. Run a scan and open **Inventory** to search and review the candidate fields.
4. Visit **Rules**, **Metadata**, **Evidence Gaps**, **Evaluation**, and **Reports** to inspect the checklist, purpose/retention links, missing metadata, metrics, and exports.
5. Use the floating Privexis helper in the lower-right corner for product guidance.

## How it works

```text
Synthetic CSV / SQLite
        ↓
Schema and column-name inspection
        ↓
Configurable C1–C5 detection rules
        ↓
Candidate findings ──→ Human review and decision history
        ↓
Purpose + retention mapping ──→ Evidence-gap report
        ↓
Per-class evaluation and downloadable reports
```

1. **Register a source.** Choose a bundled fixture or upload a UTF-8 CSV with a header row, or a SQLite database. SQLite inputs are inspected read-only.
2. **Inspect and scan.** Privexis examines column names and bounded samples (the default is up to 500 rows, configurable from 1 to 5,000). It records candidate class, rule, confidence signal, and a value-free evidence summary. Raw samples are not copied into findings.
3. **Review candidates.** Search and filter the inventory; mark a finding confirmed, rejected, or reclassified, and retain a review note/history for human context.
4. **Record declared context.** Map a source/table/column to a business purpose and retention description. These are declarations entered by the reviewer, not conclusions inferred by Privexis.
5. **Find evidence gaps.** The gap view lists candidate fields missing purpose or retention details so reviewers can follow up.
6. **Evaluate and report.** Compare rule output with the included synthetic labels, inspect precision/recall per class, and download inventory, gaps, review activity, or summary reports.

### Feature guide

| Feature | What it does | Suggested demo action |
| --- | --- | --- |
| **Get started / Dashboard** | Shows workspace activity and shortcuts into the scan workflow. | Start here and add a sample source. |
| **Data Sources** | Lists registered sources, bundles ten sample files, previews schema, uploads CSV/SQLite, and starts scans. | Add `personal_identity.csv`; inspect its columns. |
| **Scanner** | Selects a source and bounded row sample, then records a scan run. | Run a scan and open its findings. |
| **Inventory** | Searchable/filterable list of candidate fields and their class, confidence, source, and review state. | Search for `email`, filter a class, then open a finding. |
| **Review** | Human triage queue with decisions, optional notes/reclassification, and review history. | Record a decision to see it reflected in the inventory. |
| **Rules** | Displays the five-class checklist and provides a rule sandbox; enabled class rules can be changed for future scans. | Disable a class, save, then inspect the checklist used by a new scan. |
| **Metadata** | Stores declared purpose and retention details by source/table/column. | Add a purpose and retention entry for a candidate. |
| **Evidence Gaps** | Identifies candidate fields without declared purpose or retention and supports a CSV export. | Review the gaps left by the sample scan. |
| **Evaluation** | Reports per-class precision, recall, F1, and aggregate results against synthetic labels; supports custom evaluation uploads. | Compare each class and inspect false positives. |
| **Scan History** | Shows previous scan runs and their status/results. | Return to the run after navigating to other areas. |
| **Reports** | Exports inventory, evidence gaps, review history, and a printable technical summary. | Download a CSV and open the printable report. |
| **Search** | Finds product pages and can pass a term into inventory search. | Search for `retention` or `phone`. |
| **Floating assistant** | Answers common product/evaluation questions from local guidance; it is not a general AI model and does not send source data to an external provider. | Ask which five classes are supported. |
| **Settings** | Shows API connectivity, workspace/storage behavior, upload/sample limits, and enabled class overview. | Check the API status before scanning. |

Navigation names may be grouped under the workspace menu depending on screen width. The top-level workflow remains data sources → scan → inventory/review → metadata/gaps → evaluation/reports.

### Workspace and storage behavior

No login is required. Each browser generates a random workspace key; the API uses it to isolate that browser’s sources, findings, rules, and metadata. Clearing site storage removes the browser key and therefore its link to that workspace. On another PC, opening the live demo creates a separate workspace. The hosted demo uses a Render Free API with ephemeral uploads and a free database that expires after 30 days; details are in [deployment notes](docs/DEPLOYMENT.md). Local runs use a local SQLite application database by default.

### Safe demo sequence

For a concise evaluator walkthrough, add `personal_identity.csv`, scan it, review one of its eight candidate fields, map purpose/retention for one field, inspect the remaining evidence gaps, then open Evaluation and Reports. The sample values are synthetic. Do not upload real Aadhaar, PAN, passport, bank, card, contact, or address data.

## What the scanner covers

| Code | Data class | Example fields | CSV fixture | SQLite fixture |
| --- | --- | --- | --- | --- |
| C1 | Personal identity | Name, date of birth, gender, age | [personal_identity.csv](backend/data/demo_files/personal_identity.csv) | [personal_identity.sqlite3](backend/data/demo_files/personal_identity.sqlite3) |
| C2 | Contact information | Email address, phone number | [contact_information.csv](backend/data/demo_files/contact_information.csv) | [contact_information.sqlite3](backend/data/demo_files/contact_information.sqlite3) |
| C3 | Government identifiers | Aadhaar, PAN, passport, voter ID, driving licence | [government_identifiers.csv](backend/data/demo_files/government_identifiers.csv) | [government_identifiers.sqlite3](backend/data/demo_files/government_identifiers.sqlite3) |
| C4 | Financial information | Bank account, IFSC, card number, UPI ID | [financial_information.csv](backend/data/demo_files/financial_information.csv) | [financial_information.sqlite3](backend/data/demo_files/financial_information.sqlite3) |
| C5 | Location / address | Postal address, PIN code, coordinates | [location_address.csv](backend/data/demo_files/location_address.csv) | [location_address.sqlite3](backend/data/demo_files/location_address.sqlite3) |

Each of the ten fixtures contains 20 synthetic rows and negative look-alike fields. Fields matching none of the five classes are labelled **not personal data**. The repeatable generator uses seed `20261031`; the separate ground-truth file contains 25 positive labels per class and 50 negative labels (175 fields total).

## Example scan output

This is the recorded demo scan of `personal_identity.csv` (20 rows):

| Output | Result |
| --- | ---: |
| Candidate fields added to Inventory | 8 |
| Findings requiring human review | 8 |
| Purpose/retention evidence gaps to inspect | 8 |

The scanner reports candidates, not confirmed identities. Reviewers can search findings, change their review status, attach metadata, and export the resulting evidence.

## Evaluation snapshot

Baseline for `privexis-rules/2.0` against the committed synthetic field-level labels:

| Class | Precision | Recall | F1 |
| --- | ---: | ---: | ---: |
| C1 Personal identity | 92.59% | 100.00% | 96.15% |
| C2 Contact information | 86.21% | 100.00% | 92.59% |
| C3 Government identifiers | 89.29% | 100.00% | 94.34% |
| C4 Financial information | 92.59% | 100.00% | 96.15% |
| C5 Location / address | 89.29% | 100.00% | 94.34% |
| **Macro average** | **89.99%** | **100.00%** | **94.72%** |

These are results on a small, synthetic, field-name evaluation set—not real-world accuracy claims. The negatives intentionally include look-alike identifiers so false positives are measurable. See [Evaluation details](docs/EVALUATION.md) and the [technical report](docs/TECHNICAL_REPORT.md).

## Run locally

Requirements: Python 3.12+, Node.js 20.9+, and pnpm.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
Copy-Item .env.example .env
```

Set `PRIVEXIS_SECRET_KEY` in `.env` to a random secret of at least 32 characters. Then start the API and frontend in separate terminals:

```powershell
uvicorn backend.app.main:app --reload --port 8000
```

```powershell
corepack pnpm install
corepack pnpm dev
```

Open <http://localhost:3000>. No account or sign-in is required. A browser-local workspace key isolates each workspace; clearing browser storage removes the key needed to return to it.

For a local run, start both processes: FastAPI at `http://localhost:8000` and Next.js at `http://localhost:3000`. Keep both terminals open while using the app. The `NEXT_PUBLIC_API_URL` in `.env` should be `http://localhost:8000`; restart the Next.js dev server after changing it. More deployment context is in [Deployment](docs/DEPLOYMENT.md).

To regenerate the ten fixtures and metadata template without changing the independently labelled evaluation set:

```powershell
python -m backend.data.generate_synthetic_datasets
```

## Team

| Name | Role |
| --- | --- |
| Vibhakar Gangwar | Team Lead |
| Vaibhav Tiwari | Team Member |
| Aditya Pandey | Mentor |

## Repository map

| Location | Contents |
| --- | --- |
| `backend/` | FastAPI service, migrations, scanner, synthetic fixtures, and tests |
| `src/` | Next.js application and interface components |
| `public/` | Brand assets, favicon, and public metadata |
| `docs/` | API, architecture, evaluation, security, and technical report |
| `assets/hackathon/` | Original problem statement, proposed structure, and team intro link |
| `deploy/oci/` | Optional OCI Docker Compose and Caddy configuration |
| `render.yaml` | Render Blueprint for the live API and PostgreSQL database |

## Important links

- [Live app](https://privexis.vercel.app/)
- [API health](https://privexis-api.onrender.com/api/v1/health/ready)
- [API guide](docs/API.md)
- [Hackathon source repository](https://github.com/aiori-hackathon/A3-PS019-TC155)
- [Synthetic fixtures](backend/data/demo_files/README.md)
- [Deployment notes](docs/DEPLOYMENT.md)
- [Problem statement PDF](assets/hackathon/Privexis.pdf)
- [Proposed structure PDF](assets/hackathon/Proposed-structure-hackathon.pdf)

> **Scope:** All included evaluation fixtures are synthetic. Findings are technical evidence for human review, not legal interpretations or compliance determinations.
