from types import SimpleNamespace

from privexis.linker import link, orphaned_metadata


def f(col, cls="EMAIL"):
    return SimpleNamespace(source="a.csv", table="-", column=col, cls=cls,
                           confidence=1.0, evidence="e")


META = {
    "a.csv:-:full": {"purpose": "p", "retention": "r", "owner": "o"},
    "a.csv:-:no_ret": {"purpose": "p"},
    "a.csv:-:no_purpose": {"retention": "r"},
    "a.csv:-:stale": {"purpose": "p", "retention": "r"},
}


def gaps_for(col):
    return link([f(col)], META)[0].gaps


def test_fully_linked_has_no_gaps():
    assert gaps_for("full") == []


def test_missing_retention():
    assert gaps_for("no_ret") == ["MISSING_RETENTION"]


def test_missing_purpose():
    assert gaps_for("no_purpose") == ["MISSING_PURPOSE"]


def test_undocumented_field_has_all_gaps():
    assert gaps_for("unknown") == ["NO_METADATA_ENTRY", "MISSING_PURPOSE", "MISSING_RETENTION"]


def test_non_personal_columns_are_skipped():
    assert link([f("x", "NONE")], META) == []


def test_orphaned_metadata():
    assert orphaned_metadata([f("full")], META) == [
        "a.csv:-:no_purpose", "a.csv:-:no_ret", "a.csv:-:stale"]