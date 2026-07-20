# voice-checkin

A low-friction daily voice memo that flags meaningful drift in someone's own
speech patterns - a nudge for a distant caregiver, not a diagnosis.

Early markers of depression, dementia, and Parkinson's show up in speech years
before a formal diagnosis: longer pauses, slower speech rate, flatter pitch
(prosody), more filler words, voice tremor. This is published digital-phenotyping
research, not speculation. The trick that makes it useful instead of noisy:
compare each recording to **that person's own rolling baseline**, never a
population norm. A naturally slow talker isn't abnormal - a change from their
own normal is what's worth a phone call.

## How it works

1. Someone records a short daily voice memo ("how was your day" - no script,
   no app friction).
2. `faster-whisper` transcribes it; the transcript gives word count and a
   filler-word rate ("um", "uh", "like", ...).
3. `librosa` extracts acoustic features directly from the audio:
   - **pause ratio** - fraction of the clip that's silence (`librosa.effects.split`)
   - **speech rate** - words per second of actual speaking time
   - **pitch variance** - std dev of voiced F0 (`librosa.pyin`), a prosody proxy
   - **energy variance** - std dev of RMS energy
   - **jitter proxy** - frame-to-frame pitch perturbation, a voice-tremor proxy
4. Each new day's features are compared against the mean/std of that person's
   own prior days (`app/analyze.py`). Every feature has a "concerning direction"
   (more pausing, slower speech, flatter prosody, more filler words); the
   composite drift score averages the signed z-scores across whatever features
   have an established baseline (5+ prior days).
5. If the composite drift or any single feature crosses a threshold, the day
   gets flagged. The dashboard message is always a nudge - *"worth a call this
   week"* -- never a clinical claim.

## Install

```bash
pip install -r requirements.txt
```

`faster-whisper` downloads its model (default: `base`) on first use - no GPU
required, runs fine on CPU for a short clip.

## Run it on a real recording

```bash
python cli.py record mom recording_2026-07-04.wav
python cli.py dashboard mom
```

`record` transcribes, extracts features, compares to that profile's baseline,
and stores the day. `dashboard` renders `reports/<profile>.html` - small
multiples for pause ratio / speech rate / pitch variance, each with a shaded
band showing that person's own normal range, and the flagged day (if any)
marked with a red diamond.

## Demo (no audio needed)

```bash
python demo/generate_demo_data.py
```

Synthesizes 14 days of realistic feature data for a "demo" profile - 13 normal
days plus one day with a clear synthetic decline (more pausing, slower speech,
flatter pitch, more filler words) - and writes `reports/demo.html`. This is
what to open for a walkthrough without needing multiple real days of audio on
hand.

## Data storage

Per-profile history lives in `data/<profile>.json` - a flat list of
`{date, features, flagged}` records. No server, no account system; it's meant
to run on a family member's own machine.

## Scope / limitations

Feature extraction and drift scoring are real signal processing, not a trained
clinical model - this is a screening nudge, not a diagnostic tool, and it
should never be presented to an end user as one. A single flagged day can be a
bad night's sleep or a head cold; the value is in sustained drift over time,
and any real flag should prompt a conversation, not an assumption.
