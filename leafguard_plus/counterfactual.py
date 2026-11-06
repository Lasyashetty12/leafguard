"""'What would change my mind?' - proof that the decision came from the disease spots.

YOLO models (two tests, like a scientist's control experiment):
  1. HIDE THE SPOTS      : grey out the regions the model flagged. Does the disease disappear?
                           -> the spots were NECESSARY for the diagnosis.
  2. HIDE EVERYTHING ELSE: grey out all but the flagged regions. Is it still detected?
                           -> the spots alone are SUFFICIENT; background/table played no part.
Classifiers: digitally heal the spot pixels and ask again.
If the answer does NOT change, LeafGuard says so honestly instead of claiming a proof.
"""
import cv2
import numpy as np

from .decide import quick_decision
from .severity import lesion_pixels

GREY = (128, 128, 128)


def _hide(img, region, keep=False):
    out = img.copy()
    sel = region if not keep else ~region
    out[sel] = GREY
    return out


def _detector_test(guard, img, result):
    th = guard.th
    region = np.zeros(img.shape[:2], bool)
    for d in result.get("detections", []):
        if d["conf"] >= th["det_conf_low"]:
            x1, y1, x2, y2 = [max(0, v) for v in d["box"]]
            region[y1:y2, x1:x2] = True
    if not region.any():
        return None
    hidden = _hide(img, region)
    only = _hide(img, region, keep=True)
    after_hidden = quick_decision(guard, hidden)
    after_only = quick_decision(guard, only)
    cls = result["cls"]
    necessary = not (after_hidden["verdict"] == "DISEASED" and after_hidden["cls"] == cls)
    sufficient = after_only["verdict"] == "DISEASED" and after_only["cls"] == cls
    if necessary and sufficient:
        status, msg = "proven", ("Hide the spots and the disease disappears. Show ONLY the spots and it is still "
                                 "found. The diagnosis came from these spots, not the background.")
    elif necessary:
        status, msg = "mostly", ("Hide the spots and the disease disappears, so the spots are the reason. "
                                 "The model also uses a little surrounding context.")
    else:
        status, msg = "not_proven", ("Even with the flagged spots hidden, the model still sees the disease. "
                                     "It may be relying on something else, so treat this answer with care.")
    return {"status": status, "message": msg, "before": {"cls": cls, "confidence": result.get("confidence")},
            "tests": [{"name": "Spots hidden", "image": hidden, **after_hidden,
                       "expect": "disease should disappear", "passed": necessary},
                      {"name": "Only the spots", "image": only, **after_only,
                       "expect": "disease should still be found", "passed": sufficient}]}


def _classifier_test(guard, img, result):
    mask = result["images"].get("mask")
    if mask is None:
        return None
    lesion = lesion_pixels(img, mask)
    if lesion.sum() == 0:
        return None
    m = cv2.dilate(lesion.astype(np.uint8) * 255, np.ones((7, 7), np.uint8))
    healed = cv2.inpaint(img, m, 7, cv2.INPAINT_TELEA)
    after = quick_decision(guard, healed)
    changed = not (after["verdict"] == "DISEASED" and after["cls"] == result["cls"])
    status = "proven" if changed else "not_proven"
    msg = ("With the spots digitally healed, the model no longer sees the disease. The spots caused the diagnosis."
           if changed else "Even with the spots healed, the model still says the same. Treat this answer with care.")
    return {"status": status, "message": msg, "before": {"cls": result["cls"], "confidence": result.get("confidence")},
            "tests": [{"name": "Spots healed", "image": healed, **after,
                       "expect": "disease should disappear", "passed": changed}]}


def what_would_change_my_mind(guard, rgb, result, sev=None):
    """result = guard.analyze(rgb). Only meaningful when the verdict is DISEASED."""
    from leafguard.quality_gate import resize_max

    if result.get("verdict") != "DISEASED":
        return None
    img = resize_max(rgb, 1024)  # same size LeafGuard analysed, so boxes line up
    if guard.is_detector:
        return _detector_test(guard, img, result)
    return _classifier_test(guard, img, result)
