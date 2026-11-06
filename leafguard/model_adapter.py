"""Plug YOUR existing leaf-disease model into LeafGuard.

Every adapter exposes the same three things:
    class_names              list of class labels
    logits(list_of_rgb)      -> np.ndarray [N, C]  (log-probabilities are fine)
    gradcam(rgb, class_idx)  -> heatmap [H, W] in 0..1, or None if not supported
"""
import os

import cv2
import numpy as np

from .config import resolve

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], np.float32)


def load_class_names(cfg, n_outputs=None):
    path = resolve(cfg, cfg["class_names_file"])
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            names = [line.strip() for line in f if line.strip()]
        if n_outputs and len(names) != n_outputs:
            raise ValueError(f"class_names.txt has {len(names)} names but the model outputs "
                             f"{n_outputs} classes. They must match, in training order.")
        return names
    if n_outputs:
        return [f"class_{i}" for i in range(n_outputs)]
    raise FileNotFoundError(path)


def preprocess(batch_rgb, size_hw, mode):
    h, w = size_hw
    x = np.stack([cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA) for im in batch_rgb])
    x = x.astype(np.float32)
    if mode == "divide255":
        x = x / 255.0
    elif mode == "imagenet":
        x = (x / 255.0 - IMAGENET_MEAN) / IMAGENET_STD
    elif mode == "minus1to1":
        x = x / 127.5 - 1.0
    elif mode == "caffe":
        x = x[..., ::-1] - np.array([103.939, 116.779, 123.68], np.float32)
    elif mode != "none":
        raise ValueError(f"Unknown preprocess mode: {mode}")
    return x


def to_logits(out):
    """Turn model outputs into logits. Softmax outputs become log-probabilities."""
    out = np.asarray(out, dtype=np.float64)
    if out.min() >= 0 and np.allclose(out.sum(axis=1), 1.0, atol=1e-3):
        return np.log(np.clip(out, 1e-12, 1.0))
    return out


def _normalise_cam(cam, out_hw):
    cam = np.maximum(cam, 0)
    if cam.max() <= 0:
        return None
    cam = cam / cam.max()
    return cv2.resize(cam.astype(np.float32), (out_hw[1], out_hw[0]), interpolation=cv2.INTER_CUBIC).clip(0, 1)


# --------------------------------------------------------------------------- Keras
class KerasModel:
    def __init__(self, cfg):
        import tensorflow as tf

        self.tf = tf
        self.model = tf.keras.models.load_model(resolve(cfg, cfg["model_path"]), compile=False)
        shape = self.model.input_shape
        shape = shape[0] if isinstance(shape, list) else shape
        self.size = tuple(cfg["input_size"])
        if shape[1] and shape[2]:
            self.size = (int(shape[1]), int(shape[2]))
        self.mode = cfg["preprocess"]
        n_out = int(self.model.output_shape[-1])
        self.class_names = load_class_names(cfg, n_out)

    def logits(self, batch_rgb):
        x = preprocess(batch_rgb, self.size, self.mode)
        return to_logits(self.model(x, training=False).numpy())

    def _conv_layer(self):
        for layer in reversed(self.model.layers):
            try:
                if len(layer.output.shape) == 4:
                    return layer
            except Exception:
                continue
        return None

    def gradcam(self, rgb, idx):
        tf = self.tf
        layer = self._conv_layer()
        if layer is None:
            return None
        x = tf.convert_to_tensor(preprocess([rgb], self.size, self.mode))
        try:
            if isinstance(self.model, tf.keras.Sequential):
                with tf.GradientTape() as tape:
                    h, conv = x, None
                    for lyr in self.model.layers:
                        h = lyr(h, training=False)
                        if lyr is layer:
                            conv = h
                            tape.watch(conv)
                    score = h[:, idx]
            else:
                gm = tf.keras.Model(self.model.inputs, [layer.output, self.model.output])
                with tf.GradientTape() as tape:
                    conv, out = gm(x, training=False)
                    score = out[:, idx]
            grads = tape.gradient(score, conv)
            if grads is None:
                return None
            weights = tf.reduce_mean(grads, axis=(0, 1, 2))
            cam = tf.reduce_sum(conv[0] * weights, axis=-1).numpy()
            return _normalise_cam(cam, rgb.shape[:2])
        except Exception:
            return None


