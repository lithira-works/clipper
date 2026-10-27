"""Claude picks and packages the viral moments.

The signal pass (signals.py) shortlists ~3x more candidates than requested. Claude reads the
transcript of each, judges hook strength, payoff, emotional peak and stand-alone clarity, may
tighten the cut, and writes a Shorts title, on-screen hook and hashtags. If Claude is unavailable
the heuristic ranking is used so a job never fails on the AI step alone.
"""

from __future__ import annotations

import json
from typing import Any

import anthropic
import structlog
from pydantic import BaseModel, Field, ValidationError

from ..config import get_settings
from .download import SourceInfo
from .signals import Candidate

log = structlog.get_logger()

SYSTEM_PROMPT = """\
You are a senior YouTube Shorts editor who has grown multiple channels past 1M subscribers.
You receive candidate moments from a long-form video: transcript text plus engagement signals
(heat = YouTube "Most replayed" intensity, energy = loudness peaks, density = speech pace; all 0-1).

Pick the moments most likely to go viral as stand-alone vertical Shorts. Judge each on:
1. Hook - the first 2 seconds must create curiosity, tension or surprise. Prefer cuts that open
   on a bold claim, question, conflict or punchline set-up, never on filler ("so", "um", "anyway").
2. Payoff - the clip must resolve: a punchline, reveal, answer, or strong opinion.
3. Stand-alone clarity - a viewer with zero context understands it.
4. Emotion - humor, shock, inspiration, controversy, relatability.
5. Signals - high heat is strong evidence real viewers rewatched it; use it, but content wins.

Rules:
- Return at most the requested number of clips, best first. Fewer is fine if candidates are weak.
- You may tighten start/end inside the candidate window to sharpen the hook or ending, but stay
  within the allowed duration range and never cut mid-sentence.
- title: <= 60 chars, curiosity-driven, no clickbait lies, no emojis, no hashtags.
- hook: <= 8 words, punchy on-screen text shown in the first seconds.
- reason: one sentence on why this will perform.
- virality_score: 0-100, calibrated (80+ only for genuinely exceptional moments).
- hashtags: 3-5, lowercase, no '#', relevant to the clip, include "shorts".
"""

_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "clips": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "candidate_id": {"type": "integer"},
                    "start": {"type": "number"},
                    "end": {"type": "number"},
                    "title": {"type": "string"},
                    "hook": {"type": "string"},
                    "reason": {"type": "string"},
                    "virality_score": {"type": "integer"},
                    "hashtags": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "candidate_id", "start", "end", "title", "hook",
                    "reason", "virality_score", "hashtags",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["clips"],
    "additionalProperties": False,
}


class RankedClip(BaseModel):
    candidate_id: int
    start: float
    end: float
    title: str = Field(max_length=120)
    hook: str
    reason: str
    virality_score: int
    hashtags: list[str]


class Ranking(BaseModel):
    clips: list[RankedClip]


def _fmt(t: float) -> str:
    return f"{int(t // 60):02d}:{t % 60:05.2f}"


def _user_prompt(
    source: SourceInfo, cands: list[Candidate], max_clips: int, min_d: int, max_d: int
) -> str:
    chapters = ", ".join(f"{_fmt(c['start_time'])} {c['title']}" for c in source.chapters[:30])
    blocks = "\n\n".join(
        f'<candidate id="{i}" start="{c.start:.2f}" end="{c.end:.2f}" ({_fmt(c.start)}-{_fmt(c.end)}) '
        f'heat="{c.heat}" energy="{c.energy}" density="{c.density}">\n{c.text}\n</candidate>'
        for i, c in enumerate(cands)
    )
    return (
        f"<video>\ntitle: {source.title}\nchannel: {source.channel or 'unknown'}\n"
        f"duration: {_fmt(source.duration)}\nchapters: {chapters or 'none'}\n"
        f"description: {source.description[:1500]}\n</video>\n\n"
        f"{blocks}\n\n"
        f"Select up to {max_clips} clips. Each clip must be {min_d}-{max_d} seconds long. "
        "Times are in seconds from the start of the video."
    )


def rank(
    source: SourceInfo, cands: list[Candidate], max_clips: int, min_d: int, max_d: int
) -> list[RankedClip]:
    settings = get_settings()
    if not cands:
        return []
    if not any(c.text.strip() for c in cands):
        # No transcript to judge (audio-only candidates); Claude would only be guessing.
        return _heuristic(source, cands, max_clips)
    if settings.anthropic_api_key:
        try:
            ranked = _rank_with_claude(source, cands, max_clips, min_d, max_d)
            if ranked:
                return ranked
        except (anthropic.APIError, ValidationError, json.JSONDecodeError) as e:
            log.warning("scoring.claude_failed", error=str(e))
    else:
        log.info("scoring.no_api_key", fallback="heuristic")
    return _heuristic(source, cands, max_clips)


def _rank_with_claude(
    source: SourceInfo, cands: list[Candidate], max_clips: int, min_d: int, max_d: int
) -> list[RankedClip]:
    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.beta.messages.create(
        model=settings.claude_model,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        # Re-runs a safety-declined request on Anthropic's recommended fallback model.
        fallbacks="default",
        thinking={"type": "adaptive"},
        output_config={
            "effort": settings.claude_effort,
            "format": {"type": "json_schema", "schema": _SCHEMA},
        },
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": _user_prompt(source, cands, max_clips, min_d, max_d)}
        ],
    )
    if response.stop_reason == "refusal":
        log.warning("scoring.refusal", details=str(response.stop_details))
        return []
    text = "".join(b.text for b in response.content if b.type == "text")
    ranking = Ranking.model_validate_json(text)

    clips: list[RankedClip] = []
    for c in ranking.clips[:max_clips]:
        if not 0 <= c.candidate_id < len(cands):
            continue
        cand = cands[c.candidate_id]
        # Clamp into the candidate window and the requested duration range.
        start = max(cand.start, min(c.start, cand.end - min_d))
        end = min(cand.end, max(c.end, start + min_d))
        end = min(end, start + max_d)
        clips.append(
            c.model_copy(
                update={
                    "start": start,
                    "end": end,
                    "virality_score": max(0, min(100, c.virality_score)),
                    "hashtags": [h.lstrip("#").lower() for h in c.hashtags][:5],
                }
            )
        )
    log.info("scoring.claude_ok", clips=len(clips), usage=response.usage.model_dump())
    return clips


def _heuristic(source: SourceInfo, cands: list[Candidate], max_clips: int) -> list[RankedClip]:
    best = sorted(enumerate(cands), key=lambda ic: ic[1].score, reverse=True)[:max_clips]
    out = []
    for i, c in best:
        words = c.text.split()
        out.append(
            RankedClip(
                candidate_id=i,
                start=c.start,
                end=c.end,
                title=f"{source.title[:45]} - part {len(out) + 1}",
                hook=" ".join(words[:6]) + ("..." if len(words) > 6 else ""),
                reason=(
                    "Ranked by replay heatmap, loudness and speech pace."
                    if c.text
                    else "Picked by replay heatmap and loudness peaks (little speech detected)."
                ),
                virality_score=int(round(c.score * 100)),
                hashtags=["shorts", "viral", "clips"],
            )
        )
    return out
