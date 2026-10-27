# Viral scoring

Clipper picks moments in two passes ([ADR-0003](adr/0003-two-pass-moment-mining.md)). A cheap,
deterministic signal pass shortlists candidates. Then Claude makes the editorial call. The editorial
rules both passes follow are in [VIRAL_PLAYBOOK.md](VIRAL_PLAYBOOK.md). Packaging (hooks, titles,
emphasis) is a separate step. See ARCHITECTURE §5.4.

## Pass 1: signals (`pipeline/signals.py`)

Candidate windows start and end on sentence boundaries. A sentence ends at `. ! ? …` or after
a pause of 0.8 s or more. A window qualifies when its length is within `[min_duration, max_duration]`.

Each signal is min-max normalized per video to 0..1:

| Signal | Source | Why it matters |
|---|---|---|
| `heat` | YouTube "Most replayed" heatmap (`yt-dlp` `heatmap` field). The window score is the mean of the window average and the window peak. | Direct evidence that real viewers rewound to this part |
| `energy` | Peak per-second RMS loudness of the audio | Laughter, applause, shouting and music drops |
| `density` | Words per second, capped at 3 w/s | Fast speech holds attention; dead air does not |

```
score = 0.55·heat + 0.25·energy + 0.20·density     (with heatmap)
score = 0.60·energy + 0.40·density                 (no heatmap: new or small videos)
```

Windows are sorted by score and accepted greedily if they overlap every accepted window by
less than 30%. The top `3 × max_clips` go to pass 2.

## Pass 2: Claude (`pipeline/scoring.py`)

- Model: `claude-opus-5-5`, adaptive thinking, `effort` from `CLAUDE_EFFORT` (default `high`).
- Input: the video title, channel, chapters and description, plus each candidate's transcript and signal values.
- Output: a JSON schema enforced through structured outputs (`output_config.format`) and then
  validated with Pydantic. Each clip has `candidate_id, start, end, title, hook, reason, virality_score, hashtags`.
- Rubric (from the system prompt):
  - **hook** in the first 2 s
  - **payoff**
  - **stand-alone clarity**
  - **emotion**
  - **signals**, used as evidence, with content judged first
- Claude may tighten the cut inside the candidate window. The server clamps the result back into
  the window and the duration range, then snaps it to word boundaries (−0.15 s / +0.35 s padding).

### Fallbacks

| Situation | Behavior |
|---|---|
| No `ANTHROPIC_API_KEY` | Heuristic ranking: top signal scores with generic titles |
| API error, invalid JSON or schema mismatch | Logged as `scoring.claude_failed`, then heuristic ranking |
| Safety decline | The `fallbacks: "default"` server-side fallback re-runs the request on Anthropic's recommended model. If the final `stop_reason` is still `refusal`, heuristic ranking is used. |

## Evaluation

These are planned (CLP-300). The procedure is in the `eval-moments` skill.
1. Collect about 50 diverse long-form videos with 3–5 human-picked "best Short" windows each.
2. Metric: **hit@k**, where a pick counts as a hit if it has IoU ≥ 0.5 with any human window. Secondary
   metric: the correlation between `virality_score` and real Shorts view counts, once uploads exist.
3. Run the eval on every change to the prompt, weights or model, and record the cost per job.

## Tuning knobs

| Knob | Where |
|---|---|
| Signal weights | `signals.candidates` → `weights` |
| Shortlist size | `orchestrator` → `limit=req.max_clips * 3` |
| Rubric / tone | `scoring.SYSTEM_PROMPT` |
| Depth vs cost | `CLAUDE_EFFORT` (`medium` is cheaper; `xhigh` is for harder content) |
