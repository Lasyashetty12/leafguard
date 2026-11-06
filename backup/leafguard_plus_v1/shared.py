"""Streamlit helpers shared by the new pages (the original app.py is not touched)."""
import glob
import json
import os

import cv2
import numpy as np
import streamlit as st

from leafguard import LeafGuard, load_config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STYLE = {"HEALTHY": ("#e8f5e9", "#2e7d32", "✅"), "DISEASED": ("#fff3e0", "#e65100", "🩺"),
         "UNCERTAIN": ("#fffde7", "#8d6e00", "🤔"), "RETAKE": ("#e3f2fd", "#1565c0", "📸"),
         "NOT_A_LEAF": ("#fce4ec", "#ad1457", "🚫")}

CSS = """<style>
.block-container{padding-top:1.4rem}
.card{border-radius:14px;padding:16px 20px;margin:4px 0 12px 0;border:1px solid rgba(0,0,0,.06)}
.card h2{margin:0 0 6px 0;font-size:1.45rem} .card p{margin:3px 0}
.small{font-size:.85rem;opacity:.75}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:.8rem;font-weight:600}
.big{font-size:2.6rem;font-weight:800;line-height:1}
</style>"""


@st.cache_resource(show_spinner="Loading the model and safety layer ...")
def _load(cfg_json):
    return LeafGuard(json.loads(cfg_json))


def get_guard():
    cfg = load_config(os.path.join(ROOT, "config.json"))
    return _load(json.dumps(cfg))


def decode(file_bytes):
    img = cv2.imdecode(np.frombuffer(file_bytes, np.uint8), cv2.IMREAD_COLOR)
    return None if img is None else cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def photo_input(key, allow_samples=True):
    """Upload / phone camera / webcam / samples -> RGB array or None."""
    options = ["Upload / phone camera", "Webcam"] + (["Sample photos"] if allow_samples else [])
    src = st.radio("Photo source", options, horizontal=True, key=f"{key}_src")
    if src == "Upload / phone camera":
        f = st.file_uploader("Upload a photo (on a phone this can open the camera)",
                             type=["jpg", "jpeg", "png", "webp"], key=f"{key}_up")
        return decode(f.getvalue()) if f else None
    if src == "Webcam":
        f = st.camera_input("Take a photo", key=f"{key}_cam")
        return decode(f.getvalue()) if f else None
    samples = sorted(glob.glob(os.path.join(ROOT, "sample_images", "*")))
    if not samples:
        st.info("No sample photos found.")
        return None
    pick = st.selectbox("Sample", samples, format_func=os.path.basename, key=f"{key}_sample")
    return cv2.cvtColor(cv2.imread(pick), cv2.COLOR_BGR2RGB)


def card(verdict, headline, lines, label="LEAFGUARD SAYS", extra_html=""):
    bg, fg, icon = STYLE[verdict]
    body = "".join(f"<p>• {line}</p>" for line in lines)
    st.markdown(f"<div class='card' style='background:{bg};color:{fg}'><p class='small'>{label}</p>"
                f"<h2>{icon} {headline}</h2>{body}{extra_html}</div>", unsafe_allow_html=True)
