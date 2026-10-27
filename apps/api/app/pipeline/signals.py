"""Cheap, deterministic engagement signals used to shortlist candidate clips before Claude ranks them.

Signals (each normalized to 0..1 per video):
  * heat    - YouTube "Most replayed" heatmap, the strongest public proxy for what viewers rewatch
  * energy  - loudness peaks (laughter, shouting, music drops, applause)
  * density - words per second; dead air rarely makes a good Short
"""

from __future__ import annotations

import re
import wave
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .download import HeatPoint
from .transcribe import Transcript, Word

_SENTENCE_END = re.compile(r"[.!?…]['\")\]]*$")
_PAUSE_SPLIT = 0.8  # seconds of silence that also ends a sentence


@dataclass(slots=True)
class Sentence:
    start: float
    end: float
    text: str


@dataclass(slots=True)
class Candidate:
    start: float
    end: float
    text: str
    heat: float
    energy: float
    density: float
    score: float


def sentences(words: list[Word]) -> list[Sentence]:
    out: list[Sentence] = []
    buf: list[Word] = []
    for i, w in enumerate(words):
        buf.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        gap = (nxt.start - w.end) if nxt else 999.0
        if _SENTENCE_END.search(w.text) or gap >= _PAUSE_SPLIT or nxt is None:
            out.append(Sentence(buf[0].start, buf[-1].end, " ".join(x.text for x in buf)))
            buf = []
    return out


def energy_per_second(wav_path: Path) -> np.ndarray:
    """RMS loudness per second from a 16-bit mono WAV, min-max normalized."""
    with wave.open(str(wav_path), "rb") as wf:
        rate = wf.getframerate()
        raw = wf.readframes(wf.getnframes())
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    n = len(samples) // rate
    if n == 0:
        return np.zeros(1, dtype=np.float32)
    rms = np.sqrt(np.mean(samples[: n * rate].reshape(n, rate) ** 2, axis=1))
    return _normalize(rms)


def heat_per_second(heatmap: list[HeatPoint], duration: float) -> np.ndarray | None:
    if not heatmap:
        return None
    arr = np.zeros(int(np.ceil(duration)) + 1, dtype=np.float32)
    for h in heatmap:
        arr[int(h.start) : int(np.ceil(h.end)) + 1] = np.maximum(
            arr[int(h.start) : int(np.ceil(h.end)) + 1], h.value
        )
    return _normalize(arr)


def _normalize(x: np.ndarray) -> np.ndarray:
    lo, hi = float(np.min(x)), float(np.max(x))
    if hi - lo < 1e-9:
        return np.zeros_like(x, dtype=np.float32)
    return ((x - lo) / (hi - lo)).astype(np.float32)


def _window_mean(series: np.ndarray | None, start: float, end: float) -> float:
    if series is None or len(series) == 0:
        return 0.0
    a, b = int(start), max(int(start) + 1, int(np.ceil(end)))
    window = series[a : min(b, len(series))]
    return float(window.mean()) if len(window) else 0.0


def _window_peak(series: np.ndarray | None, start: float, end: float) -> float:
    if series is None or len(series) == 0:
        return 0.0
    a, b = int(start), max(int(start) + 1, int(np.ceil(end)))
    window = series[a : min(b, len(series))]
    return float(window.max()) if len(window) else 0.0


def candidates(
    transcript: Transcript,
    heat: np.ndarray | None,
    energy: np.ndarray | None,
    min_duration: float,
    max_duration: float,
    limit: int,
) -> list[Candidate]:
    """Sentence-aligned windows within the duration bounds, scored and de-overlapped greedily."""
    sents = sentences(transcript.words)
    weights = (0.55, 0.25, 0.20) if heat is not None else (0.0, 0.6, 0.4)
    starts = [w.start for w in transcript.words]
    ends = [w.end for w in transcript.words]
    pool: list[Candidate] = []

    for i, first in enumerate(sents):
        for last in sents[i:]:
            length = last.end - first.start
            if length > max_duration:
                break
            if length < min_duration:
                continue
            n_words = bisect_right(ends, last.end) - bisect_left(starts, first.start)
            density = min(1.0, (n_words / length) / 3.0)  # ~3 words/s is fast, engaging speech
            h = 0.5 * _window_mean(heat, first.start, last.end) + 0.5 * _window_peak(
                heat, first.start, last.end
            )
            e = _window_peak(energy, first.start, last.end)
            score = weights[0] * h + weights[1] * e + weights[2] * density
            pool.append(
                Candidate(
                    start=first.start,
                    end=last.end,
                    text="",
                    heat=round(h, 3),
                    energy=round(e, 3),
                    density=round(density, 3),
                    score=round(score, 4),
                )
            )

    pool.sort(key=lambda c: c.score, reverse=True)
    picked: list[Candidate] = []
    for c in pool:
        if all(_overlap(c, p) < 0.3 for p in picked):
            c.text = transcript.text_between(c.start, c.end)
            picked.append(c)
        if len(picked) >= limit:
            break
    return sorted(picked, key=lambda c: c.start)


def audio_candidates(
    heat: np.ndarray | None,
    energy: np.ndarray | None,
    duration: float,
    min_duration: float,
    max_duration: float,
    limit: int,
) -> list[Candidate]:
    """Fixed-length windows scored on heat/loudness only.

    Fallback for music videos, performances and other clips where Whisper finds too little
    speech to build sentence-aligned windows. Never needs a transcript.
    """
    if duration < min_duration:
        return []
    length = min(duration, max(min_duration, min(max_duration, (min_duration + max_duration) / 2)))
    pool: list[Candidate] = []
    t = 0.0
    while t + length <= duration + 1e-6:
        e = 0.5 * _window_mean(energy, t, t + length) + 0.5 * _window_peak(energy, t, t + length)
        h = 0.5 * _window_mean(heat, t, t + length) + 0.5 * _window_peak(heat, t, t + length)
        score = 0.6 * h + 0.4 * e if heat is not None else e
        pool.append(Candidate(t, t + length, "", round(h, 3), round(e, 3), 0.0, round(score, 4)))
        t += 1.0

    pool.sort(key=lambda c: c.score, reverse=True)
    picked: list[Candidate] = []
    for c in pool:
        if all(_overlap(c, p) < 0.3 for p in picked):
            picked.append(c)
        if len(picked) >= limit:
            break
    return sorted(picked, key=lambda c: c.start)


def _overlap(a: Candidate, b: Candidate) -> float:
    inter = max(0.0, min(a.end, b.end) - max(a.start, b.start))
    return inter / min(a.end - a.start, b.end - b.start)


def snap_to_words(words: list[Word], start: float, end: float) -> tuple[float, float]:
    """Move cut points onto word boundaries with a little breathing room."""
    inside = [w for w in words if w.end > start and w.start < end]
    if not inside:
        return start, end
    return max(0.0, inside[0].start - 0.15), inside[-1].end + 0.35
