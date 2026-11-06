# 🌿 LeafGuard: The Lab-Coat Illusion

**A plant-disease detector that knows when it doesn't know.**

Our YOLO model finds 5 leaf diseases (Bacterial Spot, Early Blight, Late Blight, Powdery Mildew, Rust). On clean test photos it works well. But real users send blurry photos, dark photos, a thumb over the lens, a coffee mug, or a healthy leaf lying next to sick ones, and a raw model still answers. LeafGuard wraps the **unchanged model** with safety checks, so it says *"retake the photo"*, *"this isn't a leaf"* or *"not sure"* instead of giving a wrong answer. It also shows **why**, with boxes on the leaf.

Tested with our own model (`models/best.pt`, YOLOv10n) on a real powdery-mildew photo:

| Photo | Raw YOLO says | LeafGuard says |
|---|---|---|
| Powdery mildew leaf | Powdery mildew 93% ✅ | 🩺 Disease detected: Powdery mildew ✅ |
| Same photo, blurry | **"Healthy"** ❌ (missed the disease) | 📸 Retake ✅ |
| Same photo, dark | Powdery mildew 83% (a guess) | 📸 Retake ✅ |
| Same photo, thumb over lens | Powdery mildew 90% (a guess) | 📸 Retake ✅ |
| Coffee mug | **"Healthy"** (old `model.pt`: **"Rust 33%"**) ❌ | 🚫 Not a leaf ✅ |
| Healthy leaf with a sick leaf beside it | **Powdery mildew** ❌ | ✅ No disease, sick leaf's box ignored |

## How it works

```
photo ─► 1 Quality gate ─► 2 Is it a leaf? ─► 3 Find THE leaf ─► 4 YOLO boxes
             │                  │                                  │
          RETAKE           NOT A LEAF            5 keep only boxes ON the leaf (others ignored)
                                                                   │
                                     6 strong box = DISEASED · faint box = NOT SURE · none = NO DISEASE
```

1. **Quality gate:** blur (Laplacian variance), too dark, glare, blank or covered lens, finger on lens (a smooth, skin-coloured blob at the edge).
2. **Is it a leaf?** CLIP zero-shot ("looks like a coffee mug"). Falls back to a plant-colour check if CLIP can't load.
3. **Find the leaf:** colour segmentation grown from the green core, plus GrabCut. Only the **main, central leaf** counts.
4. **Detect:** our YOLO model, unchanged.
5. **Background check:** boxes that are not on the main leaf are ignored and shown dashed. This defeats the "healthy leaf on a sick leaf's table" trick.
6. **Honest decision:** a box ≥ `det_conf_high` means disease. A box between `det_conf_low` and high means "not sure". No box means "no disease found", with a note that the model only knows its 5 diseases. If two diseases are equally strong, it says "not sure which."

## Quick start (Windows)

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/smoke_test.py
streamlit run app.py
```

On Mac or Linux, activate with `source .venv/bin/activate`. The first run downloads CLIP (~600 MB) once. Use `python scripts/smoke_test.py --no-clip` to skip it.

## Models

`config.json` uses **`models/best.pt`** (YOLOv10n via the `ultralytics` package; mAP50 0.65, the more confident of our two):

```json
{ "framework": "yolo", "model_path": "models/best.pt", "input_size": [640, 640], "use_clip": true }
```

To use the older **`models/model.pt`** (original YOLOv5 repo format) instead, point to your Yolov5 folder:

```json
{ "framework": "yolov5", "model_path": "models/model.pt", "yolov5_repo": "C:/path/to/Yolov5",
  "input_size": [640, 640], "use_clip": true }
```

LeafGuard also supports classifiers: `"framework": "keras" | "torch" | "onnx"` with `class_names.txt` (see `leafguard/config.py`).

## Make the numbers (proof for the judges)

Use your Roboflow / YOLO dataset folders (each has `images/` and `labels/`):

```powershell
python scripts/calibrate.py --val_dir C:\path\to\dataset\valid
python scripts/stress_test.py --test_dir C:\path\to\dataset\test --ood_dir data\ood --healthy_dir data\healthy
```

- `calibrate.py` picks the box-confidence threshold where LeafGuard's diagnoses reach 97% accuracy, and saves it to `config.json`.
- `stress_test.py` builds blurry, dark, thumb-over-lens, healthy-on-sick-table and not-a-leaf versions of your test photos. It then compares the **unsafe answer rate** (confident and wrong) of the raw model vs LeafGuard, and writes `reports/stress_test.html`. The app's **Proof** tab shows it too.
- `data/ood/`: 20+ photos of non-leaf things (mug, hand, keyboard, floor).
- `data/healthy/`: 10+ healthy leaf photos. These enable the sick-table test and check the "no disease" answer.

Turn any real photo into bad-photo test cases with:

```powershell
python scripts/make_samples.py my_leaf.jpg
```

## Tuning

All thresholds are in `leafguard/config.py` (override any of them in `config.json` under `"thresholds"`). The app sidebar has live sliders.

## Project layout

```
app.py                    Streamlit demo (Diagnose / Proof / How it works)
config.json               which model to use
models/best.pt            our YOLOv10n disease detector (5 classes)
models/model.pt           our older YOLOv5s detector
leafguard/
  pipeline.py             the decision logic (classifier + detector modes)
  quality_gate.py         blur, light, finger, blank checks
  leaf_gate.py            CLIP / colour "is it a leaf?"
  segment.py              find the main leaf
  model_adapter.py        YOLO / Keras / PyTorch / ONNX loaders
  calibration.py          temperature scaling, ECE (classifiers)
  explain.py              Grad-CAM / occlusion heatmaps (classifiers)
  augment.py              blur, dark, thumb, background-swap generators
scripts/
  smoke_test.py           quick check on sample_images/
  calibrate.py            choose thresholds on validation data
  stress_test.py          raw model vs LeafGuard report
  detector_eval.py        YOLO versions of the two above
  make_samples.py         bad-photo versions of a real photo
```
