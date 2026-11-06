"""Field Scan: diagnose many photos from one field at once and get a field-level decision."""
import glob
import html
import io
import os
import sys

import cv2
import pandas as pd
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from leafguard_plus import fieldscan, severity, treatment, ui  # noqa: E402
from leafguard_plus.diary import Diary  # noqa: E402
from leafguard_plus.i18n import disease_name  # noqa: E402
from leafguard_plus.shared import decode, get_guard, setup_page  # noqa: E402

setup_page("Field Scan", ":material/grid_view:")
guard = get_guard()

ui.header("Field Scan", "Walk the field, photograph 10–30 leaves from different plants, and get one decision "
          "for the whole field.", "scan", eyebrow="Whole-field health")

src = st.radio("Photos", ["Upload many photos", "Use the sample photos"], horizontal=True)
images = []
if src == "Upload many photos":
    files = st.file_uploader("Select several leaf photos (on a phone you can pick many at once)",
                             type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True)
    for f in files or []:
        img = decode(f.getvalue())
        if img is not None:
            images.append((f.name, img))
else:
    for pth in sorted(glob.glob(os.path.join(ROOT, "sample_images", "*"))):
        img = cv2.imread(pth)
        if img is not None:
            images.append((os.path.basename(pth), cv2.cvtColor(img, cv2.COLOR_BGR2RGB)))

if not images:
    ui.features([("camera", "Spread out", "Photograph leaves from different rows and corners, not just one plant."),
                 ("leaf", "One leaf per photo", "Fill the screen with a single leaf, in daylight."),
                 ("gauge", "Get a decision", "Treat the whole field, spot-treat, or keep monitoring.")])
    st.stop()

key = tuple((n, im.shape) for n, im in images)
if st.session_state.get("fs_key") != key:
    results = []
    bar = st.progress(0.0, text="Scanning the field ...")
    for k, (name, img) in enumerate(images):
        r = guard.analyze(img, do_explain=True)
        sev = severity.estimate(img, r, guard.th) if r["verdict"] == "DISEASED" else None
        results.append({"name": name, "verdict": r["verdict"], "cls": r.get("cls"),
                        "label": r.get("label") or r["headline"], "confidence": r.get("confidence"),
                        "severity": sev["percent"] if sev else None, "level": sev["level"] if sev else None,
                        "thumb": r["images"].get("heatmap", img)})
        bar.progress((k + 1) / len(images), text=f"Scanned {k + 1} of {len(images)} photos")
    bar.empty()
    st.session_state["fs_key"], st.session_state["fs_results"] = key, results
results = st.session_state["fs_results"]
s = fieldscan.summarise(results)

# ---------------------------------------------------------------- the decision
reliable = s["decision"] != "Retake photos"
tiles = [ui.stat(s["n"], "Photos scanned", "neutral", "camera"),
         ui.stat(s["health"] if reliable and s["health"] is not None else "–",
                 "Field health score (0–100)" if reliable else "Health score: needs more usable photos",
                 ("good" if (s["health"] or 0) >= 80 else "warn" if (s["health"] or 0) >= 50 else "bad")
                 if reliable else "neutral", "leaf"),
         ui.stat(f"{round(s['diseased_share'] * 100)}%" if reliable else "–",
                 "Of checked plants diseased" if reliable else "Diseased share: needs more usable photos",
                 ("bad" if s["diseased_share"] >= .2 else "warn" if s["diseased_share"] > .05 else "good")
                 if reliable else "neutral", "alert"),
         ui.stat(s["unusable"] + s["counts"]["UNCERTAIN"], "Photos LeafGuard refused to guess on", "info", "shield")]
for col, t in zip(st.columns(4, gap="small"), tiles):
    col.markdown(t, unsafe_allow_html=True)
st.write("")
verdict_style = {"good": "HEALTHY", "warn": "UNCERTAIN", "bad": "DISEASED", "neutral": "UNCERTAIN"}[s["tone"]]
lines = [s["why"]]
if s["diseases"]:
    lines.append("Found: " + ", ".join(f"{disease_name(c, 'en')} ({n})" for c, n in s["diseases"].most_common()))
if s["avg_severity"] is not None:
    lines.append(f"Average affected area on diseased leaves: {s['avg_severity']:.0f}%")
ui.verdict_card(verdict_style, s["decision"], lines, label="Field decision")

if s["diseases"]:
    top_cls = s["diseases"].most_common(1)[0][0]
    if treatment.key_for(top_cls):
        top = next(r for r in results if r["cls"] == top_cls)
        st.session_state["lg_last"] = {"verdict": "DISEASED", "cls": top_cls, "label": top["label"],
                                       "confidence": top["confidence"], "severity": s["avg_severity"],
                                       "level": top["level"], "thumb": top["thumb"]}
        ui.link("pages/4_Treatment_Plan.py", f"Open the treatment plan for {disease_name(top_cls, 'en')}",
                     icon=":material/healing:")

# ---------------------------------------------------------------- breakdown
a, b = st.columns([1, 1.3], gap="large")
with a:
    st.markdown("### What the photos show")
    breakdown = pd.DataFrame({"Photos": [s["counts"][v] for v in ui.STATUS]},
                             index=[ui.STATUS[v][0] for v in ui.STATUS])
    st.bar_chart(breakdown, horizontal=True, color="#15803D", height=230)
with b:
    st.markdown("### Save & export")
    plot = st.text_input("Plot name", value=st.session_state.get("lg_plot", "My field"), key="fs_plot")
    c1, c2 = st.columns(2)
    if c1.button("Save to Field Diary", icon=":material/bookmark_add:", width="stretch"):
        st.session_state["lg_plot"] = plot
        top_cls = s["diseases"].most_common(1)[0][0] if s["diseases"] else "healthy"
        Diary(ROOT).add(plot, "DISEASED" if s["diseases"] else "HEALTHY", top_cls,
                        s["avg_severity"] if s["avg_severity"] is not None else 0.0, None, None,
                        note=f"Field scan: {s['decision']} · {s['n']} photos · health {s['health']}",
                        rgb=results[0]["thumb"])
        st.success("Saved. See the trend in the Field Diary.", icon=":material/check_circle:")
    table = pd.DataFrame([{k: r[k] for k in ("name", "verdict", "label", "confidence", "severity", "level")}
                          for r in results])
    buf = io.StringIO()
    table.to_csv(buf, index=False)
    c2.download_button("Download CSV", buf.getvalue().encode(), "field_scan.csv", icon=":material/download:",
                       width="stretch")

st.markdown("### Every photo")
cols = st.columns(4, gap="small")
for k, r in enumerate(results):
    with cols[k % 4]:
        st.image(r["thumb"], width="stretch")
        extra = f" · {round(r['severity'])}%" if r.get("severity") is not None else ""
        st.markdown(f"{ui.status_chip(r['verdict'])}<div style='font-size:.85rem;margin-top:4px'>"
                    f"{html.escape(r['name'])}{extra}</div>", unsafe_allow_html=True)
