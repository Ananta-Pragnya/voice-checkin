"""Transcription + filler-word / word-finding signal.

Uses faster-whisper (CTranslate2) since it runs the "tiny"/"base" models fast
on CPU with no GPU requirement — fine for a short daily check-in clip.
"""

import re

FILLER_WORDS = {
    "um", "uh", "erm", "er", "ah", "hmm", "like", "you know", "i mean", "sort of", "kind of",
}

_MODEL = None


def _get_model(model_size="base"):
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel

        _MODEL = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _MODEL


def transcribe(path, model_size="base"):
    model = _get_model(model_size)
    segments, info = model.transcribe(path, beam_size=5, vad_filter=True)
    text = " ".join(seg.text.strip() for seg in segments)
    return text.strip()


def analyze_transcript(text):
    words = re.findall(r"[a-zA-Z']+", text.lower())
    word_count = len(words)

    lowered = text.lower()
    filler_count = 0
    for filler in FILLER_WORDS:
        filler_count += len(re.findall(rf"\b{re.escape(filler)}\b", lowered))

    filler_rate = filler_count / word_count if word_count > 0 else 0.0

    return {
        "text": text,
        "word_count": word_count,
        "filler_count": filler_count,
        "filler_rate": round(filler_rate, 4),
    }
