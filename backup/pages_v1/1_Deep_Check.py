"""Deep Check: diagnosis + self-doubt test + 'what would change my mind?' + severity + local language & voice."""
import os
import sys

import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from leafguard_plus import counterfactual, report, severity, stability  # noqa: E402
from leafguard_plus.i18n import LANGS, disease_name, farmer_message  # noqa: E402
from leafguard_plus.shared import CSS, card, get_guard, photo_input  # noqa: E402
from leafguard_plus.voice import browser_speak_html, tts_mp3  # noqa: E402

st.set_page_config(page_title="LeafGuard · Deep Check", page_icon="🔬", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def speech(text, lang):
    return tts_mp3(text, lang)


guard = get_guard()
st.title("🔬 Deep Check")
st.caption("Diagnosis that doubts itself, proves itself, measures severity and speaks the farmer's language.")

c1, c2, c3, c4 = st.columns([1.4, 1, 1, 1])
lang_name = c1.selectbox("Language for the farmer", list(LANGS), index=0)
lang = LANGS[lang_name]
do_stab = c2.toggle("Self-doubt test", value=True, help="Re-check 8 changed copies of the photo")
do_cf = c3.toggle("Proof test", value=True, help="What would change my mind?")
do_voice = c4.toggle("Speak result", value=True)

rgb = photo_input("deep")
if rgb is None:
    st.stop()

with st.spinner("Checking photo, finding leaf, asking the model ..."):
    r = guard.analyze(rgb)
stab = sev = cf = None
if do_stab and r["verdict"] in ("HEALTHY", "DISEASED"):
    with st.spinner("Self-doubt test: re-checking 8 changed copies ..."):
        stab = stability.self_doubt_test(guard, rgb, r)
final = stab["adjusted_verdict"] if stab else r["verdict"]
sev = severity.estimate(rgb, r, guard.th) if final == "DISEASED" else None
if do_cf and final == "DISEASED":
    with st.spinner("Proof test ..."):
        cf = counterfactual.what_would_change_my_mind(guard, rgb, r, sev)

# ---------------------------------------------------------------- the answer
headline, lines = farmer_message(final, r.get("cls"), lang, sev)
extra = []
if stab and not stab["stable"] and r["verdict"] in ("HEALTHY", "DISEASED"):
    extra.append(f"Self-doubt test: only {stab['n_agree']} of {stab['n']} re-checks agreed, "
                 f"so the answer was downgraded to 'not sure'.")
if final in ("RETAKE", "NOT_A_LEAF", "UNCERTAIN"):
    extra += r["reasons"][:2]
left, right = st.columns([1.3, 1])
with left:
    card(final, headline, lines + [f"<span class='small'>{x}</span>" for x in extra])
    if do_voice:
        say = headline + ". " + " ".join(lines)
        mp3 = speech(say, lang)
        if mp3:
            st.audio(mp3, format="audio/mp3")
        components.html(browser_speak_html(say, lang), height=48)
        if lang != "en":
            st.caption("Translations were written for this demo. Have a native speaker review them before real use.")
with right:
    st.image(r["images"].get("heatmap", rgb), caption="Where the disease was found" if "heatmap" in r["images"]
             else "Your photo", width="stretch")

# ---------------------------------------------------------------- the proof
tabs = st.tabs(["🔁 Self-doubt test", "🧪 What would change my mind?", "📏 Severity", "✅ Safety checks", "📄 Report"])

with tabs[0]:
    if not stab:
        st.info("Runs when LeafGuard gives a diagnosis (Healthy / Disease).")
    else:
        colour = "#2e7d32" if stab["stable"] else "#c62828"
        st.markdown(f"<span class='big' style='color:{colour}'>{stab['n_agree']}/{stab['n']}</span> "
                    f"re-checks agree with the answer · "
                    f"<b>{'Stable ✅' if stab['stable'] else 'Unstable ⚠️ → downgraded to Not sure'}</b>",
                    unsafe_allow_html=True)
        st.caption("A real disease does not disappear when you tilt the phone or the light changes. "
                   "If the answer flips, the model was guessing.")
        cols = st.columns(4)
        for k, v in enumerate(stab["variants"]):
            label = "No disease" if v["verdict"] == "HEALTHY" else (
                disease_name(v["cls"], "en") if v["verdict"] == "DISEASED" else v["verdict"].replace("_", " ").title())
            conf = f" {round(v['confidence'] * 100)}%" if v["verdict"] == "DISEASED" and v["confidence"] else ""
            cols[k % 4].image(v["image"], caption=f"{'✅' if v['agrees'] else '❌'} {v['name']}: {label}{conf}",
                              width="stretch")

with tabs[1]:
    if not cf:
        st.info("Runs when a disease is detected.")
    else:
        icon = {"proven": "✅ Proven", "mostly": "🟡 Mostly proven", "not_proven": "⚠️ Not proven"}[cf["status"]]
        st.subheader(icon)
        st.write(cf["message"])
        cols = st.columns(len(cf["tests"]) + 1)
        cols[0].image(r["images"].get("heatmap", rgb), caption=f"Original: {disease_name(cf['before']['cls'], 'en')} "
                      f"{round((cf['before']['confidence'] or 0) * 100)}%", width="stretch")
        for col, t in zip(cols[1:], cf["tests"]):
            said = "no disease" if t["verdict"] == "HEALTHY" else (
                disease_name(t["cls"], "en") if t["verdict"] == "DISEASED" else t["verdict"].lower())
            col.image(t["image"], caption=f"{'✅' if t['passed'] else '❌'} {t['name']}: model says {said} "
                      f"(expected: {t['expect']})", width="stretch")

with tabs[2]:
    if not sev:
        st.info("Runs when a disease is detected.")
    else:
        a, b = st.columns([1, 1.4])
        a.markdown(f"<span class='big'>{round(sev['percent'])}%</span> of the leaf affected", unsafe_allow_html=True)
        a.progress(min(sev["percent"] / 100, 1.0))
        a.markdown(f"**Severity: {sev['level'].upper()}**  \nMeasured as: {sev['method']}.")
        a.caption("Mild < 15% · Moderate 15–45% · Severe > 45%" if guard.is_detector
                  else "Mild < 5% · Moderate 5–25% · Severe > 25%")
        b.image(sev["overlay"], caption="Red = affected area, green outline = the leaf", width="stretch")

with tabs[3]:
    for c in r["checks"]:
        st.markdown(f"{'✅' if c['passed'] else '❌'} **{c['name']}** <span class='small'>({c['value']})</span>",
                    unsafe_allow_html=True)
    st.caption(f"Raw model alone would have said: {r['baseline']['label']}")

with tabs[4]:
    page = report.build(rgb, r, final, lang, sev, stab, cf)
    st.download_button("⬇️ Download diagnosis report (HTML, open in any browser and print)", page.encode("utf-8"),
                       file_name="leafguard_report.html", mime="text/html")
    st.caption("The farmer can show this to an agriculture officer or save it as PDF from the browser.")
