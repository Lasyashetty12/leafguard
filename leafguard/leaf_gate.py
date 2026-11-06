"""Gate 2: is there actually a leaf in the photo?

Uses CLIP (a general-purpose vision-language model) when available, so it can say
"this looks like a coffee mug". Falls back to a plant-colour check otherwise.
"""
import numpy as np

from .segment import plant_mask
from .quality_gate import resize_max

LEAF_PROMPTS = [
    "a close-up photo of a plant leaf",
    "a photo of a diseased leaf with spots",
    "a photo of a healthy green leaf",
    "a photo of a crop leaf in a field",
    "a photo of a yellowing leaf",
]
OTHER_PROMPTS = {
    "a coffee mug or cup": "a photo of a coffee mug or cup",
    "a finger over the lens": "a blurry photo of a finger covering the camera lens",
    "a hand": "a photo of a human hand",
    "a person": "a photo of a person's face",
    "an animal": "a photo of a pet or animal",
    "a table or floor": "a photo of an empty table or floor",
    "a screen or text": "a screenshot or a photo of text",
    "a household object": "a photo of a household object",
    "a dark / black photo": "a completely dark black photo",
    "food": "a photo of food on a plate",
    "a flower": "a photo of a flower",
    "a fruit or vegetable": "a photo of a fruit or vegetable",
    "a car or vehicle": "a photo of a car or vehicle",
}


class LeafGate:
    def __init__(self, cfg):
        self.th = cfg["thresholds"]
        self.clip = None
        self.clip_error = None
        if cfg.get("use_clip", True):
            try:
                import torch  # noqa: F401
                from transformers import CLIPModel, CLIPProcessor

                self.processor = CLIPProcessor.from_pretrained(cfg["clip_model"])
                self.clip = CLIPModel.from_pretrained(cfg["clip_model"]).eval()
                self.prompts = LEAF_PROMPTS + list(OTHER_PROMPTS.values())
                self.other_names = list(OTHER_PROMPTS.keys())
                with torch.no_grad():
                    tok = self.processor(text=self.prompts, return_tensors="pt", padding=True)
                    t = self.clip.get_text_features(**tok)
                    t = t if isinstance(t, torch.Tensor) else t.pooler_output
                    self.text_emb = t / t.norm(dim=-1, keepdim=True)
            except Exception as e:  # no internet / not installed -> colour fallback
                self.clip = None
                self.clip_error = f"{type(e).__name__}: {e}"[:200]

    @property
    def method(self):
        return "CLIP zero-shot" if self.clip is not None else "plant-colour check"

    def _clip_scores(self, rgb):
        import torch

        with torch.no_grad():
            px = self.processor(images=resize_max(rgb, 448), return_tensors="pt")
            v = self.clip.get_image_features(**px)
            v = v if isinstance(v, torch.Tensor) else v.pooler_output
            v = v / v.norm(dim=-1, keepdim=True)
            logits = 100.0 * v @ self.text_emb.T
            p = logits.softmax(dim=-1)[0].numpy()
        n = len(LEAF_PROMPTS)
        leaf_p = float(p[:n].sum())
        other = p[n:]
        j = int(np.argmax(other))
        return leaf_p, self.other_names[j], float(other[j])

    def check(self, rgb):
        small = resize_max(rgb, 384)
        mask, green = plant_mask(small)
        plant_frac = float(mask.mean() / 255)
        green_frac = float(green.mean())
        result = {"plant_frac": plant_frac, "method": self.method, "looks_like": None}

        if self.clip is not None:
            leaf_p, other_name, other_p = self._clip_scores(rgb)
            result.update(leaf_prob=leaf_p, looks_like=other_name if leaf_p < 0.5 else None)
            passed = leaf_p >= self.th["clip_leaf_min"]
            value = f"{round(leaf_p * 100)}% leaf"
            if not passed:
                value += f" (looks like {other_name})"
        else:
            # Leaves must contain plant colours, and some real green (stops brown tables passing)
            passed = plant_frac >= self.th["plant_frac_min"] and green_frac >= 0.02
            result["leaf_prob"] = None
            value = f"{round(plant_frac * 100)}% plant-coloured"

        result["check"] = {
            "gate": "leaf", "name": "Is it a leaf?", "passed": bool(passed), "value": value,
            "tip": "No leaf found. Photograph a single leaf filling most of the frame.",
        }
        return result
