# How Privexis Works (a guide you can actually read)

Put this file at `docs/HOW_IT_WORKS.md`. It explains every part of the project in plain language. You do not need to memorise it. If you understand the **story** and the **one example**, you can work out the rest.

---

## 1. The story in one minute

Companies pile up personal data (names, emails, phones, ID numbers, birth dates) in old tables and spreadsheets. Privacy law (India's DPDP Act 2023) expects every kind of personal data to have:

- a **purpose** (why do we keep it?)
- a **retention period** (how long, and what happens after?)

You cannot attach a purpose to a field you don't know exists. So Privexis does three things:

1. **Find** columns that look like personal data.
2. **Link** each one to its declared purpose / retention.
3. **Flag** what is missing, and **measure** how accurate step 1 was.

It only produces *technical evidence*. It never says "legal" or "illegal". A human decides that.

---

## 2. The pipeline (one picture)

```
 data/*.csv, *.sqlite
        |
   connectors.py   -> reads files the same way, whatever the type
        |
   sampler.py      -> picks up to 50 values from every column
        |
   engine.py       -> scores each column using config/rules.yaml
        |                (uses validators.py for strict checks)
        |
   linker.py       -> attaches purpose/retention from config/metadata.yaml,
        |                flags gaps
        |
   report.py       -> writes reports/inventory.csv, inventory.json, gap_report.md
        |
   evaluator.py    -> compares findings with data/labels.csv -> precision/recall
        |
   cli.py          -> the `privexis scan` command that runs all of the above
```

Each box is one small file with one job. That is deliberate: you can explain any one of them in a sentence.

---

## 3. The repo, file by file

### `src/privexis/` (the actual program)

| File | Its one job | Idea worth knowing |
|---|---|---|
| `validators.py` | "Is this value *really* an Aadhaar / PAN / email / birth date?" | A **regex** checks the *shape* (12 digits). A **validator** checks the value is *plausible* (the Verhoeff checksum passes). Random 12-digit numbers pass the checksum only about 1 time in 10, so this removes most false alarms. |
| `connectors.py` | Opens a CSV or SQLite file and hands back rows in one common format. | SQLite is opened **read-only**: a scanner must never change what it inspects. Adding another source type means adding one function. |
| `sampler.py` | Takes at most 50 values per column. | **Reservoir sampling**: you get a fair random sample in one pass without knowing the row count. A fixed seed (42) makes it **reproducible**. Real tables can have millions of rows; 50 values are enough to tell an email column from a city column. |
| `engine.py` | Scores every column against every class and keeps the best. | **Evidence fusion** (section 5). |
| `linker.py` | Matches each detected field with its declared purpose/retention and records gaps. | Gaps are *facts* ("retention is absent"), not *verdicts* ("you are non-compliant"). |
| `report.py` | Writes the three output files. Stamps a disclaimer in each. | This is how "technical evidence vs legal interpretation" is shown. |
| `evaluator.py` | Compares the scanner's answers with the answer key. | Precision and recall (section 6). |
| `cli.py` | Runs everything from one command. | `privexis scan` |
| `__main__.py` | 2 lines that let you also run `python -m privexis scan`. | Same command, no install needed. |
| `__init__.py` | Empty. Tells Python this folder is a package. | |

### `config/` (settings you can change without touching code)

| File | What it holds |
|---|---|
| `rules.yaml` | For each of the 5 classes: column-name hints, regex patterns, which validator to use. Also the weights (0.4 / 0.6) and the threshold (0.5). |
| `metadata.yaml` | The "declared" purpose / retention / owner of some fields. A field missing here (or missing a key) becomes a gap. Some entries are left out **on purpose** so the demo has gaps to find. |

### `data/` (all fake, made by `generate_data.py`)

| File | Role |
|---|---|
| `onboarding.csv`, `temp_dump.csv`, `hard_cases.csv`, `users.sqlite` | The synthetic data being scanned. |
| `labels.csv` | The **answer key**: the true class of every column. Without it we could not compute accuracy. |

### `scripts/generate_data.py`

Creates all of the data above plus the answer key. Seeded, so it produces identical files every time. We keep it so anyone can rebuild the data, and so the data and the answer key can never drift apart.

### `tests/` (22 tests)

Small checks that prove each part works (`pytest -q`). When you change a rule, they tell you immediately if something else broke.

### `reports/` (the outputs, committed as evidence)

`inventory.csv` / `inventory.json` (every candidate field with its evidence and gaps), `gap_report.md` (readable summary), `metrics.json` (precision and recall).

### Root files

`pyproject.toml` (project name, where the code lives, the `privexis` command), `requirements.txt` (packages to install), `.gitignore` (files Git should skip), `README.md`, the proposal PDF, and the video link file.

---

## 4. One example, start to finish

Take the column **`tmp_id`** in `temp_dump.csv`. It holds values like `ABCDE1234F`.

1. **Connector** reads the file and finds a column called `tmp_id`.
2. **Sampler** picks 50 of its values.
3. **Engine** asks every class "how well do you fit?". For GOVT_ID:
   - *Name hint?* `tmp_id` contains none of the hints (`pan`, `aadhaar`, `uid`...). → 0 points.
   - *Value check?* All 50 values match the PAN pattern **and** pass the PAN validator. → 50/50 = 100%.
   - Score = 0.4 × 0 + 0.6 × 1.0 = **0.6**.
4. 0.6 is above the threshold 0.5, so it is flagged as **GOVT_ID**, found by its values alone, even though the column name tells you nothing.
5. **Linker** looks for `temp_dump.csv:-:tmp_id` in `metadata.yaml`: not there. Gaps: `NO_METADATA_ENTRY`, `MISSING_PURPOSE`, `MISSING_RETENTION`.
6. **Report** lists it as an "EVIDENCE GAP FLAG" for a human to review.

That is the whole project in miniature.

---

## 5. How detection decides (the core idea)

For each column and each class:

```
confidence = 0.4 × (column name matches a hint? 1 or 0)
           + 0.6 × (fraction of sampled values that pass pattern AND validator)
```

If the best class scores **at least 0.5**, the column is flagged. Otherwise it is `NONE`.

What this gives you:

- **Name only is never enough.** A column called `file_name` full of filenames scores 0.4, below 0.5.
- **Values alone can be enough.** Perfect values score 0.6, so a column with a meaningless name can still be found (`tmp_id`).
- **Two-stage value check.** A cheap regex first, then the strict validator. The 12-digit `ref_no` decoy passes the regex but fails the checksum, so it is correctly ignored.
- **Hints match whole words.** `pan` matches `pan_no` but not `company`.

The weights 0.4 / 0.6 and the threshold 0.5 are **our design choices**, not learned from data. They are easy to change in `rules.yaml`.

---

## 6. Precision and recall (and why we have 4 errors)

- **Precision**: of the columns the scanner flagged as EMAIL, how many really are? (punishes false alarms)
- **Recall**: of the real EMAIL columns, how many did it find? (punishes misses)

Our results on 22 labelled columns:

| Class | Precision | Recall |
|---|---|---|
| NAME | 1.0 | 0.75 |
| EMAIL | 1.0 | 0.75 |
| PHONE | 0.75 | 1.0 |
| GOVT_ID | 1.0 | 1.0 |
| DOB | 0.667 | 1.0 |

The four errors are **planted on purpose** in `hard_cases.csv`:

| Column | What happens | Why |
|---|---|---|
| `created_at` | wrongly flagged as DOB | Valid dates, but a date check can't know it isn't a *birth* date. |
| `emp_code` | wrongly flagged as PHONE | 10 digits starting 6-9 looks exactly like a mobile number. |
| `comments` | EMAIL missed | Only 25% of its values are emails, so the score is 0.15. |
| `holder` | NAME missed | Single-word names; our NAME pattern wants two or more words. |

A scanner that scored 100% on easy data would prove nothing. Showing where it fails and why is what makes the numbers believable. The unit measured is the **column**, not each individual value.

---

## 6b. Things to try (this is how it sticks)

1. In `rules.yaml` set `threshold: 0.7`, run `privexis scan`. Watch `tmp_id` disappear. You traded recall for precision.
2. Set it to `0.3`. Name-only matches start to count.
3. Remove `mobile` from the PHONE hints. The column is still found, through its values.
4. Add a `users.sqlite:acc:birth_date` entry to `metadata.yaml`. One gap disappears.
5. In a Python shell, run `is_aadhaar_like` on a number from `national_id`, then change one digit and run it again.

Undo your experiments afterwards (`git checkout config`) so the demo still shows the gaps.

---


---

## 8. Known limitations (say them before they are asked)

- A date column that isn't a birth date (`created_at`) can be flagged as DOB.
- `05/06/1990` is ambiguous between DD/MM and MM/DD.
- Email validation is a practical subset of RFC 5322, not the full grammar.
- Columns where only a small share of values are PII fall below the threshold.
- Synthetic data only; thresholds were not tuned on real data.
