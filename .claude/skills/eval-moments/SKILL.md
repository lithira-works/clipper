---
name: eval-moments
description: Measure whether a change to signal weights, the shortlist, the ranking or packaging prompt, or the Claude model/effort actually improves Clipper's clip picks. Use before merging any change to signals.py, scoring.py, package.py, SYSTEM_PROMPT or CLAUDE_MODEL/CLAUDE_EFFORT, or when asked "are the clips good / did this help".
---

# Moment eval

Never tune prompts or weights by eyeballing one video. Use this eval (ticket CLP-300).

## Dataset: `apps/api/evals/moments/`

```
videos.jsonl      {"video_id": "...", "url": "...", "genre": "podcast|talk|gaming|vlog|interview",
                   "license": "CC-BY|owned|permission", "duration": 3621}
labels.jsonl      {"video_id": "...", "windows": [[812.4, 851.9], [1203.0, 1240.5]], "labeler": "a"}
cache/            transcripts + signals per video (so runs don't re-download or re-transcribe)
```

- Aim for about 50 videos across genres, each with 3–5 human-picked "best Short" windows from two labelers.
- Only use videos you have rights to evaluate. Record `license` for each one.

## Metrics

| Metric | Definition | Target |
|---|---|---|
| **pass-1 recall** | Share of human windows overlapped (IoU ≥ 0.5) by any shortlist candidate | ≥ 0.85 |
| **hit@k** | Share of the final top-k picks that hit a human window (IoU ≥ 0.5) | Track; must not regress |
| **hook-valid rate** | Share of picks whose first 3 s pass the stand-alone check | ≥ 0.9 |
| **cost/job** | Mean Claude input+output tokens × price | Report |
| **latency** | p50/p95 scoring time | Report |

If recall is low, the shortlist is the bottleneck: widen `limit` or add signals. Prompt
work can't recover windows that never reach Claude.

## Running it

```bash
cd apps/api
uv run python -m evals.moments.run --tag baseline           # current main
uv run python -m evals.moments.run --tag my-change          # your branch
uv run python -m evals.moments.compare baseline my-change   # table + per-video diff
```

The runner must:
- Use cached transcripts and signals.
- Call only `signals.candidates` + `scoring.rank` (+ `package` if relevant).
- Write `results/<tag>.jsonl` with picks, scores, usage and timings.

## Rules

- **Get approval before spending money.** A full run calls Claude about 50 times. State the estimated
  cost (tokens × price for `claude-opus-5-5`) and get the user's OK first.
- Change one thing per run (weights *or* prompt *or* effort), so the effect is attributable.
- Report the comparison table in the PR. Merge only if the metrics improve or hold, and explain any trade-off.
- Keep a held-out 20% split that you look at only for the final check. This avoids overfitting prompts.
