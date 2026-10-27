# Architecture

> **Status legend:** ✅ built (v0.1) · 🔨 next milestone · 🗺️ planned.
> Ticket IDs (`CLP-xxx`) refer to [TODO.md](../TODO.md). Decisions are recorded in [docs/adr/](adr/).

## 1. Product goal

When a user pastes a YouTube URL, Clipper returns ranked, ready-to-upload YouTube Shorts (9:16,
≤60 s). Each Short:
- is the most engaging moment of the source video
- has animated speech captions
- has a scroll-stopping hook
- includes the publishing package: titles, description, hashtags and pinned comment

The bar is "a Short a professional editor would post without changes."

## 2. Design principles

1. **AI decides, code renders.** Models produce a declarative **Edit Decision List (EDL)**.
   A deterministic renderer turns the EDL into pixels. This keeps rendering testable,
   lets a human editor change the EDL in the UI, and means a re-render never calls an
   LLM ([ADR-0002](adr/0002-edit-decision-list.md)).
2. **Signals before LLM.** Cheap deterministic signals shortlist candidates, and Claude only judges
   the shortlist. This bounds cost and latency ([ADR-0003](adr/0003-two-pass-moment-mining.md)).
3. **Every AI step degrades.** If a model is missing, errors or refuses, the job falls back
   to heuristics. The job never fails because of the AI step.
4. **Stages are pure.** Each pipeline stage maps paths and data to data. Only the orchestrator
   performs side effects (store, progress, storage).
5. **One source of truth per contract.** Pydantic models in `apps/api/app/schemas.py` (and
   `app/edl.py` 🔨) define the contracts. The TypeScript types mirror them, and generation from
   OpenAPI is planned (CLP-204).

## 3. System context

```
                ┌────────────────────────── Browser ───────────────────────────┐
                │  Next.js 16 app: paste URL · live progress · clip editor     │
                └───────────────┬──────────────────────────────▲───────────────┘
                     HTTPS /api/v1, /media              SSE job snapshots
                ┌───────────────▼──────────────────────────────┴───────────────┐
                │ web (Next.js, RSC)  ──rewrite──▶  api (FastAPI)              │
                └───────────────────────────────────────┬──────────────────────┘
                                         enqueue (arq)  │  read/write Job JSON
                                   ┌────────────────────▼────────┐
                                   │ Redis 7: queue · state · pub/sub │
                                   └────────────────────┬────────┘
                       ┌────────────────────────────────▼───────────────────────────┐
                       │ worker × N (CPU or GPU)  — pipeline (§5)                  │
                       └──┬──────────────┬────────────────┬──────────────┬──────────┘
                     YouTube        Claude API       Object store     Postgres 🔨
                     (yt-dlp)    (Opus 5.5, vision)   (local ✅ / R2 🔨)  (users, jobs, clips)
```

| Container | Tech | Responsibility | Scaling |
|---|---|---|---|
| `web` | Next.js 16, React 19, Tailwind v4 | UI, same-origin proxy | Stateless, horizontal |
| `api` | FastAPI, Pydantic v2, sse-starlette | Validation, auth 🔨, rate limiting, job CRUD, SSE, media | Stateless, horizontal |
| `redis` | Redis 7 | arq queue, live Job JSON, progress pub/sub, rate-limit counters | Managed Redis |
| `worker` | arq, ffmpeg, faster-whisper, OpenCV, Anthropic SDK | Whole pipeline | `WORKER_REPLICAS`, GPU pool 🗺️ |
| `postgres` 🔨 | Postgres 17 + SQLAlchemy 2 + Alembic | Durable users, jobs, clips, EDLs | Managed PG |
| object store 🔨 | S3 / Cloudflare R2 | Sources (short TTL), renders, thumbnails | CDN + signed URLs |

## 4. Job lifecycle

```
queued ─▶ running[downloading ▸ transcribing ▸ analyzing ▸ packaging🔨 ▸ reframing ▸ rendering] ─▶ succeeded
                                     └──────────────────── any exception ─────────────────▶ failed
```

