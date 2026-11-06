"""Gate 1: is the photo itself usable? (blur, darkness, glare, finger over lens, blank)."""
import cv2
import numpy as np


def resize_max(img, max_side=512):
    h, w = img.shape[:2]
    scale = max_side / max(h, w)
    if scale >= 1:
        return img
    return cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)


def _check(name, passed, value, tip):
    return {"gate": "quality", "name": name, "passed": bool(passed), "value": value, "tip": tip}


def skin_mask(rgb):
    ycrcb = cv2.cvtColor(rgb, cv2.COLOR_RGB2YCrCb)
    _, cr, cb = cv2.split(ycrcb)
    mask = ((cr >= 138) & (cr <= 180) & (cb >= 77) & (cb <= 127)).astype(np.uint8) * 255
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    not_green = (hsv[..., 0] < 22) | (hsv[..., 0] > 165)  # skin is red/orange, never green
    mask[~not_green] = 0
    return mask


def finger_blob(rgb, gray):
    """Large, out-of-focus, skin-coloured region touching the border = finger over lens."""
    mask = skin_mask(rgb)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    h, w = mask.shape
    best = 0.0
    for i in range(1, n):
        x, y, bw, bh, area = stats[i]
        touches_edge = x == 0 or y == 0 or x + bw >= w or y + bh >= h
        if not touches_edge:
            continue
        frac = area / (h * w)
        if frac <= best:
            continue
        region = (labels == i).astype(np.uint8)
        inner = cv2.erode(region, np.ones((15, 15), np.uint8)) > 0  # ignore the edge where it meets the scene
        if inner.sum() < 50:
            continue
        sharp = cv2.Laplacian(gray, cv2.CV_64F)[inner].var()
        if sharp < 10:  # a finger on the lens is always extremely out of focus (very smooth)
            best = frac
    return best


def check_quality(rgb, th):
    h, w = rgb.shape[:2]
    small = resize_max(rgb, 512)
    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)

    mean = float(gray.mean())
    std = float(gray.std())
    blown = float((gray > 245).mean())
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    finger = float(finger_blob(small, gray))

    return [
        _check("Resolution", min(h, w) >= th["min_side"], f"{w}x{h}",
               "Image is too small. Use the full camera resolution."),
        _check("Not blank / covered", std >= th["flat_std_min"], round(std, 1),
               "The photo has almost no detail. Is the lens covered?"),
        _check("Lighting (not too dark)", mean >= th["dark_max_mean"], round(mean, 1),
               "Too dark. Move to daylight or turn on the flash."),
        _check("Lighting (no glare)", mean <= th["bright_min_mean"] and blown <= th["overexposed_frac"],
               f"{round(mean, 1)} / {round(blown * 100)}% blown",
               "Too bright or glare. Avoid direct sun on the leaf."),
        _check("No finger on lens", finger <= th["finger_frac"], f"{round(finger * 100)}%",
               "Something (a finger?) is covering part of the lens."),
        _check("Sharp focus", blur >= th["blur_min"], round(blur, 1),
               "Photo is blurry. Hold steady and tap the leaf to focus."),
    ]
