"""Deep Check: diagnosis + self-doubt test + 'what would change my mind?' + severity + local language & voice."""
import os
import sys

import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from leafguard_plus import counterfactual, report, severity, stability, ui  # noqa: E402
from leafguard_plus.i18n import LANGS, disease_name, farmer_message  # noqa: E402
from leafguard_plus.shared import get_guard, photo_input, remember_diagnosis, setup_page  # noqa: E402
from leafguard_plus.voice import browser_speak_html, tts_mp3  # noqa: E402

setup_page("Deep Check", ":material/biotech:")


@st.cache_data(show_spinner=False)
def speech(text, lang):
    return tts_mp3(text, lang)


def said(v):
    if v["verdict"] == "HEALTHY":
        return "No disease"
    if v["verdict"] == "DISEASED":
        return disease_name(v["cls"], "en")
    return ui.STATUS[v["verdict"]][0]


guard = get_guard()
ui.header("Deep Check", "A diagnosis that doubts itself, proves itself, measures severity and speaks the "
          "farmer's language.", "flask", eyebrow="Explainable diagnosis")

c1, c2, c3, c4 = st.columns([1.4, 1, 1, 1])
lang_name = c1.selectbox("Language for the farmer", list(LANGS), index=0)
lang = LANGS[lang_name]
do_stab = c2.toggle("Self-doubt test", value=True, help="Re-check 8 changed copies of the photo")
do_cf = c3.toggle("Proof test", value=True, help="What would change my mind?")
do_voice = c4.toggle("Speak result", value=True)

rgb = photo_input("deep")
if rgb is None:
    st.stop()

with st.status("Running the deep check ...", expanded=False) as status_box:
    st.write("Checking photo, finding the leaf, asking the model ...")
    r = guard.analyze(rgb)
    stab = sev = cf = None
    if do_stab and r["verdict"] in ("HEALTHY", "DISEASED"):
        st.write("Self-doubt test: re-checking 8 changed copies ...")
        stab = stability.self_doubt_test(guard, rgb, r)
    final = stab["adjusted_verdict"] if stab else r["verdict"]
    if final == "DISEASED":
        st.write("Measuring severity ...")
        sev = severity.estimate(rgb, r, guard.th)
        if do_cf:
            st.write("Proof test: hiding the spots ...")
            cf = counterfactual.what_would_change_my_mind(guard, rgb, r, sev)
    status_box.update(label="Deep check complete", state="complete")
remember_diagnosis(r, rgb, sev, verdict=final)

ui.pipeline_steps(dict(r, verdict=final))

# ---------------------------------------------------------------- the answer
headline, lines = farmer_message(final, r.get("cls"), lang, sev)
notes = []
if stab and not stab["stable"] and r["verdict"] in ("HEALTHY", "DISEASED"):
    notes.append(f"Self-doubt test: only {stab['n_agree']} of {stab['n']} re-checks agreed, "
                 f"so the answer was downgraded to 'not sure'.")
if final in ("RETAKE", "NOT_A_LEAF", "UNCERTAIN"):
    notes += r["reasons"][:2]

left, right = st.columns([1.25, 1], gap="medium")
with left:
    ui.verdict_card(final, headline, lines, footnotes=notes)
    proof_chips = []
    if stab:
        proof_chips.append(ui.chip(f"{stab['n_agree']}/{stab['n']} re-checks agree", "good" if stab["stable"] else "bad",
                                   "repeat"))
    if cf:
        proof_chips.append(ui.chip({"proven": "Cause proven", "mostly": "Cause mostly proven",
                                    "not_proven": "Cause not proven"}[cf["status"]],
                                   {"proven": "good", "mostly": "warn", "not_proven": "bad"}[cf["status"]], "flask"))
    if sev and sev.get("level"):
        proof_chips.append(ui.chip(f"{round(sev['percent'])}% affected · {sev['level']}",
                                   {"mild": "good", "moderate": "warn", "severe": "bad"}[sev["level"]], "gauge"))
    if proof_chips:
        st.markdown(" ".join(proof_chips), unsafe_allow_html=True)
    if final == "DISEASED":
        ui.link("pages/4_Treatment_Plan.py", "Get the treatment plan & spray-weather check",
                     icon=":material/healing:")
    if do_voice:
        st.markdown(f"<div style='margin-top:12px;font-weight:600'>{ui.icon('volume', 18, '#15803D')} "
                    f"Listen to the result</div>", unsafe_allow_html=True)
        say = headline + ". " + " ".join(lines)
        mp3 = speech(say, lang)
        if mp3:
            st.audio(mp3, format="audio/mp3")
        components.html(browser_speak_html(say, lang, label="Speak with this computer's voice"), height=48)
        if lang != "en":
            st.caption("Translations were written for this demo. Have a native speaker review them before real use.")
