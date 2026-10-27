# ADR-0003: Two-pass moment mining: signals, then Claude

- **Status:** Accepted
- **Date:** 2026-10-08
- **Tickets:** CLP-140, CLP-300

## Context
A 60-minute video has about 9k words and thousands of possible 20–60 s windows. Sending the whole
transcript to an LLM for every job is costly and slow. Signal-only ranking (heatmap, loudness)
misses context: it can't tell a joke from a shout.

## Options
1. **LLM-only** on the full transcript. Best judgment, but highest cost and latency, and long-context drift.
2. **Signals-only.** Cheap and deterministic, but poor editorial quality and no titles or hooks.
3. **Two-pass.** Deterministic signals shortlist `3 × max_clips` sentence-aligned windows, then Claude
   judges only those.

## Decision
Use two-pass. Claude Opus 5.5 with adaptive thinking ranks the shortlist using structured outputs.
If Claude fails or refuses, the signal ranking is the fallback.

## Consequences
- Input is about 5–15k tokens per job, so cost is predictable.
- Shortlist recall caps the final quality. Pass-1 recall is measured in the eval (CLP-300). If
  recall is low, widen the shortlist or add signals (laughter, speaker change, scene cuts).
