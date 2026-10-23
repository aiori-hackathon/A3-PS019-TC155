# How the answer key was labelled

`data/labels.csv` is the answer key used to compute precision and recall (PS-019: "small manually labelled test set").

## What was labelled

- 22 columns across four files: `onboarding.csv`, `temp_dump.csv`, `hard_cases.csv`, `users.sqlite` (table `acc`).
- The unit is the **column**, not the individual value.
- Each column gets one class: `NAME`, `EMAIL`, `PHONE`, `GOVT_ID`, `DOB`, or `NONE`.

## Rules used

1. Open the file and read the header and a sample of rows.
2. Give the column a class if it holds personal data of that class in **any** of its rows. Otherwise label it `NONE`.
3. Judge only from what the column contains, not from what the scanner says.

Examples:

| Column | Label | Reason |
|---|---|---|
| `ref_no` | NONE | 12 digits, but they fail the Verhoeff checksum, so they are not ID numbers |
| `created_at` | NONE | valid dates, but record-creation dates, not birth dates |
| `emp_code` | NONE | 10 digits, but an employee code, not a phone number |
| `comments` | EMAIL | free text, but about a quarter of the rows contain an email address |

## Who labelled it

Labelled by: ______________________  Date: ____________
Checked by a second team member: ______________________

*(Fill this in after you have actually reviewed every row of `labels.csv` against the data files.)*

## Why the file is not generated

`scripts/generate_data.py` writes the data files only. It does not write `labels.csv`, so the answer key does not come from the code that made the data. `tests/test_labels.py` fails if the labelled columns and the data files stop matching.

## Limitation

The team that labelled the data also designed it, so the labelling is not fully independent. A stronger test would use a second labeller who has not seen the generator.