# --------------------------------------------------------------------------- PyTorch
def build_torch_model(num_classes):
    """ONLY needed if you saved a state_dict (torch.save(model.state_dict(), ...)).
    Re-create the SAME architecture you trained, e.g.:

        import torchvision
        m = torchvision.models.resnet18()
        m.fc = torch.nn.Linear(m.fc.in_features, num_classes)
        return m
    """
    raise NotImplementedError(
        "Your .pth file contains only weights (a state_dict). Open leafguard/model_adapter.py, "
        "fill in build_torch_model() with your network architecture, and run again.")


class TorchModel:
    def __init__(self, cfg):
        import torch

        self.torch = torch
        path = resolve(cfg, cfg["model_path"])
        try:
            obj = torch.jit.load(path, map_location="cpu")
        except Exception:
            obj = torch.load(path, map_location="cpu", weights_only=False)
        if isinstance(obj, dict):
            state = obj.get("state_dict", obj.get("model_state_dict", obj))
            names = load_class_names(cfg)
            obj = build_torch_model(len(names))
            obj.load_state_dict(state)
        self.model = obj.eval()
        self.size = tuple(cfg["input_size"])
        self.mode = cfg["preprocess"]
        with torch.no_grad():
            n_out = self.model(torch.zeros(1, 3, *self.size)).shape[-1]
        self.class_names = load_class_names(cfg, int(n_out))

    def _tensor(self, batch_rgb):
        x = preprocess(batch_rgb, self.size, self.mode)
        return self.torch.from_numpy(np.ascontiguousarray(x.transpose(0, 3, 1, 2)))

    def logits(self, batch_rgb):
        with self.torch.no_grad():
            return to_logits(self.model(self._tensor(batch_rgb)).numpy())

    def gradcam(self, rgb, idx):
        torch = self.torch
        convs = [m for m in self.model.modules() if isinstance(m, torch.nn.Conv2d)]
        if not convs:
            return None
        store = {}

        def hook(_, __, out):
            store["act"] = out
            out.register_hook(lambda g: store.__setitem__("grad", g))

        handle = convs[-1].register_forward_hook(hook)
        try:
            x = self._tensor([rgb]).requires_grad_(True)
            out = self.model(x)
            self.model.zero_grad()
            out[0, idx].backward()
            act, grad = store["act"][0].detach(), store["grad"][0].detach()
            cam = (grad.mean(dim=(1, 2))[:, None, None] * act).sum(0).numpy()
            return _normalise_cam(cam, rgb.shape[:2])
        except Exception:
            return None
        finally:
            handle.remove()


# --------------------------------------------------------------------------- ONNX
class OnnxModel:
    def __init__(self, cfg):
        import onnxruntime as ort

        self.sess = ort.InferenceSession(resolve(cfg, cfg["model_path"]), providers=["CPUExecutionProvider"])
        inp = self.sess.get_inputs()[0]
        self.input_name = inp.name
        shape = inp.shape
        self.fixed_batch_1 = shape[0] == 1
        self.nchw = shape[1] == 3
        self.size = tuple(cfg["input_size"])
        dims = shape[2:4] if self.nchw else shape[1:3]
        if all(isinstance(d, int) for d in dims):
            self.size = tuple(dims)
        self.mode = cfg["preprocess"]
        n_out = self.sess.get_outputs()[0].shape[-1]
        self.class_names = load_class_names(cfg, n_out if isinstance(n_out, int) else None)

    def logits(self, batch_rgb):
        x = preprocess(batch_rgb, self.size, self.mode)
        if self.nchw:
            x = x.transpose(0, 3, 1, 2)
        x = np.ascontiguousarray(x)
        if self.fixed_batch_1:  # many exported models only accept one image at a time
            outs = [self.sess.run(None, {self.input_name: x[i:i + 1]})[0] for i in range(len(x))]
            return to_logits(np.concatenate(outs))
        return to_logits(self.sess.run(None, {self.input_name: x})[0])

    def gradcam(self, rgb, idx):
        return None  # uses model-agnostic occlusion map instead


