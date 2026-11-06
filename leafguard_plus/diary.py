"""Field Diary: a simple log of diagnoses per plot, to see whether the disease is getting better or worse.
Stored in reports/diary/ (git-ignored)."""
import json
import os
import time
import uuid

import cv2


class Diary:
    def __init__(self, root):
        self.dir = os.path.join(root, "reports", "diary")
        self.path = os.path.join(self.dir, "diary.json")
        os.makedirs(self.dir, exist_ok=True)

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save(self, rows):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=1, ensure_ascii=False)

    def add(self, plot, verdict, disease, severity_pct=None, level=None, confidence=None, note="", rgb=None,
            when=None):
        rows = self.load()
        eid = uuid.uuid4().hex[:10]
        img = None
        if rgb is not None:
            img = f"{eid}.jpg"
            s = min(1.0, 360 / max(rgb.shape[:2]))
            small = cv2.resize(rgb, None, fx=s, fy=s, interpolation=cv2.INTER_AREA) if s < 1 else rgb
            cv2.imwrite(os.path.join(self.dir, img), cv2.cvtColor(small, cv2.COLOR_RGB2BGR))
        entry = {"id": eid, "plot": plot.strip() or "My field", "time": when or time.strftime("%Y-%m-%d %H:%M"),
                 "verdict": verdict, "disease": disease, "severity": None if severity_pct is None else round(float(severity_pct), 1),
                 "level": level, "confidence": None if confidence is None else round(float(confidence), 3),
                 "note": note, "image": img}
        rows.append(entry)
        self._save(rows)
        return entry

    def delete(self, eid):
        rows = self.load()
        keep = [r for r in rows if r["id"] != eid]
        for r in rows:
            if r["id"] == eid and r.get("image"):
                try:
                    os.remove(os.path.join(self.dir, r["image"]))
                except OSError:
                    pass
        self._save(keep)

    def plots(self):
        return sorted({r["plot"] for r in self.load()})


def trend(entries):
    """Compare the last two severity readings of a plot -> ('better'|'worse'|'same'|None, text)."""
    pts = [e for e in entries if e.get("severity") is not None or e["verdict"] == "HEALTHY"]
    if len(pts) < 2:
        return None, "Add another check-up in a few days to see the trend."
    a = pts[-2].get("severity") or 0.0
    b = pts[-1].get("severity") or 0.0
    if b < a - 3:
        return "better", f"Improving: affected area fell from {a:.0f}% to {b:.0f}%. The treatment seems to work."
    if b > a + 3:
        return "worse", (f"Getting worse: affected area rose from {a:.0f}% to {b:.0f}%. "
                         f"Review the treatment with your agriculture officer.")
    return "same", f"About the same ({a:.0f}% → {b:.0f}%). Keep monitoring and follow the plan."
