"""Look and feel of the web app: plain functions that return HTML and CSS strings.

This file does not import Streamlit, so it can be tested without it.
Everything that comes from an uploaded file (column names, values, metadata) is
escaped before it goes into HTML. Sample values are masked, so full values are
never shown on screen.
"""
from html import escape

# Class -> (display label, colour). Colour is never the only signal: the label is always printed too.
CLASS_META = {
    "NAME": ("Name", "#FF8FB1"),
    "EMAIL": ("Email", "#8EB8FF"),
    "PHONE": ("Phone", "#6FE0B5"),
    "GOVT_ID": ("Government ID", "#FFB067"),
    "DOB": ("Date of birth", "#C3A6FF"),
}

GAP_LABELS = {
    "NO_METADATA_ENTRY": "Not documented",
    "MISSING_PURPOSE": "No purpose",
    "MISSING_RETENTION": "No retention period",
    "MISSING_OWNER": "No owner",
    "MISSING_NAME_HINT": "No name hint",
    "MISSING_VALUE_CHECK": "Values fail the check",
}
# Gaps that "Not documented" already covers, so they are not repeated as extra chips.
_METADATA_GAPS = {"MISSING_PURPOSE", "MISSING_RETENTION", "MISSING_OWNER"}


def _e(value) -> str:
    return escape(str(value), quote=True)


def mask_value(value, keep: int = 1, limit: int = 26) -> str:
    """Keep the first `keep` characters of each word/number and hide the rest.
    'asha.sharma12@example.com' -> 'a•••.s•••••••@e••••••.c••'"""
    out, seen = [], 0
    for ch in str(value):
        if ch.isalnum():
            out.append(ch if seen < keep else "•")
            seen += 1
        else:
            out.append(ch)
            seen = 0
    text = "".join(out)
    return text if len(text) <= limit else text[:limit - 1] + "…"


def _where(source, table) -> str:
    return _e(source) if table in ("-", "", None) else f"{_e(source)} / {_e(table)}"


# --------------------------------------------------------------------------- hero
def hero_html() -> str:
    def col(i, name, tag_label, tag_style, widths, color=""):
        bars = "".join(f'<i style="--w:{w}%"></i>' for w in widths)
        tint = f"--c:{color};" if color else ""
        return (f'<div class="px-col" style="--i:{i}">'
                f'<span class="px-colname">{name}</span>{bars}'
                f'<span class="px-result {tag_style}" style="{tint}">{tag_label}</span></div>')

    strip = "".join([
        col(0, "full_name", "Name", "hit", (82, 70, 90, 64, 76), CLASS_META["NAME"][1]),
        col(1, "national_id", "Government ID", "hit", (96, 96, 96, 96, 96), CLASS_META["GOVT_ID"][1]),
        col(2, "ref_no", "Fails checksum", "skip", (96, 96, 96, 96, 96)),
        col(3, "city", "No match", "skip", (48, 40, 56, 44, 52)),
    ])
    return (
        '<section class="px-hero">'
        '<div class="px-copy">'
        '<p class="px-brand"><span>Privexis</span></p>'
        '<h1 class="px-title">Personal data hides in files nobody documented.</h1>'
        '<p class="px-lede">Add a CSV or SQLite file. Privexis points to the columns that look like '
        'names, emails, phone numbers, ID numbers and birth dates, then shows which of them '
        'have no stated purpose or retention period.</p>'
        '</div>'
        '<div class="px-scan">'
        f'<div class="px-strip" role="img" aria-label="Example: a scan marks the full_name column '
        f'as Name and national_id as Government ID, and skips ref_no because its checksum fails, and city.">'
        f'{strip}</div>'
        '<p class="px-cap">Values stay hidden. Privexis labels the columns and says why.</p>'
        '</div>'
        '</section>'
    )


def notice_html() -> str:
    return ('<div class="px-notice"><strong>Synthetic or test data only.</strong> '
            'Do not upload real personal data. Uploaded files are read in a temporary folder '
            'that is deleted right after the scan. This app saves nothing, and sample values '
            'are masked on screen.</div>')


def heading_html(text: str, sub: str = "") -> str:
    subtitle = f'<p class="px-sub">{_e(sub)}</p>' if sub else ""
    return f'<h2 class="px-h2">{_e(text)}</h2>{subtitle}'


