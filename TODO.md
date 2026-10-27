# TODO

The backlog is organized into milestones. Each ticket has an ID (`CLP-xxx`, referenced from
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)), a size (**S** ≤ ½ day, **M** 1–2 days, **L** 3–5
days) and acceptance criteria (AC).

**Definition of done (every ticket):**

- Code, tests, docs and CHANGELOG are updated.
- `make check` is green.
- Contracts are in sync (`schemas.py` ↔ `types.ts`, `edl.py` ↔ `edl.ts`).
- The demo has been verified in the running stack.

---

## ✅ v0.1 Scaffold (done)

Monorepo, Docker, CI · FastAPI job API + SSE · arq worker · yt-dlp with heatmap and cookies ·
faster-whisper word timestamps · signal shortlist · Claude Opus 5.5 ranking with fallbacks ·
YuNet reframe · ASS karaoke captions + hook · ffmpeg 1080×1920 −14 LUFS · Next.js 16 UI.

---

## M0: Prove it end to end (now)

| ID | Task | Size |
|---|---|---|
| CLP-001 | **First real job end to end.** Run one job with `secrets/cookies.txt` and `ANTHROPIC_API_KEY`, then review the output on a phone | S |
| CLP-002 | **Local-file source for tests.** `JobCreate.file_id` (dev-only) skips yt-dlp | S |
| CLP-003 | **Pipeline integration test.** A 45 s CC-BY speech fixture runs through every stage in CI with Claude mocked | M |
| CLP-004 | **Render golden test.** A fixed EDL plus fixture must match frame hashes at t = 0.5, 5 and 10 s | S |

**AC for CLP-001:**
- The clip starts on a full sentence.
- Captions are in sync to within 100 ms.
- The face stays in frame.
- Audio measures −14 ±1 LUFS (`ffmpeg -af ebur128`).

**AC for CLP-003:**
- CI runs the full pipeline in < 4 min on CPU.
- The job ends with `succeeded`.
- The MP4 is 1080×1920 at 30 fps with an audio stream.

---

## M1 · v0.2: Viral Shorts quality ⭐ core product

The goal is that every Short looks hand-edited: a strong hook, emphasized speech captions,
punch-in zooms and a full publishing package.

| ID | Task | Size | Depends |
|---|---|---|---|
| CLP-160 | **EDL contract and `direct.py`.** `app/edl.py` (Pydantic) per [specs/edl.md](docs/specs/edl.md). The renderer reads only the EDL. | L | — |
| CLP-150 | **Viral packaging call.** `package.py` returns hook, 3 titles, description, hashtags, pinned comment, emphasis words, thumbnail_t and loop_hint, following the [playbook](docs/VIRAL_PLAYBOOK.md) | M | 160 |
| CLP-170 | **Caption templates.** `bold-gold`, `minimal`, `boxed`, `none` as data. Safe-zone placement. | M | 160 |
| CLP-171 | **Emphasis rendering.** Color and scale on emphasis words, 1.12× punch-in zoom | M | 150, 170 |
| CLP-172 | **Emoji overlays.** Twemoji PNGs (CC-BY) over emphasis words | S | 171 |
| CLP-173 | **Progress bar overlay** (optional per job) | S | 160 |
| CLP-140 | **Hook self-check.** A Claude pass rejects finalists whose first 3 s need context | S | — |
| CLP-130 | **Speaker diarization** (pyannote). Avoid cuts mid-speaker-turn. Speaker-change signal. | M | — |
| CLP-131 | **Scene detection** (PySceneDetect). Scene-cut signal. | S | — |
| CLP-161 | **Active-speaker reframe.** Pick the face of the current diarized speaker | M | 130 |
| CLP-162 | **Hard cut on scene change** in the crop path | S | 131 |
| CLP-120 | **Reuse YouTube auto-captions** as a seed. Whisper only re-times words (big CPU win). | M | — |
| CLP-121 | **Source cache** by `video_id` (24 h TTL) | S | — |
| CLP-180 | **Publishing package UI.** Title picker, description, pinned comment, copy-all | S | 150 |

