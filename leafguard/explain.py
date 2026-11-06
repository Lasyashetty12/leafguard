"""'Prove why': where did the model look?

Uses Grad-CAM when the framework supports it, otherwise occlusion sensitivity
(cover patches of the image and see how much the answer drops) - works with ANY model.
"""
import cv2
import numpy as np

from .calibration import softmax


def occlusion_map(model, rgb, idx, grid=7, batch=16):
    h, w = model.size if hasattr(model, "size") else (224, 224)
    img = cv2.resize(rgb, (w, h), interpolation=cv2.INTER_AREA)
    base = softmax(model.logits([img]))[0, idx]
    ph, pw = int(h / grid * 1.6), int(w / grid * 1.6)
    ys = np.linspace(0, h - ph, grid).astype(int)
    xs = np.linspace(0, w - pw, grid).astype(int)
    fill = img.reshape(-1, 3).mean(0).astype(np.uint8)
    jobs, coords = [], []
    for y in ys:
        for x in xs:
            occ = img.copy()
            occ[y:y + ph, x:x + pw] = fill
            jobs.append(occ)
            coords.append((y, x))
    drops = []
    for i in range(0, len(jobs), batch):
        p = softmax(model.logits(jobs[i:i + batch]))[:, idx]
        drops.extend(base - p)
    heat = np.zeros((h, w), np.float32)
    count = np.zeros((h, w), np.float32)
    for (y, x), d in zip(coords, drops):
        heat[y:y + ph, x:x + pw] += max(d, 0)
        count[y:y + ph, x:x + pw] += 1
    heat = heat / np.maximum(count, 1)
    if heat.max() <= 0:
        return None
    heat = cv2.GaussianBlur(heat / heat.max(), (0, 0), sigmaX=w / 30)
    heat = heat / max(heat.max(), 1e-6)
    return cv2.resize(heat, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_CUBIC).clip(0, 1)


def explain(model, rgb, idx):
    heat = model.gradcam(rgb, idx)
    if heat is not None:
        return heat, "Grad-CAM"
    return occlusion_map(model, rgb, idx), "occlusion map"


def leaf_focus(heat, mask):
    """Share of the model's attention that falls on the leaf (0..1)."""
    if heat is None or mask is None:
        return None
    m = cv2.resize(mask, (heat.shape[1], heat.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
    total = heat.sum()
    return float(heat[m].sum() / total) if total > 0 else None


def overlay(rgb, heat, alpha=0.45):
    if heat is None:
        return rgb
    colour = cv2.applyColorMap((heat * 255).astype(np.uint8), cv2.COLORMAP_JET)
    colour = cv2.cvtColor(colour, cv2.COLOR_BGR2RGB)
    return (rgb * (1 - alpha) + colour * alpha).astype(np.uint8)