# --------------------------------------------------------------------------- summary
def summary_html(n_columns: int, n_candidates: int, n_with_gaps: int) -> str:
    total = max(n_columns, 1)
    ok = n_candidates - n_with_gaps
    other = n_columns - n_candidates

    def pct(n):
        return f"{100 * n / total:.2f}"

    if n_candidates == 0:
        big = "No columns look like personal data at this threshold."
        sub = "Lower the threshold under Tuning to see weaker matches."
    else:
        big = f"{n_candidates} of {n_columns} columns look like personal data."
        sub = (f"{n_with_gaps} of them have no declared purpose, no retention period, or both."
               if n_with_gaps else "All of them have a declared purpose and retention period.")
    label = (f"{ok} documented, {n_with_gaps} with gaps, {other} not flagged")
    return (
        '<section class="px-summary">'
        f'<p class="px-big">{_e(big)}</p><p class="px-sub">{_e(sub)}</p>'
        f'<div class="px-bar" role="img" aria-label="{_e(label)}">'
        f'<span class="ok" style="--w:{pct(ok)}%"></span>'
        f'<span class="gap" style="--w:{pct(n_with_gaps)}%"></span>'
        f'<span class="other" style="--w:{pct(other)}%"></span></div>'
        '<ul class="px-legend">'
        f'<li><i class="ok"></i>{ok} fully documented</li>'
        f'<li><i class="gap"></i>{n_with_gaps} with gaps</li>'
        f'<li><i class="other"></i>{other} not flagged</li></ul>'
        '</section>'
    )


# --------------------------------------------------------------------------- evidence tags
def tag_html(row, examples, threshold: float) -> str:
    label, color = CLASS_META.get(row.cls, (row.cls, "#DDDDDD"))
    conf = max(0.0, min(float(row.confidence), 1.0))
    thr = max(0.0, min(float(threshold), 1.0))

    gaps = list(row.gaps)
    if "NO_METADATA_ENTRY" in gaps:
        gaps = [g for g in gaps if g not in _METADATA_GAPS]
    if gaps:
        chips = "".join(f'<span class="px-chip gap">{GAP_LABELS.get(g, _e(g))}</span>'
                        for g in gaps)
    else:
        chips = '<span class="px-chip ok">Checklist complete</span>'

    # detection evidence the scanner collected itself (kind "detection" in checklist.yaml)
    marks = "".join(
        f'<li class="{"yes" if c["present"] else "no"}">'
        f'{"Yes" if c["present"] else "No"}: {_e(c["label"])}'
        f'{" (required)" if c["required"] else "" if c["present"] else " (advisory)"}</li>'
        for c in (getattr(row, "checklist", None) or []) if c["kind"] == "detection")
    detection = f'<ul class="px-marks">{marks}</ul>' if marks else ""

    shown = "".join(f"<code>{_e(mask_value(v))}</code>" for v in (examples or [])[:3])
    sample_row = f'<div class="px-examples" aria-label="Masked example values">{shown}</div>' if shown else ""

    def line(name, value):
        text = _e(value) if value else '<span class="px-none">not declared</span>'
        return f"<dt>{name}</dt><dd>{text}</dd>"

    return (
        f'<article class="px-card" style="--c:{color}">'
        f'<div class="px-cardtop"><span class="px-class">{_e(label)}</span>'
        f'<span class="px-score">{conf:.2f}</span></div>'
        f'<h3 class="px-colhead">{_e(row.column)}</h3>'
        f'<p class="px-where">{_where(row.source, row.table)}</p>'
        f'<div class="px-meter" role="img" aria-label="Confidence {conf:.2f}, threshold {thr:.2f}">'
        f'<i style="--w:{conf * 100:.1f}%"></i><b style="--t:{thr * 100:.1f}%"></b></div>'
        f'{sample_row}'
        f'<div class="px-chips">{chips}</div>'
        f'<dl class="px-meta">{line("Purpose", row.purpose)}{line("Retention", row.retention)}'
        f'{line("Owner", row.owner)}</dl>'
        f'{detection}'
        f'<p class="px-why">{_e(row.evidence)}</p>'
        '</article>'
    )


def tags_grid_html(cards: list) -> str:
    return f'<div class="px-grid">{"".join(cards)}</div>'


def unflagged_html(findings) -> str:
    items = "".join(
        f'<li><code>{_e(f.column)}</code><span>{_e(f.evidence)}</span></li>' for f in findings)
    return f'<ul class="px-plain">{items}</ul>'


def review_html(findings) -> str:
    """Columns that were not flagged but scored between the review floor and the threshold."""
    items = "".join(
        f'<li><code>{_e(f.column)}</code><span>{_e(f.source)}: {_e(f.evidence)}</span></li>'
        for f in findings)
    return f'<ul class="px-plain px-review">{items}</ul>'


