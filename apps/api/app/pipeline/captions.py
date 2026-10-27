"""Shorts-style animated captions as an ASS subtitle file (burned in by ffmpeg/libass).

Bold style: 1-3 words on screen, UPPERCASE, heavy outline, the spoken word pops in dark yellow.
A hook banner (dark-yellow box, black text) sits at the top for the first seconds.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..config import get_settings
from ..schemas import CaptionStyle
from .transcribe import Word

# ASS colours are &HAABBGGRR
YELLOW = "&H0000A8E0"  # #E0A800 dark yellow (brand accent)
WHITE = "&H00FFFFFF"
BLACK = "&H00000000"

MAX_WORDS_PER_CHUNK = 3
CHUNK_PAUSE = 0.45
HOOK_SECONDS = 2.8


def _ts(t: float) -> str:
    t = max(t, 0.0)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def _clean(text: str) -> str:
    return re.sub(r"[{}\\]", "", text).replace("\n", " ").strip()


def chunk_words(words: list[Word]) -> list[list[Word]]:
    chunks: list[list[Word]] = []
    cur: list[Word] = []
    for w in words:
        if cur and (
            len(cur) >= MAX_WORDS_PER_CHUNK
            or w.start - cur[-1].end > CHUNK_PAUSE
            or re.search(r"[.!?,;:]$", cur[-1].text)
        ):
            chunks.append(cur)
            cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    return chunks


def build_ass(
    words: list[Word], clip_start: float, clip_end: float, style: CaptionStyle, hook: str
) -> str:
    s = get_settings()
    font = s.caption_font
    W, H = s.output_width, s.output_height
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Bold,{font},96,{WHITE},{YELLOW},{BLACK},&H80000000,-1,0,0,0,100,100,1,0,1,7,3,2,60,60,560,1
Style: Minimal,{font},64,{WHITE},{WHITE},{BLACK},&H80000000,-1,0,0,0,100,100,0,0,1,4,1,2,80,80,420,1
Style: Hook,{font},70,{BLACK},{BLACK},{YELLOW},{YELLOW},-1,0,0,0,100,100,0,0,3,18,0,8,80,80,260,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events: list[str] = []
    if hook.strip():
        events.append(
            f"Dialogue: 1,{_ts(0)},{_ts(HOOK_SECONDS)},Hook,,0,0,0,,"
            f"{{\\fad(120,200)}}{_clean(hook).upper()}"
        )

    clip_words = [
        Word(w.start - clip_start, min(w.end, clip_end) - clip_start, _clean(w.text))
        for w in words
        if w.end > clip_start and w.start < clip_end and _clean(w.text)
    ]

    if style == CaptionStyle.none:
        return header + "\n".join(events) + "\n"

    for chunk in chunk_words(clip_words):
        if style == CaptionStyle.minimal:
            text = " ".join(w.text for w in chunk)
            events.append(
                f"Dialogue: 0,{_ts(chunk[0].start)},{_ts(chunk[-1].end)},Minimal,,0,0,0,,{text}"
            )
            continue
        # One event per spoken word: whole chunk visible, active word yellow + slight pop.
        for i, w in enumerate(chunk):
            end = chunk[i + 1].start if i + 1 < len(chunk) else w.end
            parts = []
            for j, other in enumerate(chunk):
                word = other.text.upper()
                if j == i:
                    parts.append(
                        f"{{\\c{YELLOW}\\fscx112\\fscy112\\t(0,80,\\fscx100\\fscy100)}}"
                        f"{word}{{\\c{WHITE}\\fscx100\\fscy100}}"
                    )
                else:
                    parts.append(word)
            events.append(
                f"Dialogue: 0,{_ts(w.start)},{_ts(max(end, w.start + 0.05))},Bold,,0,0,0,,"
                + " ".join(parts)
            )
    return header + "\n".join(events) + "\n"


def write_ass(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path
