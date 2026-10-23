from types import SimpleNamespace

import pytest

from privexis.linker import (STATUS_COMPLETE, STATUS_GAP, link, load_checklist,
                             orphaned_metadata)

CHECKLIST = load_checklist()     # run pytest from the repo root so this path resolves


def f(col, cls="EMAIL", name_score=1.0, value_score=1.0):
    return SimpleNamespace(source="a.csv", table="-", column=col, cls=cls, confidence=1.0,
                           evidence="e", name_score=name_score, value_score=value_score)


META = {
    "a.csv:-:full": {"purpose": "p", "retention": "r", "owner": "o"},
    "a.csv:-:no_ret": {"purpose": "p", "owner": "o"},
    "a.csv:-:no_purpose": {"retention": "r", "owner": "o"},
    "a.csv:-:no_owner": {"purpose": "p", "retention": "r"},
    "a.csv:-:stale": {"purpose": "p", "retention": "r", "owner": "o"},
}


def one(col, **kw):
    return link([f(col, **kw)], META, CHECKLIST)[0]


def test_fully_linked_has_no_gaps():
    row = one("full")
    assert row.gaps == [] and row.review_status == STATUS_COMPLETE


def test_missing_retention():
    assert one("no_ret").gaps == ["MISSING_RETENTION"]


def test_missing_purpose():
    assert one("no_purpose").gaps == ["MISSING_PURPOSE"]


def test_missing_owner_is_a_gap_because_the_checklist_requires_it():
    row = one("no_owner")
    assert row.gaps == ["MISSING_OWNER"] and row.review_status == STATUS_GAP


def test_undocumented_field_has_all_metadata_gaps():
    assert one("unknown").gaps == [
        "NO_METADATA_ENTRY", "MISSING_PURPOSE", "MISSING_RETENTION", "MISSING_OWNER"]


def test_advisory_item_missing_is_shown_but_is_not_a_gap():
    row = one("full", name_score=0.0)
    assert row.gaps == []
    hint = next(c for c in row.checklist if c["item"] == "name_hint")
    assert hint["present"] is False and hint["required"] is False


def test_government_id_requires_the_strict_validator_to_pass():
    weak = one("full", cls="GOVT_ID", value_score=0.5)
    assert weak.gaps == ["MISSING_VALUE_CHECK"]
    assert one("full", cls="EMAIL", value_score=0.5).gaps == []      # advisory for other classes


def test_non_personal_columns_are_skipped():
    assert link([f("x", "NONE")], META, CHECKLIST) == []


def test_orphaned_metadata():
    assert orphaned_metadata([f("full")], META) == [
        "a.csv:-:no_owner", "a.csv:-:no_purpose", "a.csv:-:no_ret", "a.csv:-:stale"]


def write(tmp_path, text):
    p = tmp_path / "c.yaml"
    p.write_text(text, encoding="utf-8")
    return p


def test_checklist_rejects_unknown_item_reference(tmp_path):
    p = write(tmp_path, "items:\n  purpose: {kind: metadata}\nrequired: [purpose, nope]\n")
    with pytest.raises(ValueError):
        load_checklist(p)


def test_checklist_rejects_unknown_detection_check(tmp_path):
    p = write(tmp_path, "items:\n  magic: {kind: detection}\nrequired: [magic]\n")
    with pytest.raises(ValueError):
        load_checklist(p)


def test_checklist_rejects_bad_kind(tmp_path):
    p = write(tmp_path, "items:\n  purpose: {kind: other}\nrequired: [purpose]\n")
    with pytest.raises(ValueError):
        load_checklist(p)
