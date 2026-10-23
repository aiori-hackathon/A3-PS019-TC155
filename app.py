"""Privexis web app.  Run it with:   streamlit run app.py

The page layout and styling live in src/privexis/ui.py. The scanning logic is the same
pipeline the command line uses (src/privexis/pipeline.py).
"""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))      # lets Streamlit Cloud import privexis without installing it

import streamlit as st

from privexis import demos, ui
from privexis.engine import load_config
from privexis.evaluator import evaluate, load_labels
from privexis.linker import load_checklist, load_metadata
from privexis.pipeline import (find_sources, metadata_template_csv, parse_metadata,
                               run_pipeline, scan_labelled)
from privexis.report import DISCLAIMER, write_gap_report, write_inventory

CONFIG, DEMO_DATA = ROOT / "config", ROOT / "data"
HOLDOUT = DEMO_DATA / "holdout"
MAX_MB = 25

st.set_page_config(page_title="Privexis: find undocumented personal data",
                   page_icon="🟨", layout="wide")
st.markdown(f"<style>{ui.CSS}</style>", unsafe_allow_html=True)


def html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


checklist = load_checklist(CONFIG / "checklist.yaml")


@st.cache_data(show_spinner=False)
def run_demo(threshold: float, k: int):
    rules, scoring = load_config(CONFIG / "rules.yaml")
    scoring = {**scoring, "threshold": threshold}
    metadata = load_metadata(CONFIG / "metadata.yaml")
    result = run_pipeline(find_sources(DEMO_DATA), rules, scoring, metadata, checklist, k)
    metrics = evaluate(result.findings, load_labels(DEMO_DATA / "labels.csv"))
    return result, metrics


@st.cache_data(show_spinner=False)
def run_holdout(threshold: float, k: int):
    rules, scoring = load_config(CONFIG / "rules.yaml")
    scoring = {**scoring, "threshold": threshold}
    return scan_labelled(HOLDOUT, HOLDOUT / "labels.csv", rules, scoring, k)[1]


# ------------------------------------------------------------------ top of page
html(ui.hero_html())
html(ui.notice_html())

base_rules, base_scoring = load_config(CONFIG / "rules.yaml")

mode = st.radio("Where should the data come from?", ["Demo data", "Upload my files"],
                horizontal=True)

with st.expander("Tuning: threshold and sample size"):
    threshold = st.slider(
        "Detection threshold", 0.1, 0.9, float(base_scoring["threshold"]), 0.05,
        help="How confident Privexis must be before it flags a column. "
             "Higher means fewer false alarms but more misses.")
    k = st.slider("Values sampled per column", 10, 200, 50, 10)
scoring = {**base_scoring, "threshold": threshold}

# ------------------------------------------------------------------ get a result (or explain why not)
result, waiting = None, ""
if mode == "Demo data":
    result = run_demo(threshold, k)[0]
else:
    html(ui.heading_html("Add your files",
                         f"CSV or SQLite, up to {MAX_MB} MB each. A metadata file is optional."))
    files = st.file_uploader("Data files", accept_multiple_files=True,
                             type=["csv", "sqlite", "sqlite3", "db"])
    meta_file = st.file_uploader("Metadata file: purpose and retention per column (YAML or CSV)",
                                 type=["yaml", "yml", "csv"])
    st.download_button("Download a metadata template (CSV)", metadata_template_csv(),
                       file_name="metadata_template.csv", mime="text/csv")
    if not files:
        waiting = ("Add at least one CSV or SQLite file to scan it. "
                   "Or switch to Demo data to see a finished example.")
    elif any(f.size > MAX_MB * 1024 * 1024 for f in files):
        st.error(f"Each file must be under {MAX_MB} MB. Remove the larger file and try again.")
        waiting = "The scan is waiting for files that fit the size limit."
    else:
        try:
            metadata = parse_metadata(meta_file.getvalue(), meta_file.name) if meta_file else {}
            with tempfile.TemporaryDirectory() as tmp:     # deleted as soon as this block ends
                paths = []
                for f in files:
                    p = Path(tmp) / Path(f.name).name      # .name drops any folder part of the file name
                    p.write_bytes(f.getvalue())
                    paths.append(p)
                result = run_pipeline(paths, base_rules, scoring, metadata, checklist, k)
        except UnicodeDecodeError:
            st.error("One of the files is not UTF-8 text. In Excel, use Save As > CSV UTF-8, "
                     "then upload it again.")
            waiting = "The scan is waiting for a readable file."
        except Exception as e:                              # corrupt database, bad metadata file, and so on
            st.error(f"Could not read these files: {e}")
            waiting = "The scan is waiting for readable files."

