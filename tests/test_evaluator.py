import pytest

from sentry.evaluator import LabelRecord, evaluate_findings
from sentry.models import Finding


def _finding(pii_type: str, row: int, col: str = "data") -> Finding:
    return Finding(
        rule_id=f"{pii_type}_TEST",
        pii_type=pii_type,
        source_file="synthetic.csv",
        row_number=row,
        column_name=col,
        masked_evidence="j***@example.com" if pii_type == "EMAIL" else "XXXXX1234X",
    )


def _label(pii_type: str, row: int, is_pii: bool, col: str = "data") -> LabelRecord:
    return LabelRecord(
        source_file="synthetic.csv",
        row_number=row,
        column_name=col,
        pii_type=pii_type,
        is_pii=is_pii,
    )


def test_evaluator_reports_tp_fp_fn_and_unlabelled_predictions():
    labels = [
        _label("EMAIL", 2, True),
        _label("EMAIL", 3, False),
        _label("EMAIL", 4, True),
        _label("PAN", 2, False),
    ]
    findings = [
        _finding("EMAIL", 2),  # TP
        _finding("EMAIL", 3),  # FP
        _finding("PAN", 2),    # FP
        _finding("EMAIL", 5),  # unlabelled; not silently scored
    ]

    report = evaluate_findings(findings, labels)
    email = report.by_pii_type["EMAIL"]
    assert email.true_positive == 1
    assert email.false_positive == 1
    assert email.false_negative == 1
    assert email.precision == pytest.approx(0.5)
    assert email.recall == pytest.approx(0.5)
    assert report.micro.false_positive == 2
    assert report.unlabelled_predictions == 1


def test_evaluator_rejects_duplicate_labels():
    duplicate_labels = [_label("EMAIL", 2, True), _label("EMAIL", 2, False)]
    with pytest.raises(ValueError, match="Duplicate"):
        evaluate_findings([], duplicate_labels)


def test_evaluator_rejects_empty_labels():
    with pytest.raises(ValueError, match="At least one"):
        evaluate_findings([], [])
