#!/usr/bin/env python3
"""voice-checkin CLI.

Usage:
  python cli.py record <profile> <audio_file> [--date YYYY-MM-DD] [--no-transcribe]
  python cli.py dashboard <profile> [--out reports/<profile>.html]
"""

import argparse
import datetime
import os
import sys

from app.baseline import add_record, load_records, history_before
from app.analyze import analyze_day
from app.dashboard import render_dashboard


def cmd_record(args):
    from app.features import extract_from_file

    word_count = None
    if not args.no_transcribe:
        from app.transcribe import transcribe, analyze_transcript

        print("Transcribing...")
        text = transcribe(args.audio_file)
        t = analyze_transcript(text)
        word_count = t["word_count"]
        print(f"  {t['word_count']} words, filler rate {t['filler_rate']}")

    print("Extracting acoustic features...")
    features = extract_from_file(args.audio_file, word_count=word_count)
    if not args.no_transcribe:
        features["filler_rate"] = t["filler_rate"]

    date = args.date or datetime.date.today().isoformat()
    history = history_before(args.profile, date)
    result = analyze_day(features, history)

    add_record(args.profile, date, features, flagged=result["flagged"])

    print(f"\n{date} — {args.profile}")
    for k, v in features.items():
        print(f"  {k}: {v}")
    print(f"\n{result['message']}")
    print(f"composite drift: {result['composite_drift']}  (baseline days: {result['baseline_days']})")


def cmd_dashboard(args):
    records = load_records(args.profile)
    if not records:
        print(f"No records for profile '{args.profile}'. Run `record` first, or see demo/generate_demo_data.py.")
        sys.exit(1)

    latest = records[-1]
    history = history_before(args.profile, latest["date"])
    result = analyze_day(latest["features"], history)

    out_path = args.out or os.path.join("reports", f"{args.profile}.html")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    html = render_dashboard(args.profile, records, result, flagged_date=latest["date"] if result["flagged"] else None)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"{result['message']}")
    print(f"Dashboard written to {out_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_record = sub.add_parser("record", help="Process a new voice check-in recording")
    p_record.add_argument("profile")
    p_record.add_argument("audio_file")
    p_record.add_argument("--date")
    p_record.add_argument("--no-transcribe", action="store_true", help="Skip transcription (acoustic features only)")
    p_record.set_defaults(func=cmd_record)

    p_dash = sub.add_parser("dashboard", help="Render the trend dashboard for a profile")
    p_dash.add_argument("profile")
    p_dash.add_argument("--out")
    p_dash.set_defaults(func=cmd_dashboard)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