with right:
    st.image(r["images"].get("heatmap", rgb), caption="Where the disease was found" if "heatmap" in r["images"]
             else "Your photo", width="stretch")

# ---------------------------------------------------------------- the proof
tabs = st.tabs([":material/repeat: Self-doubt test", ":material/science: What would change my mind?",
                ":material/speed: Severity", ":material/checklist: Safety checks", ":material/description: Report"])

with tabs[0]:
    if not stab:
        st.info("Runs when LeafGuard gives a diagnosis (no disease / disease).")
    else:
        tone = "good" if stab["stable"] else "bad"
        a, b = st.columns([1, 3])
        a.markdown(ui.stat(f"{stab['n_agree']}/{stab['n']}", "re-checks agree", tone, "repeat"), unsafe_allow_html=True)
        b.markdown(f"<div class='lg-card'><h3>{'Stable answer' if stab['stable'] else 'Unstable answer, downgraded to Not sure'}"
                   f"</h3><p style='margin:0'>A real disease does not disappear when you tilt the phone or the light "
                   f"changes. If the answer flips, the model was guessing, so LeafGuard refuses to answer.</p></div>",
                   unsafe_allow_html=True)
        cols = st.columns(4, gap="small")
        for k, v in enumerate(stab["variants"]):
            conf = f" {round(v['confidence'] * 100)}%" if v["verdict"] == "DISEASED" and v["confidence"] else ""
            cols[k % 4].image(v["image"], caption=f"{'Agrees' if v['agrees'] else 'DISAGREES'} · {v['name']}: "
                              f"{said(v)}{conf}", width="stretch")

with tabs[1]:
    if not cf:
        st.info("Runs when a disease is detected.")
    else:
        tone = {"proven": "good", "mostly": "warn", "not_proven": "bad"}[cf["status"]]
        title = {"proven": "Proven: the spots caused the diagnosis", "mostly": "Mostly proven",
                 "not_proven": "Not proven, treat this answer with care"}[cf["status"]]
        st.markdown(f"<div class='lg-card'><h3>{ui.chip(title, tone, 'flask')}</h3><p style='margin:0'>{cf['message']}</p>"
                    f"</div>", unsafe_allow_html=True)
        cols = st.columns(len(cf["tests"]) + 1, gap="small")
        cols[0].image(r["images"].get("heatmap", rgb), caption=f"Original: {disease_name(cf['before']['cls'], 'en')} "
                      f"{round((cf['before']['confidence'] or 0) * 100)}%", width="stretch")
        for col, t in zip(cols[1:], cf["tests"]):
            col.image(t["image"], caption=f"{'PASS' if t['passed'] else 'FAIL'} · {t['name']}: model says "
                      f"{said(t).lower()} (expected: {t['expect']})", width="stretch")

with tabs[2]:
    if not sev:
        st.info("Runs when a disease is detected.")
    else:
        a, b = st.columns([1, 1.4], gap="medium")
        tone = {"mild": "good", "moderate": "warn", "severe": "bad"}[sev["level"]]
        a.markdown(ui.stat(f"{round(sev['percent'])}%", f"of the leaf affected · {sev['level']}", tone, "gauge"),
                   unsafe_allow_html=True)
        a.progress(min(sev["percent"] / 100, 1.0))
        a.caption(f"Measured as: {sev['method']}. " + ("Mild < 15% · Moderate 15–45% · Severe > 45%" if guard.is_detector
                                                      else "Mild < 5% · Moderate 5–25% · Severe > 25%"))
        b.image(sev["overlay"], caption="Red = affected area, green outline = the leaf", width="stretch")

with tabs[3]:
    ui.checks_list(r["checks"])
    st.caption(f"Raw model alone would have said: {r['baseline']['label']}")

with tabs[4]:
    page = report.build(rgb, r, final, lang, sev, stab, cf)
    st.download_button("Download diagnosis report (opens in any browser, printable)", page.encode("utf-8"),
                       file_name="leafguard_report.html", mime="text/html", icon=":material/download:")
    st.caption("The farmer can show this to an agriculture officer or save it as PDF from the browser.")
