"""Word-level speech-to-text with faster-whisper (CTranslate2)."""

from __future__ import annotations

import wave
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

from ..config import get_settings

WHISPER_RATE = 16000


@dataclass(slots=True)
class Word:
    start: float
    end: float
    text: str


@dataclass(slots=True)
class Transcript:
    language: str
    words: list[Word]

    def text_between(self, start: float, end: float) -> str:
        return " ".join(w.text for w in self.words if w.start >= start and w.end <= end).strip()


@lru_cache(maxsize=1)
def _model():  # type: ignore[no-untyped-def]
    from faster_whisper import WhisperModel

    s = get_settings()
    return WhisperModel(s.whisper_model, device=s.whisper_device, compute_type=s.whisper_compute_type)


def load_wav(path: Path) -> np.ndarray:
    """16 kHz mono 16-bit WAV -> float32 in [-1, 1].

    Feeding samples directly skips faster-whisper's PyAV decoder, which breaks across PyAV
    releases (faster-whisper 1.2.1 passes `metadata_errors`, removed in newer PyAV).
    """
    with wave.open(str(path), "rb") as wf:
        if wf.getframerate() != WHISPER_RATE or wf.getnchannels() != 1 or wf.getsampwidth() != 2:
            raise ValueError("Expected 16 kHz mono 16-bit WAV (see render.extract_audio)")
        raw = wf.readframes(wf.getnframes())
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def transcribe(audio_path: Path, language: str | None = None) -> Transcript:
    segments, info = _model().transcribe(
        load_wav(audio_path),
        language=language,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 400},
        beam_size=5,
    )
    words = [
        Word(start=float(w.start), end=float(w.end), text=w.word.strip())
        for seg in segments
        for w in (seg.words or [])
        if w.word.strip()
    ]
    return Transcript(language=info.language, words=words)
