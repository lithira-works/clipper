# Clipper

**Paste a YouTube link. Get viral, captioned 9:16 Shorts.**

Clipper downloads a long-form YouTube video, finds its most replayed and most shareable
moments, and renders each one as a ready-to-upload YouTube Short: 1080×1920, speaker-tracked,
with animated word-by-word captions and loudness-normalized audio.

```
YouTube URL ─▶ download ─▶ transcribe ─▶ score signals ─▶ Claude ranks ─▶ reframe 9:16 ─▶ captions ─▶ MP4 Shorts
              yt-dlp       Whisper       heatmap+audio     Opus 5.5        YuNet face     libass       ffmpeg
```

## Features

- **Most-replayed detection.** Uses YouTube's public "Most replayed" heatmap, the strongest
  signal of what viewers actually rewatch.
- **AI virality ranking.** Claude (`claude-opus-5-5`) judges hook, payoff, emotion and
  stand-alone clarity. It tightens each cut and writes the title, on-screen hook and hashtags.
- **Word-level transcript.** faster-whisper `large-v3-turbo` timestamps every word, so cuts
  never land mid-sentence.
- **Speaker tracking.** The OpenCV YuNet face detector plus smoothing makes a 9:16 crop that
  follows the speaker. Videos without a clear face use a blurred-fill layout.
- **Shorts-style captions.** 1–3 uppercase words on screen. The spoken word pops in dark yellow.
- **Platform-ready output.** H.264 High at 30 fps, AAC 48 kHz, −14 LUFS, `+faststart`.
- **Live progress.** Progress streams over Server-Sent Events, with a polling fallback.

## Stack

| Layer | Tech |
|---|---|
| Web | Next.js 16 (App Router, React 19), TypeScript, Tailwind CSS v4 |
| API | FastAPI, Pydantic v2, SSE (`sse-starlette`) |
| Queue / state | Redis 7 + arq workers |
| AI | Claude Opus 5.5 (Anthropic SDK 1.x, structured outputs), faster-whisper |
| Video | yt-dlp (+ Deno), ffmpeg/libass, OpenCV YuNet |
| Ops | Docker Compose, GitHub Actions CI, structlog JSON logs |

## Quick start (Docker)

```bash
cp .env.example .env          # add your ANTHROPIC_API_KEY
docker compose up --build
```

Open http://localhost:3000 and paste a YouTube link. The API docs are at
http://localhost:8000/docs.

The first job downloads the Whisper model (~1.6 GB), so it is slower than later jobs. On a CPU-only
machine, set `WHISPER_MODEL=small` for faster transcription.

## Local development

You need Python 3.12, [uv](https://docs.astral.sh/uv/), Node 24, ffmpeg, Deno and Redis.

```bash
make face-model               # one-time: download the face detector
redis-server &                # or: docker compose up -d redis
make dev-api                  # http://localhost:8000
make dev-worker               # in another terminal
make dev-web                  # http://localhost:3000
make check                    # lint + tests + typecheck + web build
```

## Repository layout

```
apps/
  api/                 FastAPI service + arq worker (one image, two commands)
    app/
      routes/          HTTP endpoints
      pipeline/        download, transcribe, signals, scoring, reframe, captions, render
      worker.py        arq entrypoint
    tests/
  web/                 Next.js 16 frontend
    src/app/           routes (landing, /jobs/[id])
    src/components/    UI components
    src/lib/           API client, types, hooks
docs/                  architecture, API, design system, scoring, deployment
.claude/skills/        Claude Code skills for working on this repo
TODO.md                prioritized backlog
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md): system, pipeline, and what is built vs planned
- [Viral playbook](docs/VIRAL_PLAYBOOK.md): the editorial rules behind hooks, captions and packaging
- [Viral scoring](docs/VIRAL_SCORING.md): how moments are found and evaluated
- [EDL spec](docs/specs/edl.md): the edit format between AI and renderer
- [Decision records](docs/adr/README.md)
- [API reference](docs/API.md) · [Design system](docs/DESIGN_SYSTEM.md) · [Deployment](docs/DEPLOYMENT.md)
- [Roadmap](docs/ROADMAP.md) and [TODO](TODO.md) (tickets `CLP-xxx` with acceptance criteria)

## Legal

Clip only videos that you own or have permission to reuse. Downloading content may be
restricted by YouTube's Terms of Service and by copyright law in your country. Operators must
add their own terms of use, takedown process and usage policy before offering Clipper publicly.
