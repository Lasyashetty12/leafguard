"""Make your model's confidence HONEST, then choose when LeafGuard should say "not sure".

    python scripts/calibrate.py --val_dir data/val --target_accuracy 0.97

data/val must look like:  data/val/<class name>/*.jpg   (images your model was NOT trained on)
For YOLO models, point --val_dir at your Roboflow/YOLO 'valid' folder (with images/ and labels/).

What it does
  1. Runs your model on the leaf-only version of each validation photo.
  2. Fits a 'temperature' so that 90% confidence really means ~90% correct (temperature scaling).
  3. Picks the lowest confidence threshold where the answers LeafGuard gives are >= target accuracy.
  4. Saves both into config.json and prints before/after numbers for your slides.
"""
import argparse
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dataset import labelled_images, read_rgb  # noqa: E402
from leafguard import load_config, save_config  # noqa: E402
from leafguard.calibration import choose_threshold, ece, fit_temperature, softmax  # noqa: E402
from leafguard.model_adapter import load_model  # noqa: E402
from leafguard.segment import leaf_mask, leaf_only  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--val_dir", required=True)
    ap.add_argument("--config", default=os.path.join(ROOT, "config.json"))
    ap.add_argument("--target_accuracy", type=float, default=0.97)
    ap.add_argument("--per_class", type=int, default=60, help="max images per class (speed)")
    ap.add_argument("--max_images", type=int, default=200, help="(YOLO models) max validation images")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if cfg["framework"].lower() in ("yolo", "ultralytics", "yolov5"):
        from detector_eval import calibrate_detector
        from leafguard import LeafGuard

        guard = LeafGuard(cfg, load_clip=False)
        calibrate_detector(guard, cfg, args.val_dir, args.target_accuracy, args.max_images,
                           save_config, args.config, ROOT)
        return
    model = load_model(cfg)
    items = labelled_images(args.val_dir, model.class_names, args.per_class)
    print(f"Calibrating on {len(items)} images ...")

    logits, labels, raw_correct = [], [], []
    for n, (path, y) in enumerate(items, 1):
        rgb = read_rgb(path)
        if rgb is None:
            continue
        mask, _ = leaf_mask(rgb)
        clean, _ = leaf_only(rgb, mask, tuple(cfg["neutral_background"]))
        both = model.logits([clean, rgb])
        logits.append(both[0])
        raw_correct.append(int(both[1].argmax()) == y)
        labels.append(y)
        if n % 50 == 0:
            print(f"  {n}/{len(items)}")
    logits, labels = np.array(logits), np.array(labels)

    p_before = softmax(logits, 1.0)
    T = fit_temperature(logits, labels)
    p_after = softmax(logits, T)
    conf, correct = p_after.max(1), p_after.argmax(1) == labels
    thr = choose_threshold(conf, correct, args.target_accuracy)
    answered = conf >= thr

    cfg["temperature"] = round(T, 4)
    cfg["thresholds"]["min_confidence"] = round(thr, 4)
    save_config(cfg, args.config)

    summary = {
        "images": int(len(labels)),
        "accuracy_full_photo": float(np.mean(raw_correct)),
        "accuracy_leaf_only": float(correct.mean()),
        "temperature": T,
        "ece_before": ece(p_before, labels),
        "ece_after": ece(p_after, labels),
        "min_confidence": thr,
        "coverage": float(answered.mean()),
        "accuracy_when_answering": float(correct[answered].mean()) if answered.any() else None,
    }
    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
    with open(os.path.join(ROOT, "reports", "calibration.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print("\n=== Calibration result (put this on a slide) ===")
    print(f"Accuracy on full photos (raw)     : {summary['accuracy_full_photo']:.1%}")
    print(f"Accuracy on leaf-only images      : {summary['accuracy_leaf_only']:.1%}")
    if summary["accuracy_leaf_only"] < summary["accuracy_full_photo"] - 0.05:
        print("  NOTE: your model was trained with backgrounds, so it is weaker on cut-out leaves.")
        print("        Try setting 'neutral_background' in config.json to your training background colour")
        print("        (e.g. [0,0,0] for black, [255,255,255] for white), or fine-tune on cut-out leaves.")
    print(f"Calibration error (ECE) before    : {summary['ece_before']:.3f}")
    print(f"Calibration error (ECE) after     : {summary['ece_after']:.3f}   (lower = more honest)")
    print(f"Temperature                       : {T:.3f}")
    print(f"Abstain below confidence          : {thr:.2f}")
    print(f"Answers given (coverage)          : {summary['coverage']:.1%}")
    if summary["accuracy_when_answering"] is not None:
        print(f"Accuracy on answers given         : {summary['accuracy_when_answering']:.1%}")
    print(f"\nSaved temperature + threshold to {args.config}")


if __name__ == "__main__":
    main()
