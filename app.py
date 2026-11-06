"""LeafGuard demo app.   Run:  streamlit run app.py
(UI redesigned with the 'Organic Biophilic' design system; the previous version is in backup/app_v1.py)"""
import glob
import json
import os

import cv2
import numpy as np
import streamlit as st

from leafguard import LeafGuard, load_config
from leafguard_plus import ui

ROOT = os.path.dirname(os.path.abspath(__file__))
st.set_page_config(page_title="LeafGuard · Diagnose", page_icon=":material/eco:", layout="wide")
ui.apply()


def get_guard(cfg_json):
    # Shared with the other pages, so the model + CLIP are loaded only ONCE (matters on Streamlit Cloud's memory limit)
    from leafguard_plus.shared import _load
    return _load(cfg_json)


cfg = load_config(os.path.join(ROOT, "config.json"))

# ---------------------------------------------------------------- sidebar
guard = get_guard(json.dumps(cfg))  # loaded once; sliders below only change thresholds
ui.sidebar()

with st.sidebar:
    with st.expander("Safety settings", expanded=False, icon=":material/tune:"):
        th = dict(cfg["thresholds"])
        if guard.is_detector:
            th["det_conf_high"] = st.slider("Box confidence = disease detected", 0.2, 0.95, float(th["det_conf_high"]), 0.01)
            th["det_conf_low"] = st.slider("Box confidence = 'possible, not sure'", 0.05, 0.6, float(th["det_conf_low"]), 0.01)
            th["det_on_leaf"] = st.slider("Box must be on the leaf (share)", 0.0, 1.0, float(th["det_on_leaf"]), 0.05)
        else:
            th["min_confidence"] = st.slider("Min confidence to diagnose", 0.3, 0.99, float(th["min_confidence"]), 0.01)
            th["min_margin"] = st.slider("Min gap to 2nd answer", 0.0, 0.8, float(th["min_margin"]), 0.05)
            th["min_leaf_focus"] = st.slider("Min attention on leaf", 0.0, 0.9, float(th["min_leaf_focus"]), 0.05)
        th["blur_min"] = st.slider("Blur limit (lower = allow blurrier)", 5.0, 200.0, float(th["blur_min"]), 5.0)
    guard.th = th
    guard.leaf_gate.th = th
    explain_on = st.toggle("Show where it looked", value=True)
    compare_on = st.toggle("Compare with raw model", value=True)
    st.divider()
    kind = "Detector" if guard.is_detector else "Classifier"
    st.markdown(
        f"<div class='lg-muted' style='font-size:.85rem;line-height:1.7'>"
        f"{ui.chip(kind + ' · ' + cfg['framework'], 'brand', 'cpu')}<br>"
        f"{ui.chip(str(len(guard.class_names)) + ' diseases known', 'neutral', 'leaf')}<br>"
        f"{ui.chip('Leaf check: ' + guard.leaf_gate.method, 'info', 'eye')}</div>", unsafe_allow_html=True)
    with st.expander("Diseases the model knows", icon=":material/list:"):
        st.write(", ".join(n.replace("_", " ") for n in guard.class_names))
    if cfg["framework"] == "demo":
        st.warning("Running the built-in DEMO model. Put your model in config.json.")
    if guard.leaf_gate.clip_error:
        st.caption(f"CLIP unavailable, using colour check ({guard.leaf_gate.clip_error[:80]})")

ui.header("LeafGuard", "A plant-disease checker that says \"I'm not sure\" instead of guessing.",
          "shield", eyebrow="Diagnose a leaf")
tab_diag, tab_proof, tab_how = st.tabs([":material/photo_camera: Diagnose", ":material/science: Proof",
                                        ":material/account_tree: How it works"])

