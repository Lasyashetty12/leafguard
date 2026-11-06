"""Field Scan: diagnose many photos from one field and turn them into a field-level decision."""
from collections import Counter


def summarise(results):
    """results = list of dicts with 'verdict', 'cls', 'severity' (pct or None).
    Returns counts, health score and a field decision."""
    n = len(results)
    counts = Counter(r["verdict"] for r in results)
    answered = counts["HEALTHY"] + counts["DISEASED"]
    unusable = counts["RETAKE"] + counts["NOT_A_LEAF"]
    diseases = Counter(r["cls"] for r in results if r["verdict"] == "DISEASED")
    sev = [r["severity"] for r in results if r["verdict"] == "DISEASED" and r.get("severity") is not None]
    diseased_share = counts["DISEASED"] / answered if answered else 0.0
    health = round(100 * counts["HEALTHY"] / answered) if answered else None

    if n == 0:
        decision, tone, why = "No photos yet", "neutral", ""
    elif answered < max(3, 0.5 * n):
        decision, tone = "Retake photos", "warn"
        why = (f"Only {answered} of {n} photos could be diagnosed safely ({unusable} unusable, "
               f"{counts['UNCERTAIN']} unsure). Take clearer photos of single leaves.")
    elif diseased_share >= 0.20:
        decision, tone = "Treat the whole field", "bad"
        why = f"{round(diseased_share * 100)}% of checked plants show disease, enough that it is likely spreading."
    elif diseased_share > 0.05:
        decision, tone = "Spot-treat affected plants", "warn"
        why = (f"{round(diseased_share * 100)}% of checked plants show disease. Treat those plants and their "
               f"neighbours, then re-check in 3–4 days.")
    else:
        decision, tone = "Healthy: keep monitoring", "good"
        why = "Little or no disease found. Check again in a week, or sooner after rain."
    return {"n": n, "counts": counts, "answered": answered, "unusable": unusable, "diseases": diseases,
            "avg_severity": round(sum(sev) / len(sev), 1) if sev else None, "health": health,
            "diseased_share": diseased_share, "decision": decision, "tone": tone, "why": why}
