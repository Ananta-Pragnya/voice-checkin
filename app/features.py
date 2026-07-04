"""Acoustic feature extraction for daily voice check-ins.

These are the same broad feature families used in published digital-phenotyping
research on speech biomarkers of depression, dementia, and Parkinson's: pause
behavior, speech rate, pitch (prosody) variance, energy variance, and voice
tremor proxies. None of this diagnoses anything — it produces a feature vector
that only becomes meaningful when compared against a person's own baseline.
"""

import numpy as np
import librosa

SR = 16000


def load_audio(path):
    y, sr = librosa.load(path, sr=SR, mono=True)
    return y, sr


def _voiced_f0(y, sr):
    f0, voiced_flag, _ = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C6"),
        sr=sr,
    )
    if f0 is None:
        return np.array([])
    voiced = f0[voiced_flag & ~np.isnan(f0)]
    return voiced


def extract_features(y, sr, word_count=None):
    duration_s = len(y) / sr

    intervals = librosa.effects.split(y, top_db=30)
    speaking_s = sum((end - start) for start, end in intervals) / sr
    pause_ratio = 1.0 - (speaking_s / duration_s if duration_s > 0 else 0.0)

    f0 = _voiced_f0(y, sr)
    if f0.size >= 2:
        pitch_mean_hz = float(np.mean(f0))
        pitch_std_hz = float(np.std(f0))
        frame_diffs = np.abs(np.diff(f0))
        jitter_proxy = float(np.mean(frame_diffs) / pitch_mean_hz) if pitch_mean_hz > 0 else 0.0
    else:
        pitch_mean_hz = 0.0
        pitch_std_hz = 0.0
        jitter_proxy = 0.0

    rms = librosa.feature.rms(y=y)[0]
    energy_std = float(np.std(rms))

    speech_rate_wps = None
    if word_count is not None and speaking_s > 0:
        speech_rate_wps = word_count / speaking_s

    return {
        "duration_s": round(duration_s, 2),
        "speaking_s": round(speaking_s, 2),
        "pause_ratio": round(pause_ratio, 4),
        "pitch_mean_hz": round(pitch_mean_hz, 2),
        "pitch_std_hz": round(pitch_std_hz, 2),
        "jitter_proxy": round(jitter_proxy, 5),
        "energy_std": round(energy_std, 5),
        "speech_rate_wps": round(speech_rate_wps, 3) if speech_rate_wps is not None else None,
    }


def extract_from_file(path, word_count=None):
    y, sr = load_audio(path)
    return extract_features(y, sr, word_count=word_count)
