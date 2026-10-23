# Demo script (5 minutes)

Follow the order of the PS-019 outputs. Show the web app last.

1. **The problem (30 s).** Personal data piles up in files nobody documented. You cannot attach a purpose or retention period to a field you have not found.
2. **Scan (45 s).** `privexis scan`. Say: 22 columns scanned, 13 flagged as candidates, 7 with evidence gaps, 1 needs review.
3. **Inventory (45 s).** Open `reports/inventory.csv`. Point at one row: class, confidence, evidence text, declared purpose/retention/owner, status. Say: every row is a *candidate*, never "verified".
4. **Evidence gap report (60 s).** Open `reports/gap_report.md`. Show the checklist table: `yes`, `**NO**` (required, missing) and `no` (advisory). Show a field with `NO_METADATA_ENTRY` (`temp_dump.csv`) and one with a single gap (`mobile`: no retention). Show the needs-review list (`comments`).
5. **Configurability (30 s).** Open `config/checklist.yaml`. Move `owner` to `advisory`, rerun, and the owner gaps disappear. Undo it with `git checkout config`.
6. **Accuracy (60 s).** Use the printed table. Say what precision and recall mean. Show the main set (22 columns), then the fresh set (21 columns the rules never saw): its numbers are lower, and say so. Name the families of mistakes (free text read as a name, dates read as birth dates, passports and spelled-out dates not supported). Say the labels were written by hand (`docs/LABELLING.md`).
7. **Boundary (15 s).** Show the disclaimer. Say: no lawful-basis decision, no data-flow inference.
8. **Web app (90 s, optional).** Open the live link and go through the tabs: **Evidence** (tags and the threshold slider), **Gaps** (the checklist table), **Accuracy** (both sets), **Try to fool it** (pick `ref_no`: a name-only tool says "not personal data", Privexis finds the Aadhaar numbers by their checksum; then pick `aadhaar`, the trap the other way), **Rules** (the config, live). Optionally upload a small synthetic CSV. Say why uploads are safe: temporary folder, deleted after the scan, masked values, synthetic data only.

Pseudocode for the mentor: `PSEUDOCODE.md`.
