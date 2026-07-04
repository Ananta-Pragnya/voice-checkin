"""Synthesizes 14 days of feature data for a demo profile, ending in one day
with a clear acoustic drift (more pausing, slower speech, flatter prosody,
more filler words), then renders the dashboard.

Run from the project root:
    python demo/generate_demo_data.py
"""

import datetime
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.baseline import add_record, load_records, history_before  # noqa: E402
from app.analyze import analyze_day  # noqa: E402
from app.dashboard import render_dashboard  # noqa: E402

PROFILE = "demo"
BASE = {
    "pause_ratio": 0.28,
    "speech_rate_wps": 2.6,
    "pitch_std_hz": 32.0,
    "energy_std": 0.015,
    "jitter_proxy": 0.02,
    "filler_rate": 0.03,
}


def normal_day(rng):
    return {
        "pause_ratio": round(max(0.05, rng.gauss(BASE["pause_ratio"], 0.02)), 4),
        "speech_rate_wps": round(max(0.5, rng.gauss(BASE["speech_rate_wps"], 0.15)), 3),
        "pitch_std_hz": round(max(5.0, rng.gauss(BASE["pitch_std_hz"], 2.5)), 2),
        "energy_std": round(max(0.001, rng.gauss(BASE["energy_std"], 0.002)), 5),
        "jitter_proxy": round(max(0.001, rng.gauss(BASE["jitter_proxy"], 0.003)), 5),
        "filler_rate": round(max(0.0, rng.gauss(BASE["filler_rate"], 0.01)), 4),
        "duration_s": round(rng.gauss(45, 5), 2),
        "speaking_s": None,
    }


def flagged_day(rng):
    return {
        "pause_ratio": round(BASE["pause_ratio"] * 1.55, 4),
        "speech_rate_wps": round(BASE["speech_rate_wps"] * 0.72, 3),
        "pitch_std_hz": round(BASE["pitch_std_hz"] * 0.62, 2),
        "energy_std": round(BASE["energy_std"] * 0.75, 5),
        "jitter_proxy": round(BASE["jitter_proxy"] * 1.6, 5),
        "filler_rate": round(BASE["filler_rate"] * 3.2, 4),
        "duration_s": round(rng.gauss(45, 5), 2),
        "speaking_s": None,
    }


def main():
    rng = random.Random(42)
    today = datetime.date.today()

    for r in load_records(PROFILE):
        pass  # existing records (if any) are upserted by date below, not cleared

    dates = []
    for i in range(13, -1, -1):
        date = (today - datetime.timedelta(days=i)).isoformat()
        dates.append(date)
        features = flagged_day(rng) if i == 0 else normal_day(rng)
        add_record(PROFILE, date, features)

    records = load_records(PROFILE)
    latest = records[-1]
    history = history_before(PROFILE, latest["date"])
    result = analyze_day(latest["features"], history)

    out_path = os.path.join("reports", "demo.html")
    os.makedirs("reports", exist_ok=True)
    html = render_dashboard(PROFILE, records, result, flagged_date=latest["date"] if result["flagged"] else None)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(result["message"])
    print(f"composite drift: {result['composite_drift']}")
    print(f"Dashboard written to {out_path}")


if __name__ == "__main__":
    main()