# --------------------------------------------------------------------------- Demo
class DemoModel:
    """A fake colour-based 'disease model' so the app runs before you plug in yours.
    Like many real models, it is fooled by brown backgrounds - useful for showing the problem."""

    class_names = ["Tomato___healthy", "Tomato___Early_blight", "Tomato___Late_blight"]
    size = (224, 224)

    def logits(self, batch_rgb):
        out = []
        for im in batch_rgb:
            im = cv2.resize(im, (128, 128))
            hsv = cv2.cvtColor(im, cv2.COLOR_RGB2HSV).astype(int)
            h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
            green = ((h >= 33) & (h <= 90) & (s > 50)).mean()
            brown = ((h >= 5) & (h < 25) & (s > 60) & (v < 200)).mean()
            dark = ((v < 70) & (s > 30)).mean()
            r = brown / (green + brown + 1e-6)  # share of 'sick-looking' colour (anywhere!)
            out.append([4.0 - 22 * r, 30 * r - 1.5, 25 * dark - 2.0])
        return np.array(out)

    def gradcam(self, rgb, idx):
        return None


# --------------------------------------------------------------------------- YOLO detectors
class YoloDetector:
    """Object detector that draws boxes on disease spots (YOLOv5 / v8 / v10 / v11).

    framework "yolo"   -> Ultralytics package (best.pt trained with `yolo train`, YOLOv8/v10/v11)
    framework "yolov5" -> original YOLOv5 repo checkpoint (model.pt trained with yolov5/train.py);
                          set "yolov5_repo" in config.json to your Yolov5 folder.

    detect(rgb) -> list of {"box": (x1, y1, x2, y2), "cls": int, "conf": float}
    """

    kind = "detector"

    def __init__(self, cfg):
        import torch

        self.torch = torch
        self.size = int(cfg["input_size"][0])
        path = resolve(cfg, cfg["model_path"])
        self.v5 = cfg["framework"].lower() == "yolov5"
        if self.v5:
            import pathlib
            import platform
            import sys

            if platform.system() == "Windows":  # checkpoints trained on Colab/Linux
                pathlib.PosixPath = pathlib.WindowsPath
            repo = resolve(cfg, cfg.get("yolov5_repo", "yolov5"))
            if not os.path.isdir(os.path.join(repo, "models")):
                raise FileNotFoundError(f"YOLOv5 repo not found at {repo}. Set 'yolov5_repo' in config.json.")
            sys.path.insert(0, repo)
            from models.common import DetectMultiBackend
            from utils.augmentations import letterbox
            from utils.general import non_max_suppression, scale_boxes

            self._letterbox, self._nms, self._scale = letterbox, non_max_suppression, scale_boxes
            self.model = DetectMultiBackend(path, device=torch.device("cpu"))
            names = self.model.names
        else:
            from ultralytics import YOLO

            self.model = YOLO(path)
            names = self.model.names
        names = [names[i] for i in sorted(names)] if isinstance(names, dict) else list(names)
        self.class_names = names

    def detect(self, rgb, conf=0.05):
        if self.v5:
            torch = self.torch
            bgr = rgb[..., ::-1]
            im = self._letterbox(bgr, self.size, stride=self.model.stride, auto=True)[0]
            im = np.ascontiguousarray(im[..., ::-1].transpose(2, 0, 1))
            x = torch.from_numpy(im).float()[None] / 255.0
            with torch.no_grad():
                pred = self._nms(self.model(x), conf, 0.45)[0]
            if len(pred):
                pred[:, :4] = self._scale(x.shape[2:], pred[:, :4], rgb.shape).round()
            rows = pred.tolist()
        else:
            r = self.model.predict(np.ascontiguousarray(rgb[..., ::-1]), conf=conf, imgsz=self.size, verbose=False)[0]
            rows = [b + [s, c] for b, s, c in zip(r.boxes.xyxy.tolist(), r.boxes.conf.tolist(), r.boxes.cls.tolist())]
        return [{"box": tuple(int(v) for v in row[:4]), "conf": float(row[4]), "cls": int(row[5])} for row in rows]

    # Detectors are not used through logits/gradcam; these keep other code paths safe.
    def logits(self, batch_rgb):
        raise NotImplementedError("Detector models use detect(), not logits().")

    def gradcam(self, rgb, idx):
        return None


def load_model(cfg):
    fw = cfg["framework"].lower()
    if fw in ("yolo", "ultralytics", "yolov5"):
        return YoloDetector(cfg)
    if fw == "demo":
        return DemoModel()
    if fw in ("keras", "tensorflow", "tf"):
        return KerasModel(cfg)
    if fw in ("torch", "pytorch"):
        return TorchModel(cfg)
    if fw == "onnx":
        return OnnxModel(cfg)
    raise ValueError(f"Unknown framework '{cfg['framework']}'. Use keras, torch, onnx or demo.")