t_ev, t_gap, t_acc, t_fool, t_rules, t_about = st.tabs(
    ["Evidence", "Gaps", "Accuracy", "Try to fool it", "Rules", "About"])

# ------------------------------------------------------------------ evidence
with t_ev:
    if result is None:
        st.info(waiting)
    else:
        rows, findings = result.rows, result.findings
        n_gaps = sum(1 for r in rows if r.gaps)
        html(ui.summary_html(len(findings), len(rows), n_gaps))

        if rows:
            html(ui.heading_html("Evidence tags",
                                 "One tag per column that looks like personal data. The bar shows the "
                                 "confidence score, and the yellow mark is the threshold. "
                                 "Each tag is checked against the evidence checklist."))
            c1, c2 = st.columns([2, 3])
            with c1:
                view = st.radio("Show", ["All fields", "Only fields with gaps"], horizontal=True)
            with c2:
                classes = sorted({r.cls for r in rows})
                picked = st.multiselect("Data classes", classes, default=classes)

            shown = [r for r in rows if r.cls in picked and (view == "All fields" or r.gaps)]
            order = {c: i for i, c in enumerate(ui.CLASS_META)}
            shown.sort(key=lambda r: (order.get(r.cls, 99), r.source, r.column))
            cards = [ui.tag_html(r, result.samples.get((r.source, r.table, r.column), []), threshold)
                     for r in shown]
            html(ui.tags_grid_html(cards) if cards else
                 '<p class="px-sub">No fields match this filter.</p>')

        if result.review:
            html(ui.heading_html("Needs a closer look",
                                 "Not flagged, but some evidence points to personal data. "
                                 "Listed so a person can decide."))
            html(ui.review_html(result.review))

        unflagged = [f for f in findings if f.cls == "NONE" and f not in result.review]
        if unflagged:
            with st.expander(f"{len(unflagged)} other columns were not flagged"):
                html(ui.unflagged_html(unflagged))

# ------------------------------------------------------------------ gaps
with t_gap:
    if result is None:
        st.info(waiting)
    else:
        rows = result.rows
        html(ui.heading_html("Evidence gaps",
                             "Every flagged field against the evidence checklist. A missing "
                             "required item is a gap for a person to follow up. It is not a "
                             "legal finding."))
        if rows:
            html(ui.gap_tally_html(rows))
            html(ui.matrix_html(rows, checklist))
        else:
            st.info("No columns were flagged, so there is nothing to check yet.")

        if result.orphans:
            html(ui.heading_html("Declared but not found",
                                 "These metadata entries do not match any flagged column. The "
                                 "documentation may be out of date, or the scanner may have missed "
                                 "a field."))
            html(ui.orphans_html(result.orphans))

        html(ui.heading_html("Take the results with you"))
        with tempfile.TemporaryDirectory() as out:
            write_inventory(rows, out)
            write_gap_report(rows, result.orphans, out, result.review)
            files_out = {n: (Path(out) / n).read_bytes()
                         for n in ("inventory.csv", "inventory.json", "gap_report.md")}
        for col, (name, data) in zip(st.columns(3), files_out.items()):
            col.download_button(f"Download {name}", data, file_name=name)