def orphans_html(orphans: list) -> str:
    items = "".join(f"<li><code>{_e(o)}</code></li>" for o in orphans)
    return f'<ul class="px-plain">{items}</ul>'


# --------------------------------------------------------------------------- accuracy
def _ratio(value) -> str:
    return "n/a" if value is None else f"{value:.2f}"


def accuracy_html(metrics: dict) -> str:
    rows = []
    for cls, m in metrics["per_class"].items():
        label, color = CLASS_META.get(cls, (cls, "#DDDDDD"))

        def bar(v):
            width = 0 if v is None else v * 100
            return f'<div class="px-abar"><i style="--w:{width:.1f}%"></i></div>'

        rows.append(
            f'<div class="px-arow" style="--c:{color}">'
            f'<span class="px-class">{_e(label)}</span>'
            f'<div><span class="px-alabel">Precision</span>{bar(m["precision"])}'
            f'<b>{_ratio(m["precision"])}</b></div>'
            f'<div><span class="px-alabel">Recall</span>{bar(m["recall"])}'
            f'<b>{_ratio(m["recall"])}</b></div>'
            f'<span class="px-counts">{m["tp"]} right, {m["fp"]} false alarms, {m["fn"]} missed</span>'
            '</div>')
    return f'<div class="px-acc">{"".join(rows)}</div>'


def errors_html(errors: list) -> str:
    if not errors:
        return '<p class="px-sub">No mistakes on this labelled set.</p>'
    items = []
    for (source, _table, column), truth, pred in errors:
        name = lambda c: _e(CLASS_META.get(c, (c,))[0])
        if pred == "NONE":
            what = f"missed: should be {name(truth)}, but it was not flagged."
        elif truth == "NONE":
            what = f"false alarm: flagged as {name(pred)}, but it is not personal data."
        else:
            what = f"wrong class: should be {name(truth)}, flagged as {name(pred)}."
        items.append(f'<li><code>{_e(column)}</code> <span>{_e(source)}</span> {what}</li>')
    return f'<ul class="px-plain px-errors">{"".join(items)}</ul>'


# --------------------------------------------------------------------------- split panel
def split_html(disclaimer: str) -> str:
    return (
        '<section class="px-split">'
        '<div class="px-found"><h3>What Privexis found</h3><ul>'
        '<li>Which columns look like the five data classes</li>'
        '<li>The score and the reasons behind each decision</li>'
        '<li>Which items on the evidence checklist are present or missing</li>'
        '<li>Declared metadata that points at nothing</li></ul></div>'
        '<div class="px-decide"><h3>What a person must decide</h3><ul>'
        '<li>Whether a flagged column really is personal data</li>'
        '<li>The lawful basis for processing it</li>'
        '<li>Whether a declared purpose or retention period is adequate</li>'
        '<li>What to fix, if anything</li></ul></div>'
        '</section>'
        f'<p class="px-fine">{_e(disclaimer)}</p>'
    )


# --------------------------------------------------------------------------- try to fool it
def _cls_label(cls: str) -> str:
    return "Not personal data" if cls == "NONE" else CLASS_META.get(cls, (cls,))[0]


def _verdict(who: str, cls: str, truth, extra: str = "") -> str:
    color = CLASS_META.get(cls, ("", "#E3E8DD"))[1]
    mark = ""
    if truth is not None:
        mark = ('<span class="px-mark right">Right</span>' if cls == truth
                else '<span class="px-mark wrong">Wrong</span>')
    return (f'<div class="px-verdict" style="--c:{color}"><span class="px-who">{_e(who)}</span>'
            f'<b>{_e(_cls_label(cls))}</b>{mark}'
            f'{f"<small>{_e(extra)}</small>" if extra else ""}</div>')


