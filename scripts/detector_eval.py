"""Calibration + stress test for YOLO detector models (used automatically by calibrate.py / stress_test.py)."""
import json
import os
import time

import numpy as np

from dataset import is_yolo_dataset, list_images, read_rgb, yolo_images


def load_items(test_dir, healthy_dir, max_images):
    if not is_yolo_dataset(test_dir):
        raise SystemExit(f"{test_dir} must contain images/ and labels/ folders (YOLO / Roboflow export).")
    items = yolo_images(test_dir, max_images)
    if healthy_dir and os.path.isdir(healthy_dir):
        items += [(p, set()) for p in list_images(healthy_dir)[:max_images]]
    return items


def answer_ok(answer, labels):
    """answer = class id, or None for 'healthy'."""
    return (answer is None and not labels) or (answer is not None and answer in labels)


# ------------------------------------------------------------------ calibration
def calibrate_detector(guard, cfg, val_dir, target, max_images, save_config, config_path, root):
    from leafguard.segment import leaf_mask

    items = load_items(val_dir, None, max_images)
    print(f"Calibrating detector on {len(items)} images ...")
    th = cfg["thresholds"]
    rows = []
    for n, (path, labels) in enumerate(items, 1):
        rgb = read_rgb(path)
        if rgb is None:
            continue
        dets = guard.model.detect(rgb)
        mask, _ = leaf_mask(rgb)
        best = (None, 0.0)
        for d in dets:
            x1, y1, x2, y2 = d["box"]
            sub = mask[max(0, y1):max(0, y2), max(0, x1):max(0, x2)]
            if sub.size and (sub > 0).mean() >= th["det_on_leaf"] and d["conf"] > best[1]:
                best = (d["cls"], d["conf"])
        rows.append((best[0], best[1], labels))
        if n % 50 == 0:
            print(f"  {n}/{len(items)}")

    confs = np.array([r[1] for r in rows])
    correct = np.array([r[0] is not None and r[0] in r[2] for r in rows])
    diseased = np.array([bool(r[2]) for r in rows])
    best_thr = 0.9
    for thr in np.arange(0.30, 0.91, 0.01):  # never trust a box below 30%
        sel = confs >= thr
        if sel.sum() >= 5 and correct[sel].mean() >= target:
            best_thr = float(thr)
            break
    sel = confs >= best_thr
    th["det_conf_high"] = round(best_thr, 2)
    th["det_conf_low"] = round(max(0.15, min(0.20, best_thr / 2)), 2)
    save_config(cfg, config_path)
    summary = {
        "images": len(rows), "det_conf_high": best_thr,
        "precision_when_diagnosing": float(correct[sel].mean()) if sel.any() else None,
        "share_diagnosed": float(sel.mean()),
        "diseased_images_caught": float((sel & diseased).sum() / max(diseased.sum(), 1)),
        "precision_at_0.25_raw": float(correct[confs >= 0.25].mean()) if (confs >= 0.25).any() else None,
    }
    os.makedirs(os.path.join(root, "reports"), exist_ok=True)
    with open(os.path.join(root, "reports", "calibration.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print("\n=== Detector calibration (put this on a slide) ===")
    if summary["precision_at_0.25_raw"] is not None:
        print(f"Raw YOLO (conf 0.25) diagnosis accuracy : {summary['precision_at_0.25_raw']:.1%}")
    print(f"LeafGuard 'disease detected' threshold  : {best_thr:.2f}")
    if summary["precision_when_diagnosing"] is not None:
        print(f"Accuracy when LeafGuard diagnoses       : {summary['precision_when_diagnosing']:.1%}")
    print(f"Diseased images it confidently catches  : {summary['diseased_images_caught']:.1%}")
    print(f"(below the threshold it says 'not sure' instead of guessing)\nSaved thresholds to {config_path}")


# ------------------------------------------------------------------ stress test
def stress_detector(guard, cfg, args, root, render_html, scenarios, synthetic_ood):
    from leafguard.augment import add_finger, background_swap, blur, darken

    rng = np.random.default_rng(0)
    items = load_items(args.test_dir, args.healthy_dir, args.max_images)
    print(f"Leaf check: {guard.leaf_gate.method}. Building scenarios from {len(items)} test photos ...")
    names = guard.class_names
    cases, sick_photos, healthy_photos = [], [], []
    for path, labels in items:
        rgb = read_rgb(path)
        if rgb is None:
            continue
        cases += [("clean", rgb, labels), ("blurry", blur(rgb), labels), ("dark", darken(rgb), labels),
                  ("thumb", add_finger(rgb, rng), labels)]
        (sick_photos if labels else healthy_photos).append(rgb)
    for k, h in enumerate(healthy_photos):
        if sick_photos:
            cases.append(("sick_table", background_swap(h, sick_photos[k % len(sick_photos)]), set()))
    ood = [read_rgb(p) for p in list_images(args.ood_dir)] if args.ood_dir and os.path.isdir(args.ood_dir) else []
    cases += [("not_a_leaf", o, "ood") for o in [o for o in ood if o is not None] + synthetic_ood(rng)]

    stats = {s: {"n": 0, "raw_unsafe": 0, "raw_correct": 0, "lg_unsafe": 0, "lg_correct": 0, "lg_abstain": 0}
             for s in scenarios}
    t0 = time.time()
    for k, (scen, rgb, labels) in enumerate(cases, 1):
        r = guard.analyze(rgb, do_explain=False)
        s = stats[scen]
        s["n"] += 1
        raw = r["baseline"]["index"]
        raw_ok = labels != "ood" and answer_ok(None if raw == -1 else raw, labels)
        s["raw_correct"] += raw_ok
        s["raw_unsafe"] += not raw_ok
        if r["verdict"] in ("HEALTHY", "DISEASED"):
            ans = None if r["verdict"] == "HEALTHY" else names.index(r["cls"])
            ok = labels != "ood" and answer_ok(ans, labels)
            s["lg_correct"] += ok
            s["lg_unsafe"] += not ok
        else:
            s["lg_abstain"] += 1
        if k % 25 == 0:
            print(f"  {k}/{len(cases)}  ({time.time() - t0:.0f}s)")

    rows = []
    for scen, s in stats.items():
        if s["n"]:
            n = s["n"]
            rows.append({"scenario": scen, "description": scenarios[scen], "n": n,
                         "raw_unsafe_rate": s["raw_unsafe"] / n, "leafguard_unsafe_rate": s["lg_unsafe"] / n,
                         "raw_accuracy": s["raw_correct"] / n, "leafguard_correct": s["lg_correct"] / n,
                         "leafguard_abstain": s["lg_abstain"] / n})
    hard = [r for r in rows if r["scenario"] != "clean"]
    tot = max(sum(r["n"] for r in hard), 1)
    out = {"model": cfg["framework"], "leaf_check": guard.leaf_gate.method, "rows": rows,
           "hard_cases_unsafe": {"raw": sum(r["raw_unsafe_rate"] * r["n"] for r in hard) / tot,
                                 "leafguard": sum(r["leafguard_unsafe_rate"] * r["n"] for r in hard) / tot}}
    os.makedirs(os.path.join(root, "reports"), exist_ok=True)
    with open(os.path.join(root, "reports", "stress_test.json"), "w") as f:
        json.dump(out, f, indent=2)
    with open(os.path.join(root, "reports", "stress_test.html"), "w", encoding="utf-8") as f:
        f.write(render_html(out))
    return out