1. `POST /v1/jobs` validates the request (YouTube-only URL, duration bounds) and applies the per-IP
   rate limit. It then writes a `queued` Job, enqueues `process_job`, and returns `202 {id}`. ✅
2. The browser opens `GET /v1/jobs/{id}/events` (SSE). Every `JobStore.update` publishes the
   **full** Job snapshot. The SSE handler re-reads Redis every 5 s if it misses a message. ✅
3. Clips are appended to `job.clips` as each one finishes, so the UI fills in progressively. ✅
4. Re-render 🔨 `POST /v1/clips/{id}/render` takes an edited EDL and runs only the
   render stage (no LLM, no download if the source is cached).

## 5. Pipeline

```
 ┌─────────┐   ┌───────────┐   ┌──────────┐   ┌───────────┐   ┌──────────┐   ┌──────────┐   ┌────────┐
 │ 1 Ingest│──▶│2 Understand│──▶│3 Mine    │──▶│4 Package  │──▶│5 Direct  │──▶│6 Render  │──▶│7 Publish│
 │ yt-dlp  │   │ ASR, diar.,│   │ signals +│   │ Claude:   │   │ reframe, │   │ ffmpeg + │   │ package │
 │ heatmap │   │ scenes,    │   │ Claude   │   │ hook,title│   │ EDL build│   │ libass   │   │ YouTube🗺️│
 └─────────┘   │ audio evts │   │ ranking  │   │ emphasis  │   └──────────┘   └──────────┘   └────────┘
               └───────────┘   └──────────┘   └───────────┘
```

### 5.1 Ingest: `pipeline/download.py`

| Item | Status |
|---|---|
| `probe` (metadata only) rejects live streams, videos over the max duration and private videos before downloading | ✅ |
| ≤1080p MP4 via yt-dlp. Deno runtime for YouTube JS challenges. Optional `cookies.txt` | ✅ |
| Reads the **"Most replayed" heatmap**, chapters, description and thumbnail | ✅ |
| Reuses YouTube auto-captions as a transcript seed (skips ASR on CPU deployments) | 🔨 CLP-120 |
| Source cache keyed by `video_id` with TTL, so repeated URLs are instant | 🔨 CLP-121 |

### 5.2 Understand

| Signal | Tech | Status |
|---|---|---|
| Word-level transcript | faster-whisper (`large-v3-turbo` on GPU, `small` on CPU), VAD, word timestamps | ✅ |
| Forced alignment for tighter word timing | WhisperX-style wav2vec2 alignment | 🗺️ CLP-310 |
| Speaker diarization (who speaks when) | pyannote.audio community pipeline | 🔨 CLP-130 |
| Shot boundaries | PySceneDetect `AdaptiveDetector` | 🔨 CLP-131 |
| Audio events (laughter, applause, music) | PANNs / YAMNet classifier | 🗺️ CLP-311 |
| Loudness envelope | RMS per second (numpy) | ✅ |
| Visual hook check | Claude vision on 3–6 keyframes per finalist | 🗺️ CLP-312 |

### 5.3 Mine: find the viral moment (`signals.py`, `scoring.py`)

This is a two-pass design ([ADR-0003](adr/0003-two-pass-moment-mining.md)). The full rubric and the eval are in
[VIRAL_SCORING.md](VIRAL_SCORING.md).

- **Pass 1 (signals ✅).** Pass 1 builds sentence-aligned windows within [min, max] seconds and scores them:
  `0.55·heat + 0.25·energy + 0.20·density`. It keeps the top `3 × max_clips` after greedy
  de-overlap. Laughter, speaker-change and scene features join the score in 🔨.
- **Pass 2 (Claude ✅).** `claude-opus-5-5` uses adaptive thinking, structured output and `fallbacks:"default"`.
  It judges hook, payoff, stand-alone clarity and emotion, tightens the cut and scores 0–100. The result is
  clamped and snapped to word boundaries.
- **Self-check 🔨 CLP-140.** A second short Claude call re-reads each finalist's first 3 seconds and
  rejects any whose hook depends on earlier context.