**AC for CLP-150:**
- Every finalist has all package fields.
- Titles are ≤ 60 chars with no emoji.
- The hook text does not repeat the first spoken line.
- Validated by Pydantic. Heuristic fallback on failure.
- Prompt caching is on for the system prompt.

**AC for CLP-171:**
- At most 1 emphasis per 3 s.
- A zoom never crosses a scene cut.
- The golden test is updated.

**AC for milestone M1:** blind review of 20 clips from 5 videos: ≥ 70% rated "would post as-is"
by 2 reviewers.

---

## M2 · v0.3: Editor and contracts

| ID | Task | Size |
|---|---|---|
| CLP-204 | Generate `types.ts` and `edl.ts` from OpenAPI (`openapi-typescript`). CI fails on drift. | S |
| CLP-210 | **Clip editor** `/clips/[id]/edit`: trim handles on the waveform, edit hook and caption text, choose a template, CSS live preview | L |
| CLP-211 | `POST /v1/clips/{id}/render` re-renders from an edited EDL (no LLM, cached source) | M |
| CLP-212 | Render history (versions per clip) and download of any version | S |
| CLP-213 | Cancel job `DELETE /v1/jobs/{id}` (arq abort plus cleanup) | S |
| CLP-214 | shadcn/ui primitives on our tokens (Dialog, Slider, Tabs, Toast) | S |

---

## M3 · v0.4: Launchable (security, durability, operations)

| ID | Task | Size |
|---|---|---|
| CLP-101 | Postgres 17 + SQLAlchemy 2 async + Alembic: `users`, `jobs`, `clips` (EDL JSONB), `renders` | L |
| CLP-102 | Auth: write ADR-0005 (Clerk vs Better Auth), then implement. Per-user job history. | M |
| CLP-103 | Cloudflare R2 storage and signed URLs. Remove the local `/media` mount. | M |
| CLP-104 | TTL cleanup cron for sources (24 h) and renders (per plan) | S |
| CLP-105 | Terms of use, takedown flow, and a required "I own or may reuse this video" checkbox | S |
| CLP-106 | Sentry (api, worker, web) and an OpenTelemetry span per pipeline stage | M |
| CLP-107 | Cloudflare Turnstile on submit. Per-user quotas. | S |
| CLP-108 | Persist Claude token usage and cost per job. Admin cost dashboard. | S |
| CLP-109 | Production deploy: web/api on Cloud Run or Fly, GPU workers on Modal or RunPod, managed Redis/PG | L |

---

## M4: Quality research

| ID | Task | Size |
|---|---|---|
| CLP-300 | **Moment eval set.** 50 videos with human-picked windows. Metrics: hit@k (IoU ≥ 0.5) and pass-1 recall. Runs on prompt/model PRs (see the `eval-moments` skill). | L |
| CLP-310 | Forced alignment (wav2vec2) for ±30 ms caption timing | M |
| CLP-311 | Audio-event detection (laughter, applause) as a signal | M |
| CLP-312 | Claude vision on finalist keyframes to judge the visual hook | M |
| CLP-320 | Split-screen layout for two-speaker clips | M |
| CLP-330 | B-roll from a stock API (Pexels) using `broll_queries` | M |
| CLP-331 | SFX pack (CC0) and cues from packaging | S |
| CLP-332 | Licensed background music with ducking | M |
| CLP-333 | NVENC GPU encoding path | S |

---

## M5 · v1.0: Platform

| ID | Task | Size |
|---|---|---|
| CLP-400 | One-click YouTube upload (Data API v3, OAuth, schedule) | L |
| CLP-401 | TikTok and Instagram Reels export (safe zones per platform) | M |
| CLP-402 | Translated captions | M |
| CLP-403 | Stripe usage billing | L |
| CLP-404 | Public API keys and webhooks | M |
| CLP-405 | Channel import: auto-clip new uploads (Temporal, see ADR-0004) | L |
