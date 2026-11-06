"""Quick check that everything works: runs LeafGuard on every photo in sample_images/.

    python scripts/smoke_test.py            (uses config.json)
    python scripts/smoke_test.py --no-clip  (skip the CLIP download)
"""
import argparse
import glob
import os
import sys

import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from leafguard import LeafGuard, load_config  # noqa: E402


def main():
    try:
        sys.stdout.reconfigure(errors="replace")  # Windows terminals + unusual class names
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(ROOT, "config.json"))
    ap.add_argument("--images", default=os.path.join(ROOT, "sample_images"))
    ap.add_argument("--no-clip", action="store_true")
    args = ap.parse_args()

    cfg = load_config(args.config)
    guard = LeafGuard(cfg, load_clip=not args.no_clip)
    print(f"Model: {cfg['framework']} | classes: {len(guard.class_names)} | leaf check: {guard.leaf_gate.method}")
    if guard.leaf_gate.clip_error:
        print(f"  (CLIP not used: {guard.leaf_gate.clip_error})")
    print()
    print(f"{'image':38} {'raw model says':32} {'LeafGuard says'}")
    print("-" * 100)
    for path in sorted(glob.glob(os.path.join(args.images, "*"))):
        img = cv2.imread(path)
        if img is None:
            continue
        r = guard.analyze(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        b = r["baseline"]
        raw = b['label'][:24] + (f" {round(b['confidence'] * 100)}%" if b['confidence'] is not None else "")
        lg = r["verdict"] + (f": {r['label']}" if r["verdict"] in ("HEALTHY", "DISEASED") else "")
        print(f"{os.path.basename(path)[:38]:38} {raw:32} {lg}")
        for reason in r["reasons"][:2]:
            print(f"{'':38}   - {reason}")


if __name__ == "__main__":
    main()
