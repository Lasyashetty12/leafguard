"""Weather for farmers: is it a good time to spray, and how risky are the next 3 days for disease?

Data: Open-Meteo (free, no API key, CC BY 4.0, https://open-meteo.com). Needs internet.
Risk rules are simple rules of thumb from extension guidance (UC IPM / TNAU), NOT validated forecast models.
"""
import json
import urllib.parse
import urllib.request
from datetime import datetime

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HOURLY = "temperature_2m,relative_humidity_2m,precipitation,precipitation_probability,wind_speed_10m"


def _get(url, params, timeout=8):
    full = url + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(full, timeout=timeout) as r:
        return json.loads(r.read().decode())


def geocode(place):
    """'Kolar' -> {name, admin1, country, latitude, longitude} or None."""
    data = _get(GEO_URL, {"name": place, "count": 1, "language": "en", "format": "json"})
    res = (data or {}).get("results") or []
    return res[0] if res else None


def forecast(lat, lon, days=3):
    data = _get(FORECAST_URL, {"latitude": lat, "longitude": lon, "hourly": HOURLY, "forecast_days": days,
                               "timezone": "auto", "wind_speed_unit": "kmh"})
    h = data["hourly"]
    rows = []
    for i, t in enumerate(h["time"]):
        rows.append({"time": datetime.fromisoformat(t), "temp": h["temperature_2m"][i],
                     "rh": h["relative_humidity_2m"][i], "rain": h["precipitation"][i] or 0.0,
                     "rain_prob": h["precipitation_probability"][i] if h["precipitation_probability"][i] is not None else 0,
                     "wind": h["wind_speed_10m"][i]})
    return rows


# ---------------------------------------------------------------- spraying
def spray_ok(hour):
    """Reasons an hour is bad for spraying (empty list = OK)."""
    bad = []
    if hour["wind"] > 15:
        bad.append("too windy (spray drifts)")
    if hour["temp"] > 32:
        bad.append("too hot (leaf burn, fast drying)")
    if hour["rain"] > 0.1 or hour["rain_prob"] >= 40:
        bad.append("rain likely (washes spray off)")
    if not 6 <= hour["time"].hour <= 18:
        bad.append("dark")
    return bad


def spray_windows(rows, now=None, min_hours=2, rain_free_after=4):
    """Find spray windows: >= min_hours good hours in a row, and no rain in the following hours."""
    now = now or rows[0]["time"]
    future = [r for r in rows if r["time"] >= now.replace(minute=0, second=0, microsecond=0)]
    windows, run = [], []
    for i, r in enumerate(future):
        later = future[i + 1:i + 1 + rain_free_after]
        good = not spray_ok(r) and not any(x["rain"] > 0.1 or x["rain_prob"] >= 50 for x in later)
        if good:
            run.append(r)
        if (not good or i == len(future) - 1) and len(run) >= min_hours:
            windows.append({"start": run[0]["time"], "end": run[-1]["time"],
                            "wind": max(x["wind"] for x in run), "temp": max(x["temp"] for x in run)})
        if not good:
            run = []
    return windows


def spray_now(rows, now=None):
    """Verdict for right now: (ok: bool, reasons)."""
    now = now or rows[0]["time"]
    cur = min(rows, key=lambda r: abs((r["time"] - now).total_seconds()))
    i = rows.index(cur)
    reasons = spray_ok(cur)
    if any(x["rain"] > 0.1 or x["rain_prob"] >= 50 for x in rows[i + 1:i + 5]):
        reasons.append("rain expected in the next 4 hours")
    return not reasons, reasons, cur


# ---------------------------------------------------------------- disease risk (rules of thumb)
def _day_hours(rows):
    days = {}
    for r in rows:
        days.setdefault(r["time"].date(), []).append(r)
    return days


def disease_risk(rows, disease_key):
    """Per-day risk 'low' / 'medium' / 'high' with a plain-language reason."""
    out = []
    for day, hrs in _day_hours(rows).items():
        wet = sum(1 for h in hrs if h["rh"] >= 90)
        rainy = sum(1 for h in hrs if h["rain"] > 0.1 or h["rain_prob"] >= 60)
        mild_wet = sum(1 for h in hrs if h["rh"] >= 90 and 10 <= h["temp"] <= 25)
        warm_humid = sum(1 for h in hrs if h["rh"] >= 85 and 20 <= h["temp"] <= 30)
        warm_wet = sum(1 for h in hrs if (h["rain"] > 0.1 or h["rh"] >= 95) and h["temp"] >= 20)
        pm_hours = sum(1 for h in hrs if 20 <= h["temp"] <= 30 and h["rh"] >= 70 and h["rain"] <= 0.1)
        if disease_key == "late":
            score, why = mild_wet, f"{mild_wet} h of >90% humidity at 10–25 °C"
            level = "high" if mild_wet >= 10 else "medium" if mild_wet >= 5 else "low"
        elif disease_key == "early":
            score, why = warm_humid + 2 * rainy, f"{warm_humid} warm humid hours, {rainy} rainy hours"
            level = "high" if score >= 14 else "medium" if score >= 6 else "low"
        elif disease_key == "powdery":
            # warm days + humid nights + NO rain (spores die in water) = classic mildew weather
            warm = sum(1 for h in hrs if 20 <= h["temp"] <= 30)
            humid = sum(1 for h in hrs if h["rh"] >= 75)
            rain_mm = sum(h["rain"] for h in hrs)
            dry = rain_mm < 1.0
            score = (warm + humid) if dry else 0
            why = f"{warm} warm hours (20–30 °C), {humid} humid hours, {'dry' if dry else f'{rain_mm:.0f} mm rain'}"
            level = ("high" if dry and warm >= 8 and humid >= 6 else
                     "medium" if dry and warm >= 5 and humid >= 3 else "low")
        elif disease_key == "bacterial":
            score, why = warm_wet + rainy, f"{warm_wet} warm wet hours, {rainy} rainy hours"
            level = "high" if score >= 10 else "medium" if score >= 4 else "low"
        elif disease_key == "rust":
            dew = sum(1 for h in hrs if h["rh"] >= 95 and 15 <= h["temp"] <= 28)
            score, why = dew, f"{dew} h of dew-level humidity at 15–28 °C"
            level = "high" if dew >= 8 else "medium" if dew >= 4 else "low"
        else:
            score, why = wet, f"{wet} h above 90% humidity"
            level = "high" if wet >= 12 else "medium" if wet >= 6 else "low"
        out.append({"day": day, "level": level, "why": why, "score": score,
                    "tmin": min(h["temp"] for h in hrs), "tmax": max(h["temp"] for h in hrs),
                    "rain_mm": round(sum(h["rain"] for h in hrs), 1), "rh_max": max(h["rh"] for h in hrs)})
    return out
