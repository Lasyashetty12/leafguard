"""Treatment Plan: what to do today, treatment options, prevention, spray-weather check and disease risk forecast."""
import html
import os
import sys

import streamlit as st
import streamlit.components.v1 as components

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from leafguard_plus import share, treatment, ui, weather  # noqa: E402
from leafguard_plus.diary import Diary  # noqa: E402
from leafguard_plus.i18n import LANGS, farmer_message  # noqa: E402
from leafguard_plus.shared import get_guard, last_diagnosis, setup_page  # noqa: E402
from leafguard_plus.voice import browser_speak_html  # noqa: E402

setup_page("Treatment Plan", ":material/healing:")
guard = get_guard()

ui.header("Treatment Plan", "What to do today, which treatments to discuss with your officer, and whether the "
          "weather allows spraying.", "shield", eyebrow="From diagnosis to action")

# ---------------------------------------------------------------- which disease?
last = last_diagnosis()
disease_classes = [c for c in guard.class_names if treatment.key_for(c)]
levels = ["mild", "moderate", "severe"]
c1, c2, c3 = st.columns([1.4, 1, 1])
default_cls = last["cls"] if last and last.get("verdict") == "DISEASED" and last.get("cls") in disease_classes \
    else disease_classes[0]
cls = c1.selectbox("Disease", disease_classes, index=disease_classes.index(default_cls),
                   format_func=lambda c: treatment.DISEASES[treatment.key_for(c)]["name"])
default_level = last["level"] if last and last.get("cls") == cls and last.get("level") in levels else "moderate"
level = c2.selectbox("Severity", levels, index=levels.index(default_level), format_func=str.title)
lang = LANGS[c3.selectbox("Farmer language", list(LANGS))]
if last and last.get("verdict") == "DISEASED" and last.get("cls") == cls:
    sev_txt = f" · {round(last['severity'])}% of leaf affected" if last.get("severity") is not None else ""
    st.markdown(ui.chip(f"Loaded from your last diagnosis{sev_txt}", "info", "check_circle"), unsafe_allow_html=True)
elif not last:
    st.caption("Tip: diagnose a leaf first (Diagnose or Deep Check) and the plan fills in automatically.")

p = treatment.plan(cls, level)
tone = {"Today": "bad"}.get(p["act_by"].split(":")[0], "warn")

