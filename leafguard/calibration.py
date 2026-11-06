"""Make the model's confidence honest (temperature scaling) and pick the abstain threshold."""
import numpy as np


def softmax(logits, T=1.0):
    z = np.asarray(logits, np.float64) / T
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def norm_entropy(p):
    """0 = completely sure, 1 = spread evenly over every class."""
    p = np.clip(p, 1e-12, 1)
    return -(p * np.log(p)).sum(axis=-1) / np.log(p.shape[-1])


def nll(logits, labels, T):
    p = softmax(logits, T)
    return float(-np.log(np.clip(p[np.arange(len(labels)), labels], 1e-12, 1)).mean())


def fit_temperature(logits, labels):
    grid = np.exp(np.linspace(np.log(0.3), np.log(10), 300))
    losses = [nll(logits, labels, t) for t in grid]
    return float(grid[int(np.argmin(losses))])


def ece(probs, labels, bins=15):
    """Expected Calibration Error: how far 'confidence' is from real accuracy (lower is better)."""
    conf = probs.max(1)
    correct = probs.argmax(1) == labels
    edges = np.linspace(0, 1, bins + 1)
    total = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = (conf > lo) & (conf <= hi)
        if sel.any():
            total += sel.mean() * abs(correct[sel].mean() - conf[sel].mean())
    return float(total)


def choose_threshold(conf, correct, target_accuracy=0.97, floor=0.5):
    """Lowest confidence threshold where the answers we DO give are >= target accuracy."""
    order = np.argsort(-conf)
    conf_sorted, correct_sorted = conf[order], correct[order]
    acc_running = np.cumsum(correct_sorted) / np.arange(1, len(conf) + 1)
    ok = np.where(acc_running >= target_accuracy)[0]
    if len(ok) == 0:
        return 0.99
    return float(max(floor, conf_sorted[ok[-1]]))
