"""'Fool Me' Arena: judges try to trick LeafGuard. Every attempt is scored for BOTH the raw model
and LeafGuard, and saved to reports/arena/ (already git-ignored)."""
import json
import os
import time

import cv2

TRUTHS = {
    "not_leaf": "Not a leaf (hand, mug, phone screen, paper...)",
    "bad_photo": "Bad photo (blurry, dark, finger on lens)",
    "healthy": "Healthy leaf",
    "diseased": "Diseased leaf",
}
OUTCOME_TEXT = {"win": "✅ Correct", "safe": "🛡️ Safely refused", "fooled": "❌ Fooled"}


def score(truth, truth_cls, verdict, cls):
    """Return 'win' (right), 'safe' (refused to guess, no harm done) or 'fooled' (confident + wrong)."""
    abstain = verdict in ("RETAKE", "NOT_A_LEAF", "UNCERTAIN")
    if truth == "not_leaf":
        return "win" if verdict == "NOT_A_LEAF" else ("safe" if abstain else "fooled")
    if truth == "bad_photo":
        return "win" if verdict == "RETAKE" else ("safe" if abstain else "fooled")
    if truth == "healthy":
        return "win" if verdict == "HEALTHY" else ("safe" if abstain else "fooled")
    if truth == "diseased":
        if verdict == "DISEASED":
            return "win" if (truth_cls is None or cls == truth_cls) else "fooled"
        return "safe" if abstain else "fooled"
    raise ValueError(truth)


def raw_verdict(guard, result):
    """What the raw model alone would have told the user (it never refuses)."""
    b = result["baseline"]
    if guard.is_detector:
        return ("HEALTHY", "healthy") if b["index"] == -1 else ("DISEASED", b["class"])
    healthy = guard.cfg["healthy_keyword"].lower() in b["class"].lower()
    return ("HEALTHY" if healthy else "DISEASED"), b["class"]


def caught_by(result):
    failed = [c["name"] for c in result.get("checks", []) if not c["passed"]]
    return failed[0] if failed else None


class Scoreboard:
    def __init__(self, root):
        self.dir = os.path.join(root, "reports", "arena")
        self.path = os.path.join(self.dir, "scoreboard.json")
        os.makedirs(self.dir, exist_ok=True)

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def add(self, entry, rgb):
        rows = self.load()
        stamp = time.strftime("%Y%m%d-%H%M%S")
        img_name = f"attempt_{len(rows) + 1:03d}_{stamp}.jpg"
        small = rgb if max(rgb.shape[:2]) <= 480 else cv2.resize(
            rgb, None, fx=480 / max(rgb.shape[:2]), fy=480 / max(rgb.shape[:2]), interpolation=cv2.INTER_AREA)
        cv2.imwrite(os.path.join(self.dir, img_name), cv2.cvtColor(small, cv2.COLOR_RGB2BGR))
        entry = dict(entry, image=img_name, time=time.strftime("%H:%M:%S"), id=len(rows) + 1)
        rows.append(entry)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=1, ensure_ascii=False)
        return entry

    def reset(self):
        for f in os.listdir(self.dir):
            if f.startswith("attempt_") or f == "scoreboard.json":
                os.remove(os.path.join(self.dir, f))

    def totals(self):
        rows = self.load()
        out = {"n": len(rows)}
        for who in ("raw", "leafguard"):
            for k in ("win", "safe", "fooled"):
                out[f"{who}_{k}"] = sum(1 for r in rows if r[f"{who}_outcome"] == k)
        return out