# ---------------------------------------------------------------- diagnose
with tab_diag:
    src = st.radio("Photo source", ["Upload / phone camera", "Webcam", "Sample photos"], horizontal=True)
    rgb = None
    if src == "Upload / phone camera":
        f = st.file_uploader("Upload a leaf photo (on a phone this opens the camera)", type=["jpg", "jpeg", "png", "webp"])
        if f:
            rgb = cv2.cvtColor(cv2.imdecode(np.frombuffer(f.read(), np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
    elif src == "Webcam":
        f = st.camera_input("Take a photo")
        if f:
            rgb = cv2.cvtColor(cv2.imdecode(np.frombuffer(f.getvalue(), np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
    else:
        samples = sorted(glob.glob(os.path.join(ROOT, "sample_images", "*")))
        if samples:
            pick = st.selectbox("Pick a sample", samples, format_func=os.path.basename)
            rgb = cv2.cvtColor(cv2.imread(pick), cv2.COLOR_BGR2RGB)
        else:
            st.info("No samples yet. Run: python scripts/make_samples.py")

    if rgb is None:
        ui.features([
            ("camera", "Refuses bad photos", "Blurry, dark or thumb-covered shots get 'retake', never a guess."),
            ("ban", "Knows what a leaf is", "Coffee mugs, hands and screens are rejected before diagnosis."),
            ("scan", "Ignores the background", "Only spots on the main leaf count, so sick leaves nearby can't fool it."),
            ("flask", "Proves its answer", "Boxes, a self-doubt test and a hide-the-spots test show why."),
        ])
        ui.card("How to take a good photo",
                "<ul style='margin:0;padding-left:18px;line-height:1.8'>"
                "<li>One leaf, filling most of the screen</li><li>Daylight, no harsh glare</li>"
                "<li>Hold steady, tap the leaf to focus</li><li>Keep fingers away from the lens</li></ul>", "camera")

    if rgb is not None:
        with st.spinner("Checking photo, finding leaf, asking the model, explaining ..."):
            r = guard.analyze(rgb, do_explain=explain_on, explain_baseline=explain_on and compare_on)

        ui.pipeline_steps(r)

        show_conf = r["verdict"] == "DISEASED" or (r["verdict"] == "HEALTHY" and not guard.is_detector)
        lines = []
        if r["verdict"] in ("HEALTHY", "DISEASED") and not (r["reasons"] and r["reasons"][0].startswith(r["label"])):
            lines.append(r["label"] + (f" · {round(r['confidence'] * 100)}% confident" if show_conf else ""))
        lines += [x for x in r["reasons"] if x not in lines]

        if compare_on:
            c1, c2 = st.columns(2, gap="medium")
            with c1:
                b = r["baseline"]
                ui.raw_card(b["label"], f"{round(b['confidence'] * 100)}% confident" if b["confidence"] is not None
                            else "No disease boxes found")
            with c2:
                ui.verdict_card(r["verdict"], r["headline"], lines)
        else:
            ui.verdict_card(r["verdict"], r["headline"], lines)

        left, right = st.columns([1, 2], gap="medium")
        with left:
            ui.checks_list(r["checks"])
            if r.get("top3"):
                st.markdown("**Strongest detection per disease**" if guard.is_detector else "**Top answers (calibrated)**")
                for t in r["top3"]:
                    st.progress(float(t["prob"]), text=f"{t['label']}: {round(t['prob'] * 100)}%")
            st.caption(f"Analysed in {r['seconds']} s")
        with right:
            imgs = [("Your photo", rgb)]
            if guard.is_detector:
                if "heatmap" in r["images"]:
                    focus = r.get("leaf_focus")
                    imgs.append(("LeafGuard: spots on the leaf (grey dashed = ignored, off the leaf)"
                                 + (f" · {round(focus * 100)}% on leaf" if focus is not None else ""),
                                 r["images"]["heatmap"]))
                if "baseline_heatmap" in r["images"]:
                    imgs.append(("Raw model boxes (what the farmer sees without LeafGuard)",
                                 r["images"]["baseline_heatmap"]))
                if "leaf_only" in r["images"]:
                    imgs.append(("The leaf LeafGuard found", r["images"]["leaf_only"]))
            else:
                if "leaf_only" in r["images"]:
                    imgs.append(("Leaf only (background removed)", r["images"]["leaf_only"]))
                if "heatmap" in r["images"]:
                    focus = r.get("leaf_focus")
                    cap = f"Where LeafGuard's model looked ({r.get('explain_method')})"
                    if focus is not None:
                        cap += f": {round(focus * 100)}% on leaf"
                    imgs.append((cap, r["images"]["heatmap"]))
                if "baseline_heatmap" in r["images"]:
                    bf = r["baseline"].get("leaf_focus")
                    imgs.append(("Where the RAW model looked" + (f": {round(bf * 100)}% on leaf" if bf is not None else ""),
                                 r["images"]["baseline_heatmap"]))
            cols = st.columns(2, gap="small")
            for k, (cap, im) in enumerate(imgs):
                cols[k % 2].image(im, caption=cap, width="stretch")
        if r["verdict"] in ("UNCERTAIN", "DISEASED"):
            st.page_link("pages/1_Deep_Check.py", label="Open Deep Check: self-doubt test, proof, severity and voice", icon=":material/biotech:")

# ---------------------------------------------------------------- proof
with tab_proof:
    st.markdown("### Does the safety layer actually help?")
    path = os.path.join(ROOT, "reports", "stress_test.json")
    if os.path.exists(path):
        rep = json.load(open(path))
        h = rep["hard_cases_unsafe"]
        clean = next((x for x in rep["rows"] if x["scenario"] == "clean"), None)
        tiles = [ui.stat(f"{h['raw']:.0%}", "Raw model: unsafe answers on hard photos", "bad", "cpu"),
                 ui.stat(f"{h['leafguard']:.0%}", "LeafGuard: unsafe answers on hard photos", "good", "shield")]
        if clean:
            tiles.append(ui.stat(f"{clean['leafguard_correct'] / max(1e-9, 1 - clean['leafguard_abstain']):.0%}",
                                 "Clean photos: correct when LeafGuard answers", "info", "check_circle"))
        for col, t in zip(st.columns(len(tiles)), tiles):
            col.markdown(t, unsafe_allow_html=True)
        import pandas as pd
        df = pd.DataFrame([{"Scenario": x["description"], "Raw model": x["raw_unsafe_rate"] * 100,
                            "LeafGuard": x["leafguard_unsafe_rate"] * 100} for x in rep["rows"]]).set_index("Scenario")
        st.caption("Unsafe answer rate (%): a confident but wrong diagnosis. Lower is better.")
        st.bar_chart(df, horizontal=True, color=["#DC2626", "#15803D"], stack=False)  # Raw model red, LeafGuard green
        st.dataframe(pd.DataFrame(rep["rows"]).round(3), hide_index=True, width="stretch")
    else:
        ui.card("No report yet", "<p style='margin:0'>Generate the numbers with:</p>"
                "<code>python scripts/stress_test.py --test_dir &lt;dataset&gt;/test --ood_dir data/ood</code>", "flask")
    cpath = os.path.join(ROOT, "reports", "calibration.json")
    if os.path.exists(cpath):
        c = json.load(open(cpath))
        st.markdown("### Calibration: is the confidence honest?")
        if "ece_before" in c:
            tiles = [ui.stat(f"{c['ece_before']:.3f} → {c['ece_after']:.3f}", "Calibration error before → after", "info"),
                     ui.stat(f"{c['coverage']:.0%}", "Answers given (coverage)", "neutral")]
            if c.get("accuracy_when_answering") is not None:
                tiles.append(ui.stat(f"{c['accuracy_when_answering']:.1%}", "Accuracy when it answers", "good"))
        else:
            tiles = [ui.stat(f"{c['det_conf_high']:.2f}", "'Disease detected' box threshold", "info")]
            if c.get("precision_when_diagnosing") is not None:
                tiles.append(ui.stat(f"{c['precision_when_diagnosing']:.1%}", "Accuracy when LeafGuard diagnoses", "good"))
            tiles.append(ui.stat(f"{c['diseased_images_caught']:.0%}", "Diseased photos confidently caught", "neutral"))
        for col, t in zip(st.columns(len(tiles)), tiles):
            col.markdown(t, unsafe_allow_html=True)

# ---------------------------------------------------------------- how
with tab_how:
    st.markdown("### Your model is not changed. LeafGuard wraps it with safety stages.")
    stages = [
        ("camera", "1 · Photo quality", "Blur, darkness, glare, a thumb on the lens, a covered camera.",
         "Sharpness, brightness and skin-colour checks"),
        ("eye", "2 · Is it a leaf?", "Coffee mugs, hands, floors, phone screens.",
         "CLIP zero-shot vision model (colour check if offline)"),
        ("scan", "3 · Find THE leaf", "A healthy leaf lying next to sick ones.",
         "Segmentation picks the central leaf; detections off it are ignored"),
        ("cpu", "4 · Disease check", "Your trained model, unchanged.",
         "YOLO boxes / classifier with honest, calibrated confidence"),
        ("gavel", "5 · Decide & prove", "Close calls and lucky guesses.",
         "Strong = diagnose, faint = not sure, plus boxes / heatmap as proof"),
    ]
    cols = st.columns(len(stages), gap="small")
    for col, (ic, title, catches, how) in zip(cols, stages):
        col.markdown(f"<div class='lg-card' style='height:100%'><div style='margin-bottom:8px'>{ui.icon(ic, 26, '#15803D')}"
                     f"</div><h3>{title}</h3><p style='margin:0 0 8px 0'><b>Catches:</b> {catches}</p>"
                     f"<p class='lg-muted' style='margin:0;font-size:.88rem'>{how}</p></div>", unsafe_allow_html=True)
    st.markdown("#### Every possible answer")
    st.markdown(" ".join(ui.status_chip(v) for v in ui.STATUS), unsafe_allow_html=True)
    st.caption("Each answer uses an icon, a word and a colour, so it is clear even without colour vision.")
