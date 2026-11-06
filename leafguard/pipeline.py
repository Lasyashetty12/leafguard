"""LeafGuard: the full decision pipeline wrapped around your model.

    photo -> [1 quality gate] -> [2 is-it-a-leaf gate] -> [3 cut out the leaf]
          -> [4 your model on leaf-only image, calibrated] -> [5 uncertainty + background check]
          -> [6 where did it look?] -> verdict

Verdicts: RETAKE, NOT_A_LEAF, UNCERTAIN, HEALTHY, DISEASED
"""
import time

import numpy as np

from .calibration import norm_entropy, softmax
from .explain import explain, leaf_focus, overlay
from .leaf_gate import LeafGate
from .model_adapter import load_model
from .quality_gate import check_quality, resize_max
from .segment import leaf_mask, leaf_only

HEADLINES = {
    "RETAKE": "Please retake the photo",
    "NOT_A_LEAF": "This doesn't look like a leaf",
    "UNCERTAIN": "Not sure. Get a second opinion",
    "HEALTHY": "Leaf looks healthy",
    "DISEASED": "Disease detected",
}


def pretty(name):
    name = name.replace("___", " - ").replace("__", " - ").replace("_", " ")
    return " ".join(name.split())


def to_rgb_uint8(img):
    img = np.asarray(img)
    if img.ndim == 2:
        img = np.stack([img] * 3, -1)
    if img.shape[-1] == 4:
        img = img[..., :3]
    if img.dtype != np.uint8:
        img = np.clip(img * (255 if img.max() <= 1 else 1), 0, 255).astype(np.uint8)
    return np.ascontiguousarray(img)


