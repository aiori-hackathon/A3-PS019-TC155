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


# ---- the held-out set: columns the rules were never tuned on ----
HOLDOUT = Path("data/holdout")


def test_holdout_labels_match_its_files_and_cover_every_class():
    truth = load_labels(HOLDOUT / "labels.csv")
    assert set(truth.values()) <= set(CLASSES) | {"NONE"}
    assert set(CLASSES) <= set(truth.values())
    assert list(truth.values()).count("NONE") >= 5
    rules, scoring = load_config()
    res = run_pipeline(find_sources(HOLDOUT), rules, scoring, {}, load_checklist())
    evaluate(res.findings, truth)          # raises ValueError if the two sets differ


def test_holdout_and_main_set_share_no_column_file():
    main = {k[0] for k in TRUTH}
    held = {k[0] for k in load_labels(HOLDOUT / "labels.csv")}
    assert not main & held
