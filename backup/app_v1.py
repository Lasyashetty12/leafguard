"""LeafGuard demo app.   Run:  streamlit run app.py"""
import glob
import json
import os

import cv2
import numpy as np
import streamlit as st

from leafguard import LeafGuard, load_config

ROOT = os.path.dirname(os.path.abspath(__file__))
st.set_page_config(page_title="LeafGuard", page_icon="🌿", layout="wide")

COLOURS = {"HEALTHY": ("#e8f5e9", "#2e7d32", "✅"), "DISEASED": ("#fff3e0", "#e65100", "🩺"),
           "UNCERTAIN": ("#fffde7", "#8d6e00", "🤔"), "RETAKE": ("#e3f2fd", "#1565c0", "📸"),
           "NOT_A_LEAF": ("#fce4ec", "#ad1457", "🚫")}

st.markdown("""<style>
.block-container{padding-top:1.6rem}
.card{border-radius:14px;padding:18px 20px;margin:4px 0 12px 0;border:1px solid rgba(0,0,0,.06)}
.card h2{margin:0 0 4px 0;font-size:1.55rem}
.card p{margin:2px 0}
.raw{background:#f4f4f4;color:#333}
.small{font-size:.85rem;opacity:.75}
.check{padding:3px 0;font-size:.95rem}
</style>""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading your model and the safety layer ...")
def get_guard(cfg_json):
    return LeafGuard(json.loads(cfg_json))


cfg = load_config(os.path.join(ROOT, "config.json"))

# ---------------------------------------------------------------- sidebar
guard = get_guard(json.dumps(cfg))  # loaded once; sliders below only change thresholds

with st.sidebar:
    st.header("🌿 LeafGuard")
    st.caption("A safety layer that makes a leaf-disease model say **\"I don't know\"** instead of guessing.")
    with st.expander("Safety settings", expanded=False):
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
    explain_on = st.toggle("Explain (heatmap / boxes)", value=True)
    compare_on = st.toggle("Show raw model side-by-side", value=True)
    st.divider()
    kind = "detector" if guard.is_detector else "classifier"
    extra = "" if guard.is_detector else f"  \n**Temperature:** {cfg['temperature']}"
    st.markdown(f"**Model:** `{cfg['framework']}` {kind} · {len(guard.class_names)} classes  \n"
                f"**Leaf check:** {guard.leaf_gate.method}{extra}")
    with st.expander("Classes the model knows"):
        st.write(", ".join(n.replace("_", " ") for n in guard.class_names))
    if cfg["framework"] == "demo":
        st.warning("Running the built-in DEMO model. Put your model in config.json.")
    if guard.leaf_gate.clip_error:
        st.caption(f"CLIP unavailable, using colour check ({guard.leaf_gate.clip_error[:80]})")

tab_diag, tab_proof, tab_how = st.tabs(["📷 Diagnose", "🧪 Proof", "⚙️ How it works"])

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

    if rgb is not None:
        with st.spinner("Checking photo, finding leaf, asking the model, explaining ..."):
            r = guard.analyze(rgb, do_explain=explain_on, explain_baseline=explain_on and compare_on)
        bg, fg, icon = COLOURS[r["verdict"]]
        show_conf = r["verdict"] == "DISEASED" or (r["verdict"] == "HEALTHY" and not guard.is_detector)
        conf_txt = f" · {round(r['confidence'] * 100)}% confident" if show_conf else ""
        label_txt = f"<p><b>{r['label']}</b>{conf_txt}</p>" if r["verdict"] in ("HEALTHY", "DISEASED") else ""
        reasons = "".join(f"<p>• {x}</p>" for x in r["reasons"])
        lg_card = (f"<div class='card' style='background:{bg};color:{fg}'><p class='small'>LEAFGUARD SAYS</p>"
                   f"<h2>{icon} {r['headline']}</h2>{label_txt}{reasons}</div>")

        if compare_on:
            c1, c2 = st.columns(2)
            b = r["baseline"]
            raw_conf = f"<p>{round(b['confidence'] * 100)}% confident</p>" if b["confidence"] is not None else "<p>No boxes found</p>"
            c1.markdown(f"<div class='card raw'><p class='small'>RAW MODEL (no safety layer)</p>"
                        f"<h2>{b['label']}</h2>{raw_conf}"
                        f"<p class='small'>It always answers, even for a mug or a blurry photo.</p></div>",
                        unsafe_allow_html=True)
            c2.markdown(lg_card, unsafe_allow_html=True)
        else:
            st.markdown(lg_card, unsafe_allow_html=True)

        left, right = st.columns([1, 2])
        with left:
            st.subheader("Safety checks")
            for c in r["checks"]:
                mark = "✅" if c["passed"] else "❌"
                st.markdown(f"<div class='check'>{mark} <b>{c['name']}</b> <span class='small'>({c['value']})</span></div>",
                            unsafe_allow_html=True)
            if r.get("top3"):
                st.subheader("Strongest detection per disease" if guard.is_detector else "Top answers (calibrated)")
                for t in r["top3"]:
                    st.progress(float(t["prob"]), text=f"{t['label']}: {round(t['prob'] * 100)}%")
            st.caption(f"Analysed in {r['seconds']} s")
        with right:
            imgs = [("Your photo", rgb)]
            if guard.is_detector:
                if "heatmap" in r["images"]:
                    focus = r.get("leaf_focus")
                    imgs.append(("LeafGuard: spots counted on the leaf (grey dashed = ignored, off leaf)"
                                 + (f" · {round(focus * 100)}% on leaf" if focus is not None else ""),
                                 r["images"]["heatmap"]))
                if "baseline_heatmap" in r["images"]:
                    imgs.append(("Raw YOLO boxes (what the farmer would see without LeafGuard)",
                                 r["images"]["baseline_heatmap"]))
                if "leaf_only" in r["images"]:
                    imgs.append(("Leaf LeafGuard found", r["images"]["leaf_only"]))
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
            cols = st.columns(2)
            for k, (cap, im) in enumerate(imgs):
                cols[k % 2].image(im, caption=cap, width="stretch")

# ---------------------------------------------------------------- proof
with tab_proof:
    st.subheader("Does the safety layer actually help? The numbers")
    path = os.path.join(ROOT, "reports", "stress_test.json")
    if os.path.exists(path):
        rep = json.load(open(path))
        h = rep["hard_cases_unsafe"]
        m1, m2, m3 = st.columns(3)
        m1.metric("Raw model: unsafe answers on hard photos", f"{h['raw']:.0%}")
        m2.metric("LeafGuard: unsafe answers on hard photos", f"{h['leafguard']:.0%}",
                  delta=f"{(h['leafguard'] - h['raw']) * 100:.0f} pts", delta_color="inverse")
        clean = next((x for x in rep["rows"] if x["scenario"] == "clean"), None)
        if clean:
            m3.metric("Clean photos: LeafGuard correct when it answers",
                      f"{clean['leafguard_correct'] / max(1e-9, 1 - clean['leafguard_abstain']):.0%}")
        import pandas as pd
        df = pd.DataFrame([{"Scenario": x["description"], "Raw model": x["raw_unsafe_rate"] * 100,
                            "LeafGuard": x["leafguard_unsafe_rate"] * 100} for x in rep["rows"]]).set_index("Scenario")
        st.caption("Unsafe answer rate (%): a confident but wrong diagnosis. Lower is better.")
        st.bar_chart(df, horizontal=True, color=["#66bb6a", "#e57373"], stack=False)
        st.dataframe(pd.DataFrame(rep["rows"]).round(3), hide_index=True, width="stretch")
    else:
        st.info("No report yet. Run:  python scripts/stress_test.py --test_dir data/test --ood_dir data/ood")
    cpath = os.path.join(ROOT, "reports", "calibration.json")
    if os.path.exists(cpath):
        c = json.load(open(cpath))
        st.subheader("Calibration: is the confidence honest?")
        a, b_, cc = st.columns(3)
        a.metric("Calibration error before → after", f"{c['ece_before']:.3f} → {c['ece_after']:.3f}")
        b_.metric("Answers given (coverage)", f"{c['coverage']:.0%}")
        if c.get("accuracy_when_answering") is not None:
            cc.metric("Accuracy when it answers", f"{c['accuracy_when_answering']:.1%}")

# ---------------------------------------------------------------- how
with tab_how:
    st.markdown("""
**Your model is not changed.** LeafGuard wraps it with six checks:

| # | Check | Catches | How |
|---|---|---|---|
| 1 | Photo quality | blur, darkness, glare, thumb on lens, blank | Laplacian sharpness, brightness stats, skin-colour + smoothness |
| 2 | Is it a leaf? | coffee mug, hand, floor, screen | CLIP zero-shot (falls back to plant-colour check) |
| 3 | Cut out the leaf | the "healthy leaf on a sick table" trick | colour segmentation + GrabCut; background painted neutral |
| 4 | Honest confidence | over-confident wrong answers | temperature scaling on validation data |
| 5 | Uncertainty + background check | close calls, background shortcuts | confidence, margin, entropy; full photo vs leaf-only disagreement |
| 6 | Prove why | model looking at the wrong thing | Grad-CAM / occlusion map, % of attention on the leaf |

**With a YOLO detector** (boxes on disease spots), steps 4-6 become: keep only boxes that sit **on the leaf**
(boxes on the table/background are ignored and shown dashed), strong box = disease, faint box = "not sure",
no box = "no disease found" (with a note that the model only knows its trained diseases).

**Possible answers:** Healthy · Disease detected · Not sure · Retake photo · Not a leaf
""")
