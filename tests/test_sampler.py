import csv
import sqlite3

from privexis.sampler import sample_path


def make_csv(path, n):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["a", "b"])
        for i in range(n):
            w.writerow([i, "" if i % 2 else "x"])


def get(cols, name):
    return next(c for c in cols if c.column == name)


def test_sample_is_bounded(tmp_path):
    p = tmp_path / "t.csv"
    make_csv(p, 500)
    a = get(sample_path(p, k=20), "a")
    assert len(a.values) == 20
    assert a.non_empty == 500


def test_empty_values_are_skipped(tmp_path):
    p = tmp_path / "t.csv"
    make_csv(p, 500)
    b = get(sample_path(p, k=20), "b")
    assert b.non_empty == 250
    assert "" not in b.values


def test_sampling_is_deterministic(tmp_path):
    p = tmp_path / "t.csv"
    make_csv(p, 500)
    first = get(sample_path(p, k=20), "a").values
    second = get(sample_path(p, k=20), "a").values
    assert first == second


def test_sqlite_connector(tmp_path):
    db = tmp_path / "t.sqlite"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE people (name TEXT, age INTEGER)")
    con.executemany("INSERT INTO people VALUES (?,?)", [("Asha", 30), ("Rohan", 41)])
    con.commit()
    con.close()

    cols = sample_path(db, k=5)
    assert {c.table for c in cols} == {"people"}
    assert sorted(get(cols, "age").values) == ["30", "41"]
