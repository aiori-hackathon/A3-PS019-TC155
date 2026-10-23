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
 data/*.csv, *.sqlite     (or files uploaded in the web app)
        |
   connectors.py   -> reads files the same way, whatever the type
        |
   sampler.py      -> picks up to 50 values from every column
        |
   engine.py       -> scores each column using config/rules.yaml
        |                (uses validators.py for strict checks)
        |
   linker.py       -> checks each flagged field against the evidence checklist
        |                (config/checklist.yaml) using config/metadata.yaml,
        |                flags gaps
        |
   pipeline.py     -> the four steps above as ONE reusable function
        |
   +----+-------------------------+
   |                              |
 cli.py                         app.py (+ ui.py)
 `privexis scan`                the web app
   |                              |
   +--> report.py  -> reports/inventory.csv, inventory.json, gap_report.md
   +--> evaluator.py -> compares findings with data/labels.csv -> precision/recall
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
| `engine.py` | Scores every column against every class and keeps the best. | **Evidence fusion** (section 5). It also applies *negative hints* (a column called `created_at` can never be a birth date). |
| `linker.py` | Matches each detected field with its declared metadata and checks it against the **evidence checklist**. | Gaps are *facts* ("retention is absent"), not *verdicts* ("you are non-compliant"). What counts as a gap is set in `checklist.yaml`, not in code. |
| `pipeline.py` | Runs sample -> score -> link in one function, builds the "needs review" list, and reads uploaded metadata files. | The command line and the web app both call it, so they can never disagree. This is why adding the web app took so little code. |
| `report.py` | Writes the inventory and the gap report (with the checklist table). Stamps a disclaimer in each. | This is how "technical evidence vs legal interpretation" is shown. |
| `evaluator.py` | Compares the scanner's answers with the answer key. | Precision and recall (section 6). |
| `cli.py` | Runs everything from one command. | `privexis scan` |
| `ui.py` | The web app's HTML and CSS as plain functions. | It does not import Streamlit, so it can be tested. Everything from an uploaded file is escaped, and sample values are masked. |
| `__main__.py` | 2 lines that let you also run `python -m privexis scan`. | Same command, no install needed. |
| `__init__.py` | Empty. Tells Python this folder is a package. | |

### `config/` (settings you can change without touching code)

| File | What it holds |
|---|---|
| `rules.yaml` | For each of the 5 classes: column-name hints, negative hints, regex patterns, which validator to use, and a plain-English name for the check. Also the weights (0.4 / 0.6), the threshold (0.5) and the review floor (0.1). |
| `checklist.yaml` | The **evidence checklist**: which items a reviewer expects for every candidate field (purpose, retention, owner, name hint, value check), which are required, and per-class overrides. A missing *required* item is an evidence gap. |
| `metadata.yaml` | The "declared" purpose / retention / owner of some fields. A field missing here (or missing a key) becomes a gap. Some entries are left out **on purpose** so the demo has gaps to find. |

### `data/` (all fake; the data files are made by `generate_data.py`)

| File | Role |
|---|---|
| `onboarding.csv`, `temp_dump.csv`, `hard_cases.csv`, `users.sqlite` | The synthetic data being scanned. |
| `labels.csv` | The **answer key**: the true class of every column, **written by hand** (not generated). See `docs/LABELLING.md`. Without it we could not compute accuracy. |

### `scripts/generate_data.py`

Creates the four data files. Seeded, so it produces identical files every time, and anyone can rebuild the data. It deliberately does **not** write `labels.csv`: the answer key is labelled by hand, so it does not come from the same code that made the data. A test (`tests/test_labels.py`) fails if the labels and the data files ever stop matching.

### `tests/` (57 tests)

Small checks that prove each part works (`pytest -q`). When you change a rule, they tell you immediately if something else broke.

### `reports/` (the outputs, committed as evidence)

`inventory.csv` / `inventory.json` (every candidate field with its evidence and gaps), `gap_report.md` (readable summary), `metrics.json` (precision and recall).

### Root files

- `app.py`: the web app (see section 4b).
- `.streamlit/config.toml`: the web app's colours and its 25 MB upload limit.
- `PSEUDOCODE.md`: the whole scan-score-link-report flow in about 20 lines, for the mentor demo.
- `docs/LABELLING.md`: how the answer key was labelled.
- `pyproject.toml`: project name, where the code lives, the `privexis` command.
- `requirements.txt`: what the deployed web app needs (`pyyaml`, `streamlit`). `requirements-dev.txt`: the same plus `pytest`, for working on the project.
- `.gitignore`: files Git should skip.
- `README.md`, the proposal PDF, and the video link file.

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
5. **Linker** goes through the checklist for GOVT_ID. It looks for `temp_dump.csv:-:tmp_id` in `metadata.yaml`: not there. So purpose, retention and owner are all missing. The name hint is missing too, but that item is only *advisory*. The values did pass the strict check, so that required item is present. Gaps: `NO_METADATA_ENTRY`, `MISSING_PURPOSE`, `MISSING_RETENTION`, `MISSING_OWNER`.
6. **Report** lists it as an "EVIDENCE GAP FLAG" for a human to review, with the checklist row showing exactly which items are present.

That is the whole project in miniature.

---

## 4b. The web app

`streamlit run app.py` starts a page where you can scan the demo data or **upload your own files**.

How an upload is handled:

1. The file is written into a **temporary folder**.
2. The same `run_pipeline` function scans it.
3. The temporary folder is **deleted** as soon as the scan ends. Nothing is saved.
4. On screen, sample values are **masked** (`asha.sharma12@example.com` shows as `a•••.s•••••••@e••••••.c••`), so full values are never displayed.

Why these choices matter for a privacy tool:

- **Escaping.** A column called `<script>...` would be dangerous if pasted into a web page raw. `ui.py` escapes every piece of uploaded text, and a test checks it.
- **Limits.** Files over 25 MB are refused. Bad encodings and corrupt databases show a plain error message instead of crashing.
- **Metadata upload.** You can upload a CSV with `source, table, column, purpose, retention, owner`, or a YAML file like `config/metadata.yaml`. The app offers a template to download.
- **Accuracy only for the demo.** Precision and recall need an answer key. Uploaded files do not have one, so the page says so instead of inventing a number.

The page itself is built from `ui.py` (looks) and `app.py` (what happens). Each flagged column becomes an **evidence tag**: class, a confidence bar with the threshold marked on it, masked examples, declared purpose / retention / owner, the detection checks that passed, and any gaps. A separate list, **Needs a closer look**, shows columns that were *not* flagged but had some evidence.

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
- **Negative hints rule a class out.** `created_at` holds valid dates, but the word `created` says it is not a birth date, so DOB is ruled out for that column. These live in `rules.yaml`, not in code.
- **Near misses are not hidden.** A column that scores between 0.1 (the review floor) and 0.5 is not flagged, but it goes on the **needs review** list with its evidence, so a person can decide.

The weights 0.4 / 0.6 and the threshold 0.5 are **our design choices**, not learned from data. They are easy to change in `rules.yaml`.

### 5b. The evidence checklist (what an "evidence gap" means)

Detection finds the field. The checklist says what evidence a reviewer expects for it. It lives in `config/checklist.yaml`:

| Item | Where it comes from | Required? |
|---|---|---|
| Declared purpose | `metadata.yaml` | yes |
| Retention period | `metadata.yaml` | yes |
| Data owner | `metadata.yaml` | yes |
| Column name matches a known hint | the scanner | advisory |
| Sampled values pass the class checks | the scanner | advisory (required for government IDs) |

- A missing **required** item is an **evidence gap** (`MISSING_PURPOSE`, `MISSING_OWNER`, ...). A missing **advisory** item is only shown to the reviewer.
- Owner is on the list because our own proposal says a retention schedule records "how long each category of data is kept, who owns it, and what happens at the end of its life".
- To change what counts as a gap, edit the YAML. For example, move `owner` to `advisory` and the owner gaps disappear, with no code change.
- The checklist table in `gap_report.md` and the checklist marks on each web-app tag are generated from this one file.

---

## 6. Precision and recall (and why we still have errors)

- **Precision**: of the columns the scanner flagged as EMAIL, how many really are? (punishes false alarms)
- **Recall**: of the real EMAIL columns, how many did it find? (punishes misses)

Results on the 22 hand-labelled columns, before and after we added negative hints to `rules.yaml`:

| Class | Precision before | Precision after | Recall |
|---|---|---|---|
| NAME | 1.0 | 1.0 | 0.75 |
| EMAIL | 1.0 | 1.0 | 0.75 |
| PHONE | 0.75 | 1.0 | 1.0 |
| GOVT_ID | 1.0 | 1.0 | 1.0 |
| DOB | 0.667 | 1.0 | 1.0 |

Four errors were **planted on purpose** in `hard_cases.csv`. Two were then fixed through configuration; two remain as honest limitations:

| Column | What happened | Status |
|---|---|---|
| `created_at` | wrongly flagged as DOB (valid dates, but not a *birth* date) | fixed by the negative hint `created` |
| `emp_code` | wrongly flagged as PHONE (10 digits starting 6-9) | fixed by the negative hint `emp` |
| `comments` | EMAIL missed: only 25% of values are emails, so the score is below the threshold | **remains**; the column now appears on the *needs review* list |
| `holder` | NAME missed: single-word names, and our NAME pattern wants two or more words | **remains** |

**Be upfront about this:** we wrote the negative hints *after* seeing these errors, on the same 22 columns. So the "after" column is **not** an unbiased estimate of accuracy on new data. It shows that errors can be fixed through configuration alone. The "before" column is the more honest first look. A scanner that scored 100% on easy data would prove nothing. The unit measured is the **column**, not each individual value.

---

## 6b. Things to try (this is how it sticks)

1. In `rules.yaml` set `threshold: 0.7`, run `privexis scan`. Watch `tmp_id` disappear. You traded recall for precision.
2. Set it to `0.3`. Name-only matches start to count.
3. Remove `mobile` from the PHONE hints. The column is still found, through its values.
4. Add a `users.sqlite:acc:birth_date` entry to `metadata.yaml`. One gap disappears.
5. In a Python shell, run `is_aadhaar_like` on a number from `national_id`, then change one digit and run it again.

6. Move `owner` from `required` to `advisory` in `checklist.yaml`. Rerun, and the owner gaps disappear.
7. Delete the `negative_hints` line under DOB in `rules.yaml`. `created_at` comes back as a false alarm.

Undo your experiments afterwards (`git checkout config`) so the demo still shows the gaps.

---

## 7. Known limitations (say them before they are asked)

- A date column that isn't a birth date can still be flagged as DOB unless a negative hint covers its name (`created_at` is covered; an oddly named column would not be).
- `05/06/1990` is ambiguous between DD/MM and MM/DD.
- Email validation is a practical subset of RFC 5322, not the full grammar.
- Columns where only a small share of values are PII fall below the threshold.
- Synthetic data only; thresholds were not tuned on real data. Negative hints were added after seeing errors on the same test set, so the improved precision is not an independent measurement.
- The answer key was labelled by the team that also designed the data, so it is not an independent labelling.
- Name detection uses a pattern, not a language model. Our proposal mentions spaCy NER as a possible extension; it is **future work** and is not in the code.
- Accuracy can only be measured where an answer key exists, so uploads are scanned but not scored.
