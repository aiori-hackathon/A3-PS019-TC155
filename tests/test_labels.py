"""Checks on the hand-written answer key (data/labels.csv)."""
from pathlib import Path

from privexis.engine import load_config
from privexis.evaluator import CLASSES, evaluate, load_labels
from privexis.linker import load_checklist
from privexis.pipeline import find_sources, run_pipeline

TRUTH = load_labels()     # run pytest from the repo root so this path resolves


def test_labels_use_only_known_classes():
    assert set(TRUTH.values()) <= set(CLASSES) | {"NONE"}


def test_labels_include_every_class_and_some_non_personal_columns():
    assert set(CLASSES) <= set(TRUTH.values())
    assert list(TRUTH.values()).count("NONE") >= 5


def test_labels_match_the_columns_in_the_data_files():
    rules, scoring = load_config()
    res = run_pipeline(find_sources("data"), rules, scoring, {}, load_checklist())
    evaluate(res.findings, TRUTH)          # raises ValueError if the two sets differ
