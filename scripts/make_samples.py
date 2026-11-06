"""Create test photos in sample_images/.

    python scripts/make_samples.py                  synthetic cartoon set (for the demo model only)
    python scripts/make_samples.py my_leaf.jpg      blurry / dark / thumb versions of a REAL photo
"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from leafguard.augment import add_finger, background_swap, darken  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_images")
rng = np.random.default_rng(7)


def texture(h, w, base, amp=18):
    noise = rng.normal(0, amp, (h, w, 3))
    noise = cv2.GaussianBlur(noise, (0, 0), 1.2)
    return np.clip(np.array(base, np.float32) + noise, 0, 255)


def draw_leaf(bg, spots=0, spot_colour=(95, 60, 30)):
    img = bg.copy()
    h, w = img.shape[:2]
    leaf = np.zeros((h, w), np.uint8)
    cv2.ellipse(leaf, (w // 2, h // 2), (int(w * 0.30), int(h * 0.42)), 25, 0, 360, 255, -1)
    green = texture(h, w, (55, 140, 45), 22)
    img[leaf > 0] = green[leaf > 0]
    c, ang = (w // 2, h // 2), np.deg2rad(25 + 90)
    L = int(h * 0.42)
    p1 = (int(c[0] - L * np.cos(ang)), int(c[1] - L * np.sin(ang)))
    p2 = (int(c[0] + L * np.cos(ang)), int(c[1] + L * np.sin(ang)))
    cv2.line(img, p1, p2, (120, 185, 95), 3)
    for t in np.linspace(-0.8, 0.8, 9):
        q = (int(c[0] + t * L * np.cos(ang)), int(c[1] + t * L * np.sin(ang)))
        for s in (-1, 1):
            a = ang + s * 0.9
            e = (int(q[0] + 0.35 * L * np.cos(a)), int(q[1] + 0.35 * L * np.sin(a)))
            cv2.line(img, q, e, (105, 170, 85), 2)
    ys, xs = np.where(leaf > 0)
    for _ in range(spots):
        k = rng.integers(len(ys))
        r = int(rng.integers(8, 22))
        cv2.circle(img, (int(xs[k]), int(ys[k])), r + 5, (170, 160, 60), -1)
        cv2.circle(img, (int(xs[k]), int(ys[k])), r, spot_colour, -1)
    img[leaf == 0] = bg[leaf == 0]
    return img


def mug(h, w):
    img = texture(h, w, (200, 190, 175), 10).astype(np.uint8)
    cv2.rectangle(img, (int(w * .3), int(h * .3)), (int(w * .65), int(h * .8)), (235, 235, 240), -1)
    cv2.ellipse(img, (int(w * .475), int(h * .3)), (int(w * .175), int(h * .05)), 0, 0, 360, (90, 60, 40), -1)
    cv2.ellipse(img, (int(w * .65), int(h * .55)), (int(w * .09), int(h * .12)), 0, -90, 90, (225, 225, 230), 14)
    cv2.putText(img, "COFFEE", (int(w * .34), int(h * .6)), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (40, 40, 160), 3)
    return np.clip(img.astype(np.float32) + rng.normal(0, 6, img.shape), 0, 255)


def from_real_photo(path):
    """Make bad-photo versions of a REAL leaf photo (best for a real model)."""
    from leafguard.augment import blur

    bgr = cv2.imread(path)
    if bgr is None:
        raise SystemExit(f"Can't read {path}")
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    base = os.path.splitext(os.path.basename(path))[0]
    out = {f"{base}_blurry.jpg": blur(rgb), f"{base}_dark.jpg": darken(rgb, 0.12),
           f"{base}_thumb.jpg": add_finger(rgb, rng)}
    for name, img in out.items():
        cv2.imwrite(os.path.join(OUT, name), cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(f"Wrote {len(out)} variants of {path} to {OUT}")


def main():
    if len(sys.argv) > 1:  # python scripts/make_samples.py my_leaf.jpg
        from_real_photo(sys.argv[1])
        return
    os.makedirs(OUT, exist_ok=True)
    h, w = 480, 480
    grey_table = texture(h, w, (150, 150, 145), 12)
    healthy = draw_leaf(grey_table)
    sick = draw_leaf(grey_table, spots=28)
    samples = {
        "1_healthy_leaf.jpg": healthy,
        "2_diseased_leaf.jpg": sick,
        "3_coffee_mug.jpg": mug(h, w),
        "4_thumb_over_lens.jpg": add_finger(healthy.astype(np.uint8), rng),
        "5_blurry_leaf.jpg": cv2.GaussianBlur(sick, (0, 0), 6),
        "6_too_dark.jpg": darken(sick.astype(np.uint8), 0.12),
        "7_healthy_leaf_on_sick_table.jpg": background_swap(
            healthy.astype(np.uint8), texture(h, w, (120, 75, 35), 25).astype(np.uint8)),
    }
    for name, img in samples.items():
        cv2.imwrite(os.path.join(OUT, name), cv2.cvtColor(np.clip(img, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
    print(f"Wrote {len(samples)} images to {OUT}")


if __name__ == "__main__":
    main()
