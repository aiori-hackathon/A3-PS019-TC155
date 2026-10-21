from types import SimpleNamespace

from privexis.evaluator import evaluate


def f(col, cls):
    return SimpleNamespace(source="a.csv", table="-", column=col, cls=cls)


def test_precision_and_recall():
    truth = {("a.csv", "-", "c1"): "EMAIL", ("a.csv", "-", "c2"): "EMAIL",
             ("a.csv", "-", "c3"): "NONE"}
    # finds c1 (correct), misses c2, wrongly flags c3
    out = evaluate([f("c1", "EMAIL"), f("c2", "NONE"), f("c3", "EMAIL")], truth)
    m = out["per_class"]["EMAIL"]
    assert (m["tp"], m["fp"], m["fn"]) == (1, 1, 1)
    assert m["precision"] == 0.5 and m["recall"] == 0.5


def test_undefined_is_none_not_zero():
    truth = {("a.csv", "-", "c1"): "NONE"}
    out = evaluate([f("c1", "NONE")], truth)
    assert out["per_class"]["PHONE"]["precision"] is None