# ---------------------------------------------------------------- headline
st.markdown(
    f"<div class='lg-verdict' style='background:#FFF7ED;color:#9A3412;border-color:#FDBA74'>"
    f"<div class='row lg-v-diseased'><div class='ib'>{ui.icon('alert', 26, '#9A3412', 2.2)}</div><div style='flex:1'>"
    f"<div style='display:flex;gap:8px;flex-wrap:wrap;align-items:center'><span class='lg-eyebrow' style='color:#9A3412'>"
    f"Treatment plan</span>{ui.chip('Act by: ' + p['act_by'], tone, 'alert')}"
    f"{ui.chip('Severity: ' + level, {'mild': 'good', 'moderate': 'warn', 'severe': 'bad'}[level], 'gauge')}</div>"
    f"<div class='title'>{html.escape(p['name'])}</div><div>{html.escape(p['what'])}</div>"
    f"<div class='lg-muted' style='margin-top:6px;font-size:.9rem'><b>Spreads:</b> {html.escape(p['spreads'])} "
    f"<b>Favoured by:</b> {html.escape(p['weather'])}</div></div></div></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------- today / options / prevention
left, right = st.columns([1, 1.35], gap="large")
with left:
    st.markdown("### Do this today")
    done = 0
    for i, step in enumerate(p["today"]):
        done += st.checkbox(step, key=f"today_{p['key']}_{i}")
    st.progress(done / len(p["today"]), text=f"{done} of {len(p['today'])} done")
    st.markdown("### Prevent it next season")
    st.markdown("".join(f"<div class='lg-card' style='padding:12px 16px;margin-bottom:8px'>"
                        f"{ui.icon('leaf', 16, '#15803D')} {html.escape(x)}</div>" for x in p["prevent"]),
                unsafe_allow_html=True)
with right:
    st.markdown("### Treatment options to discuss with your officer")
    t_org, t_chem, t_safe = st.tabs([":material/eco: Organic / biological", ":material/science: Chemical",
                                     ":material/health_and_safety: Safe spraying"])
    with t_org:
        for name, note in p["organic"]:
            ui.card(name, f"<p style='margin:0'>{html.escape(note)}</p>", "leaf")
    with t_chem:
        for name, note in p["chemical"]:
            ui.card(name, f"<p style='margin:0'>{html.escape(note)}</p>", "flask")
        st.info(treatment.RESISTANCE_TIP, icon=":material/autorenew:")
    with t_safe:
        st.markdown("".join(f"<div style='display:flex;gap:8px;margin:8px 0'>{ui.icon('shield', 18, '#15803D')}"
                            f"<span>{html.escape(x)}</span></div>" for x in treatment.SAFETY), unsafe_allow_html=True)
    st.warning(treatment.DOSE_NOTE, icon=":material/info:")

# ---------------------------------------------------------------- weather
st.divider()
st.markdown("### Spray-weather check & 3-day disease risk")
w1, w2 = st.columns([2, 1])
place = w1.text_input("Village / town", value=st.session_state.get("lg_place", "Bengaluru"),
                      help="Used only to fetch the weather forecast (Open-Meteo, free).")
st.session_state["lg_place"] = place
check = w2.button("Check weather", icon=":material/partly_cloudy_day:", width="stretch")


@st.cache_data(ttl=1800, show_spinner=False)
def get_weather(place_name):
    loc = weather.geocode(place_name)
    if not loc:
        return None, None
    return loc, weather.forecast(loc["latitude"], loc["longitude"], days=3)


if check or st.session_state.get("lg_weather_on"):
    st.session_state["lg_weather_on"] = True
    try:
        with st.spinner("Fetching the forecast ..."):
            loc, rows = get_weather(place)
        if not loc:
            st.error(f"Couldn't find '{place}'. Try the nearest town name.", icon=":material/location_off:")
        else:
            st.caption(f"Forecast for {loc['name']}, {loc.get('admin1', '')} · weather data by "
                       f"[Open-Meteo](https://open-meteo.com) (CC BY 4.0)")
            ok, reasons, cur = weather.spray_now(rows)
            a, b = st.columns([1, 1.3], gap="medium")
            with a:
                if ok:
                    ui.verdict_card("HEALTHY", "Good time to spray now", [
                        f"{cur['temp']:.0f} °C, wind {cur['wind']:.0f} km/h, no rain expected for 4 hours."],
                        label="Spray check")
                else:
                    ui.verdict_card("UNCERTAIN", "Don't spray right now", [r.capitalize() for r in reasons],
                                    label="Spray check")
                wins = weather.spray_windows(rows)[:3]
                if wins:
                    st.markdown("**Next good spray windows**")
                    for w in wins:
                        st.markdown(ui.chip(f"{w['start'].strftime('%a %d %b, %H:%M')} – {w['end'].strftime('%H:%M')}",
                                            "good", "check_circle") + f" <span class='lg-muted'>max {w['temp']:.0f} °C, "
                                    f"wind ≤ {w['wind']:.0f} km/h</span>", unsafe_allow_html=True)
                else:
                    st.caption("No good spray window in the next 3 days (rain, wind or heat).")
            with b:
                risk = weather.disease_risk(rows, p["key"])
                tones = {"low": "good", "medium": "warn", "high": "bad"}
                cols = st.columns(len(risk), gap="small")
                for col, r in zip(cols, risk):
                    col.markdown(ui.stat(r["level"].title(), f"{r['day'].strftime('%a %d %b')} · {p['name']} risk",
                                         tones[r["level"]], "gauge") +
                                 f"<div class='lg-muted' style='font-size:.8rem;margin-top:6px'>{r['tmin']:.0f}–{r['tmax']:.0f} °C · "
                                 f"rain {r['rain_mm']} mm<br>{html.escape(r['why'])}</div>", unsafe_allow_html=True)
                st.caption("Risk = rule of thumb from extension guidance on the weather this disease likes; "
                           "not a validated forecast model.")
    except Exception as e:  # no internet, API down, ...
        st.warning(f"Weather is unavailable right now ({type(e).__name__}). It needs an internet connection. "
                   f"General rule: spray in calm, dry, cool hours with no rain due for at least 4 hours.",
                   icon=":material/cloud_off:")

# ---------------------------------------------------------------- share / speak / save
st.divider()
s1, s2, s3 = st.columns(3, gap="medium")
sev_text = None
if last and last.get("cls") == cls and last.get("severity") is not None:
    sev_text = f"{round(last['severity'])}% ({level})"
msg = share.diagnosis_message(p["name"], "Disease detected", sev_text or level, p["act_by"], p["today"], place)
with s1:
    st.markdown("**Ask an expert**")
    st.link_button("Share on WhatsApp", share.whatsapp_link(msg), icon=":material/share:", width="stretch")
    plan_txt = msg + "\n\nTreatment options:\n" + "\n".join(f"- {n}: {x}" for n, x in p["organic"] + p["chemical"]) + \
        f"\n\n{treatment.DOSE_NOTE}\n\nSafety:\n" + "\n".join(f"- {x}" for x in treatment.SAFETY)
    st.download_button("Download plan (text)", plan_txt.encode("utf-8"), "leafguard_treatment_plan.txt",
                       icon=":material/download:", width="stretch")
with s2:
    st.markdown("**Hear it in your language**")
    head, lines = farmer_message("DISEASED", cls, lang, {"percent": last["severity"], "level": level}
                                 if sev_text else None)
    components.html(browser_speak_html(head + ". " + " ".join(lines), lang, label="Speak the advice"), height=52)
    st.caption(head)
with s3:
    st.markdown("**Track it in the Field Diary**")
    plot = st.text_input("Plot name", value=st.session_state.get("lg_plot", "My field"), key="tp_plot")
    if st.button("Save this check-up", icon=":material/bookmark_add:", width="stretch",
                 disabled=not (last and last.get("verdict") == "DISEASED")):
        st.session_state["lg_plot"] = plot
        Diary(ROOT).add(plot, "DISEASED", cls, last.get("severity"), level, last.get("confidence"),
                        note=f"Plan: act by {p['act_by']}", rgb=last.get("thumb"))
        st.success("Saved to the Field Diary.", icon=":material/check_circle:")
    if not (last and last.get("verdict") == "DISEASED"):
        st.caption("Diagnose a leaf first to save it.")

with st.expander("Sources for this advice", icon=":material/menu_book:"):
    st.markdown("\n".join(f"- [{t}]({u.replace(' ', '%20')})" for t, u in treatment.SOURCES))
    st.caption("LeafGuard is a decision aid, not a prescription. Always confirm treatment and dose with your "
               "agriculture officer, KVK or the Kisan Call Centre (1800-180-1551).")
