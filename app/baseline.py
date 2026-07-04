"""Rolling personal baseline storage.

Deliberately per-person, not population-normed: a naturally slow talker isn't
"abnormal," they're just themselves. What matters is drift away from their own
history, so every comparison in analyze.py is against this file, never a
population average.
"""

import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def _path(profile):
    os.makedirs(DATA_DIR, exist_ok=True)
    safe = "".join(c for c in profile if c.isalnum() or c in ("-", "_")) or "default"
    return os.path.join(DATA_DIR, f"{safe}.json")


def load_records(profile):
    path = _path(profile)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f).get("records", [])


def save_records(profile, records):
    records = sorted(records, key=lambda r: r["date"])
    with open(_path(profile), "w", encoding="utf-8") as f:
        json.dump({"records": records}, f, indent=2)


def add_record(profile, date, features, flagged=None):
    records = load_records(profile)
    records = [r for r in records if r["date"] != date]
    entry = {"date": date, "features": features}
    if flagged is not None:
        entry["flagged"] = flagged
    records.append(entry)
    save_records(profile, records)
    return records


def history_before(profile, date):
    records = load_records(profile)
    return [r for r in records if r["date"] < date]


def compute_baseline(records, feature_keys):
    import statistics

    baseline = {}
    for key in feature_keys:
        values = [r["features"].get(key) for r in records if r["features"].get(key) is not None]
        if len(values) < 3:
            baseline[key] = {"mean": None, "std": None, "n": len(values)}
            continue
        baseline[key] = {
            "mean": statistics.mean(values),
            "std": statistics.pstdev(values) or 1e-6,
            "n": len(values),
        }
    return baseline
