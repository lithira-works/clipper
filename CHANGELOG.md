# Changelog

All notable changes to this project are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versioning: [SemVer](https://semver.org/).

## [Unreleased]

### Added
- Architecture v2: EDL-centred design, packaging stage, status markers and ticket links.
- ADRs 0001–0004, EDL spec v1, viral playbook.
- Phased TODO with `CLP-xxx` tickets and acceptance criteria.
- Claude Code skills: `viral-packaging`, `eval-moments`, `debug-job`. Updated `clip-pipeline` and `release-check`.
- `YTDLP_COOKIES_FILE` support for YouTube's bot check. Cookies are a fallback only: downloads try
  anonymously first, and cookies are used from a temp copy, so the read-only mount is never written.

### Changed
- Results page redesign: source header card with status pill and settings chips, progress panel with
  elapsed timer and connected stepper, fixed clip grid with skeleton cards (no layout jumps), compact
  clip cards (2-line titles, ink Download button), clearer error state.
- Page shell: shared `.container-page` width and gutters, sticky footer, `New Shorts` header action.
- Home page: job options are always visible. Captions on/off switch (Bold karaoke or Minimal when on),
  Short length (Short 15–30s, Medium 30–45s, Long 45–60s), and a 1–12 Shorts stepper.
- Videos with little or no speech (music, performances) are clipped by replay heat and loudness
  instead of failing.

### Fixed
- Transcription crash `open() got an unexpected keyword argument 'metadata_errors'` (faster-whisper
  1.2.1 vs PyAV 19): the WAV is now passed to Whisper as samples, bypassing PyAV.
- yt-dlp progress bars no longer flood worker logs.
- Docker: Montserrat fetched upstream (not packaged in bookworm), Whisper cache dir ownership,
  worker healthcheck disabled.
- Raw OS errors are no longer shown to users.

## [0.1.0] - 2026-10-08

### Added
- Initial monorepo: FastAPI API and arq worker (`apps/api`), Next.js 16 web app (`apps/web`).
- End-to-end pipeline: yt-dlp download with heatmap, faster-whisper transcription, signal
  shortlist, Claude Opus 5.5 ranking, YuNet speaker-tracked 9:16 reframe, ASS karaoke captions,
  ffmpeg render.
- Live job progress over Server-Sent Events.
- Docker Compose stack, GitHub Actions CI, and project documentation and Claude Code skills.
