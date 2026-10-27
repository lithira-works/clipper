---
name: clip-pipeline
description: Change, debug or tune Clipper's video pipeline (download, transcribe, signals, Claude scoring, reframe, captions, render). Use for any edit under apps/api/app/pipeline/, bad clip picks, crop/caption glitches, ffmpeg errors, or yt-dlp failures.
---

# Clip pipeline

The pipeline lives in `apps/api/app/pipeline/`. `orchestrator.py` is the only module that
touches the job store. Every other module is a pure function over paths and data.

```
ingest      download.probe/download                      (yt-dlp, heatmap, cookies)
understand  render.extract_audio -> transcribe.transcribe (+ diarize/scenes 🔨)
mine        signals.candidates -> scoring.rank (Claude)  -> signals.snap_to_words
package     package.build 🔨 (Claude: hook, titles, emphasis)  -> see the viral-packaging skill
direct      reframe.plan + captions + package -> direct.build_edl 🔨 (EDL)
render      render.render_clip(EDL) -> render.thumbnail  (deterministic, no LLM)
```

v0.1 renders directly from `reframe.plan` and `captions.build_ass`. Once CLP-160 lands, the
renderer takes **only** an EDL ([docs/specs/edl.md](../../../docs/specs/edl.md)). New visual
features go into the EDL first, then into the renderer.

## Before you change anything

1. Read `docs/ARCHITECTURE.md` §5 (Pipeline) and, for ranking changes, `docs/VIRAL_SCORING.md`.
2. Find the stage that owns the behavior. Don't patch a symptom downstream. For example, fix a
   bad cut in `snap_to_words` or `scoring` clamping, not in `render`.

## Rules

- Blocking work (yt-dlp, Whisper, OpenCV, ffmpeg) must be called from the orchestrator through
  `asyncio.to_thread`.
- New progress messages go through `report(stage, frac, message)` and stay within that stage's `_BANDS`.
- Every Claude call must keep these four things:
  - structured output (`output_config.format`) plus Pydantic validation
  - `stop_reason == "refusal"` check
  - `fallbacks="default"` with beta `server-side-fallback-2026-07-01`
  - a heuristic fallback, so AI never fails a job
- Model `claude-opus-5-5`: no `temperature`/`top_p`/`budget_tokens`/forced `tool_choice`/prefill (all 400).
- Any user or model text that reaches the ASS file goes through `captions._clean`, which prevents libass tag injection.
- ffmpeg filter expressions: escape `,` as `\,` inside expressions. Paths in `ass=` go through `render._ass_path`.
- The renderer must be deterministic: no LLM, network calls or randomness.
- User-facing errors come from `orchestrator._public_error`. Never leak stack traces or file paths.

## Debugging recipes

| Symptom | Look at |
|---|---|
| "Sign in to confirm you're not a bot" | Cookies are missing or expired. The user refreshes `secrets/cookies.txt` (never read that file). |
| Other `DownloadError` | yt-dlp is out of date (`uv lock --upgrade-package yt-dlp`), Deno is missing, or the video is age-gated |
| Clips start mid-sentence | `signals.sentences` (`_PAUSE_SPLIT`), `snap_to_words` padding |
| Clips feel random | Run `candidates` alone and print scores. Check `has_heatmap`. Read the `scoring.claude_failed` logs. |
| Crop jitters | `reframe.DEADZONE`, EMA factor in `_smooth`, `SAMPLE_FPS` |
| Speaker cut off | `MIN_FACE_COVERAGE`, or force `fit` mode to compare |
| Captions missing in output | Font not installed (`fc-list \| grep -i montserrat`), or a bad `ass=` path escape |
| Audio too quiet or loud | `loudnorm` params in `render_clip` |

For a failing user job, start with the `debug-job` skill. For ranking quality, use `eval-moments`.

Run a single stage in a Python shell from `apps/api`:

```python
from pathlib import Path
from app.pipeline import reframe
p = reframe.plan(Path("data/work/<job>/source.mp4"), 120.0, 160.0)
print(p.mode, p.x_expr[:200])
```

## Verify

```bash
cd apps/api && uv run ruff check app tests && uv run pytest -q
```

Add or extend a unit test in `apps/api/tests/` for any pure-function change. For render or
reframe changes, update the golden render test (CLP-004). Then run one real job end to end with
`docker compose up` and watch the result on a phone-sized viewport.
