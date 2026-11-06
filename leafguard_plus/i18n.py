"""Farmer-friendly messages in English, Kannada and Hindi.

NOTE: translations were written for this demo - ask a native speaker to review them before real use.
"""

LANGS = {"English": "en", "ಕನ್ನಡ (Kannada)": "kn", "हिन्दी (Hindi)": "hi"}
KCC = "1800-180-1551"  # Kisan Call Centre, Government of India, toll-free

HEADLINE = {
    "RETAKE": {"en": "Please retake the photo",
               "kn": "ದಯವಿಟ್ಟು ಫೋಟೋವನ್ನು ಮತ್ತೆ ತೆಗೆಯಿರಿ",
               "hi": "कृपया फोटो दोबारा लें"},
    "NOT_A_LEAF": {"en": "This doesn't look like a leaf",
                   "kn": "ಇದು ಎಲೆಯಂತೆ ಕಾಣುತ್ತಿಲ್ಲ",
                   "hi": "यह पत्ता नहीं लगता"},
    "UNCERTAIN": {"en": "Not sure. Please get a second opinion",
                  "kn": "ಖಚಿತವಾಗಿ ಹೇಳಲು ಆಗುತ್ತಿಲ್ಲ. ದಯವಿಟ್ಟು ತಜ್ಞರನ್ನು ಕೇಳಿ",
                  "hi": "पक्का नहीं कह सकते। कृपया किसी विशेषज्ञ से पूछें"},
    "HEALTHY": {"en": "The leaf looks healthy",
                "kn": "ಎಲೆ ಆರೋಗ್ಯವಾಗಿ ಕಾಣುತ್ತದೆ",
                "hi": "पत्ता स्वस्थ दिखता है"},
    "DISEASED": {"en": "Disease found: {disease}",
                 "kn": "ರೋಗ ಕಂಡುಬಂದಿದೆ: {disease}",
                 "hi": "रोग मिला: {disease}"},
}

# keyword in the class name -> local name (English kept in brackets so nothing is lost)
DISEASES = [
    ("powdery", {"en": "Powdery mildew", "kn": "ಬೂದಿ ರೋಗ (Powdery mildew)", "hi": "चूर्णिल आसिता (Powdery mildew)"}),
    ("early", {"en": "Early blight", "kn": "ಆರಂಭಿಕ ಅಂಗಮಾರಿ ರೋಗ (Early blight)", "hi": "अगेती झुलसा (Early blight)"}),
    ("late", {"en": "Late blight", "kn": "ತಡವಾದ ಅಂಗಮಾರಿ ರೋಗ (Late blight)", "hi": "पछेती झुलसा (Late blight)"}),
    ("bacterial", {"en": "Bacterial spot", "kn": "ಬ್ಯಾಕ್ಟೀರಿಯಾ ಚುಕ್ಕೆ ರೋಗ (Bacterial spot)", "hi": "बैक्टीरियल धब्बा रोग (Bacterial spot)"}),
    ("rust", {"en": "Rust", "kn": "ತುಕ್ಕು ರೋಗ (Rust)", "hi": "रतुआ रोग (Rust)"}),
]

TIPS = {
    "powdery": {"en": "Improve air flow between plants and avoid crowding.",
                "kn": "ಗಿಡಗಳ ನಡುವೆ ಗಾಳಿ ಓಡಾಡುವಂತೆ ಅಂತರ ಇಡಿ.",
                "hi": "पौधों के बीच हवा का संचार बढ़ाएँ और भीड़ से बचें।"},
    "early": {"en": "Remove lower infected leaves and fallen plant waste.",
              "kn": "ಕೆಳಗಿನ ಸೋಂಕಿತ ಎಲೆಗಳು ಮತ್ತು ಬಿದ್ದ ಕಸವನ್ನು ತೆಗೆಯಿರಿ.",
              "hi": "नीचे की संक्रमित पत्तियाँ और गिरा हुआ कचरा हटाएँ।"},
    "late": {"en": "It spreads fast in cool, wet weather. Act today.",
             "kn": "ತಂಪಾದ, ತೇವದ ಹವಾಮಾನದಲ್ಲಿ ಇದು ವೇಗವಾಗಿ ಹರಡುತ್ತದೆ. ಇಂದೇ ಕ್ರಮ ಕೈಗೊಳ್ಳಿ.",
             "hi": "ठंडे और नम मौसम में यह तेज़ी से फैलता है। आज ही कदम उठाएँ।"},
    "bacterial": {"en": "Don't work with the plants while they are wet, and clean your tools.",
                  "kn": "ಗಿಡಗಳು ಒದ್ದೆಯಾಗಿರುವಾಗ ಕೆಲಸ ಮಾಡಬೇಡಿ; ಉಪಕರಣಗಳನ್ನು ಸ್ವಚ್ಛಗೊಳಿಸಿ.",
                  "hi": "पौधे गीले हों तब उन्हें न छुएँ; औज़ारों को साफ़ करें।"},
    "rust": {"en": "Remove leaves with orange-brown pustules early.",
             "kn": "ಕಿತ್ತಳೆ-ಕಂದು ಗುಳ್ಳೆಗಳಿರುವ ಎಲೆಗಳನ್ನು ಬೇಗ ತೆಗೆಯಿರಿ.",
             "hi": "नारंगी-भूरे दानों वाली पत्तियों को जल्दी हटाएँ।"},
}