### 5.4 Package: content that makes it go viral 🔨 CLP-150

This is one structured Claude call per finalist. Rules come from [VIRAL_PLAYBOOK.md](VIRAL_PLAYBOOK.md).

| Output | Used for |
|---|---|
| `hook_text` (≤ 8 words) and `hook_style` | On-screen banner in the first ~2.5 s |
| `titles[3]` (≤ 60 chars, ranked) | YouTube title, A/B candidates |
| `description`, `hashtags[3–5]`, `pinned_comment` | Publishing package (§5.7) |
| `emphasis[]`: word indices plus `color` / `emoji` / `zoom` | Caption highlights, punch-in zooms |
| `broll_queries[]` (optional) | Stock B-roll lookup 🗺️ CLP-330 |
| `sfx_cues[]` (whoosh / pop / ding at word index) | Sound design 🗺️ CLP-331 |
| `thumbnail_t` | Best frame for the cover |
| `loop_hint` | Whether the ending can cut back to the start seamlessly |

Today (v0.1) the ranking call already returns `title`, `hook`, `hashtags` and `reason`. CLP-150 moves these
into a dedicated packaging call that returns the richer schema above.

### 5.5 Direct: build the EDL 🔨 CLP-160

`pipeline/direct.py` merges the following into one `EditDecisionList` per clip:
- the cut (`start`/`end`)
- the crop path (from `reframe.py` ✅)
- caption chunks (from `captions.py` ✅)
- packaging (emphasis, hook, zooms)
- the audio settings

The schema is in [specs/edl.md](specs/edl.md). The EDL is persisted with the clip and is the
**only** input to the renderer.

Reframe details (✅):
- YuNet face detection at 2 fps.
- A median filter, then dead-zone EMA smoothing.
- The result is a piecewise-linear ffmpeg `crop` x-expression.
- If face coverage is below 25%, the clip falls back to `fit` (sharp video over a blurred fill).

Planned improvements:
- Active-speaker selection using diarization and mouth motion (CLP-161).
- Hard cuts on scene changes instead of glides (CLP-162).
- Split-screen for two-speaker clips (CLP-320).

### 5.6 Render: `pipeline/render.py`, `pipeline/captions.py`

The renderer is one ffmpeg pass ([ADR-0001](adr/0001-ffmpeg-libass-renderer.md)):

```
-ss/-to ─▶ crop(x(t)) | fit+blur ─▶ scale 1080×1920 lanczos ─▶ zoompan punch-ins🔨 ─▶ fps 30
        ─▶ ass (captions + hook) ─▶ overlay emoji PNGs🔨 ─▶ progress bar🔨
audio   ─▶ loudnorm I=-14 TP=-1.5 ─▶ sfx mix🔨 ─▶ AAC 48 kHz
out     ─▶ H.264 High 4.2, CRF 20, yuv420p, +faststart · JPG thumbnail
```

Speech captions ✅:
- Text comes from the word-level transcript.
- Chunks of 1–3 words, in uppercase Montserrat with a heavy outline.
- The active word turns dark yellow and gets a slight scale-pop.
- Placement sits inside the YouTube Shorts safe zone, clear of the bottom UI and right-rail buttons.

Caption templates (CLP-170) make style data-driven: font, colors, position, animation and
emoji, chosen per job.

### 5.7 Publish 🗺️

- The publishing package is shown in the UI with copy buttons (✅ for title and hashtags).
- One-click upload through the YouTube Data API v3 (OAuth, `videos.insert`, `#Shorts`) is planned (CLP-400).

## 6. Data model

```
Job(id, status, stage, progress, message, request: JobCreate, source: SourceVideo?,
    clips: Clip[], error?, created_at, updated_at)                                 ✅ Redis JSON
Clip(id, rank, start, end, duration, title, hook, reason, virality_score,
     hashtags[], video_url, thumbnail_url, edl🔨, package🔨)                         ✅ / 🔨
```

Postgres schema 🔨 (CLP-101):
- `users`
- `jobs` (request, status, source metadata, cost)
- `clips` (EDL JSONB, package JSONB, storage keys, scores)
- `renders` (version history per clip)

