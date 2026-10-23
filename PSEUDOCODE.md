# Privexis pseudocode (scan, score, link, report)

The whole flow in about 20 lines. Real code: `src/privexis/` (`sampler.py`, `engine.py`, `linker.py`, `report.py`, `evaluator.py`).

```text
load rules.yaml, checklist.yaml, metadata.yaml

for each file in data/ (CSV or SQLite, opened read-only):
    for each column:
        sample = up to 50 random non-empty values            # reservoir sampling, fixed seed
        for each class in [NAME, EMAIL, PHONE, GOVT_ID, DOB]:
            if column name matches a negative hint: skip this class
            name_score  = 1 if column name matches a name hint else 0
            value_score = share of sampled values that pass the regex AND the strict validator
            confidence  = 0.4 * name_score + 0.6 * value_score
        best = class with the highest confidence
        if confidence >= 0.5:  flag column as a CANDIDATE of that class
        elif confidence >= 0.1: add column to the "needs review" list

for each candidate field:
    entry = metadata["file:table:column"]                    # may be missing
    for each item on the checklist (purpose, retention, owner, name hint, value check):
        mark the item present or missing
    gaps   = required checklist items that are missing
    status = "EVIDENCE GAP FLAG" if gaps else "Candidate: checklist complete"

write inventory.csv, inventory.json, gap_report.md           # every report carries the disclaimer
compare flagged classes with the hand-labelled labels.csv    # per-class precision and recall
```

Nothing in this flow decides a lawful basis or says whether a purpose or retention period is adequate. That is left to a human reviewer.
