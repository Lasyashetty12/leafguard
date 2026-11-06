"""Treatment knowledge base for the 5 diseases our model detects.

Compiled from agricultural extension sources (TNAU Agritech Portal, UC IPM, Ohio State Vegetable Crops
Hotline), see SOURCES. On purpose we give NO doses: they depend on the product, crop and region,
and a wrong dose can harm crops and people. Every chemical option says to follow the label / officer.
This is a decision aid, not a prescription.
"""

SOURCES = [
    ("TNAU Agritech: Tomato early blight", "https://agritech.tnau.ac.in/crop_protection/tomato_diseases_2.html"),
    ("TNAU Agritech: Potato late blight", "https://agritech.tnau.ac.in/crop_protection/crop_prot_crop diseases_veg_potato_1.html"),
    ("TNAU Agritech: Chilli powdery mildew", "https://agritech.tnau.ac.in/crop_protection/chilli_diseases_3.html"),
    ("TNAU Agritech: Groundnut rust", "https://agritech.tnau.ac.in/crop_protection/groundnut_diseases/groundnut_d3.html"),
    ("UC IPM: Tomato early blight", "https://ipm.ucanr.edu/agriculture/tomato/Early-Blight"),
    ("UC IPM: Tomato late blight", "https://ipm.ucanr.edu/agriculture/tomato/late-blight/"),
    ("UC IPM: Powdery mildew", "https://ipm.ucanr.edu/agriculture/floriculture-and-ornamental-nurseries/powdery-mildew/"),
    ("Ohio State VegNet: Copper and bacterial spot",
     "https://vegcropshotline.org/an-update-on-the-use-of-copper-products-for-managing-bacterial-spot-of-tomato/"),
]

DOSE_NOTE = "Dose and spray interval: follow the product label, or ask your agriculture officer / KVK."

SAFETY = [
    "Wear gloves, a mask and full sleeves while mixing and spraying.",
    "Spray in the calm early morning or evening, never against the wind.",
    "Keep children, animals and water sources away from the spray.",
    "Do not mix two products unless both labels allow it.",
    "Respect the waiting period on the label before harvesting (pre-harvest interval).",
    "Wash hands and clothes after spraying; never reuse empty pesticide containers.",
]

RESISTANCE_TIP = ("Rotate between products from different fungicide groups (the FRAC code on the label). "
                  "Do not use strobilurins (group 11, e.g. azoxystrobin) twice in a row.")

