"""Cell/type-level evaluation against an exhaustively hand-labelled CSV."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sentry.models import Finding, PIIType

PII_TYPES: tuple[PIIType, ...] = ("EMAIL", "AADHAAR", "PAN", "DOB")


class LabelRecord(BaseModel):
    """One hand label for a source row, column, and PII class.

    Each key must appear exactly once in the label file, including negative
    labels. This evaluator measures whether a cell contains a PII type; it does
    not measure exact character-span boundaries.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_file: str = Field(min_length=1)
    row_number: int = Field(ge=2)
    column_name: str = Field(min_length=1)
    pii_type: PIIType
    is_pii: bool

    @field_validator("is_pii", mode="before")
    @classmethod
    def parse_boolean_label(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, int) and value in (0, 1):
            return bool(value)
        if isinstance(value, str):
            normalized = value.strip().casefold()
            if normalized in {"true", "1", "yes", "y"}:
                return True
            if normalized in {"false", "0", "no", "n"}:
                return False
        raise ValueError("is_pii must be true/false, yes/no, or 1/0")


class Metrics(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    true_positive: int = Field(ge=0)
    false_positive: int = Field(ge=0)
    false_negative: int = Field(ge=0)
    true_negative: int = Field(ge=0)
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    f1: float = Field(ge=0.0, le=1.0)
    labelled_items: int = Field(ge=0)


class EvaluationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    metric_level: Literal["cell_type"] = "cell_type"
    micro: Metrics
    by_pii_type: dict[str, Metrics]
    unlabelled_predictions: int = Field(ge=0)
    labelled_items: int = Field(ge=0)
    unique_predictions: int = Field(ge=0)


Key = tuple[str, int, str, str]


def _key(source_file: str, row_number: int, column_name: str, pii_type: str) -> Key:
    return (source_file, row_number, column_name, pii_type)


def _make_metrics(tp: int, fp: int, fn: int, tn: int, labelled_items: int) -> Metrics:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return Metrics(
        true_positive=tp,
        false_positive=fp,
        false_negative=fn,
        true_negative=tn,
        precision=precision,
        recall=recall,
        f1=f1,
        labelled_items=labelled_items,
    )


def load_labels_csv(path: str | Path, *, encoding: str = "utf-8-sig") -> list[LabelRecord]:
    """Read labels from CSV with headers source_file,row_number,column_name,pii_type,is_pii."""
    required = {"source_file", "row_number", "column_name", "pii_type", "is_pii"}
    try:
        with Path(path).open("r", encoding=encoding, newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
                raise ValueError("Label CSV is missing one or more required headers.")
            return [LabelRecord.model_validate(row) for row in reader]
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ValueError("Label CSV could not be read. Check its encoding and structure.") from None


def evaluate_findings(
    findings: Iterable[Finding],
    labels: Iterable[LabelRecord],
) -> EvaluationReport:
    """Return aggregate metrics; predictions outside label coverage are reported separately.

    The label file must cover positives and negatives for every cell/type pair
    in the evaluation scope. An unmatched prediction is not silently counted
    as a false positive; it increments `unlabelled_predictions` instead.
    """
    label_map: dict[Key, bool] = {}
    for label in labels:
        key = _key(label.source_file, label.row_number, label.column_name, label.pii_type)
        if key in label_map:
            raise ValueError("Duplicate cell/type key in hand-labelled dataset.")
        label_map[key] = label.is_pii

    if not label_map:
        raise ValueError("At least one hand-labelled item is required for evaluation.")

    predicted: set[Key] = {
        _key(f.source_file, f.row_number, f.column_name, f.pii_type)
        for f in findings
    }
    labelled_keys = set(label_map)
    unlabelled_predictions = predicted - labelled_keys
    by_type: dict[str, Metrics] = {}

    for pii_type in PII_TYPES:
        type_keys = {key for key in labelled_keys if key[3] == pii_type}
        positives = {key for key in type_keys if label_map[key]}
        negatives = type_keys - positives
        type_predictions = predicted & type_keys
        tp = len(type_predictions & positives)
        fp = len(type_predictions & negatives)
        fn = len(positives - type_predictions)
        tn = len(negatives - type_predictions)
        by_type[pii_type] = _make_metrics(tp, fp, fn, tn, len(type_keys))

    total_tp = sum(metric.true_positive for metric in by_type.values())
    total_fp = sum(metric.false_positive for metric in by_type.values())
    total_fn = sum(metric.false_negative for metric in by_type.values())
    total_tn = sum(metric.true_negative for metric in by_type.values())

    return EvaluationReport(
        micro=_make_metrics(total_tp, total_fp, total_fn, total_tn, len(labelled_keys)),
        by_pii_type=by_type,
        unlabelled_predictions=len(unlabelled_predictions),
        labelled_items=len(labelled_keys),
        unique_predictions=len(predicted),
    )
