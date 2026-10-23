# How the answer keys were labelled

There are two answer keys, used to compute precision and recall (PS-019: "small manually labelled test set"):

| Set | Key | Columns | Role |
|---|---|---|---|
| Main | `data/labels.csv` | 22 | The rules were tuned against it (see the README). |
| Fresh | `data/holdout/labels.csv` | 21 | In two files the rules were never written against. Scored before any rule change; the rules have not been touched since. |

The rest of this page describes `data/labels.csv`. The fresh set follows the same rules (below).

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

## The fresh set

`data/holdout/` holds `hr_export.csv` (11 columns) and `crm_leads.csv` (10 columns). Its labels follow the same rules as above, with these decisions worth knowing:

- `aadhaar_no`, `pan_number`, `tax_id` and `passport_no` are all labelled `GOVT_ID`. The scanner only supports Aadhaar-style numbers and PAN, so `passport_no` is a deliberate miss.
- `dob_text` holds dates such as `5 October 1976`, labelled `DOB`. That format is not supported, so it is a deliberate miss too.
- `salary`, `pincode`, `ticket_number`, `date_of_joining` and `last_contacted` are `NONE`: they are not one of the five classes.
- The files are kept as they are. `scripts/generate_data.py` does not make them.

## Who labelled it

| Set | Labelled by | Date | Checked by a second team member |
|---|---|---|---|
| Main (`data/labels.csv`) | ______________________ | ____________ | ______________________ |
| Fresh (`data/holdout/labels.csv`) | ______________________ | ____________ | ______________________ |

*(Fill this in after you have actually reviewed every row of each `labels.csv` against its data files. The fresh set was drafted with AI assistance, so it needs your review before you describe it as hand-labelled.)*

## Why the file is not generated

`scripts/generate_data.py` writes the data files only. It does not write `labels.csv`, so the answer key does not come from the code that made the data. `tests/test_labels.py` fails if the labelled columns and the data files stop matching.

## Limitation

The team that labelled the data also designed it, so the labelling is not fully independent. A stronger test would use a second labeller who has not seen the generator or the rules. Both sets are small, so a single column moves a class score a lot.
