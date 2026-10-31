# Evaluation

`backend/data/ground_truth.csv` is an independently curated UTF-8 label file. The fixed-seed fixture generator intentionally does not rewrite it. It contains 25 positive fields for each C1–C5 and 50 negative look-alikes/configuration fields (175 total). Each row has `column_name`, JSON-array `sample_values`, and `label` (`C1`–`C5` or `not personal data`). All examples are synthetic.

The evaluator reports one-vs-rest precision, recall, and F1 per class, plus macro/micro summaries and a confusion matrix. Current baseline against `privexis-rules/2.0` is:

| Class | TP | FP | FN | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| C1 Personal identity | 25 | 2 | 0 | 0.9259 | 1.0000 | 0.9615 |
| C2 Contact information | 25 | 4 | 0 | 0.8621 | 1.0000 | 0.9259 |
| C3 Government identifiers | 25 | 3 | 0 | 0.8929 | 1.0000 | 0.9434 |
| C4 Financial information | 25 | 2 | 0 | 0.9259 | 1.0000 | 0.9615 |
| C5 Location / address | 25 | 3 | 0 | 0.8929 | 1.0000 | 0.9434 |

Macro precision is 0.8999, macro recall is 1.0000, and macro F1 is 0.9472. These are results on this small field-name set, not expected production accuracy. False positives intentionally remain visible to demonstrate why findings need human review.

The 10 scan fixtures consist of one CSV and one SQLite database per class, with 20 synthetic rows each. Regenerate fixtures and the metadata template (without changing labels) with:

```powershell
.\.venv\Scripts\python.exe -m backend.data.generate_synthetic_datasets
```

No real personal data, scraped data, or leaked datasets are included.
