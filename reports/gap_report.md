# Evidence Gap Report

> TECHNICAL EVIDENCE ONLY. This report lists candidate personal-data fields and whether the evidence on the configured checklist is present. It makes no legal or compliance determination. Lawful basis and the adequacy of any purpose or retention period are for a human reviewer to decide.

- Candidate personal-data fields: **13**
- Fields with at least one required evidence item missing: **7**
- Fields with a complete checklist: **6**
- Flagged by values alone (no column-name hint): **2**
- Columns not flagged but worth a human look: **1**

## Evidence checklist

`yes` = evidence present. `**NO**` = required item missing (an evidence gap). `no` = advisory item missing (shown for the reviewer, not counted as a gap).

| Source | Column | Class | Declared purpose | Retention period | Data owner | Column name matches a known hint | Sampled values pass the class checks |
|---|---|---|---|---|---|---|---|
| hard_cases.csv | contact_person | NAME | **NO** | **NO** | **NO** | no | yes |
| onboarding.csv | customer_name | NAME | yes | yes | yes | yes | yes |
| onboarding.csv | national_id | GOVT_ID | yes | yes | yes | yes | yes |
| onboarding.csv | email_addr | EMAIL | yes | yes | yes | yes | yes |
| onboarding.csv | mobile | PHONE | yes | **NO** | yes | yes | yes |
| onboarding.csv | dob | DOB | **NO** | yes | yes | yes | yes |
| temp_dump.csv | tmp_mail | EMAIL | **NO** | **NO** | **NO** | yes | yes |
| temp_dump.csv | tmp_id | GOVT_ID | **NO** | **NO** | **NO** | no | yes |
| temp_dump.csv | tmp_ph | PHONE | **NO** | **NO** | **NO** | yes | yes |
| users.sqlite | usr_contact | PHONE | yes | yes | yes | yes | yes |
| users.sqlite | full_name | NAME | yes | yes | yes | yes | yes |
| users.sqlite | birth_date | DOB | **NO** | **NO** | **NO** | yes | yes |
| users.sqlite | contact_email | EMAIL | yes | yes | yes | yes | yes |

## Fields with gaps

| Source | Table | Column | Class | Gaps |
|---|---|---|---|---|
| hard_cases.csv | - | contact_person | NAME | NO_METADATA_ENTRY, MISSING_PURPOSE, MISSING_RETENTION, MISSING_OWNER |
| onboarding.csv | - | mobile | PHONE | MISSING_RETENTION |
| onboarding.csv | - | dob | DOB | MISSING_PURPOSE |
| temp_dump.csv | - | tmp_mail | EMAIL | NO_METADATA_ENTRY, MISSING_PURPOSE, MISSING_RETENTION, MISSING_OWNER |
| temp_dump.csv | - | tmp_id | GOVT_ID | NO_METADATA_ENTRY, MISSING_PURPOSE, MISSING_RETENTION, MISSING_OWNER |
| temp_dump.csv | - | tmp_ph | PHONE | NO_METADATA_ENTRY, MISSING_PURPOSE, MISSING_RETENTION, MISSING_OWNER |
| users.sqlite | acc | birth_date | DOB | NO_METADATA_ENTRY, MISSING_PURPOSE, MISSING_RETENTION, MISSING_OWNER |

Missing most often: `MISSING_PURPOSE` (6), `MISSING_RETENTION` (6), `NO_METADATA_ENTRY` (5), `MISSING_OWNER` (5)

## Needs human review (not flagged, but some evidence)

These columns scored below the detection threshold but above the review floor. They are listed so a person can decide, not because the scanner thinks they are personal data.

- `hard_cases.csv` / `comments`: below threshold; closest class NAME: 20/50 sampled values passed alphabetic pattern of two or more words

## Declared metadata with no matching candidate field

- none