def probe_html(column, values, finding, naive: str, truth, threshold: float,
               story: str = "") -> str:
    """One 'try to fool it' result: the column, the two verdicts, and the reasons."""
    conf = max(0.0, min(float(finding.confidence), 1.0))
    thr = max(0.0, min(float(threshold), 1.0))
    shown = "".join(f"<code>{_e(mask_value(v))}</code>" for v in values[:3])
    story_html = f'<p class="px-sub">{_e(story)}</p>' if story else ""
    expected = (f'<p class="px-fine">A careful human would say: <b>{_e(_cls_label(truth))}</b>.</p>'
                if truth is not None else "")
    return (
        '<section class="px-probe">'
        f'<h3 class="px-colhead">{_e(column)}</h3>{story_html}'
        f'<div class="px-examples" aria-label="Masked example values">{shown}</div>'
        '<div class="px-versus">'
        f'{_verdict("A tool that only reads column names says", naive, truth)}'
        f'{_verdict("Privexis says", finding.cls, truth, f"confidence {conf:.2f}")}'
        '</div>'
        f'<div class="px-meter" role="img" aria-label="Confidence {conf:.2f}, threshold {thr:.2f}">'
        f'<i style="--w:{conf * 100:.1f}%"></i><b style="--t:{thr * 100:.1f}%"></b></div>'
        f'<p class="px-why">{_e(finding.evidence)}</p>{expected}'
        '</section>')


# --------------------------------------------------------------------------- gaps tab
def gap_tally_html(rows) -> str:
    counts = {}
    for r in rows:
        for g in r.gaps:
            counts[g] = counts.get(g, 0) + 1
    if not counts:
        return '<p class="px-sub">No evidence gaps.</p>'
    chips = "".join(f'<span class="px-chip gap">{_e(GAP_LABELS.get(g, g))}: {n}</span>'
                    for g, n in sorted(counts.items(), key=lambda kv: -kv[1]))
    return f'<div class="px-chips">{chips}</div>'


def matrix_html(rows, checklist: dict) -> str:
    """Checklist matrix: one row per candidate field, one column per checklist item."""
    items = list(checklist["items"])
    head = "".join(f"<th>{_e(checklist['items'][i].get('label', i))}</th>" for i in items)
    body = []
    for r in rows:
        state = {c["item"]: c for c in (getattr(r, "checklist", None) or [])}
        cells = []
        for i in items:
            c = state.get(i)
            if c is None:
                cells.append('<td class="na">n/a</td>')
            elif c["present"]:
                cells.append('<td class="yes">Yes</td>')
            elif c["required"]:
                cells.append('<td class="miss">NO</td>')
            else:
                cells.append('<td class="adv">no</td>')
        cls = _cls_label(r.cls)
        body.append(f'<tr><th scope="row"><code>{_e(r.column)}</code>'
                    f'<span>{_where(r.source, r.table)}</span></th><td>{_e(cls)}</td>'
                    f'{"".join(cells)}</tr>')
    return ('<div class="px-tablewrap"><table class="px-table"><thead><tr><th>Field</th>'
            f'<th>Class</th>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'
            '<p class="px-fine"><b>NO</b> = a required item is missing (an evidence gap). '
            '<b>no</b> = an advisory item is missing (shown, not counted as a gap).</p>')


# --------------------------------------------------------------------------- rules tab
def rules_html(rules, scoring: dict) -> str:
    def chips(words):
        return ("".join(f"<code>{_e(w)}</code>" for w in words)
                or '<span class="px-none">none</span>')

    cards = []
    for rule in rules:
        label, color = CLASS_META.get(rule.cls, (rule.cls, "#DDDDDD"))
        validator = getattr(rule.validator, "__name__", None)
        pats = chips([p.pattern for p in rule.patterns])
        cards.append(
            f'<article class="px-card px-rule" style="--c:{color}">'
            f'<div class="px-cardtop"><span class="px-class">{_e(label)}</span></div>'
            f'<dl class="px-meta"><dt>Name hints</dt><dd class="px-examples">{chips(rule.name_hints)}</dd>'
            f'<dt>Rules it out</dt><dd class="px-examples">{chips(rule.negative_hints)}</dd>'
            f'<dt>Value check</dt><dd>{_e(rule.check)}</dd>'
            f'<dt>Patterns</dt><dd class="px-examples">{pats}</dd>'
            f'<dt>Validator</dt><dd>{_e(validator) if validator else "none"}</dd></dl>'
            '</article>')
    formula = (f'confidence = {scoring["name_weight"]} x (column name matches a hint) '
               f'+ {scoring["value_weight"]} x (share of sampled values that pass). '
               f'A column is flagged at {scoring["threshold"]} or above.')
    return (f'<p class="px-formula">{_e(formula)}</p><div class="px-grid">{"".join(cards)}</div>')


