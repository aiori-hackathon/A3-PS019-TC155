<p align="center">
  <img src="public/brand/privexis-mark.png" alt="Privexis mark" width="150" />
</p>

<h1 align="center">Privexis</h1>

<p align="center"><strong>Detect. Decrypt. Defend.</strong><br />Personal-data discovery and privacy evidence for structured datasets.</p>

<p align="center">
  <a href="https://privexis.vercel.app/"><img alt="Open live demo" src="https://img.shields.io/badge/OPEN%20LIVE%20DEMO-Privexis-087e8b?style=for-the-badge&logo=vercel&logoColor=white" /></a>
  <a href="https://github.com/aiori-hackathon/A3-PS019-TC155/blob/main/docs/API.md"><img alt="Open API guide" src="https://img.shields.io/badge/API%20GUIDE-Endpoints-4263eb?style=for-the-badge&logo=fastapi&logoColor=white" /></a>
  <a href="https://youtu.be/s2ewHvCSnIo"><img alt="Watch the team introduction" src="https://img.shields.io/badge/TEAM%20INTRO-Watch%20video-cc1f3a?style=for-the-badge&logo=youtube&logoColor=white" /></a>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-FastAPI-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-Next.js-3178C6?style=flat-square&logo=typescript&logoColor=white" />
  <img alt="PostgreSQL and SQLite" src="https://img.shields.io/badge/PostgreSQL%20%7C%20SQLite-Database-4169E1?style=flat-square&logo=postgresql&logoColor=white" />
  <img alt="Vercel and Render" src="https://img.shields.io/badge/Hosted%20on-Vercel%20%2B%20Render-111111?style=flat-square&logo=render&logoColor=white" />
</p>

Privexis scans **synthetic CSV and SQLite datasets** for candidate personal-data fields, maps them to declared purpose and retention metadata, and creates an evidence inventory for human review. It reports precision and recall against a committed, manually labelled evaluation set. It does not make legal compliance or lawful-basis decisions.

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
