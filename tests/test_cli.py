from privexis.cli import main


def make_data(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    (d / "t.csv").write_text("email\na@x.com\nb@y.org\n", encoding="utf-8")
    return d


def test_scan_writes_reports(tmp_path):
    d = make_data(tmp_path)
    out = tmp_path / "out"
    code = main(["scan", "--data", str(d), "--config", "config",
                 "--labels", str(tmp_path / "none.csv"), "--out", str(out)])
    assert code == 0
    assert (out / "inventory.json").exists()
    assert (out / "gap_report.md").exists()


def test_inventory_contains_email_candidate(tmp_path):
    d = make_data(tmp_path)
    out = tmp_path / "out"
    main(["scan", "--data", str(d), "--config", "config",
          "--labels", str(tmp_path / "none.csv"), "--out", str(out)])
    assert "EMAIL" in (out / "inventory.csv").read_text(encoding="utf-8")