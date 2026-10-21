"""Rule engine: fuse column-name hints + value patterns + validators into one score."""
import re
from dataclasses import dataclass

import yaml

from privexis import validators as V
from privexis.sampler import sample_path

# Config refers to validators by name; this maps the names to real functions.
VALIDATORS = {
    "email": V.is_email,
    "govt_id": V.is_govt_id,
    "date_plausible": V.is_plausible_dob,
}


@dataclass
class Rule:
    cls: str
    name_hints: list
    patterns: list      # compiled regexes
    validator: object   # a function, or None


@dataclass
class Finding:
    source: str
    table: str
    column: str
    cls: str            # best class, or "NONE" if below threshold
    confidence: float
    name_score: float
    value_score: float
    evidence: str


def load_config(path="config/rules.yaml"):
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)          # safe_load: never executes code from the file
    rules = []
    for cls, spec in raw["classes"].items():
        validator = VALIDATORS[spec["validator"]] if spec.get("validator") else None
        rules.append(Rule(
            cls,
            [h.lower() for h in spec.get("name_hints", [])],
            [re.compile(p) for p in spec.get("value_patterns", [])],
            validator,
        ))
    return rules, raw["scoring"]


def normalize(col: str) -> str:
    """'ContactEmail' / 'contact-email' / 'Contact Email' -> 'contact_email'."""
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", col)     # split camelCase
    return "_".join(t for t in re.split(r"[^A-Za-z0-9]+", s.lower()) if t)


def matched_hint(col: str, hints: list):
    # Pad with underscores so a hint only matches whole tokens:
    # 'pan' matches 'pan_no' but NOT 'company'.
    padded = f"_{normalize(col)}_"
    for h in hints:
        if f"_{h}_" in padded:
            return h
    return None


def value_passes(v: str, rule: Rule) -> bool:
    if rule.patterns and not any(p.match(v) for p in rule.patterns):
        return False
    if rule.validator and not rule.validator(v):
        return False
    return True


def score_column(sample, rules, scoring) -> Finding:
    best = None
    for rule in rules:
        hint = matched_hint(sample.column, rule.name_hints)
        name_score = 1.0 if hint else 0.0
        vals = sample.values
        passed = sum(value_passes(v, rule) for v in vals)
        value_score = passed / len(vals) if vals else 0.0
        conf = scoring["name_weight"] * name_score + scoring["value_weight"] * value_score

        parts = []
        if hint:
            parts.append(f"name hint '{hint}'")
        parts.append(f"{passed}/{len(vals)} sampled values passed pattern+validator")
        cand = (conf, rule.cls, name_score, value_score, "; ".join(parts))
        if best is None or cand[0] > best[0]:
            best = cand

        conf, cls, ns, vs, ev = best
    if conf < scoring["threshold"]:
        if conf == 0:
            ev = "no supporting evidence for any class"
        else:
            ev = f"below threshold; closest class {cls}: {ev}"
        cls = "NONE"
    return Finding(sample.source, sample.table, sample.column,
                   cls, round(conf, 2), ns, round(vs, 2), ev)


def scan_path(path, rules, scoring, k: int = 50) -> list:
    return [score_column(s, rules, scoring) for s in sample_path(path, k=k)]