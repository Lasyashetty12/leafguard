"""Field Diary: every check-up per plot, with a severity trend to see if treatment is working."""
import html
import io
import os
import sys

import pandas as pd
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from leafguard_plus import ui  # noqa: E402
from leafguard_plus.diary import Diary, trend  # noqa: E402
from leafguard_plus.i18n import disease_name  # noqa: E402
from leafguard_plus.shared import last_diagnosis, setup_page  # noqa: E402

setup_page("Field Diary", ":material/menu_book:")
diary = Diary(ROOT)

ui.header("Field Diary", "Every check-up for each plot in one place, so you can see whether the disease is "
          "getting better after treatment.", "gauge", eyebrow="Track progress")

# ---------------------------------------------------------------- quick add from the last diagnosis
last = last_diagnosis()
with st.expander("Add the latest diagnosis", expanded=bool(last) and not diary.load(), icon=":material/add_circle:"):
    if not last:
        st.caption("Diagnose a leaf on the Diagnose or Deep Check page first.")
    else:
        a, b, c = st.columns([1.2, 1.6, 1])
        plot = a.text_input("Plot name", value=st.session_state.get("lg_plot", "My field"))
        note = b.text_input("Note (optional)", placeholder="e.g. sprayed sulphur on Monday")
        what = "No disease" if last["verdict"] == "HEALTHY" else (
            disease_name(last.get("cls"), "en") if last["verdict"] == "DISEASED" else ui.STATUS[last["verdict"]][0])
        c.markdown(f"<div style='margin-top:30px'>{ui.status_chip(last['verdict'])}</div>", unsafe_allow_html=True)
        if st.button(f"Save: {what}", icon=":material/bookmark_add:"):
            st.session_state["lg_plot"] = plot
            diary.add(plot, last["verdict"], last.get("cls") or "", last.get("severity") if last["verdict"] == "DISEASED" else 0.0,
                      last.get("level"), last.get("confidence"), note, rgb=last.get("thumb"))
            st.rerun()

rows = diary.load()
if not rows:
    ui.card("Your diary is empty", "<p style='margin:0'>Save check-ups from <b>Treatment Plan</b>, <b>Field Scan</b> "
            "or the box above. Check the same plot every few days to see the trend.</p>", "gauge")
    st.stop()

plots = diary.plots()
plot = st.selectbox("Plot", plots, index=plots.index(st.session_state["lg_plot"])
                    if st.session_state.get("lg_plot") in plots else 0)
entries = sorted([r for r in rows if r["plot"] == plot], key=lambda r: r["time"])

# ---------------------------------------------------------------- trend
direction, text = trend(entries)
latest = entries[-1]
tiles = [ui.stat(len(entries), "Check-ups saved", "neutral", "camera"),
         ui.stat(f"{round(latest['severity'] or 0)}%", "Latest affected area",
                 "bad" if (latest["severity"] or 0) >= 45 else "warn" if (latest["severity"] or 0) >= 15 else "good", "gauge"),
         ui.stat({"better": "Improving", "worse": "Worse", "same": "Steady", None: "–"}[direction], "Trend",
                 {"better": "good", "worse": "bad", "same": "info", None: "neutral"}[direction],
                 {"better": "check_circle", "worse": "alert", "same": "repeat", None: "help"}[direction])]
for col, t in zip(st.columns(3, gap="small"), tiles):
    col.markdown(t, unsafe_allow_html=True)
st.write("")
ui.card("What the trend says", f"<p style='margin:0'>{html.escape(text)}</p>",
        {"better": "check_circle", "worse": "alert"}.get(direction, "help"))

if len(entries) >= 2:
    import altair as alt
    df = pd.DataFrame({"Date": pd.to_datetime([e["time"] for e in entries]),
                       "Affected area (%)": [e["severity"] or 0 for e in entries],
                       "Note": [e.get("note") or "" for e in entries]})
    base = alt.Chart(df).encode(
        x=alt.X("Date:T", axis=alt.Axis(format="%d %b", tickCount={"interval": "day", "step": 1}, title=None,
                                        labelAngle=0)),
        y=alt.Y("Affected area (%):Q", scale=alt.Scale(domain=[0, 100])),
        tooltip=[alt.Tooltip("Date:T", format="%d %b %Y, %H:%M"), "Affected area (%):Q", "Note:N"])
    line = base.mark_line(color="#DC2626", strokeWidth=3, interpolate="monotone")
    pts = base.mark_circle(color="#DC2626", size=110, opacity=1)
    labels = base.mark_text(dy=-14, color="#991B1B", fontWeight="bold").encode(text=alt.Text("Affected area (%):Q", format=".0f"))
    st.altair_chart((line + pts + labels).properties(height=260), width="stretch")

# ---------------------------------------------------------------- timeline
st.markdown("### Timeline")
for e in reversed(entries):
    a, b, c = st.columns([1, 3, .6], gap="medium", vertical_alignment="center")
    img = os.path.join(diary.dir, e["image"]) if e.get("image") else None
    if img and os.path.exists(img):
        a.image(img, width="stretch")
    what = "No disease" if e["verdict"] == "HEALTHY" else disease_name(e["disease"], "en") if e["verdict"] == "DISEASED" \
        else ui.STATUS.get(e["verdict"], ("-",))[0]
    sev = f" · {e['severity']:.0f}% affected" if e.get("severity") else ""
    b.markdown(f"<div style='font-weight:700'>{html.escape(e['time'])}</div>{ui.status_chip(e['verdict'])} "
               f"<span>{html.escape(what)}{sev}</span>"
               + (f"<div class='lg-muted' style='font-size:.9rem;margin-top:4px'>{html.escape(e['note'])}</div>"
                  if e.get("note") else ""), unsafe_allow_html=True)
    if c.button("Delete", key=f"del_{e['id']}", icon=":material/delete:"):
        diary.delete(e["id"])
        st.rerun()

buf = io.StringIO()
pd.DataFrame(rows).drop(columns=["image"], errors="ignore").to_csv(buf, index=False)
st.download_button("Download the whole diary (CSV)", buf.getvalue().encode(), "field_diary.csv",
                   icon=":material/download:")