DISEASES = {
    "powdery": {
        "name": "Powdery mildew",
        "what": "A fungus that grows as white, flour-like powder on the leaf surface and slowly weakens the plant.",
        "spreads": "Spores travel by wind. Unlike most fungi it does not need wet leaves, so it spreads in dry weather too.",
        "weather": "Warm days around 20–30 °C with cool, humid nights; shade and crowded plants. Very hot leaves (above about 32 °C) slow it down.",
        "urgency": {"mild": "This week", "moderate": "Within 2–3 days", "severe": "Today"},
        "today": [
            "Pick off the worst-coated leaves, put them in a bag and destroy them (do not compost).",
            "Open up the canopy: remove crowded growth and weeds to let air move through.",
            "Check nearby plants of the same crop, since powdery mildew spreads plant to plant by wind.",
        ],
        "organic": [
            ("Wettable sulphur", "Classic organic option. Do not spray above about 32 °C (leaf burn); some crops such as melons are sensitive."),
            ("Potassium bicarbonate", "Best at the first signs; needs thorough coverage of both leaf sides."),
            ("Neem oil", "Works on existing infection. Never apply within 2 weeks of a sulphur spray; repeated sprays can scorch leaves."),
        ],
        "chemical": [
            ("Wettable sulphur", "Listed by TNAU for chilli powdery mildew; repeat sprays as per label."),
            ("Carbendazim", "Listed by TNAU; resistance is common, so rotate with other groups."),
            ("Dinocap", "Listed by TNAU for powdery mildew."),
            ("Tebuconazole / myclobutanil (group 3)", "Systemic; act on existing and new infection."),
            ("Azoxystrobin (group 11)", "Protectant with some curative action; do not use twice in a row."),
        ],
        "prevent": [
            "Grow resistant varieties where available.",
            "Give plants enough spacing and sunlight; avoid excess nitrogen fertiliser.",
            "Start checking leaves weekly once days turn warm and nights humid.",
        ],
    },
    "early": {
        "name": "Early blight",
        "what": "A fungus (Alternaria) causing brown spots with target-like rings, starting on the older, lower leaves.",
        "spreads": "Spores spread by wind and rain splash and live on in crop debris and weeds like nightshade.",
        "weather": "Warm, humid weather with rain or heavy dew for several days. Hot, dry weather stops it.",
        "urgency": {"mild": "Within 3–4 days", "moderate": "Within 2 days", "severe": "Today"},
        "today": [
            "Remove the lower, spotted leaves and destroy them away from the field.",
            "Stop overhead / sprinkler watering; water the base of the plant in the morning.",
            "Mulch the soil so rain cannot splash spores up onto leaves.",
        ],
        "organic": [
            ("Bacillus subtilis biofungicide", "Biological, approved for organic use; start early and repeat as per label."),
            ("Trichoderma (seed / soil treatment)", "TNAU lists Trichoderma asperellum for seed treatment against early blight."),
            ("Fixed copper", "Contact protectant; only some copper products are approved for organic use, so check the label."),
        ],
        "chemical": [
            ("Mancozeb (group M3)", "Multi-site protectant listed by TNAU and UC IPM."),
            ("Chlorothalonil (group M5)", "Multi-site protectant ranked highly by UC IPM."),
            ("Azoxystrobin + difenoconazole", "Combination listed by TNAU; do not repeat group 11 back-to-back."),
            ("Metiram + pyraclostrobin / tebuconazole + trifloxystrobin", "Combinations listed by TNAU."),
        ],
        "prevent": [
            "Rotate crops: avoid tomato/potato in the same plot for 2–3 seasons.",
            "Clear crop debris and nightshade weeds after harvest.",
            "Stake plants and keep lower leaves off the soil.",
        ],
    },
    "late": {
        "name": "Late blight",
        "what": "A fast, destructive water-mould disease: dark, greasy-looking patches that can kill leaves and stems within days.",
        "spreads": "Spores fly on the wind to nearby fields. Under the right weather a whole field can collapse in about a week.",
        "weather": "Cool-to-mild temperatures (about 15–25 °C) with humidity above 90% for 10+ hours, rain, fog or overhead irrigation.",
        "urgency": {"mild": "Today", "moderate": "Today: act immediately", "severe": "Today: act immediately"},
        "today": [
            "Remove and destroy every infected leaf; uproot and bag badly infected plants.",
            "Tell neighbouring farmers: late blight spreads across fields on the wind.",
            "Stop sprinkler irrigation and avoid working in the field while plants are wet.",
            "Contact your agriculture officer / KVK today. Late blight needs fast, expert-guided spraying.",
        ],
        "organic": [
            ("Copper-based protectant", "Can slow spread on healthy leaves but cannot cure infected ones."),
            ("Remove infected plants", "In organic systems, fast removal is the most important control."),
        ],
        "chemical": [
            ("Mancozeb / zineb (protectant)", "TNAU lists protective sprays to stop new infection."),
            ("Cymoxanil + famoxadone", "Listed by UC IPM; has some curative action."),
            ("Dimethomorph (group 40)", "Listed by UC IPM."),
            ("Metalaxyl / mefenoxam", "Resistant strains are widespread in some regions; ask your officer if it still works locally."),
        ],
        "prevent": [
            "Use certified, disease-free seed potatoes / transplants.",
            "Grow tolerant varieties where available (e.g. TNAU lists Kufri Naveen, Kufri Jeevan for potato).",
            "Remove volunteer tomato/potato plants and nightshade weeds.",
            "Start protective sprays before the cool, foggy season if late blight comes every year.",
        ],
    },
    "bacterial": {
        "name": "Bacterial spot",
        "what": "A bacterial disease causing small, dark, water-soaked spots on leaves and fruit.",
        "spreads": "Spread by water splash, infected seed and transplants, hands and tools.",
        "weather": "Warm, wet weather; rain and overhead irrigation spread it fast.",
        "urgency": {"mild": "Within 2–3 days", "moderate": "Within 2 days", "severe": "Today"},
        "today": [
            "Do not touch or work among plants while they are wet.",
            "Switch to drip or base watering; never water in the evening.",
            "Remove badly spotted leaves and disinfect tools and hands afterwards.",
        ],
        "organic": [
            ("Fixed copper", "The main option, but copper alone does not control bacterial spot and resistance is spreading."),
            ("Bacillus subtilis biological", "Works independently of copper resistance; approved for organic use."),
        ],
        "chemical": [
            ("Copper + mancozeb (tank mix)", "Mancozeb improves how well copper works on the leaf; follow both labels."),
            ("Acibenzolar-S-methyl (plant defence activator)", "Boosts the plant's own defences; can reduce yield in drought-stressed plants."),
        ],
        "prevent": [
            "Use tested, disease-free seed and transplants.",
            "Rotate crops; strongly recommended for bacterial spot.",
            "Do not grow different varieties together in the nursery; sanitise nursery trays.",
        ],
    },
    "rust": {
        "name": "Rust",
        "what": "A fungus forming orange-brown, powdery pustules (blisters), usually on the underside of leaves.",
        "spreads": "Rust spores are carried long distances by wind.",
        "weather": "Moderate temperatures with long periods of dew or high humidity.",
        "urgency": {"mild": "This week", "moderate": "Within 2–3 days", "severe": "Today"},
        "today": [
            "Remove and destroy leaves with many pustules.",
            "Avoid overhead watering and evening irrigation so leaves dry quickly.",
            "Check the undersides of leaves on nearby plants.",
        ],
        "organic": [
            ("Wettable sulphur", "Listed by TNAU for groundnut rust; avoid spraying in very hot weather."),
        ],
        "chemical": [
            ("Mancozeb", "Listed by TNAU for groundnut rust."),
            ("Chlorothalonil", "Listed by TNAU for groundnut rust."),
            ("Tridemorph", "Listed by TNAU for groundnut rust."),
        ],
        "prevent": [
            "Grow rust-resistant varieties; ask your KVK which suit your area.",
            "Remove volunteer plants and weeds that host rust between seasons.",
            "Avoid very dense planting.",
        ],
    },
}


def key_for(class_name):
    name = (class_name or "").lower()
    for k in DISEASES:
        if k in name:
            return k
    return None


def plan(class_name, severity_level=None):
    """Return the treatment plan dict for a model class name (None if unknown)."""
    k = key_for(class_name)
    if not k:
        return None
    d = dict(DISEASES[k])
    level = severity_level or "moderate"
    d["act_by"] = d["urgency"].get(level, d["urgency"]["moderate"])
    d["key"] = k
    d["level"] = severity_level
    return d
