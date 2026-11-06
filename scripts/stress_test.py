"""THE PROOF: raw model vs LeafGuard on photos that break normal models.

    python scripts/stress_test.py --test_dir data/test --ood_dir data/ood

data/test : <class name>/*.jpg   (held-out leaf photos)
            or, for YOLO models, a Roboflow/YOLO folder with images/ and labels/ (e.g. dataset/test)
data/ood  : any NON-leaf photos  (mugs, hands, keyboards, floors, faces...)  - optional but recommended

Scenarios (built automatically from your test photos):
  clean          the normal test photo
  blurry         heavy motion/focus blur
  dark           photo taken at night
  thumb          a thumb partly over the lens
  sick_table     a HEALTHY leaf pasted onto the background of a DISEASED photo
  not_a_leaf     your data/ood photos (+ a few generated ones)

Main metric: UNSAFE ANSWER RATE = how often a confident, WRONG diagnosis reaches the farmer.
The raw model never says "I don't know", so every wrong output counts as unsafe.
Writes reports/stress_test.json and reports/stress_test.html.
"""
import argparse
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dataset import labelled_images, list_images, read_rgb  # noqa: E402
from leafguard import LeafGuard, load_config  # noqa: E402
from leafguard.augment import add_finger, background_swap, blur, darken, empty_table  # noqa: E402

SCENARIOS = {
    "clean": "Normal test photo",
    "blurry": "Out-of-focus photo",
    "dark": "Photo taken in the dark",
    "thumb": "Thumb over the lens",
    "sick_table": "Healthy leaf on a sick leaf's table",
    "not_a_leaf": "Not a leaf at all (mug, hand, floor...)",
}
# What a SAFE answer looks like in each scenario
SAFE_ABSTAIN = {"clean": set(), "blurry": {"RETAKE", "UNCERTAIN"}, "dark": {"RETAKE", "UNCERTAIN"},
                "thumb": {"RETAKE", "UNCERTAIN"}, "sick_table": {"UNCERTAIN", "RETAKE"},
                "not_a_leaf": {"NOT_A_LEAF", "RETAKE", "UNCERTAIN"}}


def synthetic_ood(rng, n=6):
    """Simple stand-ins for everyday non-leaf objects (boxes, cups, screens) in non-plant colours.
    Add REAL photos to data/ood for a stronger test."""
    import cv2

    imgs = []
    for k in range(n):
        h = w = 320
        hue = int(rng.choice([rng.integers(0, 10), rng.integers(100, 170)]))
        hsv = np.full((h, w, 3), (hue, int(rng.integers(20, 160)), int(rng.integers(90, 230))), np.uint8)
        img = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB).astype(np.float32)
        img = np.clip(img + rng.normal(0, 8, img.shape), 0, 255).astype(np.uint8)
        shape_hue = int(rng.choice([rng.integers(0, 10), rng.integers(100, 170)]))  # never plant-green
        colour = tuple(int(c) for c in cv2.cvtColor(np.uint8([[[shape_hue, 200, 200]]]), cv2.COLOR_HSV2RGB)[0, 0])
        if k % 3 == 0:
            cv2.rectangle(img, (80, 60), (240, 260), colour, -1)
        elif k % 3 == 1:
            cv2.circle(img, (160, 160), 90, colour, -1)
        else:
            cv2.putText(img, "TEXT 123", (30, 170), cv2.FONT_HERSHEY_SIMPLEX, 1.6, colour, 4)
        imgs.append(img)
    return imgs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test_dir", required=True)
    ap.add_argument("--ood_dir", default=None)
    ap.add_argument("--config", default=os.path.join(ROOT, "config.json"))
    ap.add_argument("--per_class", type=int, default=15)
    ap.add_argument("--healthy_dir", default=None, help="(YOLO models) folder of HEALTHY leaf photos")
    ap.add_argument("--max_images", type=int, default=80, help="(YOLO models) max test images")
    ap.add_argument("--no-clip", action="store_true")
    args = ap.parse_args()

    cfg = load_config(args.config)
    guard = LeafGuard(cfg, load_clip=not args.no_clip)
    if guard.is_detector:
        from detector_eval import stress_detector

        out = stress_detector(guard, cfg, args, ROOT, render_html, SCENARIOS, synthetic_ood)
        print_summary(out["rows"], out["hard_cases_unsafe"])
        return
    names = guard.class_names
    healthy_ids = [i for i, c in enumerate(names) if cfg["healthy_keyword"].lower() in c.lower()]
    rng = np.random.default_rng(0)
    items = labelled_images(args.test_dir, names, args.per_class)
    print(f"Leaf check: {guard.leaf_gate.method}. Building scenarios from {len(items)} test photos ...")

    cases = []  # (scenario, rgb, true_index or None)
    sick_backgrounds = []
    for path, y in items:
        rgb = read_rgb(path)
        if rgb is None:
            continue
        cases += [("clean", rgb, y), ("blurry", blur(rgb), y), ("dark", darken(rgb), y),
                  ("thumb", add_finger(rgb, rng), y)]
        if y not in healthy_ids and len(sick_backgrounds) < 20:
            sick_backgrounds.append(empty_table(rgb))
    healthy_items = [(p, y) for p, y in items if y in healthy_ids]
    for n, (path, y) in enumerate(healthy_items):
        if sick_backgrounds:
            cases.append(("sick_table", background_swap(read_rgb(path), sick_backgrounds[n % len(sick_backgrounds)]), y))
    ood = [read_rgb(p) for p in list_images(args.ood_dir)] if args.ood_dir and os.path.isdir(args.ood_dir) else []
    ood = [o for o in ood if o is not None] + synthetic_ood(rng)
    cases += [("not_a_leaf", o, None) for o in ood]

    stats = {s: {"n": 0, "raw_unsafe": 0, "raw_correct": 0, "lg_unsafe": 0, "lg_correct": 0, "lg_abstain": 0}
             for s in SCENARIOS}
    t0 = time.time()
    for k, (scen, rgb, y) in enumerate(cases, 1):
        r = guard.analyze(rgb, do_explain=False)
        s = stats[scen]
        s["n"] += 1
        raw_ok = y is not None and r["baseline"]["index"] == y
        s["raw_correct"] += raw_ok
        s["raw_unsafe"] += not raw_ok
        if r["verdict"] in ("HEALTHY", "DISEASED"):
            ok = y is not None and names.index(r["cls"]) == y
            s["lg_correct"] += ok
            s["lg_unsafe"] += not ok
        else:
            s["lg_abstain"] += 1
        if k % 25 == 0:
            print(f"  {k}/{len(cases)}  ({time.time() - t0:.0f}s)")

    rows = []
    for scen, s in stats.items():
        if s["n"] == 0:
            continue
        n = s["n"]
        rows.append({"scenario": scen, "description": SCENARIOS[scen], "n": n,
                     "raw_unsafe_rate": s["raw_unsafe"] / n, "leafguard_unsafe_rate": s["lg_unsafe"] / n,
                     "raw_accuracy": s["raw_correct"] / n, "leafguard_correct": s["lg_correct"] / n,
                     "leafguard_abstain": s["lg_abstain"] / n})
    tot_n = sum(r["n"] for r in rows if r["scenario"] != "clean")
    hard = {"raw": sum(r["raw_unsafe_rate"] * r["n"] for r in rows if r["scenario"] != "clean") / max(tot_n, 1),
            "leafguard": sum(r["leafguard_unsafe_rate"] * r["n"] for r in rows if r["scenario"] != "clean") / max(tot_n, 1)}

    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
    out = {"model": cfg["framework"], "leaf_check": guard.leaf_gate.method, "rows": rows, "hard_cases_unsafe": hard}
    with open(os.path.join(ROOT, "reports", "stress_test.json"), "w") as f:
        json.dump(out, f, indent=2)
    with open(os.path.join(ROOT, "reports", "stress_test.html"), "w", encoding="utf-8") as f:
        f.write(render_html(out))

    print_summary(rows, hard)


