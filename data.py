"""
data.py — Data parsing, transformation, and stats.
Pure functions only — no UI, no network calls.
"""

from datetime import datetime


MMOL_TO_MGDL = 18.01559


def parse_time(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def parse_events(raw: list) -> dict:
    """Split a flat list of Tidepool events into typed buckets."""
    buckets = {"cbg": [], "smbg": [], "basal": [], "bolus": [], "wizard": []}
    for e in raw:
        t = e.get("type")
        if t in buckets:
            buckets[t].append(e)
    for k in buckets:
        buckets[k].sort(key=lambda e: e.get("time", ""))
    return buckets


def glucose_series(events: list) -> tuple[list, list]:
    """
    Convert cbg/smbg events → (times, mg/dL values).
    Tidepool stores glucose in mmol/L — we convert here once.
    """
    times, values = [], []
    for e in events:
        try:
            v = e.get("value")
            if v is not None:
                times.append(parse_time(e["time"]))
                values.append(round(v * MMOL_TO_MGDL))
        except Exception:
            pass
    return times, values


def compute_tir(values: list, low: int, high: int) -> dict:
    """Time in Range stats from a list of mg/dL values."""
    if not values:
        return {"in_range": 0, "low": 0, "high": 0, "total": 0}
    n    = len(values)
    low_ = sum(1 for v in values if v < low)
    high_= sum(1 for v in values if v > high)
    return {
        "in_range": round((n - low_ - high_) / n * 100),
        "low":      round(low_  / n * 100),
        "high":     round(high_ / n * 100),
        "total":    n,
    }


def latest_glucose(times: list, values: list) -> tuple[datetime | None, int | None]:
    """Return the most recent (time, value) pair, or (None, None)."""
    if not values:
        return None, None
    return times[-1], values[-1]


def glucose_trend(values: list, window: int = 3) -> float | None:
    """
    Estimate rate of change (mg/dL per minute) from the last `window` readings.
    Assumes readings are ~5 minutes apart (standard CGM interval).
    Returns None if not enough data.
    """
    if len(values) < window:
        return None
    recent = values[-window:]
    delta  = recent[-1] - recent[0]
    minutes = (window - 1) * 5
    return round(delta / minutes, 2)


def check_alerts(values: list, times: list, settings: dict) -> list[dict]:
    """
    Evaluate current glucose data against alert settings.
    Returns a list of active alert dicts: {level, message, value}

    settings keys expected:
        alert_low, alert_high, rapid_rise_rate, rapid_fall_rate,
        alerts_enabled (bool)
    """
    if not settings.get("alerts_enabled", True) or not values:
        return []

    alerts = []
    current = values[-1]
    low     = settings.get("alert_low",  70)
    high    = settings.get("alert_high", 180)

    if current < 54:
        alerts.append({"level": "urgent", "message": f"URGENT LOW: {current} mg/dL", "value": current})
    elif current < low:
        alerts.append({"level": "low",    "message": f"Low glucose: {current} mg/dL", "value": current})
    elif current > 250:
        alerts.append({"level": "urgent", "message": f"URGENT HIGH: {current} mg/dL", "value": current})
    elif current > high:
        alerts.append({"level": "high",   "message": f"High glucose: {current} mg/dL", "value": current})

    trend = glucose_trend(values)
    if trend is not None:
        rise = settings.get("rapid_rise_rate", 3)
        fall = settings.get("rapid_fall_rate", -3)
        if trend >= rise:
            alerts.append({"level": "warning", "message": f"Rapid rise: +{trend} mg/dL/min", "value": trend})
        elif trend <= fall:
            alerts.append({"level": "warning", "message": f"Rapid fall: {trend} mg/dL/min", "value": trend})

    return alerts