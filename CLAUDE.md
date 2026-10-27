# CLAUDE.md

Guidance for Claude Code in this repository. Read this first, then the skill that matches the task.

## Mission

A user pastes a YouTube URL and gets ranked 9:16 YouTube Shorts. Each one is the most viral moment,
with animated speech captions, a hook, emphasis effects and a publishing package (titles,
description, hashtags). The quality bar is "a pro editor would post it unchanged."

## Map

| Need | Go to |
|---|---|
| How it fits together, and what is built vs planned | `docs/ARCHITECTURE.md` (✅ / 🔨 / 🗺️) |
| What to work on next and its acceptance criteria | `TODO.md` (ticket IDs `CLP-xxx`) |
| Why a decision was made | `docs/adr/` |
| The edit format between AI and renderer | `docs/specs/edl.md` |
| Editorial rules (hooks, captions, pacing, packaging) | `docs/VIRAL_PLAYBOOK.md` |
| Moment-ranking algorithm and eval | `docs/VIRAL_SCORING.md` |
| UI tokens and components | `docs/DESIGN_SYSTEM.md` |
| HTTP contract | `docs/API.md` |
| Running in production | `docs/DEPLOYMENT.md` |

## Commands

| Task | Command |
|---|---|
| Full stack | `docker compose up --build -d` (web :3000, API docs :8000/docs) |
| Logs | `docker compose logs -f worker api` |
| API / worker / web dev | `make dev-api` · `make dev-worker` · `make dev-web` |
| Tests | `make test` (`cd apps/api && uv run pytest -q`) |
| Lint | `make lint` |
| Everything CI runs | `make check` |

## Architecture rules (do not break)

1. **The API stays thin.** Routes validate and enqueue. Heavy work only runs in the arq worker
   (`pipeline/orchestrator.py`).
2. **Stages are pure.** Modules in `app/pipeline/*.py` take paths and data and return data. Only `orchestrator.py`
   touches the store, progress or storage. Blocking work goes through `asyncio.to_thread`.
3. **Full snapshots only.** `JobStore.update` saves and publishes the whole `Job`. Never send partial
   or diff events.
4. **AI decides, code renders** (ADR-0002). Models write the EDL. The renderer reads only the EDL and must
   be deterministic, with no LLM or network calls.
5. **AI never fails a job.** If there is no key, an error, invalid JSON or a refusal, use the heuristic fallback.
6. **Contracts move together.** `schemas.py` ↔ `apps/web/src/lib/types.ts` (and `edl.py` ↔ `edl.ts`)
   change in the same commit.
7. **User-facing errors** come only from `orchestrator._public_error`. Never leak paths or stack traces.

## Claude API conventions

- Model `claude-opus-5-5` (env `CLAUDE_MODEL`). Use adaptive thinking and set `output_config.effort` explicitly.
- Use structured outputs (`output_config.format` JSON schema), then validate with Pydantic.
- Send `betas=["server-side-fallback-2026-07-01"]` and `fallbacks="default"`. Check `stop_reason == "refusal"`
  before reading content.
- Never send `temperature`, `top_p`, `budget_tokens`, forced `tool_choice` or assistant prefill. Each is a 400.
- Put a `cache_control` breakpoint on stable system prompts. Log `response.usage`.
- Prompts are derived from `docs/VIRAL_PLAYBOOK.md`. Change the playbook first, then the prompt, then run the eval.

## Video and pipeline gotchas

- ffmpeg filter expressions: escape `,` as `\,`. Paths in `ass=` go through `render._ass_path`.
- All text reaching ASS goes through `captions._clean`, which prevents libass tag injection.
- libass can't render color emoji. Use PNG overlays (EDL `overlays.emoji`).
- Captions must stay in the Shorts safe zone: above the bottom 22% and left of the right 12%.
- yt-dlp needs Deno (in the image). "Sign in to confirm you're not a bot" means `secrets/cookies.txt`
  is missing or expired. That file is a credential: never read, print or commit it.
- On CPU-only Docker hosts, use `WHISPER_MODEL=small`.

## Style

- Python 3.12: ruff (lint and format), strict mypy. Use dataclasses inside the pipeline and Pydantic at boundaries.
- TypeScript strict. Use server components by default and `"use client"` only for interactive leaves.
- UI: only the tokens in `globals.css` (`paper`, `ink`, `gold`, ...). No raw hex in components. Light theme only.
- Comments explain *why*. Keep functions small. Name things after the domain (clip, hook, EDL).

## Workflow

1. Find the ticket in `TODO.md`. If none exists, add one with acceptance criteria before large work.
2. Load the matching skill (below) and follow it.
3. Add or extend tests next to the change. Run `make check`.
4. Update docs. Flip ✅/🔨 in `ARCHITECTURE.md`, tick `TODO.md`, add a line to `CHANGELOG.md` under `[Unreleased]`.
5. For significant decisions, write an ADR (`docs/adr/0000-template.md`).

## Skills (`.claude/skills/`)

| Skill | Use for |
|---|---|
| `clip-pipeline` | Any change or bug in download, transcribe, signals, scoring, reframe, captions or render |
| `viral-packaging` | Hooks, titles, emphasis, the EDL builder, the packaging prompt, caption templates |
| `eval-moments` | Measuring whether a prompt, model or weight change improves clip picks |
| `debug-job` | A user's job failed or looks wrong: find out why from Redis and the logs |
| `add-api-endpoint` | New or changed HTTP endpoints end to end |
| `ui-component` | Web UI work within the design system |
| `release-check` | Before a PR merge or a release tag |
