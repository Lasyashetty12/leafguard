"""How much of the leaf is affected? -> mild / moderate / severe.

YOLO models : share of the leaf covered by the model's own disease regions (boxes).
Classifiers : share of leaf pixels that stand out as spots / powder / dead patches.
"""
import cv2
import numpy as np

from leafguard.segment import leaf_mask

LEVELS = [(5, "mild"), (25, "moderate"), (101, "severe")]          # % of leaf, pixel method
BOX_LEVELS = [(15, "mild"), (45, "moderate"), (101, "severe")]     # % of leaf, detector boxes


def lesion_pixels(rgb, mask):
    """Pixels that STAND OUT from the leaf around them:
       - brown / yellow / orange spots (blight, rust, bacterial spot)
       - dark dead patches (much darker than the surrounding leaf)
       - white powder (much brighter and greyer than the surrounding leaf: powdery mildew)
    Comparing to the local surroundings means a leaf that is just pale overall is NOT counted."""
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    h, s, v = [hsv[..., i].astype(int) for i in range(3)]
    k = max(15, (min(rgb.shape[:2]) // 16) | 1)
    v_local = cv2.medianBlur(hsv[..., 2], k).astype(int)
    s_local = cv2.medianBlur(hsv[..., 1], k).astype(int)
    coloured_spot = (h >= 5) & (h < 28) & (s >= 70) & (v >= 40)
    dark_patch = (v_local - v > 55)
    white_powder = (v - v_local > 15) & (s < s_local)
    lesion = (coloured_spot | dark_patch | white_powder) & (mask > 0)
    lesion = cv2.morphologyEx(lesion.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8)) > 0
    return lesion


def estimate(rgb, result, th):
    """result = guard.analyze(rgb). Returns {"percent", "level", "overlay"} (level None if not diseased)."""
    from leafguard.quality_gate import resize_max

    img = resize_max(rgb, 1024)  # same size LeafGuard used, so boxes line up
    mask = result.get("images", {}).get("mask")
    if mask is None or mask.shape[:2] != img.shape[:2]:
        mask, _ = leaf_mask(img)
    leaf_px = max(int((mask > 0).sum()), 1)
    levels, method = LEVELS, "spot pixels"
    if result.get("detections") is not None:
        lesion = np.zeros(mask.shape, bool)
        for d in result["detections"]:
            if d["conf"] >= th["det_conf_low"]:
                x1, y1, x2, y2 = [max(0, v) for v in d["box"]]
                lesion[y1:y2, x1:x2] = True
        lesion &= mask > 0
        levels, method = BOX_LEVELS, "area inside the model's disease regions"
    else:
        lesion = lesion_pixels(img, mask)
    pct = 100.0 * lesion.sum() / leaf_px
    if result.get("verdict") != "DISEASED":
        return {"percent": pct, "level": None, "overlay": img, "lesion": lesion, "method": method}
    level = next(name for limit, name in levels if pct < limit)
    overlay = img.copy()
    overlay[lesion] = (0.45 * overlay[lesion] + 0.55 * np.array([230, 40, 40])).astype(np.uint8)
    edge = cv2.morphologyEx((mask > 0).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8)) > 0
    overlay[edge] = (40, 200, 60)
    return {"percent": pct, "level": level, "overlay": overlay, "lesion": lesion, "method": method}
