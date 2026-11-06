"""Streamlit helpers shared by the feature pages."""
import glob
import json
import os

import cv2
import numpy as np
import streamlit as st

from leafguard import LeafGuard, load_config

from . import ui

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = ui.CSS  # kept for backwards compatibility


@st.cache_resource(show_spinner="Loading the model and safety layer ...")
def _load(cfg_json):
    return LeafGuard(json.loads(cfg_json))


def get_guard():
    cfg = load_config(os.path.join(ROOT, "config.json"))
    return _load(json.dumps(cfg))


def setup_page(title, icon_name):
    """Page config + design system + sidebar navigation. Call first on every page."""
    st.set_page_config(page_title=f"LeafGuard · {title}", page_icon=icon_name, layout="wide")
    ui.apply()
    ui.sidebar()


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


def card(verdict, headline, lines, label="LeafGuard says", extra_html=""):
    """Verdict card in the design system (icon + status word + colour)."""
    ui.verdict_card(verdict, headline, lines, label=label)


# ---------------------------------------------------------------- hand-off between pages
def remember_diagnosis(result, rgb=None, sev=None, verdict=None):
    """Keep the latest diagnosis so Treatment Plan / Field Diary can pick it up (same browser session)."""
    v = verdict or result.get("verdict")
    st.session_state["lg_last"] = {
        "verdict": v, "cls": result.get("cls"), "label": result.get("label"),
        "confidence": result.get("confidence"),
        "severity": None if not sev else sev.get("percent"), "level": None if not sev else sev.get("level"),
        "thumb": None if rgb is None else _thumb(rgb),
    }


def last_diagnosis():
    return st.session_state.get("lg_last")


def _thumb(rgb, side=360):
    s = min(1.0, side / max(rgb.shape[:2]))
    return cv2.resize(rgb, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else rgb
