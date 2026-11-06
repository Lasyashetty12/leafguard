"""A fast 'what would LeafGuard decide?' used by the self-doubt and counterfactual tests.

It reuses LeafGuard's own decision code (nothing is copied or changed), but skips the slow
photo-quality and CLIP checks, because the photo already passed them once.
"""
from leafguard.segment import leaf_mask


def quick_decision(guard, rgb):
    """Returns {"verdict", "cls", "confidence"}."""
    if guard.is_detector:
        dets = guard.model.detect(rgb)
        mask, _ = leaf_mask(rgb)
        res = {"checks": [], "reasons": [], "images": {}}

        def finish(verdict, **extra):
            res.update(verdict=verdict, **extra)
            return res

        guard._detector_verdict(rgb, mask, dets, res, finish)
    else:
        res = guard.analyze(rgb, do_explain=False)
    return {"verdict": res["verdict"], "cls": res.get("cls"), "confidence": res.get("confidence")}


def same_answer(a, b):
    if a["verdict"] != b["verdict"]:
        return False
    return a["verdict"] != "DISEASED" or a["cls"] == b["cls"]
