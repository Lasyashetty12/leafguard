"""Load and save LeafGuard settings (config.json)."""
import copy
import json
import os

DEFAULTS = {
    # ---- YOUR MODEL --------------------------------------------------------
    # framework: "keras" (.h5/.keras), "torch" (.pt/.pth full model or TorchScript),
    #            "onnx" (.onnx), or "demo" (built-in fake model, no file needed)
    "framework": "demo",
    "model_path": "models/your_model.h5",
    "class_names_file": "class_names.txt",
    "input_size": [224, 224],  # [height, width] your model was trained on
    # preprocess: how pixels were scaled during YOUR training
    #   "divide255"  -> x / 255                 (most custom Keras CNNs)
    #   "imagenet"   -> (x/255 - mean) / std    (most PyTorch / torchvision models)
    #   "minus1to1"  -> x / 127.5 - 1           (Keras MobileNet / EfficientNetV2 preprocess_input)
    #   "caffe"      -> BGR minus ImageNet mean (Keras ResNet50/VGG preprocess_input)
    #   "none"       -> raw 0..255 floats       (model has its own Rescaling layer, e.g. EfficientNet)
    "preprocess": "divide255",
    "healthy_keyword": "healthy",  # class names containing this word count as healthy

    # ---- SAFETY LAYER ------------------------------------------------------
    "use_clip": True,          # use CLIP for "is this a leaf?" (auto-falls back to colour check)
    "clip_model": "openai/clip-vit-base-patch32",
    "temperature": 1.0,        # set automatically by scripts/calibrate.py
    "neutral_background": [128, 128, 128],
    "explain": True,           # compute a heatmap of where the model looked

    "thresholds": {
        "min_side": 96,              # px; smaller images are rejected
        "blur_min": 35.0,            # Laplacian variance; lower = blurrier
        "dark_max_mean": 40.0,       # mean brightness below this = too dark
        "bright_min_mean": 235.0,    # mean brightness above this = washed out
        "overexposed_frac": 0.45,    # fraction of blown-out pixels
        "flat_std_min": 12.0,        # almost no detail = lens covered / blank
        "finger_frac": 0.15,         # blurry skin-coloured blob touching the edge
        "plant_frac_min": 0.06,      # colour check: min share of plant-coloured pixels
        "clip_leaf_min": 0.50,       # CLIP check: min probability of "leaf"
        "min_leaf_area": 0.03,       # leaf must fill at least 3% of the photo
        "min_confidence": 0.70,      # calibrated confidence needed to give a diagnosis
        "min_margin": 0.20,          # gap between best and second-best class
        "max_entropy": 0.60,         # normalised uncertainty (0 = sure, 1 = clueless)
        "min_leaf_focus": 0.40,      # share of the model's attention that is on the leaf
        # --- only for YOLO detector models ---
        "det_conf_high": 0.45,       # a box this confident = disease detected
        "det_conf_low": 0.20,        # boxes between low and high = "possible, not sure"
        "det_on_leaf": 0.50,         # box must be at least this much on the leaf, else ignored
        "det_close_call": 0.80,      # 2nd disease within 80% of the top one's score = "not sure which"
    },
}


def _deep_update(base, new):
    for key, value in new.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def load_config(path="config.json"):
    cfg = copy.deepcopy(DEFAULTS)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _deep_update(cfg, json.load(f))
    cfg["_base_dir"] = os.path.dirname(os.path.abspath(path))
    return cfg


def save_config(cfg, path="config.json"):
    clean = {k: v for k, v in cfg.items() if not k.startswith("_")}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(clean, f, indent=2)


def resolve(cfg, rel_path):
    """Make a path from config.json relative to the folder config.json lives in."""
    if os.path.isabs(rel_path):
        return rel_path
    return os.path.join(cfg.get("_base_dir", "."), rel_path)
