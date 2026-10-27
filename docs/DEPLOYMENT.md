# Deployment

## Single VM (fastest path)

On a Linux VM with Docker (8 vCPU, 16 GB RAM, and an optional NVIDIA GPU):

```bash
git clone <repo> clipper && cd clipper
cp .env.example .env && $EDITOR .env      # set ANTHROPIC_API_KEY, ENV=production
docker compose up -d --build
```

Put Caddy or Nginx in front of `web:3000` for TLS. Only `web` needs to be public. The browser
reaches the API through the Next.js rewrites. If you go this way, remove the `ports` mapping
for `api` in production.

## Sizing

| Resource | Guidance |
|---|---|
| Worker CPU | Whisper `large-v3-turbo` on CPU runs at about 0.3–0.6× real time with int8. Use `small` for speed. |
| Worker GPU | A T4 or L4 transcribes about 30–60× faster. This is recommended for any real traffic. |
| Concurrency | `max_jobs = 2` per worker. Scale with `WORKER_REPLICAS`. |
| Disk | Allow about 3× the source video size per running job (source, WAV, outputs) |
| Redis | Small. Job JSON is a few KB. |

## GPU workers

1. Install `nvidia-container-toolkit` on the host.
2. Build the worker from a CUDA base image (`nvidia/cuda:12.x-cudnn-runtime-ubuntu24.04`) with
   Python 3.12, or install the cuDNN and cuBLAS wheels that CTranslate2 needs.
3. Uncomment the `deploy.resources` block in `docker-compose.yml`.
4. Set `WHISPER_DEVICE=cuda` and `WHISPER_COMPUTE_TYPE=float16`.

## Managed / scaled setup

| Piece | Option |
|---|---|
| Web | Vercel, or a container on Fly, Render or Cloud Run |
| API | Container (Cloud Run, ECS or Fly), 2 or more replicas |
| Workers | GPU instances (ECS on g6, GKE with L4, Modal or RunPod), autoscaled on arq queue depth |
| Redis | Upstash, ElastiCache or Memorystore |
| Media | S3 or R2 behind a CDN with signed URLs (TODO P0) |

## Environment variables

See `.env.example`. These matter most in production:
- `ANTHROPIC_API_KEY`: keep it in your platform's secret manager.
- `ENV=production` and `LOG_LEVEL=INFO`.
- `CORS_ORIGINS`: your web origin. It is needed only if `NEXT_PUBLIC_API_URL` points at the API directly.
- `RATE_LIMIT_PER_HOUR`, `MAX_VIDEO_SECONDS`: abuse and cost controls.

## Operations

- **Logs:** JSON on stdout from both the API and the worker. `job_id` is bound on every worker log line.
- **Health:** `/healthz` for liveness and `/readyz` for readiness (checks Redis).
- **YouTube bot check:** datacenter and busy home IPs get "Sign in to confirm you're not a
  bot". Export cookies from a logged-in browser session (a throwaway account is best) in
  Netscape format with a cookies.txt browser extension. Save the file to `secrets/cookies.txt`.
  Compose mounts it read-only into the worker. Cookies expire, so refresh them when the error
  returns. Treat the file as a credential; `secrets/` is gitignored.
  Downloads always try anonymously first and use cookies only after a bot-check error, because
  stale or rejected cookies make YouTube fail requests that work anonymously. Export from a
  **fresh incognito sign-in** and close the window right away; cookies from a normal browser
  window are rotated by YouTube and go stale. As of yt-dlp 2026.08/10, signed-in requests can
  fail ("The page needs to be reloaded" / "No video formats found") even with fresh cookies.
  If that happens, run without cookies until yt-dlp ships a fix.
- **yt-dlp drift:** YouTube changes often. Rebuild images weekly so yt-dlp stays current, and
  watch for `DownloadError` spikes.
- **Costs:** one job sends about 5–15k input tokens to Claude. Log `usage` (already logged as
  `scoring.claude_ok`) to track cost.
