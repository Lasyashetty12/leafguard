"""Find the leaf, and build a 'leaf only' copy of the photo with the background removed.

Removing the background is what defeats the "healthy leaf on a sick leaf's table" trick:
the model can no longer use the table, tray or soil as a shortcut.
"""
import cv2
import numpy as np

from .quality_gate import resize_max


def plant_mask(rgb):
    """Pixels that look like plant tissue: green, yellow-green, yellow and brown-ish lesions."""
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    h, s, v = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    green = (h >= 30) & (h <= 90) & (s >= 40) & (v >= 30)
    yellow_brown = (h >= 12) & (h < 30) & (s >= 70) & (v >= 40)
    r, g, b = [rgb[..., i].astype(int) for i in range(3)]
    exg = 2 * g - r - b > 25  # excess-green index, robust to lighting
    return ((green | yellow_brown | exg).astype(np.uint8)) * 255, green


def _largest_components(mask, min_frac=0.01):
    """Keep ONLY the main leaf: the big region nearest the centre of the photo (people centre the
    leaf they are asking about). Other leaves lying around - e.g. sick leaves on the table - are
    NOT counted as the leaf, so disease found on them is ignored."""
    n, labels, stats, cents = cv2.connectedComponentsWithStats(mask)
    if n <= 1:
        return mask * 0
    h, w = mask.shape
    total = h * w
    diag = np.hypot(h, w) / 2
    best, best_score = None, 0.0
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if area / total < min_frac:
            continue
        cx, cy = cents[i]
        x, y, bw, bh = stats[i, :4]
        covers_centre = x <= w / 2 <= x + bw and y <= h / 2 <= y + bh
        centrality = 1.0 if covers_centre else max(0.05, 1 - np.hypot(cx - w / 2, cy - h / 2) / diag)
        score = area * centrality ** 2
        if score > best_score:
            best, best_score = i, score
    out = np.zeros_like(mask)
    if best is not None:
        out[labels == best] = 255
    return out


def _fill_holes(mask):
    """Dark disease spots inside the leaf are part of the leaf, so fill interior holes."""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(mask)
    cv2.drawContours(filled, contours, -1, 255, thickness=cv2.FILLED)
    return filled


def leaf_mask(rgb):
    """Return (mask 0/255 at full size, leaf area fraction)."""
    H, W = rgb.shape[:2]
    small = resize_max(rgb, 384)
    raw, green = plant_mask(small)
    k = max(3, small.shape[0] // 60) | 1
    kernel = np.ones((k, k), np.uint8)
    # Start from the GREEN core of the leaf. Brown/yellow pixels only count when they touch
    # that core, so a brown table or soil is never mistaken for a diseased leaf.
    r, g, b = [small[..., i].astype(int) for i in range(3)]
    core = (green | (2 * g - r - b > 25)).astype(np.uint8) * 255
    core = cv2.morphologyEx(core, cv2.MORPH_CLOSE, kernel, iterations=2)
    core = cv2.morphologyEx(core, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    core = _fill_holes(_largest_components(core))
    near_core = cv2.dilate(core, kernel, iterations=2) > 0
    m = core.copy()
    m[(raw > 0) & near_core] = 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, kernel)
    m = _fill_holes(_largest_components(m))

    frac = m.mean() / 255
    if 0.02 < frac < 0.97:  # refine edges with GrabCut
        try:
            gc = np.full(m.shape, cv2.GC_PR_BGD, np.uint8)
            gc[m > 0] = cv2.GC_PR_FGD
            core = cv2.erode(m, np.ones((k, k), np.uint8), iterations=2)
            gc[core > 0] = cv2.GC_FGD
            far = cv2.dilate(m, np.ones((k * 3, k * 3), np.uint8)) == 0
            gc[far] = cv2.GC_BGD
            bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
            cv2.grabCut(cv2.cvtColor(small, cv2.COLOR_RGB2BGR), gc, None, bgd, fgd, 3,
                        cv2.GC_INIT_WITH_MASK)
            refined = np.where((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
            refined = _fill_holes(_largest_components(refined))
            if refined.mean() / 255 > 0.5 * frac:  # sanity check
                m = refined
        except cv2.error:
            pass

    full = cv2.resize(m, (W, H), interpolation=cv2.INTER_NEAREST)
    return full, float(full.mean() / 255)


def leaf_only(rgb, mask, bg_color=(128, 128, 128), pad=0.08):
    """Crop to the leaf and paint everything that is not leaf in a neutral colour.
    Returns (leaf_only_image, its_mask)."""
    if mask.max() == 0:
        return rgb.copy(), mask.copy()
    soft = cv2.GaussianBlur(mask, (5, 5), 0).astype(np.float32)[..., None] / 255
    bg = np.empty_like(rgb)
    bg[:] = np.array(bg_color, dtype=np.uint8)
    out = (rgb * soft + bg * (1 - soft)).astype(np.uint8)
    ys, xs = np.where(mask > 0)
    H, W = mask.shape
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    side = max(y1 - y0, x1 - x0) * (1 + 2 * pad)
    cy, cx = (y0 + y1) / 2, (x0 + x1) / 2
    y0, y1 = int(max(0, cy - side / 2)), int(min(H, cy + side / 2))
    x0, x1 = int(max(0, cx - side / 2)), int(min(W, cx + side / 2))
    return out[y0:y1, x0:x1], mask[y0:y1, x0:x1]
