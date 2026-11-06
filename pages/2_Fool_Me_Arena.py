"""Fool Me Arena: judges try to trick LeafGuard, live. Raw model vs LeafGuard scoreboard."""
import html
import os
import sys

import pandas as pd
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from leafguard_plus import ui  # noqa: E402
from leafguard_plus.arena import (OUTCOME_STYLE, OUTCOME_TEXT, TRUTHS, Scoreboard, caught_by,  # noqa: E402
                                  raw_verdict, score)
from leafguard_plus.i18n import disease_name  # noqa: E402
from leafguard_plus.shared import get_guard, photo_input, setup_page  # noqa: E402

setup_page("Fool Me Arena", ":material/target:")
guard = get_guard()
board = Scoreboard(ROOT)


def outcome_chip(o):
    tone, ic = OUTCOME_STYLE[o]
    return ui.chip(OUTCOME_TEXT[o], tone, ic)


ui.header("Fool Me Arena", "Judges: try to trick LeafGuard. Your hand, a mug, a leaf on a phone screen, a blurry "
          "shot, a healthy leaf next to a sick one. Both models are scored on every attempt.", "target",
          eyebrow="Live challenge")

# ---------------------------------------------------------------- scoreboard
t = board.totals()
tiles = [ui.stat(t["n"], "Attempts so far", "neutral", "user"),
         ui.stat(t["raw_fooled"], "Times the raw model was fooled", "bad", "cpu"),
         ui.stat(t["leafguard_fooled"], "Times LeafGuard was fooled", "good", "shield"),
         ui.stat(f"{(t['n'] - t['leafguard_fooled']) / t['n']:.0%}" if t["n"] else "–",
                 "LeafGuard not fooled", "info", "check_circle")]
for col, tile in zip(st.columns(4, gap="small"), tiles):
    col.markdown(tile, unsafe_allow_html=True)
if t["n"]:
    df = pd.DataFrame({"Correct": [t["raw_win"], t["leafguard_win"]],
                       "Safely refused": [t["raw_safe"], t["leafguard_safe"]],
                       "Fooled": [t["raw_fooled"], t["leafguard_fooled"]]}, index=["Raw model", "LeafGuard"])
    st.bar_chart(df, horizontal=True, color=["#15803D", "#0E7490", "#DC2626"], height=170)  # Correct, Safe, Fooled
    st.caption("Correct = right answer · Safely refused = said retake / not sure / not a leaf (no harm done) · "
               "Fooled = confident and wrong")

st.divider()

# ---------------------------------------------------------------- new attempt
left, right = st.columns([1, 1.2], gap="large")
with left:
    st.markdown("### New challenge")
    who = st.text_input("Challenger name (optional)", key="arena_who", placeholder="e.g. Judge 1")
    truth = st.radio("What are you really showing?", list(TRUTHS), format_func=TRUTHS.get, key="arena_truth")
    truth_cls = None
    if truth == "diseased":
        opts = ["Don't know which"] + guard.class_names
        pick = st.selectbox("Which disease?", opts, format_func=lambda c: c if c == opts[0] else disease_name(c, "en"))
        truth_cls = None if pick == opts[0] else pick
    rgb = photo_input("arena")
    go = st.button("Challenge LeafGuard", type="primary", disabled=rgb is None, width="stretch",
                   icon=":material/swords:")

if go and rgb is not None:
    with st.spinner("LeafGuard is thinking ..."):
        r = guard.analyze(rgb, do_explain=True)
    raw_v, raw_c = raw_verdict(guard, r)
    entry = board.add({
        "who": who or "Anonymous", "truth": truth, "truth_cls": truth_cls,
        "raw_said": r["baseline"]["label"], "raw_outcome": score(truth, truth_cls, raw_v, raw_c),
        "leafguard_said": r["headline"] + (f": {r['label']}" if r["verdict"] == "DISEASED" else ""),
        "leafguard_verdict": r["verdict"],
        "leafguard_outcome": score(truth, truth_cls, r["verdict"], r.get("cls")),
        "caught_by": caught_by(r), "reasons": r["reasons"][:2],
    }, rgb)
    st.session_state["arena_last"] = (entry, r["images"].get("heatmap"))
    st.rerun()

with right:
    last = st.session_state.get("arena_last")
    if not last:
        ui.card("How it works", "<ol style='margin:0;padding-left:18px;line-height:1.8'>"
                "<li>Tell us what you are really showing</li><li>Take or upload the photo</li>"
                "<li>Press <b>Challenge LeafGuard</b></li><li>See if you fooled the raw model, LeafGuard, or both</li>"
                "</ol>", "target")
    else:
        e, pic = last
        st.markdown(f"### Attempt #{e['id']} · {html.escape(e['who'])}")
        a, b = st.columns(2, gap="small")
        a.markdown(f"<div class='lg-verdict lg-raw'><span class='lg-eyebrow' style='color:#475569'>Raw model</span>"
                   f"<div class='title' style='color:#1E293B'>{html.escape(e['raw_said'])}</div>"
                   f"{outcome_chip(e['raw_outcome'])}</div>", unsafe_allow_html=True)
        v = e.get("leafguard_verdict", "UNCERTAIN")
        word, ic, bg, fg, border = ui.STATUS[v]
        why = (f"<div class='lg-muted' style='font-size:.85rem;margin-top:8px'>Caught by: "
               f"{html.escape(e['caught_by'])}</div>") if e.get("caught_by") else ""
        b.markdown(f"<div class='lg-verdict' style='background:{bg};color:{fg};border-color:{border}'>"
                   f"<span class='lg-eyebrow' style='color:{fg}'>LeafGuard</span>"
                   f"<div class='title'>{html.escape(e['leafguard_said'])}</div>"
                   f"{outcome_chip(e['leafguard_outcome'])}{why}</div>", unsafe_allow_html=True)
        for reason in e.get("reasons", []):
            st.caption("• " + reason)
        if pic is not None:
            st.image(pic, width="stretch")
        if e["leafguard_outcome"] == "fooled":
            st.warning("You got us! This photo is saved as an example to improve the next version.",
                       icon=":material/flag:")
        elif e["raw_outcome"] == "fooled":
            st.success("The raw model fell for it. LeafGuard didn't.", icon=":material/verified_user:")

# ---------------------------------------------------------------- history
rows = board.load()
if rows:
    st.divider()
    st.markdown("### All attempts")
    cols = st.columns(4, gap="small")
    for k, e in enumerate(reversed(rows[-16:])):
        with cols[k % 4]:
            path = os.path.join(board.dir, e["image"])
            if os.path.exists(path):
                st.image(path, width="stretch")
            st.markdown(f"<div style='font-size:.85rem;line-height:2'><b>#{e['id']} {html.escape(e['who'])}</b> · "
                        f"{TRUTHS[e['truth']].split(' (')[0]}<br>"
                        f"<span class='lg-muted'>Raw model</span> {outcome_chip(e['raw_outcome'])}<br>"
                        f"<span class='lg-muted'>LeafGuard</span> {outcome_chip(e['leafguard_outcome'])}</div>",
                        unsafe_allow_html=True)
    with st.expander("Reset the scoreboard", icon=":material/restart_alt:"):
        if st.checkbox("Yes, delete all attempts") and st.button("Reset", icon=":material/delete:"):
            board.reset()
            st.session_state.pop("arena_last", None)
            st.rerun()
