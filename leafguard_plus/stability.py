"""Self-doubt test: "Would I say the same thing again?"

Before trusting an answer, LeafGuard re-checks the photo 8 times with harmless changes
(mirror, rotate, brighter, darker, zoom, phone compression). A real disease does not
disappear when you tilt the phone. If the answer flips, the model was guessing -> "Not sure".
"""
import cv2
import numpy as np

from .decide import quick_decision, same_answer


def _rotate(img, angle):
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)


def _zoom(img, f=0.85):
    h, w = img.shape[:2]
    dh, dw = int(h * (1 - f) / 2), int(w * (1 - f) / 2)
    return cv2.resize(img[dh:h - dh, dw:w - dw], (w, h))


def _jpeg(img, q=30):
    ok, buf = cv2.imencode(".jpg", cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, q])
    return cv2.cvtColor(cv2.imdecode(buf, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)


def _gain(img, g):
    return np.clip(img.astype(np.float32) * g, 0, 255).astype(np.uint8)


VARIANTS = [
    ("Mirror", lambda im: im[:, ::-1].copy()),
    ("Upside down", lambda im: im[::-1].copy()),
    ("Tilt +15°", lambda im: _rotate(im, 15)),
    ("Tilt -15°", lambda im: _rotate(im, -15)),
    ("Brighter", lambda im: _gain(im, 1.2)),
    ("Darker", lambda im: _gain(im, 0.8)),
    ("Zoom in", _zoom),
    ("WhatsApp-style compression", _jpeg),
]


def self_doubt_test(guard, rgb, base, min_agreement=0.75, max_side=900):
    """base = the result of guard.analyze(rgb). Returns a dict with per-variant results and the
    adjusted verdict (DISEASED/HEALTHY is downgraded to UNCERTAIN if the answer is unstable)."""
    from leafguard.quality_gate import resize_max

    img = resize_max(rgb, max_side)
    ref = {"verdict": base["verdict"], "cls": base.get("cls"), "confidence": base.get("confidence")}
    rows = []
    for name, fn in VARIANTS:
        v = np.ascontiguousarray(fn(img))
        d = quick_decision(guard, v)
        rows.append({"name": name, "image": v, **d, "agrees": same_answer(ref, d)})
    agree = sum(r["agrees"] for r in rows) / len(rows)
    stable = agree >= min_agreement
    adjusted = base["verdict"]
    if base["verdict"] in ("HEALTHY", "DISEASED") and not stable:
        adjusted = "UNCERTAIN"
    return {"variants": rows, "agreement": agree, "stable": stable, "adjusted_verdict": adjusted,
            "n_agree": sum(r["agrees"] for r in rows), "n": len(rows)}
