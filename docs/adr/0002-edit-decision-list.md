# ADR-0002: AI outputs an Edit Decision List; rendering is deterministic

- **Status:** Accepted
- **Date:** 2026-10-14
- **Tickets:** CLP-160, CLP-210

## Context
In v0.1 the orchestrator calls caption, reframe and render functions directly, with values
taken from the Claude ranking. The following require a stable, serializable description of a clip:
- letting users edit a clip (trim, change hook text, change template)
- re-rendering without re-running AI
- testing rendering
- comparing prompt versions

## Options
1. **Keep imperative calls.** Simple, but every edit means re-running the pipeline.
2. **EDL.** AI and heuristics write a JSON document, and the renderer reads only that document.
3. **Store the ffmpeg command line.** Serializable, but not editable or semantic.

## Decision
Use an EDL. The spec is in [specs/edl.md](../specs/edl.md). It is stored per clip (Postgres JSONB) and versioned.

## Consequences
- The clip editor becomes "edit JSON, then POST a re-render", with no LLM cost.
- The renderer can be golden-tested: a fixture EDL and source must produce the expected frame hashes.
- Prompt and model changes show up as EDL diffs, which are reviewable in evals.
- One extra module (`direct.py`) and one contract to keep in sync with TypeScript.
