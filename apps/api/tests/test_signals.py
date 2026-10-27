import numpy as np

from app.pipeline.download import HeatPoint
from app.pipeline.signals import candidates, heat_per_second, sentences, snap_to_words
from app.pipeline.transcribe import Transcript, Word


def _words(n: int, start: float = 0.0, step: float = 0.4) -> list[Word]:
    out = []
    for i in range(n):
        text = f"w{i}." if i % 8 == 7 else f"w{i}"
        out.append(Word(start + i * step, start + i * step + 0.3, text))
    return out


def test_sentences_split_on_punctuation_and_pauses() -> None:
    words = [Word(0, 0.3, "Hello"), Word(0.4, 0.7, "world."), Word(2.0, 2.3, "Next")]
    s = sentences(words)
    assert [x.text for x in s] == ["Hello world.", "Next"]


def test_heat_per_second_normalized() -> None:
    heat = heat_per_second([HeatPoint(0, 10, 0.2), HeatPoint(10, 20, 1.0)], 20)
    assert heat is not None
    assert heat.max() == 1.0 and heat.min() == 0.0


def test_candidates_respect_bounds_and_prefer_heat() -> None:
    words = _words(400)  # ~160 s of speech
    duration = words[-1].end
    hm = [HeatPoint(0, 100, 0.1), HeatPoint(100, 130, 1.0), HeatPoint(130, duration, 0.1)]
    heat = heat_per_second(hm, duration)
    energy = np.zeros(int(duration) + 1, dtype=np.float32)
    cands = candidates(Transcript("en", words), heat, energy, 20, 40, limit=3)
    assert cands
    for c in cands:
        assert 20 <= c.end - c.start <= 40
        assert c.text
    best = max(cands, key=lambda c: c.score)
    assert best.end > 100 and best.start < 130


def test_snap_to_words_pads_edges() -> None:
    words = [Word(1.0, 1.5, "a"), Word(2.0, 2.5, "b")]
    start, end = snap_to_words(words, 1.2, 2.2)
    assert start == 0.85 and end == 2.85


def test_load_wav_returns_normalized_float32(tmp_path) -> None:  # type: ignore[no-untyped-def]
    import wave

    from app.pipeline.transcribe import load_wav

    path = tmp_path / "a.wav"
    samples = np.array([0, 16384, -32768], dtype=np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(samples.tobytes())
    out = load_wav(path)
    assert out.dtype == np.float32
    assert out.tolist() == [0.0, 0.5, -1.0]


def test_audio_candidates_pick_loud_part_without_transcript() -> None:
    from app.pipeline.signals import audio_candidates

    energy = np.zeros(200, dtype=np.float32)
    energy[120:140] = 1.0
    cands = audio_candidates(None, energy, 200.0, 15, 30, limit=3)
    assert cands and all(c.text == "" for c in cands)
    assert all(15 <= c.end - c.start <= 30 for c in cands)
    best = max(cands, key=lambda c: c.score)
    assert best.start < 140 and best.end > 120


def test_audio_candidates_empty_when_video_too_short() -> None:
    from app.pipeline.signals import audio_candidates

    assert audio_candidates(None, np.ones(10, dtype=np.float32), 10.0, 15, 30, limit=3) == []