Redis keeps the live Job snapshot and the queue only.

## 7. Cross-cutting concerns

| Concern | Approach |
|---|---|
| **Security** | YouTube-only URL regex (blocks SSRF and `file://`). `noplaylist` and duration cap. ASS text sanitized (`captions._clean`). Non-root containers. Secrets via env or secret manager. `cookies.txt` mounted read-only. Security headers on web. |
| **Abuse and cost** | Per-IP hourly limit ✅. Turnstile 🔨. Per-user quotas 🔨. Claude token usage logged per job ✅ and persisted 🔨. |
| **Observability** | structlog JSON with `job_id` bound ✅. OpenTelemetry span per stage 🔨. Sentry 🔨. Job-duration and failure-rate dashboards 🔨. |
| **Reliability** | arq `max_tries=1` (expensive, non-idempotent). User-safe error mapping. Work dir always cleaned. SSE resync. |
| **Performance targets** | 60-min source on GPU worker: ≤ 4 min to first clip, ≤ 8 min total. CPU (`small`): ≤ 15 min. |
| **Legal** | User attests rights 🔨. Takedown process 🔨. Media TTL deletion 🔨. |

## 8. Tech stack (Oct 2026)

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js 16 (App Router, RSC, Turbopack), React 19, Tailwind v4, lucide | Current stable. Server components keep the client bundle small. |
| UI kit 🔨 | shadcn/ui (Radix) on our tokens | Accessible primitives for the clip editor |
| Data fetching 🔨 | TanStack Query + SSE | Cache and retry for the editor |
| API | FastAPI + Pydantic v2 | Typed, async, OpenAPI for free |
| Queue | Redis 7 + arq | Async-native, minimal ops ([ADR-0004](adr/0004-redis-arq-queue.md)) |
| ASR | faster-whisper `large-v3-turbo` (CTranslate2) | Best speed/accuracy for word timestamps |
| LLM | Claude Opus 5.5 (`claude-opus-5-5`), Anthropic SDK 1.x | Strongest editorial judgment. Structured outputs. Vision. |
| Vision | OpenCV YuNet (faces), PySceneDetect 🔨 | Fast on CPU, permissive licenses |
| Video | ffmpeg + libass | Ubiquitous, one-pass, GPU encode possible (NVENC 🗺️) |
| Download | yt-dlp + yt-dlp-ejs + Deno | Only maintained option that keeps up with YouTube |
| DB 🔨 | Postgres 17, SQLAlchemy 2 (async), Alembic | Durable, JSONB for the EDL |
| Storage 🔨 | Cloudflare R2 (S3 API) | No egress fees for video |
| Auth 🔨 | Clerk or Better Auth | Hosted vs self-hosted; decide in ADR-0005 |
| Ops | Docker Compose → containers on Fly/Cloud Run + GPU workers (Modal/RunPod) | Same image everywhere |
| CI | GitHub Actions: ruff, pytest, tsc, next build, docker build | Already in `.github/workflows/ci.yml` |

## 9. Repository layout

```
apps/api/app/
  main.py            FastAPI app factory, lifespan, CORS, /media
  config.py          Settings (env vars)
  schemas.py         API contracts (Pydantic)
  edl.py 🔨          EditDecisionList contract
  store.py           Redis Job store + pub/sub
  worker.py          arq entrypoint
  routes/            health, jobs (clips 🔨)
  pipeline/
    orchestrator.py  the only stateful stage runner
    download.py      ingest
    transcribe.py    ASR
    signals.py       pass-1 candidate mining
    scoring.py       pass-2 Claude ranking
    package.py 🔨    Claude viral packaging
    direct.py 🔨     EDL builder
    reframe.py       9:16 crop path
    captions.py      ASS captions + hook
    render.py        ffmpeg
apps/web/src/
  app/               routes: /, /jobs/[id], /clips/[id]/edit 🔨
  components/        UI
  lib/               api client, types, hooks
docs/                architecture, specs, ADRs, playbook, API, deployment
.claude/skills/      task playbooks for Claude Code
```