class LeafGuard:
    def __init__(self, cfg, load_clip=True):
        self.cfg = cfg
        self.th = cfg["thresholds"]
        self.model = load_model(cfg)
        self.class_names = self.model.class_names
        self.is_detector = getattr(self.model, "kind", None) == "detector"
        if not load_clip:
            cfg = dict(cfg, use_clip=False)
        self.leaf_gate = LeafGate(cfg)

    # The "laptop 99%" model: raw image in, answer out, no questions asked.
    def baseline(self, rgb, dets=None):
        if self.is_detector:
            dets = self.model.detect(rgb) if dets is None else dets
            dets = [d for d in dets if d["conf"] >= 0.25]  # YOLO's usual default threshold
            if not dets:
                return {"label": "Healthy (no disease found)", "class": "healthy", "index": -1, "confidence": None}
            d = max(dets, key=lambda d: d["conf"])
            return {"label": pretty(self.class_names[d["cls"]]), "class": self.class_names[d["cls"]],
                    "index": d["cls"], "confidence": d["conf"]}
        p = softmax(self.model.logits([rgb]))[0]
        i = int(p.argmax())
        return {"label": pretty(self.class_names[i]), "class": self.class_names[i],
                "index": i, "confidence": float(p[i])}

    def _is_healthy(self, name):
        return self.cfg["healthy_keyword"].lower() in name.lower()

    def analyze(self, rgb, do_explain=None, explain_baseline=False):
        t0 = time.time()
        rgb = resize_max(to_rgb_uint8(rgb), 1024)
        do_explain = self.cfg.get("explain", True) if do_explain is None else do_explain
        dets = self.model.detect(rgb) if self.is_detector else None
        res = {"checks": [], "reasons": [], "images": {}, "verdict": None,
               "baseline": self.baseline(rgb, dets)}
        if self.is_detector and explain_baseline:  # what the raw YOLO would have shown the farmer
            raw_boxes = [d for d in dets if d["conf"] >= 0.25]
            res["images"]["baseline_heatmap"] = draw_boxes(rgb, raw_boxes, [], self.class_names,
                                                           dict(self.th, det_conf_low=0.25))

        def finish(verdict, **extra):
            res.update(verdict=verdict, headline=HEADLINES[verdict], **extra)
            res["seconds"] = round(time.time() - t0, 2)
            return res

        # 1. Quality gate ----------------------------------------------------
        quality = check_quality(rgb, self.th)
        res["checks"] += quality
        failed = [c for c in quality if not c["passed"]]
        if failed:
            res["reasons"] = [c["tip"] for c in failed]
            return finish("RETAKE")

        # 2. Is it a leaf? ---------------------------------------------------
        leaf = self.leaf_gate.check(rgb)
        res["checks"].append(leaf["check"])
        res["leaf_gate"] = {k: v for k, v in leaf.items() if k != "check"}
        if not leaf["check"]["passed"]:
            looks = leaf.get("looks_like")
            if looks == "a finger over the lens":
                res["reasons"] = ["Something (a finger?) is covering the lens."]
                return finish("RETAKE")
            res["reasons"] = [f"This looks like {looks}, not a leaf." if looks else leaf["check"]["tip"],
                              "LeafGuard only diagnoses plant leaves, so it will not guess."]
            return finish("NOT_A_LEAF")

        # 3. Cut out the leaf --------------------------------------------------
        mask, area = leaf_mask(rgb)
        area_ok = area >= self.th["min_leaf_area"]
        res["checks"].append({"gate": "leaf", "name": "Leaf found & cut out", "passed": area_ok,
                              "value": f"{round(area * 100)}% of photo",
                              "tip": "The leaf is too small. Move closer so it fills the frame."})
        res["images"]["mask"] = mask
        if not area_ok:
            res["reasons"] = ["The leaf is too small in the photo. Move closer."]
            return finish("RETAKE")
        clean, clean_mask = leaf_only(rgb, mask, tuple(self.cfg["neutral_background"]))
        res["images"]["leaf_only"] = clean
        if self.is_detector:
            return self._detector_verdict(rgb, mask, dets, res, finish)

        # 4. Your model on the leaf-only image, with honest (calibrated) confidence
        T = float(self.cfg.get("temperature", 1.0))
        logits = self.model.logits([clean, rgb])
        p_clean, p_raw = softmax(logits, T)
        order = np.argsort(-p_clean)
        i, j = int(order[0]), int(order[1]) if len(order) > 1 else int(order[0])
        conf, margin = float(p_clean[i]), float(p_clean[i] - p_clean[j])
        ent = float(norm_entropy(p_clean))
        res["top3"] = [{"label": pretty(self.class_names[k]), "prob": float(p_clean[k])} for k in order[:3]]
        res.update(label=pretty(self.class_names[i]), cls=self.class_names[i], confidence=conf,
                   margin=margin, entropy=ent)

        # 5. Did the background change the answer? ---------------------------
        raw_i = int(p_raw.argmax())
        shift = float(0.5 * np.abs(p_clean - p_raw).sum())  # 0 = same, 1 = totally different
        bg_changed = raw_i != i
        res["background_shift"] = shift
        res["checks"].append({"gate": "model", "name": "Background independent", "passed": not bg_changed,
                              "value": f"{round(shift * 100)}% shift",
                              "tip": "The raw model changed its answer because of the background."})
        if bg_changed:
            res["reasons"].append(
                f"Background trick caught: on the full photo the model said "
                f"'{pretty(self.class_names[raw_i])}', but on the leaf alone it says '{res['label']}'. "
                f"LeafGuard trusts the leaf-only answer.")

        sure = conf >= self.th["min_confidence"] and margin >= self.th["min_margin"] and ent <= self.th["max_entropy"]
        res["checks"].append({"gate": "model", "name": "Model is confident", "passed": sure,
                              "value": f"{round(conf * 100)}% (margin {round(margin * 100)}%)",
                              "tip": "The model is unsure between several answers."})

        # 6. Where did the model look? ---------------------------------------
        focus_ok = True
        if do_explain:
            heat, method = explain(self.model, clean, i)
            focus = leaf_focus(heat, clean_mask)
            res["explain_method"] = method
            res["leaf_focus"] = focus
            res["images"]["heatmap"] = overlay(clean, heat)
            if focus is not None:
                focus_ok = focus >= self.th["min_leaf_focus"]
                res["checks"].append({"gate": "model", "name": "Looked at the leaf", "passed": focus_ok,
                                      "value": f"{round(focus * 100)}% on leaf",
                                      "tip": "The model's attention was mostly outside the leaf."})
            if explain_baseline:
                b = res["baseline"]["index"]
                bheat, _ = explain(self.model, rgb, b)
                res["images"]["baseline_heatmap"] = overlay(rgb, bheat)
                res["baseline"]["leaf_focus"] = leaf_focus(bheat, mask)

        # Verdict ------------------------------------------------------------
        if not sure or not focus_ok:
            alt = pretty(self.class_names[j])
            if not sure:
                res["reasons"].append(f"Could be '{res['label']}' ({round(conf * 100)}%) or '{alt}' "
                                      f"({round(float(p_clean[j]) * 100)}%). Too close to call safely.")
            if not focus_ok:
                res["reasons"].append("The model's attention was not on the leaf, so its answer can't be trusted.")
            res["reasons"].append("Try a closer, well-lit photo of one leaf, or ask an agronomist.")
            return finish("UNCERTAIN")

        verdict = "HEALTHY" if self._is_healthy(self.class_names[i]) else "DISEASED"
        res["reasons"].insert(0, f"{res['label']} with {round(conf * 100)}% calibrated confidence.")
        return finish(verdict)

    # ------------------------------------------------------------------ YOLO detector models
    def _detector_verdict(self, rgb, mask, dets, res, finish):
        """Detector version of steps 4-6: keep only boxes that sit ON the leaf, then decide."""
        th, names = self.th, self.class_names
        kept, ignored = [], []
        for d in dets:
            x1, y1, x2, y2 = d["box"]
            sub = mask[max(0, y1):max(0, y2), max(0, x1):max(0, x2)]
            d["on_leaf"] = float((sub > 0).mean()) if sub.size else 0.0
            (kept if d["on_leaf"] >= th["det_on_leaf"] else ignored).append(d)
        res["detections"], res["ignored_detections"] = kept, ignored
        res["images"]["heatmap"] = draw_boxes(rgb, kept, ignored, names, th)
        res["explain_method"] = "detection boxes"

        # 5. Background check: confident boxes that are NOT on the leaf
        off_leaf = [d for d in ignored if d["conf"] >= th["det_conf_low"]]
        signal = [d for d in dets if d["conf"] >= th["det_conf_low"]]
        if signal:
            res["leaf_focus"] = sum(d["conf"] for d in signal if d in kept) / sum(d["conf"] for d in signal)
        res["checks"].append({"gate": "model", "name": "Spots are on the leaf", "passed": not off_leaf,
                              "value": f"{len(off_leaf)} off-leaf box(es) ignored",
                              "tip": "Some detections were on the background, not the leaf."})
        if off_leaf:
            what = ", ".join(sorted({pretty(names[d["cls"]]) for d in off_leaf}))
            res["reasons"].append(f"Background trick caught: ignored {len(off_leaf)} detection(s) of "
                                  f"{what} that were outside the leaf (on the table/background).")

        # 6. How sure is it, per disease?
        best = {}
        for d in kept:
            best[d["cls"]] = max(best.get(d["cls"], 0.0), d["conf"])
        ranked = sorted(best.items(), key=lambda kv: -kv[1])
        res["top3"] = [{"label": pretty(names[c]), "prob": p} for c, p in ranked[:3]]
        top_c, top_p = ranked[0] if ranked else (None, 0.0)
        second = ranked[1][1] if len(ranked) > 1 else 0.0
        n_spots = sum(1 for d in kept if d["cls"] == top_c and d["conf"] >= th["det_conf_low"])
        res["checks"].append({"gate": "model", "name": "Model is confident",
                              "passed": top_p >= th["det_conf_high"] or top_p < th["det_conf_low"],
                              "value": f"best spot {round(top_p * 100)}%" if ranked else "no spots",
                              "tip": "Only faint detections. The model is unsure."})

        if top_p >= th["det_conf_high"]:
            if second >= th["det_conf_high"] and second >= th["det_close_call"] * top_p:
                alt = pretty(names[ranked[1][0]])
                res["reasons"].append(f"Two diseases look equally likely: '{pretty(names[top_c])}' "
                                      f"({round(top_p * 100)}%) and '{alt}' ({round(second * 100)}%).")
                res["reasons"].append("Ask an agronomist, or take a closer photo of one affected area.")
                res.update(label=pretty(names[top_c]), cls=names[top_c], confidence=top_p)
                return finish("UNCERTAIN")
            res.update(label=pretty(names[top_c]), cls=names[top_c], confidence=top_p)
            res["reasons"].insert(0, f"{pretty(names[top_c])}: {n_spots} affected area(s) found on the leaf, "
                                     f"strongest {round(top_p * 100)}% confident.")
            return finish("DISEASED")

        if top_p >= th["det_conf_low"]:
            res.update(label=pretty(names[top_c]), cls=names[top_c], confidence=top_p)
            res["reasons"].append(f"Possible '{pretty(names[top_c])}', but only {round(top_p * 100)}% confident. "
                                  f"Too faint to be sure.")
            res["reasons"].append("Take a closer, sharper photo of the spots, or ask an agronomist.")
            return finish("UNCERTAIN")

        res.update(label="No disease found", cls="healthy", confidence=1.0 - top_p)
        res["reasons"].insert(0, "No signs of: " + ", ".join(pretty(n) for n in names) + ".")
        res["reasons"].append("Note: the model only knows these diseases. Anything else needs an expert.")
        return finish("HEALTHY")


