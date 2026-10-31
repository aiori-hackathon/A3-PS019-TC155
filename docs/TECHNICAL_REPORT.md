# PS-019: Personal-Data Discovery and Privacy Evidence Inventory

## Outcome

Privexis implements the requested local discovery workflow for synthetic structured data. It accepts UTF-8 CSV and SQLite, detects candidate personal-data fields, links findings to declared purpose and retention, supports human review, and reports per-class evaluation and metadata gaps. Findings are technical evidence and do not make legal or lawful-basis decisions.

## Requirement check

| Requirement | Result | Evidence |
| --- | --- | --- |
| CSV and one SQL database format | Pass | CSV upload and SQLite (`mode=ro`) scanning; 10 fixtures cover both formats |
| Five predefined classes | Pass | C1 identity, C2 contact, C3 government identifiers, C4 financial, C5 location/address |
| Synthetic, manually labelled evaluation set | Pass | Independent `ground_truth.csv`: 25 positive fields/class and 50 negative look-alikes (175 total) |
| Configurable detection checklist | Pass | Each workspace can enable/disable class rules; new scans snapshot the enabled list |
| Purpose and retention mapping | Pass | Field-level mapping workflow in the workspace |
| Missing metadata report | Pass | Evidence-gap endpoint and report identify missing purpose/retention |
| Per-class precision and recall | Pass | Evaluation page/API reports all five classes and F1 |
| Technical evidence separated from legal conclusions | Pass | UI, report, and documentation disclaimers; no lawful-basis determination |
| Expected deliverables | Pass | Scanner, inventory, configurable checklist, mapping, metrics, gap report, this report, and sample-file demonstration |

## Synthetic data and reproducibility

The generator uses seed `20261031` to create 10 fixtures: one CSV and one SQLite file for each class. Each contains 20 synthetic rows and 11 columns (eight class fields and three look-alike negatives). All ten fixtures scanned successfully and produced eight candidate findings each. Re-running the generator reproduced the fixture and metadata-template hashes and left the independent label file unchanged.

The evaluation label file contains 175 fields: 25 positives for each class and 50 fields labelled `not personal data`. It includes look-alike identifiers and configuration fields so precision measures false matches. No real personal data, scraped data, or leaked data is used.

## Evaluation results

Baseline results for `privexis-rules/2.0` on the committed synthetic field-level labels:

| Class | TP | FP | FN | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| C1 Personal identity | 25 | 2 | 0 | 92.59% | 100.00% | 96.15% |
| C2 Contact information | 25 | 4 | 0 | 86.21% | 100.00% | 92.59% |
| C3 Government identifiers | 25 | 3 | 0 | 89.29% | 100.00% | 94.34% |
| C4 Financial information | 25 | 2 | 0 | 92.59% | 100.00% | 96.15% |
| C5 Location / address | 25 | 3 | 0 | 89.29% | 100.00% | 94.34% |

Macro precision is 89.99%, macro recall is 100.00%, and macro F1 is 94.72%. Of the 50 negative fields, 36 were labelled `not personal data`; 14 produced candidate matches and remain visible as false positives. The rule tester and inventory let reviewers inspect those matches and record decisions.

These figures describe this small, synthetic, field-name evaluation only. They are not a claim of real-world accuracy. Rule patterns are shipped in code; the workspace checklist configures which class rules run, rather than allowing users to author arbitrary regular expressions.

## Demonstration flow

1. Open `http://localhost:3000` and choose **Get started**.
2. Choose one of the ten CSV/SQLite samples; **Add & run scan** registers and scans it.
3. Review candidate fields in the inventory. Search supports feature pages and workspace findings.
4. Open the Rules page to change the workspace evidence checklist. Future scans record the enabled class list used.
5. Map purpose/retention, inspect evidence gaps, and record a human review decision.
6. Open Evaluation and Reports for per-class metrics and exports.

## Validation run

- Backend suite: 11 passed (one non-blocking Starlette/httpx test-client deprecation warning).
- TypeScript: passed.
- ESLint: passed with `corepack pnpm lint --quiet`.
- Production build: passed with `corepack pnpm build` after the final checklist UI changes.
- Live UI smoke check: search found the evaluation page; the assistant opened and answered the five-class prompt; a synthetic identity CSV produced eight candidate findings visible in Inventory and eight corresponding metadata/review gaps in Evidence Gaps.
- Live endpoints: home, Rules, Evaluation, and backend OpenAPI returned HTTP 200 during the local smoke run. The deployed frontend is [privexis.vercel.app](https://privexis.vercel.app/) and the API readiness endpoint is [privexis-api.onrender.com/api/v1/health/ready](https://privexis-api.onrender.com/api/v1/health/ready).

## Scope notes

The assistant button provides local product guidance and does not call an external generative AI provider. The scanner is field-name/rule based, uses bounded synthetic samples, and depends on human review for context. CSV and SQLite are the supported source formats in this version.
