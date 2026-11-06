"""Live camera 'traffic light': fast checks on every frame, full diagnosis only on a good, steady shot.

  RED    photo problem (blurry, dark, glare, finger, covered)   -> tell the farmer how to fix it
  YELLOW no leaf / leaf too small                               -> "point at one leaf" / "move closer"
  GREEN  good shot                                              -> after N green frames in a row: diagnose
"""
import cv2
import numpy as np

from leafguard.quality_gate import check_quality, resize_max
from leafguard.segment import plant_mask

COLOURS = {"red": (230, 50, 50), "yellow": (245, 190, 30), "green": (40, 200, 80), "blue": (40, 120, 230)}


def frame_light(rgb, th):
    """Fast (no model, no CLIP) check of one frame -> (colour, message)."""
    small = resize_max(rgb, 480)
    for c in check_quality(small, dict(th, min_side=0)):
        if not c["passed"]:
            return "red", c["tip"]
    mask, green = plant_mask(resize_max(small, 240))
    plant = mask.mean() / 255
    if plant < th["plant_frac_min"] or green.mean() < 0.02:
        return "yellow", "Point the camera at one leaf"
    if plant < max(th["min_leaf_area"], 0.12):
        return "yellow", "Move closer, the leaf is too small"
    return "green", "Good shot, hold still..."


def draw_overlay(rgb, colour, message, progress=None):
    """Thick coloured border + message banner (+ a progress bar while holding still)."""
    img = rgb.copy()
    h, w = img.shape[:2]
    t = max(8, w // 60)
    c = COLOURS[colour]
    cv2.rectangle(img, (0, 0), (w - 1, h - 1), c, t)
    bar_h = max(34, h // 12)
    overlay = img.copy()
    cv2.rectangle(overlay, (0, h - bar_h), (w, h), (0, 0, 0), -1)
    img = cv2.addWeighted(overlay, 0.55, img, 0.45, 0)
    cv2.circle(img, (bar_h // 2 + 6, h - bar_h // 2), bar_h // 3, c, -1)
    scale = bar_h / 48
    cv2.putText(img, message, (bar_h + 12, h - bar_h // 2 + int(10 * scale)), cv2.FONT_HERSHEY_SIMPLEX,
                0.8 * scale, (255, 255, 255), max(1, int(2 * scale)), cv2.LINE_AA)
    if progress is not None:
        cv2.rectangle(img, (t, t), (t + int((w - 2 * t) * min(progress, 1.0)), t + max(6, h // 80)), c, -1)
    return img


def open_source(src):
    """'0' -> webcam 0, otherwise a URL (ESP32-CAM: http://<ip>:81/stream) or a video file path."""
    src = str(src).strip()
    cap = cv2.VideoCapture(int(src)) if src.isdigit() else cv2.VideoCapture(src)
    return cap


def read_rgb(cap):
    ok, frame = cap.read()
    if not ok or frame is None:
        return None
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


class SteadyShot:
    """Counts green frames in a row; fires once per new leaf."""

    def __init__(self, needed=6, reset_after=4):
        self.needed, self.reset_after = needed, reset_after
        self.green = 0
        self.not_green = 0
        self.armed = True

    def update(self, colour):
        if colour == "green":
            self.green += 1
            self.not_green = 0
        else:
            self.green = 0
            self.not_green += 1
            if self.not_green >= self.reset_after:
                self.armed = True  # the scene changed: allow a new diagnosis
        if self.armed and self.green >= self.needed:
            self.armed = False
            return True
        return False

    @property
    def progress(self):
        return self.green / self.needed if self.armed else None


def result_banner(result):
    v = result["verdict"]
    if v == "DISEASED":
        return "blue", f"{result['label']} ({round(result['confidence'] * 100)}%)"
    if v == "HEALTHY":
        return "green", "No disease found"
    return "yellow", {"UNCERTAIN": "Not sure - ask an expert", "RETAKE": "Retake the photo",
                      "NOT_A_LEAF": "Not a leaf"}[v]


def blank_frame(text, w=640, h=400):
    img = np.full((h, w, 3), (20, 60, 36), np.uint8)  # deep leaf green
    (tw, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
    cv2.putText(img, text, ((w - tw) // 2, h // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (220, 252, 231), 2, cv2.LINE_AA)
    return img
