# Evidence Gap Report

> TECHNICAL EVIDENCE ONLY. This report lists candidate personal-data fields and whether declared purpose/retention metadata exists. It makes no legal or compliance determination. Lawful basis and adequacy of purpose or retention are for a human reviewer to decide.

- Candidate personal-data fields: **15**
- Fields with at least one metadata gap: **9**
- Fields fully linked: **6**

## Fields with gaps

| Source | Table | Column | Class | Gaps |
|---|---|---|---|---|
| hard_cases.csv | - | created_at | DOB | NO_METADATA_ENTRY, MISSING_PURPOSE, MISSING_RETENTION |
| hard_cases.csv | - | emp_code | PHONE | NO_METADATA_ENTRY, MISSING_PURPOSE, MISSING_RETENTION |
| hard_cases.csv | - | contact_person | NAME | NO_METADATA_ENTRY, MISSING_PURPOSE, MISSING_RETENTION |
| onboarding.csv | - | mobile | PHONE | MISSING_RETENTION |
| onboarding.csv | - | dob | DOB | MISSING_PURPOSE |
| temp_dump.csv | - | tmp_mail | EMAIL | NO_METADATA_ENTRY, MISSING_PURPOSE, MISSING_RETENTION |
| temp_dump.csv | - | tmp_id | GOVT_ID | NO_METADATA_ENTRY, MISSING_PURPOSE, MISSING_RETENTION |
| temp_dump.csv | - | tmp_ph | PHONE | NO_METADATA_ENTRY, MISSING_PURPOSE, MISSING_RETENTION |
| users.sqlite | acc | birth_date | DOB | NO_METADATA_ENTRY, MISSING_PURPOSE, MISSING_RETENTION |

## Declared metadata with no matching candidate field

- none