def checklist_html(checklist: dict) -> str:
    required, advisory = set(checklist["required"]), set(checklist["advisory"])
    rows = []
    for name, spec in checklist["items"].items():
        source = ("Declared by a data steward (config/metadata.yaml)"
                  if spec["kind"] == "metadata" else "Collected by the scanner while it scans")
        level = "Required" if name in required else "Advisory" if name in advisory else "Not used"
        rows.append(f'<tr><th scope="row">{_e(spec.get("label", name))}</th>'
                    f'<td>{_e(source)}</td><td>{level}</td></tr>')
    over = "".join(
        f'<li><b>{_e(_cls_label(cls))}</b>: required = {_e(", ".join(o.get("required", [])))}</li>'
        for cls, o in checklist["overrides"].items())
    over_html = (f'<p class="px-fine">Per-class changes:</p><ul class="px-fine">{over}</ul>'
                 if over else "")
    return ('<div class="px-tablewrap"><table class="px-table"><thead><tr><th>Checklist item</th>'
            '<th>Where the evidence comes from</th><th>Default</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>{over_html}')


# --------------------------------------------------------------------------- about tab
REQUIREMENTS = [
    ("Support CSV and one SQL database", "CSV files and SQLite, opened read-only"),
    ("Identify 5 predefined data classes", "Name, email, phone, government ID, date of birth"),
    ("Detect candidates with configurable rules", "config/rules.yaml (see the Rules tab)"),
    ("Link fields to purpose and retention", "config/metadata.yaml, or an uploaded metadata file"),
    ("Configurable evidence checklist", "config/checklist.yaml (see the Rules tab)"),
    ("Flag missing purpose or retention", "Evidence gaps (see the Gaps tab)"),
    ("Small manually labelled test set", "data/labels.csv and data/holdout/labels.csv"),
    ("Per-class precision and recall", "Accuracy tab, on two separate labelled sets"),
    ("Evidence kept apart from legal interpretation", "Every report says so; status is only 'Candidate'"),
    ("No lawful-basis decision, no data-flow inference", "Nothing in the code attempts either"),
]


def about_html() -> str:
    rows = "".join(f'<tr><th scope="row">{_e(a)}</th><td>{_e(b)}</td></tr>' for a, b in REQUIREMENTS)
    return ('<div class="px-tablewrap"><table class="px-table"><thead><tr><th>PS-019 asks for</th>'
            f'<th>Where it is in Privexis</th></tr></thead><tbody>{rows}</tbody></table></div>')


# --------------------------------------------------------------------------- CSS
# "@@" is replaced with ".stApp " so these rules beat Streamlit's own element styles.
_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400..800&family=Schibsted+Grotesk:wght@400;500;700&family=JetBrains+Mono:wght@500&display=swap');

:root{
  --paper:#F2F4EE; --panel:#FFFFFF; --ink:#15181A; --mute:#586166; --soft:#E3E8DD;
  --hl:#FFE24A;
  --display:'Bricolage Grotesque','Arial Black',system-ui,sans-serif;
  --body:'Schibsted Grotesk',system-ui,-apple-system,'Segoe UI',sans-serif;
  --mono:'JetBrains Mono',ui-monospace,Menlo,Consolas,monospace;
}

.stApp{background:var(--paper);color:var(--ink);font-family:var(--body);}
.stApp [data-testid="stHeader"]{background:transparent;}
#MainMenu,footer{visibility:hidden;}
.stApp .block-container,.stApp [data-testid="stMainBlockContainer"]{
  max-width:1160px;padding:1.4rem clamp(16px,4vw,48px) 4rem;}

/* ---- hero ---- */
@@.px-hero{display:grid;gap:clamp(24px,4vw,56px);grid-template-columns:1fr;align-items:center;margin:0 0 20px;}
@media (min-width:920px){@@.px-hero{grid-template-columns:1.1fr .9fr;}}
@@p.px-brand{margin:0 0 clamp(20px,4vw,44px);font:800 1.2rem/1 var(--display);letter-spacing:-.01em;}
@@p.px-brand span{background:var(--ink);color:var(--hl);padding:.28em .55em .32em;border-radius:6px;}
@@h1.px-title{font:800 clamp(2.5rem,7vw,5rem)/.96 var(--display);letter-spacing:-.03em;
  margin:0 0 18px;padding:0;color:var(--ink);text-wrap:balance;}
@@p.px-lede{font:400 clamp(1.05rem,2vw,1.25rem)/1.5 var(--body);max-width:46ch;margin:0;color:var(--ink);}

/* the scan: values stay blacked out, the scanner labels each column once on load */
@@.px-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:0;background:var(--panel);
  border:2px solid var(--ink);border-radius:12px;overflow:hidden;}
