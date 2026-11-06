# LeafGuard+ : the innovation features

These were added as **new pages and files only**. The original `app.py` and `leafguard/` code are unchanged.
Run the app as usual (`streamlit run app.py`). The new pages appear in the **sidebar**.

## 🔬 Deep Check (`pages/1_Deep_Check.py`)

| Feature | What it does | Why judges care |
|---|---|---|
| **Self-doubt test** | Re-checks 8 changed copies of the photo (mirror, flip, ±15° tilt, brighter, darker, zoom, WhatsApp-style compression). If fewer than 6 of 8 agree, the answer is downgraded to "Not sure". | A real disease doesn't vanish when you tilt the phone. Shows the model *doubting itself* before answering. |
| **What would change my mind?** | Two control experiments: **hide the detected spots** (the disease should disappear) and **hide everything except the spots** (it should still be found). Says honestly if the proof fails. | Answers "prove why" with a causal test, not just a heatmap. |
| **Severity** | % of the leaf inside the model's disease regions → mild / moderate / severe. | Turns a label into an action level. |
| **Farmer language + voice** | Result and safe advice in **English, ಕನ್ನಡ, हिन्दी**, spoken aloud (gTTS online; browser voice offline). Includes Kisan Call Centre **1800-180-1551** (free). | Real-world impact for farmers who can't read English. |
| **Diagnosis report** | One-page HTML report (photo, boxes, severity, checks, advice) to save, print or show an officer. | Practical, shareable output. |

## 🎯 Fool Me Arena (`pages/2_Fool_Me_Arena.py`)

Judges try to trick the system live. They say what they are really showing (not a leaf / bad photo / healthy / diseased), take a photo, and both models are scored:

- ✅ **Correct**
- 🛡️ **Safely refused** (said retake / not sure / not a leaf: no harm done)
- ❌ **Fooled** (confident and wrong)

A live scoreboard compares "times the raw model was fooled" vs "times LeafGuard was fooled", with a gallery of every attempt. Data is saved in `reports/arena/` (not pushed to GitHub). Reset it from the page.

**Demo tip:** invite every judge to try one trick. Their skepticism becomes your proof.

## 📡 Live Camera (`pages/3_Live_Camera.py`)

Works with the ESP32-CAM stream (`http://<camera IP>:81/stream`), the laptop webcam (`0`) or a video file.

- 🔴 **Red:** photo problem (blurry, dark, glare, finger, lens covered), with the fix shown on screen
- 🟡 **Yellow:** no leaf / leaf too small ("point at a leaf", "move closer")
- 🟢 **Green:** good shot. After N steady green frames it **diagnoses automatically**, once per leaf.

The laptop and the ESP32-CAM must be on the same Wi-Fi / hotspot.

## Install

```powershell
.venv\Scripts\activate
python -m pip install -r requirements-plus.txt
streamlit run app.py
```

## New files

```
FEATURES.md, requirements-plus.txt
pages/1_Deep_Check.py, pages/2_Fool_Me_Arena.py, pages/3_Live_Camera.py
leafguard_plus/  stability.py  counterfactual.py  severity.py  decide.py
                 i18n.py  voice.py  arena.py  live.py  report.py  shared.py
```

Translations were written for this demo. Ask a native Kannada / Hindi speaker to review them before real use.

---

# Round 2: from diagnosis to action

## 🩹 Treatment Plan (`pages/4_Treatment_Plan.py`)

Opens automatically with the disease and severity from your last diagnosis.

- **Act-by urgency** from disease and severity (late blight is always "today").
- **Do this today:** a tick-off checklist with a progress bar.
- **Treatment options to discuss with your officer:** organic/biological and chemical active ingredients, plus a safe-spraying checklist and fungicide-rotation tip.
- **No doses on purpose:** "follow the label or ask your officer / KVK". Doses vary by product, crop and region.
- **Spray-weather check:** is it OK to spray now (wind, heat, rain in the next 4 h)? It also lists the next good spray windows.
- **3-day disease-risk forecast** for the detected disease, from weather rules of thumb (e.g. late blight after ~10 h of >90% humidity at mild temperatures). Weather comes from Open-Meteo (free, no key, needs internet).
- **Share on WhatsApp** with an agriculture officer, **download the plan**, **hear it** in Kannada/Hindi/English, **save to the Field Diary**.
- Sources: TNAU Agritech, UC IPM, Ohio State VegNet (listed on the page).

## 🗺️ Field Scan (`pages/5_Field_Scan.py`)

Upload 10–30 photos from one field and get:

- a field health score and the % of plants diseased
- a breakdown of the photos
- one decision for the whole field:
  - **Treat the whole field** (≥ 20% diseased)
  - **Spot-treat** (5–20%)
  - **Keep monitoring**
  - **Retake photos** (too few usable)

It links to the treatment plan for the most common disease. Export the results as CSV or save them to the diary.

## 📔 Field Diary (`pages/6_Field_Diary.py`)

Every check-up per plot, with a severity chart over time and a trend verdict: *Improving / Steady / Getting worse* ("is the treatment working?"). Includes notes, photos, delete and CSV export. Stored in `reports/diary/` (not pushed to GitHub).
