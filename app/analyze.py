"""Drift scoring: compare one day's features against that person's own baseline.

Each feature has a direction that counts as "concerning" if it moves that way
(e.g. more pausing, flatter prosody, slower speech, more filler words). A
composite drift score averages the signed z-scores across whichever features
have an established baseline. This is a nudge generator, not a diagnosis —
the output is meant to tell a caregiver "worth a call this week," never
anything clinical.
"""

from .baseline import compute_baseline

# True => a higher value than baseline is the concerning direction.
FEATURE_CONCERN_DIRECTION = {
    "pause_ratio": True,
    "speech_rate_wps": False,
    "pitch_std_hz": False,
    "energy_std": False,
    "jitter_proxy": True,
    "filler_rate": True,
}

SINGLE_FEATURE_Z_THRESHOLD = 2.0
COMPOSITE_DRIFT_THRESHOLD = 1.0
MIN_BASELINE_DAYS = 5


def z_score(value, mean, std):
    if value is None or mean is None or not std:
        return None
    return (value - mean) / std


def analyze_day(features, history_records):
    feature_keys = list(FEATURE_CONCERN_DIRECTION.keys())
    baseline = compute_baseline(history_records, feature_keys)

    per_feature = {}
    concern_zs = []

    for key in feature_keys:
        value = features.get(key)
        b = baseline.get(key, {})
        z = z_score(value, b.get("mean"), b.get("std"))
        concern_z = None
        if z is not None:
            concern_z = z if FEATURE_CONCERN_DIRECTION[key] else -z
            concern_zs.append(concern_z)
        per_feature[key] = {
            "value": value,
            "baseline_mean": b.get("mean"),
            "baseline_std": b.get("std"),
            "baseline_n": b.get("n", 0),
            "z": round(z, 2) if z is not None else None,
            "concern_z": round(concern_z, 2) if concern_z is not None else None,
        }

    have_baseline = len(history_records) >= MIN_BASELINE_DAYS
    composite_drift = sum(concern_zs) / len(concern_zs) if concern_zs else 0.0

    single_flags = [k for k, v in per_feature.items() if v["concern_z"] is not None and v["concern_z"] >= SINGLE_FEATURE_Z_THRESHOLD]
    flagged = have_baseline and (composite_drift >= COMPOSITE_DRIFT_THRESHOLD or len(single_flags) > 0)

    return {
        "have_baseline": have_baseline,
        "baseline_days": len(history_records),
        "composite_drift": round(composite_drift, 3),
        "flagged": flagged,
        "flagged_features": single_flags,
        "per_feature": per_feature,
        "message": _message(flagged, have_baseline, single_flags),
    }


def _message(flagged, have_baseline, single_flags):
    if not have_baseline:
        return "Still building this person's baseline — no comparison yet."
    if flagged:
        if single_flags:
            return f"Notable drift in {', '.join(single_flags)} vs. their own baseline — worth a call this week."
        return "Combined drift across several features vs. their own baseline — worth a call this week."
    return "Within this person's normal day-to-day range."