@media (max-width:520px){@@.px-strip{grid-template-columns:repeat(2,1fr);}}
@@.px-col{display:flex;flex-direction:column;gap:9px;padding:18px 14px 20px;min-width:0;
  border-right:2px solid var(--ink);animation:px-flash 1s calc(var(--i)*.75s + .4s) both;}
@@.px-col:last-of-type{border-right:0;}
@media (max-width:520px){
  @@.px-col:nth-child(2){border-right:0;}
  @@.px-col:nth-child(-n+2){border-bottom:2px solid var(--ink);}}
@@.px-colname{font:500 .78rem/1.2 var(--mono);overflow-wrap:anywhere;margin-bottom:2px;}
@@p.px-cap{font:400 .92rem/1.4 var(--body);color:var(--mute);margin:10px 2px 0;}
@@.px-col i{display:block;height:16px;width:var(--w);background:var(--ink);border-radius:2px;}
@@.px-result{margin-top:6px;font:700 .8rem/1.2 var(--body);padding:5px 8px;border-radius:6px;align-self:flex-start;
  animation:px-pop .4s calc(var(--i)*.75s + 1s) both;}
@@.px-result.hit{background:var(--c,var(--hl));border:2px solid var(--ink);}
@@.px-result.skip{border:2px dashed var(--mute);color:var(--mute);}
@keyframes px-flash{0%{background:transparent}30%{background:var(--hl)}100%{background:transparent}}
@keyframes px-pop{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){@@.px-col,@@.px-result{animation:none;}}

/* ---- notice ---- */
@@.px-notice{background:var(--hl);border:2px solid var(--ink);border-radius:10px;padding:12px 16px;
  font:500 .95rem/1.45 var(--body);margin:8px 0 22px;}

/* ---- headings ---- */
@@h2.px-h2{font:800 clamp(1.6rem,3.4vw,2.3rem)/1.05 var(--display);letter-spacing:-.02em;margin:44px 0 6px;padding:0;color:var(--ink);}
@@p.px-sub{font:400 1.05rem/1.5 var(--body);color:var(--mute);margin:0 0 14px;max-width:62ch;}

/* ---- summary ---- */
@@.px-summary{margin:26px 0 8px;}
@@p.px-big{font:800 clamp(1.7rem,4.2vw,3rem)/1.02 var(--display);letter-spacing:-.025em;margin:0 0 8px;max-width:22ch;}
@@.px-bar{display:flex;height:22px;border:2px solid var(--ink);border-radius:999px;overflow:hidden;background:var(--panel);margin:14px 0 10px;}
@@.px-bar span{width:var(--w);display:block;}
@@.px-bar .ok,@@.px-legend i.ok{background:var(--ink);}
@@.px-bar .gap,@@.px-legend i.gap{background:repeating-linear-gradient(135deg,var(--hl) 0 6px,#E8C800 6px 9px);}
@@.px-bar .other,@@.px-legend i.other{background:var(--soft);}
@@ul.px-legend{display:flex;flex-wrap:wrap;gap:6px 22px;list-style:none;margin:0;padding:0;font:500 .92rem/1.3 var(--body);}
@@ul.px-legend li{display:flex;align-items:center;gap:8px;margin:0;}
@@.px-legend i{width:14px;height:14px;border:2px solid var(--ink);border-radius:4px;display:inline-block;}

/* ---- evidence tags ---- */
@@.px-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,310px),1fr));gap:18px;margin:14px 0 8px;}
@@.px-card{position:relative;background:var(--panel);border:2px solid var(--ink);border-left:12px solid var(--c,var(--soft));
  border-radius:6px;padding:16px 16px 14px;display:flex;flex-direction:column;gap:10px;min-width:0;}
@@.px-card::after{content:"";position:absolute;right:12px;top:-2px;width:12px;height:12px;border:2px solid var(--ink);
  border-top:0;border-radius:0 0 10px 10px;background:var(--paper);}
