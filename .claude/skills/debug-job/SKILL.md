---
name: debug-job
description: Diagnose a Clipper job that failed, hung, or produced bad Shorts - read the Job from Redis, find the stage, pull the worker logs, and map the error to a fix. Use when the user says a link "didn't work", "is stuck", "failed", or the clip looks wrong.
---

# Debug a job

Work from evidence. Don't guess and don't edit code until the cause is known.

## 1. Get the job state

```bash
# Job id is in the URL: /jobs/<id>
curl -s localhost:8000/v1/jobs/<id> | python -m json.tool
# or straight from Redis
docker compose exec redis redis-cli GET clipper:job:<id>
```

Note `status`, `stage`, `progress`, `message` and `error`. The `stage` names the failing module
(see the progress bands in `docs/ARCHITECTURE.md` §5).

## 2. Get the logs for that job

```bash
docker compose logs worker --since 2h | grep <id>
docker compose logs worker --since 2h | grep -E "job.failed|Traceback|scoring\.|ERROR" | tail -50
```

Worker logs are JSON with `job_id` bound. `job.failed` carries the full traceback, even though the user only
sees the safe message.

## 3. Map symptom to cause

| Stage / message | Likely cause | Fix |
|---|---|---|
| `downloading` · "rate-limiting this server" | YouTube bot check | User refreshes `secrets/cookies.txt`. **Never read or print that file.** |
| `downloading` · "private, age-restricted or region-locked" | Video access | Use a different video, or use cookies from an account that can view it |
| `downloading` · other `DownloadError` | yt-dlp outdated after a YouTube change | `uv lock --upgrade-package yt-dlp`, then rebuild the image |
| `transcribing` · `Permission denied ... huggingface` | Volume owned by root | The image creates the cache dir. Recreate the `whisper-cache` volume. |
| `transcribing` · very slow or OOM-killed | `large-v3-turbo` on CPU or low RAM | `WHISPER_MODEL=small`, or a GPU worker |
| "No speech detected" | Music or silent video | Expected. Show the message. |
| `analyzing` · generic titles "part 1" | Heuristic fallback ran | Check `scoring.no_api_key` / `scoring.claude_failed` / `scoring.refusal` in the logs |
| `rendering` · "Video rendering failed" | ffmpeg error | Find `RenderError` stderr in the logs. Usually a bad crop expression or `ass=` path escaping. |
| Stuck at the same progress for more than 10 min | Worker died or the job timed out | `docker compose ps`, `docker compose logs worker --tail 100`. arq `job_timeout` is 60 min. |
| UI stuck but the API shows `succeeded` | SSE dropped | The client falls back to polling. Check the browser console and the proxy buffering. |

## 4. Bad output (job succeeded, clip looks wrong)

| Symptom | Where |
|---|---|
| Starts or ends mid-sentence | `signals.sentences`, `snap_to_words` padding |
| Captions out of sync | Whisper model size, VAD params. Alignment comes with CLP-310. |
| Face cut off or jittery crop | `reframe.MIN_FACE_COVERAGE`, `DEADZONE`, `_smooth` |
| Captions over the face or YouTube UI | Template `MarginV` / safe-zone rules in the playbook |
| Boring pick | Run the `eval-moments` skill. Check `has_heatmap`. |

## 5. Reproduce and fix

- Re-submit the same URL (the job is not retried automatically, because `max_tries=1`).
- Fix the cause with the `clip-pipeline` skill, and add a regression test.
- Report to the user in plain words: what failed, why, what was changed, and any action they need to take.