GENERAL_DISEASE = {
    "en": f"Remove and destroy badly affected leaves. Avoid watering on the leaves. Before using any spray, "
          f"ask your local agriculture officer or call Kisan Call Centre {KCC} (free).",
    "kn": f"ಹೆಚ್ಚು ಬಾಧಿತ ಎಲೆಗಳನ್ನು ತೆಗೆದು ನಾಶಪಡಿಸಿ. ಎಲೆಗಳ ಮೇಲೆ ನೀರು ಹಾಕಬೇಡಿ. ಯಾವುದೇ ಔಷಧಿ ಸಿಂಪಡಿಸುವ ಮೊದಲು "
          f"ಸ್ಥಳೀಯ ಕೃಷಿ ಅಧಿಕಾರಿಯನ್ನು ಸಂಪರ್ಕಿಸಿ ಅಥವಾ ಕಿಸಾನ್ ಕಾಲ್ ಸೆಂಟರ್ {KCC} (ಉಚಿತ) ಗೆ ಕರೆ ಮಾಡಿ.",
    "hi": f"बुरी तरह प्रभावित पत्तियों को हटाकर नष्ट करें। पत्तियों पर पानी न डालें। कोई भी दवा छिड़कने से पहले "
          f"स्थानीय कृषि अधिकारी से सलाह लें या किसान कॉल सेंटर {KCC} (निःशुल्क) पर कॉल करें।",
}

OTHER_ADVICE = {
    "RETAKE": {"en": "Hold the phone steady, in daylight, with one leaf filling the screen.",
               "kn": "ಫೋನ್ ಅನ್ನು ಸ್ಥಿರವಾಗಿ ಹಿಡಿಯಿರಿ, ಹಗಲು ಬೆಳಕಿನಲ್ಲಿ, ಒಂದು ಎಲೆ ಪರದೆಯನ್ನು ತುಂಬುವಂತೆ.",
               "hi": "फ़ोन को स्थिर रखें, दिन की रोशनी में, एक पत्ता पूरी स्क्रीन में हो।"},
    "NOT_A_LEAF": {"en": "Please photograph one plant leaf.",
                   "kn": "ದಯವಿಟ್ಟು ಗಿಡದ ಒಂದು ಎಲೆಯ ಫೋಟೋ ತೆಗೆಯಿರಿ.",
                   "hi": "कृपया पौधे के एक पत्ते की फोटो लें।"},
    "UNCERTAIN": {"en": f"Call Kisan Call Centre {KCC} (free) or show the leaf to your agriculture officer.",
                  "kn": f"ಕಿಸಾನ್ ಕಾಲ್ ಸೆಂಟರ್ {KCC} (ಉಚಿತ) ಗೆ ಕರೆ ಮಾಡಿ ಅಥವಾ ಎಲೆಯನ್ನು ನಿಮ್ಮ ಕೃಷಿ ಅಧಿಕಾರಿಗೆ ತೋರಿಸಿ.",
                  "hi": f"किसान कॉल सेंटर {KCC} (निःशुल्क) पर कॉल करें या पत्ता अपने कृषि अधिकारी को दिखाएँ।"},
    "HEALTHY": {"en": "Keep checking your plants every few days.",
                "kn": "ಕೆಲವು ದಿನಗಳಿಗೊಮ್ಮೆ ಗಿಡಗಳನ್ನು ಪರಿಶೀಲಿಸುತ್ತಿರಿ.",
                "hi": "हर कुछ दिनों में पौधों की जाँच करते रहें।"},
}

SEVERITY_LEVEL = {"mild": {"en": "mild", "kn": "ಸೌಮ್ಯ", "hi": "हल्का"},
                  "moderate": {"en": "moderate", "kn": "ಮಧ್ಯಮ", "hi": "मध्यम"},
                  "severe": {"en": "severe", "kn": "ತೀವ್ರ", "hi": "गंभीर"}}
SEVERITY_LINE = {"en": "About {pct}% of the leaf is affected ({level}).",
                 "kn": "ಎಲೆಯ ಸುಮಾರು {pct}% ಭಾಗ ಬಾಧಿತವಾಗಿದೆ ({level}).",
                 "hi": "पत्ते का लगभग {pct}% हिस्सा प्रभावित है ({level})।"}


def disease_key(class_name):
    name = (class_name or "").lower()
    for key, _ in DISEASES:
        if key in name:
            return key
    return None


def disease_name(class_name, lang):
    key = disease_key(class_name)
    for k, names in DISEASES:
        if k == key:
            return names[lang]
    return (class_name or "").replace("___", " - ").replace("_", " ")


def farmer_message(verdict, class_name, lang, severity=None):
    """Returns (headline, [advice lines]) in the chosen language."""
    head = HEADLINE[verdict][lang].format(disease=disease_name(class_name, lang))
    lines = []
    if verdict == "DISEASED":
        if severity and severity.get("level"):
            lines.append(SEVERITY_LINE[lang].format(pct=round(severity["percent"]),
                                                    level=SEVERITY_LEVEL[severity["level"]][lang]))
        key = disease_key(class_name)
        if key in TIPS:
            lines.append(TIPS[key][lang])
        lines.append(GENERAL_DISEASE[lang])
    else:
        lines.append(OTHER_ADVICE[verdict][lang])
    return head, lines