@@.px-cardtop{display:flex;justify-content:space-between;align-items:center;gap:10px;padding-right:26px;}
@@.px-class{background:var(--c,var(--soft));border:2px solid var(--ink);border-radius:999px;padding:3px 11px;font:700 .82rem/1.2 var(--body);}
@@.px-score{font:500 .9rem/1 var(--mono);}
@@h3.px-colhead{font:800 1.45rem/1.1 var(--display);letter-spacing:-.015em;margin:2px 0 0;padding:0;overflow-wrap:anywhere;}
@@p.px-where{font:400 .88rem/1.3 var(--body);color:var(--mute);margin:-6px 0 0;overflow-wrap:anywhere;}
@@.px-meter{position:relative;height:10px;background:var(--soft);border-radius:6px;margin:4px 0 2px;}
@@.px-meter i{position:absolute;left:0;top:0;bottom:0;width:var(--w);background:var(--ink);border-radius:6px;}
@@.px-meter b{position:absolute;top:-5px;bottom:-5px;left:var(--t);width:3px;background:var(--hl);outline:2px solid var(--ink);border-radius:2px;}
@@.px-examples{display:flex;flex-wrap:wrap;gap:6px;}
@@.px-examples code,@@ul.px-plain code,@@ul.px-errors code{font:500 .82rem/1.2 var(--mono);background:var(--soft);padding:3px 7px;border-radius:5px;color:var(--ink);}
@@.px-chips{display:flex;flex-wrap:wrap;gap:6px;}
@@.px-chip{font:700 .8rem/1.2 var(--body);padding:4px 10px;border-radius:999px;border:2px solid var(--ink);}
@@.px-chip.gap{background:var(--hl);}
@@.px-chip.ok{background:var(--ink);color:#fff;}
@@dl.px-meta{display:grid;grid-template-columns:auto 1fr;gap:4px 12px;margin:0;font:400 .92rem/1.35 var(--body);}
@@dl.px-meta dt{color:var(--mute);margin:0;}
@@dl.px-meta dd{margin:0;overflow-wrap:anywhere;}
@@.px-none{color:var(--mute);font-style:italic;}
@@ul.px-marks{list-style:none;margin:0;padding:0;display:grid;gap:3px;font:400 .85rem/1.3 var(--body);}
@@ul.px-marks li{margin:0;padding-left:1.3rem;position:relative;}
@@ul.px-marks li::before{position:absolute;left:0;font-weight:700;}
@@ul.px-marks li.yes::before{content:"\\2713";}
@@ul.px-marks li.no{color:var(--mute);}
@@ul.px-marks li.no::before{content:"\\2013";}
@@ul.px-review li{padding:10px 12px;background:var(--panel);border:2px dashed var(--ink);border-radius:8px;}
@@p.px-why{font:400 .8rem/1.4 var(--body);color:var(--mute);margin:0;padding-top:8px;border-top:1px dashed var(--mute);}

/* ---- plain lists ---- */
@@ul.px-plain{list-style:none;margin:0;padding:0;display:grid;gap:8px;}
@@ul.px-plain li{display:flex;flex-wrap:wrap;gap:4px 12px;align-items:baseline;font:400 .92rem/1.4 var(--body);margin:0;}
@@ul.px-plain li span{color:var(--mute);}
@@ul.px-errors li{padding:10px 12px;background:var(--panel);border:2px solid var(--ink);border-radius:8px;display:block;}

/* ---- accuracy ---- */
@@.px-acc{display:grid;gap:12px;margin:10px 0;}
@@.px-arow{display:grid;grid-template-columns:150px 1fr 1fr;gap:10px 22px;align-items:center;background:var(--panel);
  border:2px solid var(--ink);border-radius:10px;padding:12px 14px;}
@media (max-width:760px){@@.px-arow{grid-template-columns:1fr 1fr;}@@.px-arow .px-class{grid-column:1 / -1;}}
@media (max-width:560px){@@.px-arow{grid-template-columns:1fr;}}
@@.px-arow .px-class{justify-self:start;}
@@.px-arow>div{display:grid;grid-template-columns:auto 1fr auto;gap:10px;align-items:center;}
@@.px-alabel{font:500 .85rem/1 var(--body);color:var(--mute);min-width:4.6rem;}
@@.px-abar{height:12px;background:var(--soft);border-radius:6px;overflow:hidden;min-width:40px;}
@@.px-abar i{display:block;height:100%;width:var(--w);background:var(--ink);}
@@.px-arow b{font:500 .9rem/1 var(--mono);}
@@.px-counts{grid-column:1 / -1;font:400 .85rem/1.3 var(--body);color:var(--mute);}

/* ---- evidence vs decision ---- */
@@.px-split{display:grid;grid-template-columns:1fr;gap:16px;margin:12px 0;}
@media (min-width:760px){@@.px-split{grid-template-columns:1fr 1fr;}}
@@.px-split>div{border:2px solid var(--ink);border-radius:12px;padding:18px 20px;background:var(--panel);}
@@.px-split .px-decide{border-style:dashed;background:transparent;}
@@.px-split h3{font:800 1.3rem/1.1 var(--display);margin:0 0 10px;padding:0;}
@@.px-split ul{margin:0;padding-left:1.1rem;display:grid;gap:6px;font:400 .98rem/1.4 var(--body);}
@@p.px-fine{font:400 .85rem/1.5 var(--body);color:var(--mute);max-width:80ch;margin:10px 0 0;}

/* ---- tabs ---- */
@@ [data-baseweb="tab-list"]{gap:6px;border-bottom:2px solid var(--ink);flex-wrap:wrap;}
@@ button[role="tab"]{font:700 1rem/1.2 var(--display);color:var(--ink);padding:10px 16px;border-radius:10px 10px 0 0;}
@@ button[role="tab"][aria-selected="true"]{background:var(--hl);}
@@ [data-baseweb="tab-highlight"]{background:var(--ink);height:4px;}
@@ [data-baseweb="tab-border"]{display:none;}

/* ---- try to fool it ---- */
@@.px-probe{background:var(--panel);border:2px solid var(--ink);border-radius:12px;padding:18px 20px;display:flex;flex-direction:column;gap:12px;margin:12px 0;}
@@.px-versus{display:grid;grid-template-columns:1fr;gap:12px;}
@media (min-width:640px){@@.px-versus{grid-template-columns:1fr 1fr;}}
@@.px-verdict{border:2px solid var(--ink);border-radius:10px;padding:12px 14px;display:flex;flex-direction:column;gap:4px;background:var(--c,var(--soft));}
@@.px-who{font:500 .85rem/1.2 var(--body);}
@@.px-verdict b{font:800 1.4rem/1.1 var(--display);letter-spacing:-.01em;}
@@.px-verdict small{font:500 .82rem/1.2 var(--mono);}
@@.px-mark{align-self:flex-start;font:700 .78rem/1.2 var(--body);padding:3px 9px;border:2px solid var(--ink);border-radius:999px;background:var(--panel);}
@@.px-mark.wrong{background:var(--ink);color:#fff;}

/* ---- tables, rules ---- */
@@.px-tablewrap{overflow-x:auto;border:2px solid var(--ink);border-radius:10px;background:var(--panel);margin:10px 0;}
@@table.px-table{border-collapse:collapse;width:100%;font:400 .92rem/1.35 var(--body);min-width:560px;}
@@table.px-table th,@@table.px-table td{padding:9px 12px;text-align:left;border-bottom:1px solid var(--soft);vertical-align:top;}
@@table.px-table thead th{background:var(--ink);color:#fff;font-weight:700;white-space:nowrap;}
@@table.px-table tbody th{font-weight:500;}
@@table.px-table tbody th span{display:block;color:var(--mute);font-size:.8rem;}
@@table.px-table td.yes{font-weight:700;}
@@table.px-table td.miss{background:var(--hl);font-weight:800;}
@@table.px-table td.adv,@@table.px-table td.na{color:var(--mute);}
@@table.px-table code{font:500 .85rem/1.2 var(--mono);background:var(--soft);padding:2px 6px;border-radius:5px;}
@@p.px-formula{font:500 .95rem/1.5 var(--mono);background:var(--panel);border:2px dashed var(--ink);border-radius:10px;padding:12px 14px;margin:10px 0 14px;}
@@.px-rule dl.px-meta{grid-template-columns:auto 1fr;}
@@.px-rule .px-examples code{font:500 .78rem/1.2 var(--mono);background:var(--soft);padding:2px 6px;border-radius:5px;overflow-wrap:anywhere;}

/* ---- Streamlit widgets, restyled lightly (additive, so a missed selector is harmless) ---- */
@@ [data-testid="stRadio"] label{background:var(--panel);border:2px solid var(--ink);border-radius:999px;padding:6px 16px;cursor:pointer;}
@@ [data-testid="stRadio"] label:has(input:checked){background:var(--hl);}
@@ [data-testid="stFileUploaderDropzone"]{background:var(--panel);border:2px dashed var(--ink);border-radius:12px;}
@@ [data-testid="stExpander"]{background:var(--panel);border:2px solid var(--ink);border-radius:12px;}
@@ [data-testid="stDownloadButton"] button{background:var(--hl);color:var(--ink);border:2px solid var(--ink);border-radius:999px;font-weight:700;}
@@ [data-testid="stDownloadButton"] button:hover{background:var(--ink);color:var(--hl);border-color:var(--ink);}
@@ button:focus-visible,@@ input:focus-visible{outline:3px solid var(--ink);outline-offset:2px;}
"""

CSS = _CSS.replace("@@", ".stApp ")
