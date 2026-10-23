from types import SimpleNamespace

from privexis import ui


def row(column="email", cls="EMAIL", gaps=(), **kw):
    base = dict(source="a.csv", table="-", column=column, cls=cls, confidence=1.0,
                purpose="", retention="", owner="", gaps=list(gaps), evidence="e",
                checklist=[])
    base.update(kw)
    return SimpleNamespace(**base)


def test_mask_hides_most_of_each_word():
    assert ui.mask_value("asha.sharma12@example.com") == "a•••.s•••••••@e••••••.c••"
    assert ui.mask_value("2345 6789 0123") == "2••• 6••• 0•••"


def test_mask_truncates_long_values():
    assert len(ui.mask_value("x" * 100)) == 26


def test_uploaded_text_is_escaped():
    nasty = '<script>alert(1)</script>'
    out = ui.tag_html(row(column=nasty, source=nasty, purpose=nasty, evidence=nasty),
                      [nasty], 0.5)
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_html_blocks_are_single_line():
    # Streamlit's markdown breaks HTML blocks at blank lines, so no newlines are allowed.
    for out in (ui.hero_html(), ui.notice_html(), ui.summary_html(10, 4, 2),
                ui.tag_html(row(), ["a@x.com"], 0.5), ui.split_html("d")):
        assert "\n" not in out


def test_gap_chips_do_not_repeat_when_undocumented():
    out = ui.tag_html(row(gaps=["NO_METADATA_ENTRY", "MISSING_PURPOSE", "MISSING_RETENTION"]),
                      [], 0.5)
    assert out.count("px-chip gap") == 1
    assert "Not documented" in out


def test_complete_card():
    out = ui.tag_html(row(purpose="p", retention="r", owner="o"), [], 0.5)
    assert "Checklist complete" in out and "px-chip gap" not in out


def test_detection_gap_is_still_shown_next_to_not_documented():
    out = ui.tag_html(row(gaps=["NO_METADATA_ENTRY", "MISSING_PURPOSE", "MISSING_VALUE_CHECK"]),
                      [], 0.5)
    assert out.count("px-chip gap") == 2 and "Values fail the check" in out


def test_detection_evidence_is_listed_on_the_card():
    checks = [{"item": "name_hint", "label": "Column name matches a known hint",
               "kind": "detection", "required": False, "present": False}]
    out = ui.tag_html(row(checklist=checks), [], 0.5)
    assert "No: Column name matches a known hint (advisory)" in out


def test_review_list_is_escaped():
    f = SimpleNamespace(column="<b>x</b>", source="s.csv", evidence="e")
    assert "<b>" not in ui.review_html([f])


def test_summary_handles_empty_scan():
    assert "No columns look like personal data" in ui.summary_html(0, 0, 0)


def test_accuracy_shows_undefined_as_na():
    metrics = {"per_class": {"PHONE": {"tp": 0, "fp": 0, "fn": 0,
                                       "precision": None, "recall": None, "f1": None}}}
    assert "n/a" in ui.accuracy_html(metrics)


def test_css_respects_reduced_motion_and_prefixes_rules():
    assert "prefers-reduced-motion" in ui.CSS
    assert "@@" not in ui.CSS