def draw_boxes(rgb, kept, ignored, names, th):
    """Green-ish boxes = counted (on the leaf). Grey dashed = ignored (off the leaf)."""
    import cv2

    img = rgb.copy()
    t = max(2, img.shape[1] // 300)
    for d in ignored:
        if d["conf"] < th["det_conf_low"]:
            continue
        x1, y1, x2, y2 = d["box"]
        for x in range(x1, x2, 14):
            cv2.line(img, (x, y1), (min(x + 7, x2), y1), (160, 160, 160), t)
            cv2.line(img, (x, y2), (min(x + 7, x2), y2), (160, 160, 160), t)
        for y in range(y1, y2, 14):
            cv2.line(img, (x1, y), (x1, min(y + 7, y2)), (160, 160, 160), t)
            cv2.line(img, (x2, y), (x2, min(y + 7, y2)), (160, 160, 160), t)
        cv2.putText(img, "ignored: off leaf", (x1 + 4, max(14, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX,
                    0.4 * t, (200, 200, 200), max(1, t // 2))
    for d in sorted(kept, key=lambda d: d["conf"]):
        if d["conf"] < th["det_conf_low"]:
            continue
        x1, y1, x2, y2 = d["box"]
        colour = (230, 60, 40) if d["conf"] >= th["det_conf_high"] else (240, 190, 30)
        cv2.rectangle(img, (x1, y1), (x2, y2), colour, t)
        label = f"{pretty(names[d['cls']])} {round(d['conf'] * 100)}%"
        (tw, tht), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45 * t, max(1, t // 2))
        cv2.rectangle(img, (x1, max(0, y1 - tht - 8)), (x1 + tw + 6, y1), colour, -1)
        cv2.putText(img, label, (x1 + 3, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45 * t, (255, 255, 255), max(1, t // 2))
    return img
