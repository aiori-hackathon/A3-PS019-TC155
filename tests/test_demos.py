from privexis import demos
from privexis.engine import load_config

RULES, SCORING = load_config()    # run pytest from the repo root so this path resolves
CASES = demos.build_cases()


def test_privexis_gets_every_trap_right():
    for c in CASES:
        assert demos.probe(c.column, c.values, RULES, SCORING).cls == c.truth, c.title


def test_a_name_only_tool_is_fooled_by_the_disguised_columns():
    wrong = {c.column for c in CASES if demos.name_only_guess(c.column, RULES) != c.truth}
    assert {"ref_no", "x1", "col_a", "col_d", "aadhaar"} <= wrong


def test_cases_are_reproducible():
    assert [c.values for c in demos.build_cases()] == [c.values for c in CASES]


def test_fake_aadhaar_trap_really_fails_the_checksum():
    from privexis.validators import verhoeff_validate
    fake = next(c for c in CASES if c.column == "aadhaar")
    assert not any(verhoeff_validate(v.replace(" ", "")) for v in fake.values)


def test_probe_caps_values_and_ignores_blank_lines():
    f = demos.probe("email", ["a@x.com", "", "  "] + ["b@y.org"] * 500, RULES, SCORING)
    assert f.cls == "EMAIL"


def test_probe_with_no_values_is_not_flagged():
    assert demos.probe("email", [], RULES, SCORING).cls == "NONE"
