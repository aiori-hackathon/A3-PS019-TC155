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

from privexis import ui
from privexis.engine import load_config
from privexis.evaluator import evaluate, load_labels
from privexis.linker import load_checklist, load_metadata
from privexis.pipeline import (find_sources, metadata_template_csv, parse_metadata,
                               run_pipeline)
from privexis.report import DISCLAIMER, write_gap_report, write_inventory

CONFIG, DEMO_DATA = ROOT / "config", ROOT / "data"
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

# ------------------------------------------------------------------ get a result
metrics = None
if mode == "Demo data":
    result, metrics = run_demo(threshold, k)
    scoring = {**base_scoring, "threshold": threshold}
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
        st.info("Add at least one CSV or SQLite file to scan it. "
                "Or switch to Demo data to see a finished example.")
        st.stop()
    if any(f.size > MAX_MB * 1024 * 1024 for f in files):
        st.error(f"Each file must be under {MAX_MB} MB. Remove the larger file and try again.")
        st.stop()

    scoring = {**base_scoring, "threshold": threshold}
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
        st.error("One of the files is not UTF-8 text. In Excel, use Save As > CSV UTF-8, then upload it again.")
        st.stop()
    except Exception as e:                              # corrupt database, bad metadata file, and so on
        st.error(f"Could not read these files: {e}")
        st.stop()

rows, findings = result.rows, result.findings
n_gaps = sum(1 for r in rows if r.gaps)

# ------------------------------------------------------------------ results
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

    shown = [r for r in rows
             if r.cls in picked and (view == "All fields" or r.gaps)]
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

if result.orphans:
    html(ui.heading_html("Declared but not found",
                         "These metadata entries do not match any flagged column. The "
                         "documentation may be out of date, or the scanner may have missed a field."))
    html(ui.orphans_html(result.orphans))

# ------------------------------------------------------------------ accuracy
html(ui.heading_html("How accurate is it?"))
if metrics is None:
    html('<p class="px-sub">Accuracy needs an answer key that says what each column really is. '
         'Switch to Demo data to see it measured on the labelled synthetic set.</p>')
else:
    html('<p class="px-sub">Measured on 22 hand-labelled columns, including deliberate traps. '
         'Precision: of the columns it flagged, how many were right. Recall: of the real '
         'personal-data columns, how many it found. Move the threshold under Tuning and watch '
         'the bars change.</p>')
    html(ui.accuracy_html(metrics))
    html(ui.heading_html("Where it gets things wrong"))
    html(ui.errors_html(metrics["errors"]))

# ------------------------------------------------------------------ evidence vs decision
html(ui.heading_html("Evidence, not a verdict"))
html(ui.split_html(DISCLAIMER))

# ------------------------------------------------------------------ downloads
html(ui.heading_html("Take the results with you"))
with tempfile.TemporaryDirectory() as out:
    write_inventory(rows, out)
    write_gap_report(rows, result.orphans, out, result.review)
    files_out = {n: (Path(out) / n).read_bytes()
                 for n in ("inventory.csv", "inventory.json", "gap_report.md")}
cols = st.columns(3)
for col, (name, data) in zip(cols, files_out.items()):
    col.download_button(f"Download {name}", data, file_name=name)