# ------------------------------------------------------------------ accuracy
with t_acc:
    html(ui.heading_html("How accurate is it?",
                         "Precision: of the columns it flagged, how many were right. Recall: of "
                         "the real personal-data columns, how many it found. Measured on the "
                         "built-in labelled sets, whatever is uploaded. Move the threshold under "
                         "Tuning and watch the bars change."))
    if mode == "Upload my files":
        st.caption("Your uploads have no answer key, so they are not scored. These are the built-in sets.")

    main_metrics = run_demo(threshold, k)[1]
    html(ui.heading_html(f"Main set: {main_metrics['columns']} columns",
                         "The rules were tuned against this set, including two negative hints "
                         "added after the first run. Treat it as a demonstration, not an estimate."))
    html(ui.accuracy_html(main_metrics))
    html(ui.errors_html(main_metrics["errors"]))

    hold_metrics = run_holdout(threshold, k)
    html(ui.heading_html(f"Fresh set: {hold_metrics['columns']} columns the rules never saw",
                         "A second labelled set, scored before any rule was changed, in files "
                         "the rules were not written against. It is the more honest of the two "
                         "numbers, and it is lower. Passports, spelled-out dates and plain-language "
                         "columns are the known gaps."))
    html(ui.accuracy_html(hold_metrics))
    html(ui.errors_html(hold_metrics["errors"]))
    st.caption("Both sets are small, synthetic and labelled by the team that built the tool. "
               "The unit is the column, not the individual value.")

# ------------------------------------------------------------------ try to fool it
with t_fool:
    html(ui.heading_html("Try to fool it",
                         "Real data does not come with helpful column names. Here the header "
                         "says one thing and the values say another. Compare what a tool that "
                         "only reads column names would conclude with what Privexis concludes. "
                         "All values are synthetic."))
    cases = demos.build_cases()
    pick = st.selectbox("Pick a trap", range(len(cases)), format_func=lambda i: cases[i].title)
    case = cases[pick]
    html(ui.probe_html(case.column, case.values,
                       demos.probe(case.column, case.values, base_rules, scoring),
                       demos.name_only_guess(case.column, base_rules), case.truth,
                       threshold, case.story))

    html(ui.heading_html("Build your own",
                         "Type a made-up column name and some made-up values, one per line. "
                         "Nothing is saved. Do not paste real personal data."))
    own_name = st.text_input("Column name", value="contact_info")
    own_values = st.text_area("Values (one per line)",
                              value="asha.k@example.org\nrahul.m@example.org\nmeera.s@example.org",
                              height=140)
    values = [v for v in own_values.splitlines() if v.strip()][:200]
    if values:
        html(ui.probe_html(own_name or "column", values,
                           demos.probe(own_name, values, base_rules, scoring),
                           demos.name_only_guess(own_name, base_rules), None, threshold))
    else:
        st.info("Add at least one value to see the result.")

# ------------------------------------------------------------------ rules
with t_rules:
    html(ui.heading_html("Detection rules",
                         "This is config/rules.yaml, read live. Change the file and the scanner "
                         "changes. No code edit is needed."))
    html(ui.rules_html(base_rules, base_scoring))
    html(ui.heading_html("Evidence checklist",
                         "This is config/checklist.yaml. It decides which missing items count "
                         "as evidence gaps."))
    html(ui.checklist_html(checklist))

# ------------------------------------------------------------------ about
with t_about:
    html(ui.heading_html("What this is",
                         "Privexis scans synthetic CSV and SQLite data, finds candidate personal-data "
                         "fields in five classes, links each one to its declared purpose, retention "
                         "period and owner, and flags what is missing. It produces technical evidence "
                         "for a person to review."))
    html(ui.heading_html("PS-019, requirement by requirement"))
    html(ui.about_html())
    html(ui.heading_html("Evidence, not a verdict"))
    html(ui.split_html(DISCLAIMER))
