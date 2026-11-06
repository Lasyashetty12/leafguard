"""Realistic 'bad photo' generators used by the stress test (the proof)."""
import cv2
import numpy as np

from .segment import leaf_mask


def blur(rgb, sigma=None):
    sigma = sigma or max(rgb.shape[:2]) / 80
    return cv2.GaussianBlur(rgb, (0, 0), sigma)


def darken(rgb, factor=0.12):
    return np.clip(rgb.astype(np.float32) * factor, 0, 255).astype(np.uint8)


def add_finger(rgb, rng=None):
    """Simulate a thumb partly over the lens: a big, blurry, skin-coloured blob from a corner."""
    rng = rng or np.random.default_rng()
    h, w = rgb.shape[:2]
    corner = rng.integers(4)
    cx = 0 if corner in (0, 3) else w
    cy = 0 if corner in (0, 1) else h
    mask = np.zeros((h, w), np.float32)
    cv2.ellipse(mask, (int(cx), int(cy)), (int(w * rng.uniform(.65, .85)), int(h * rng.uniform(.55, .7))),
                float(rng.uniform(0, 90)), 0, 360, 1.0, -1)
    mask = cv2.GaussianBlur(mask, (0, 0), max(h, w) / 25)[..., None]
    tone = np.array([rng.uniform(190, 235), rng.uniform(120, 160), rng.uniform(95, 130)], np.float32)
    yy = np.linspace(0.8, 1.1, h)[:, None, None]
    skin = np.clip(tone * yy, 0, 255)
    out = rgb.astype(np.float32) * (1 - mask) + skin * mask
    return np.clip(out, 0, 255).astype(np.uint8)


def background_swap(leaf_rgb, background_rgb):
    """Put the leaf from leaf_rgb onto a different background (e.g. a sick leaf's table)."""
    h, w = leaf_rgb.shape[:2]
    bg = cv2.resize(background_rgb, (w, h))
    mask, _ = leaf_mask(leaf_rgb)
    soft = cv2.GaussianBlur(mask, (5, 5), 0).astype(np.float32)[..., None] / 255
    return (leaf_rgb * soft + bg * (1 - soft)).astype(np.uint8)


def empty_table(rgb):
    """Remove the leaf from a photo, leaving only its background (inpainting)."""
    mask, _ = leaf_mask(rgb)
    mask = cv2.dilate(mask, np.ones((15, 15), np.uint8))
    return cv2.inpaint(rgb, mask, 9, cv2.INPAINT_TELEA)
