"""Shared helper: read an image folder laid out as  folder/<class_name>/*.jpg"""
import os
import random

import cv2

IMG_EXT = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def read_rgb(path):
    img = cv2.imread(path)
    return None if img is None else cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def list_images(folder):
    return sorted(os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(IMG_EXT))


def labelled_images(root, class_names, per_class=None, seed=0):
    """Return [(path, class_index)]. Sub-folder names must match class_names.txt."""
    norm = {c.lower().strip(): i for i, c in enumerate(class_names)}
    items, unknown = [], []
    for sub in sorted(os.listdir(root)):
        full = os.path.join(root, sub)
        if not os.path.isdir(full):
            continue
        idx = norm.get(sub.lower().strip())
        if idx is None:
            unknown.append(sub)
            continue
        files = list_images(full)
        random.Random(seed).shuffle(files)
        items += [(f, idx) for f in files[:per_class]]
    if unknown:
        print(f"WARNING: these folders don't match any name in class_names.txt and were skipped: {unknown}")
    if not items:
        raise SystemExit(f"No labelled images found in {root}. Expected {root}/<class name>/*.jpg")
    return items


def is_yolo_dataset(root):
    return os.path.isdir(os.path.join(root, "images")) and os.path.isdir(os.path.join(root, "labels"))


def yolo_images(root, max_images=None, seed=0):
    """YOLO / Roboflow layout:  root/images/x.jpg  +  root/labels/x.txt  ("class cx cy w h" per line).
    Returns [(path, set_of_class_ids)]. An empty set means the image has no disease (healthy)."""
    files = list_images(os.path.join(root, "images"))
    random.Random(seed).shuffle(files)
    out = []
    for f in files[:max_images]:
        txt = os.path.join(root, "labels", os.path.splitext(os.path.basename(f))[0] + ".txt")
        classes = set()
        if os.path.exists(txt):
            with open(txt) as fh:
                classes = {int(float(line.split()[0])) for line in fh if line.strip()}
        out.append((f, classes))
    if not out:
        raise SystemExit(f"No images found in {root}/images")
    return out