def print_summary(rows, hard):
    print("\n=== UNSAFE ANSWER RATE (confident + wrong). Lower is better ===")
    print(f"{'scenario':12} {'n':>4} {'raw model':>10} {'LeafGuard':>10}  LeafGuard said 'retake/not sure'")
    for r in rows:
        print(f"{r['scenario']:12} {r['n']:>4} {r['raw_unsafe_rate']:>10.0%} {r['leafguard_unsafe_rate']:>10.0%}  {r['leafguard_abstain']:.0%}")
    print(f"\nAll hard cases: raw model {hard['raw']:.0%} unsafe  ->  LeafGuard {hard['leafguard']:.0%} unsafe")
    print("Report: reports/stress_test.html")


def render_html(out):
    bars = ""
    for r in out["rows"]:
        bars += f"""
        <div class="row"><div class="lab"><b>{r['description']}</b><span>{r['n']} photos</span></div>
          <div class="bars">
            <div class="bar raw" style="width:{r['raw_unsafe_rate'] * 100:.1f}%"><i>{r['raw_unsafe_rate']:.0%}</i></div>
            <div class="bar lg" style="width:{max(r['leafguard_unsafe_rate'] * 100, 0.6):.1f}%"><i>{r['leafguard_unsafe_rate']:.0%}</i></div>
          </div></div>"""
    h = out["hard_cases_unsafe"]
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>LeafGuard Stress Test</title>
<meta name="viewport" content="width=device-width,initial-scale=1"><style>
body{{font-family:system-ui,sans-serif;max-width:860px;margin:32px auto;padding:0 16px;color:#1d2a1f;background:#f7f8f4}}
h1{{margin-bottom:4px}} .sub{{color:#5b6b5e;margin-top:0}}
.big{{display:flex;gap:16px;margin:24px 0}} .big div{{flex:1;background:#fff;border-radius:12px;padding:16px;border:1px solid #e1e6dc}}
.big b{{font-size:40px;display:block}} .r b{{color:#c0392b}} .g b{{color:#2e7d32}}
.row{{display:flex;gap:16px;align-items:center;margin:14px 0}} .lab{{width:260px}} .lab span{{display:block;color:#7a867c;font-size:13px}}
.bars{{flex:1}} .bar{{height:22px;border-radius:4px;margin:3px 0;position:relative}} .bar i{{position:absolute;left:calc(100% + 6px);font-size:13px;font-style:normal}}
.raw{{background:#e57373}} .lg{{background:#66bb6a}} .key span{{display:inline-block;width:12px;height:12px;border-radius:3px;margin:0 6px 0 16px}}
</style></head><body><h1>LeafGuard stress test</h1>
<p class="sub">Unsafe answer rate = a confident but wrong diagnosis reaching the user. Lower is better. Model: {out['model']} · Leaf check: {out['leaf_check']}</p>
<div class="big"><div class="r"><b>{h['raw']:.0%}</b>raw model unsafe on hard photos</div>
<div class="g"><b>{h['leafguard']:.0%}</b>LeafGuard unsafe on hard photos</div></div>
<p class="key"><span style="background:#e57373"></span>Raw model <span style="background:#66bb6a"></span>LeafGuard</p>
{bars}</body></html>"""


if __name__ == "__main__":
    main()
