"""Fool Me Arena: judges try to trick LeafGuard, live. Raw model vs LeafGuard scoreboard."""
import os
import sys

import pandas as pd
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from leafguard_plus.arena import OUTCOME_TEXT, TRUTHS, Scoreboard, caught_by, raw_verdict, score  # noqa: E402
from leafguard_plus.i18n import disease_name  # noqa: E402
from leafguard_plus.shared import CSS, get_guard, photo_input  # noqa: E402

st.set_page_config(page_title="LeafGuard · Fool Me Arena", page_icon="🎯", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)
guard = get_guard()
board = Scoreboard(ROOT)

st.title("🎯 Fool Me Arena")
st.caption("Judges: try to trick LeafGuard. Show it anything: your hand, a mug, a leaf photo on a phone screen, "
           "a blurry shot, a healthy leaf on a sick one. Every attempt is scored for the raw model AND LeafGuard.")

# ---------------------------------------------------------------- scoreboard
t = board.totals()
m1, m2, m3, m4 = st.columns(4)
m1.metric("Attempts", t["n"])
m2.metric("Times the RAW model was fooled", t["raw_fooled"])
m3.metric("Times LeafGuard was fooled", t["leafguard_fooled"])
m4.metric("LeafGuard not fooled", f"{(t['n'] - t['leafguard_fooled']) / t['n']:.0%}" if t["n"] else "–")
if t["n"]:
    df = pd.DataFrame({"Correct": [t["raw_win"], t["leafguard_win"]],
                       "Safely refused": [t["raw_safe"], t["leafguard_safe"]],
                       "Fooled": [t["raw_fooled"], t["leafguard_fooled"]]}, index=["Raw model", "LeafGuard"])
    st.bar_chart(df, horizontal=True, color=["#66bb6a", "#64b5f6", "#e57373"], height=170)

st.divider()

# ---------------------------------------------------------------- new attempt
left, right = st.columns([1, 1.2])
with left:
    st.subheader("New challenge")
    who = st.text_input("Challenger name (optional)", key="arena_who")
    truth = st.radio("What are you really showing?", list(TRUTHS), format_func=TRUTHS.get, key="arena_truth")
    truth_cls = None
    if truth == "diseased":
        opts = ["Don't know which"] + guard.class_names
        pick = st.selectbox("Which disease?", opts, format_func=lambda c: c if c == opts[0] else disease_name(c, "en"))
        truth_cls = None if pick == opts[0] else pick
    rgb = photo_input("arena")
    go = st.button("⚔️ Challenge LeafGuard!", type="primary", disabled=rgb is None, width="stretch")

if go and rgb is not None:
    with st.spinner("LeafGuard is thinking ..."):
        r = guard.analyze(rgb, do_explain=True)
    raw_v, raw_c = raw_verdict(guard, r)
    entry = board.add({
        "who": who or "Anonymous", "truth": truth, "truth_cls": truth_cls,
        "raw_said": r["baseline"]["label"], "raw_outcome": score(truth, truth_cls, raw_v, raw_c),
        "leafguard_said": r["headline"] + (f": {r['label']}" if r["verdict"] == "DISEASED" else ""),
        "leafguard_outcome": score(truth, truth_cls, r["verdict"], r.get("cls")),
        "caught_by": caught_by(r), "reasons": r["reasons"][:2],
    }, rgb)
    st.session_state["arena_last"] = (entry, r["images"].get("heatmap"))
    st.rerun()

with right:
    last = st.session_state.get("arena_last")
    if last:
        e, pic = last
        st.subheader(f"Attempt #{e['id']} by {e['who']}")
        a, b = st.columns(2)
        a.markdown(f"<div class='card' style='background:#f4f4f4'><p class='small'>RAW MODEL</p>"
                   f"<h2>{e['raw_said']}</h2><p><b>{OUTCOME_TEXT[e['raw_outcome']]}</b></p></div>",
                   unsafe_allow_html=True)
        colour = {"win": "#e8f5e9", "safe": "#e3f2fd", "fooled": "#ffebee"}[e["leafguard_outcome"]]
        why = f"<p class='small'>Caught by: {e['caught_by']}</p>" if e.get("caught_by") else ""
        b.markdown(f"<div class='card' style='background:{colour}'><p class='small'>LEAFGUARD</p>"
                   f"<h2>{e['leafguard_said']}</h2><p><b>{OUTCOME_TEXT[e['leafguard_outcome']]}</b></p>{why}</div>",
                   unsafe_allow_html=True)
        for reason in e.get("reasons", []):
            st.caption("• " + reason)
        if pic is not None:
            st.image(pic, width="stretch")
        if e["leafguard_outcome"] == "fooled":
            st.warning("You got us! This photo is saved, a perfect example to improve the next version.")
        elif e["raw_outcome"] == "fooled":
            st.success("The raw model fell for it. LeafGuard didn't. 🛡️")

# ---------------------------------------------------------------- history
rows = board.load()
if rows:
    st.divider()
    st.subheader("All attempts")
    cols = st.columns(4)
    for k, e in enumerate(reversed(rows[-16:])):
        with cols[k % 4]:
            path = os.path.join(board.dir, e["image"])
            if os.path.exists(path):
                st.image(path, width="stretch")
            st.caption(f"#{e['id']} {e['who']} · {TRUTHS[e['truth']].split(' (')[0]}  \n"
                       f"Raw: {OUTCOME_TEXT[e['raw_outcome']]} · LeafGuard: {OUTCOME_TEXT[e['leafguard_outcome']]}")
    with st.expander("Reset the scoreboard"):
        if st.checkbox("Yes, delete all attempts") and st.button("Reset"):
            board.reset()
            st.session_state.pop("arena_last", None)
            st.rerun()
