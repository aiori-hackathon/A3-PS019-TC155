# Demo script (5 minutes)

Follow the order of the PS-019 outputs. Show the web app last.

1. **The problem (30 s).** Personal data piles up in files nobody documented. You cannot attach a purpose or retention period to a field you have not found.
2. **Scan (45 s).** `privexis scan`. Say: 22 columns scanned, 13 flagged as candidates, 7 with evidence gaps, 1 needs review.
3. **Inventory (45 s).** Open `reports/inventory.csv`. Point at one row: class, confidence, evidence text, declared purpose/retention/owner, status. Say: every row is a *candidate*, never "verified".
4. **Evidence gap report (60 s).** Open `reports/gap_report.md`. Show the checklist table: `yes`, `**NO**` (required, missing) and `no` (advisory). Show a field with `NO_METADATA_ENTRY` (`temp_dump.csv`) and one with a single gap (`mobile`: no retention). Show the needs-review list (`comments`).
5. **Configurability (30 s).** Open `config/checklist.yaml`. Move `owner` to `advisory`, rerun, and the owner gaps disappear. Undo it with `git checkout config`.
6. **Accuracy (45 s).** Open `reports/metrics.json` or the printed table. Say what precision and recall mean, show the two remaining misses (`comments`, `holder`), and say the labels were written by hand (`docs/LABELLING.md`).
7. **Boundary (15 s).** Show the disclaimer. Say: no lawful-basis decision, no data-flow inference.
8. **Web app (60 s, optional).** Open the live link. Show the evidence tags and the threshold slider. Upload a small synthetic CSV. Say why uploads are safe: temporary folder, deleted after the scan, masked values, synthetic data only.

Pseudocode for the mentor: `PSEUDOCODE.md`.
