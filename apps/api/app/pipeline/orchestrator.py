"""Runs one job end to end and reports progress to the JobStore.

Blocking CPU/GPU work runs in worker threads so the event loop keeps publishing progress.
"""

from __future__ import annotations

import asyncio
import shutil
from collections.abc import Awaitable, Callable

import structlog

from ..config import get_settings
from ..schemas import Clip, Job, JobStatus, SourceVideo, Stage
from ..store import JobStore
from . import captions, download, reframe, render, scoring, signals, transcribe

log = structlog.get_logger()

# Stage -> (progress at start, progress at end)
_BANDS: dict[Stage, tuple[float, float]] = {
    Stage.downloading: (0.02, 0.20),
    Stage.transcribing: (0.20, 0.45),
    Stage.analyzing: (0.45, 0.60),
    Stage.reframing: (0.60, 0.70),
    Stage.rendering: (0.70, 0.99),
}

Report = Callable[[Stage, float, str], Awaitable[Job]]


async def run_job(store: JobStore, job_id: str) -> None:
    settings = get_settings()
    job = await store.get(job_id)
    if job is None:
        log.error("job.missing", job_id=job_id)
        return
    req = job.request
    workdir = settings.work_root / job_id
    outdir = settings.media_root / job_id
    workdir.mkdir(parents=True, exist_ok=True)
    outdir.mkdir(parents=True, exist_ok=True)
    structlog.contextvars.bind_contextvars(job_id=job_id)

    async def report(stage: Stage, frac: float, message: str) -> Job:
        lo, hi = _BANDS.get(stage, (0.0, 1.0))
        return await store.update(
            job_id, status=JobStatus.running, stage=stage,
            progress=round(lo + (hi - lo) * frac, 3), message=message,
        )

    try:
        # 1. Download
        await report(Stage.downloading, 0, "Reading video details")
        info = await asyncio.to_thread(download.probe, req.url, workdir)
        await store.update(job_id, source=SourceVideo(
            id=info.video_id, title=info.title, channel=info.channel, duration=info.duration,
            thumbnail=info.thumbnail, has_heatmap=bool(info.heatmap),
        ))
        await report(Stage.downloading, 0.1, "Downloading video")
        info = await asyncio.to_thread(download.download, req.url, workdir, info)
        assert info.path is not None

        # 2. Transcribe
        await report(Stage.transcribing, 0, "Extracting audio")
        wav = await asyncio.to_thread(render.extract_audio, info.path, workdir / "audio.wav")
        await report(Stage.transcribing, 0.1, "Transcribing speech with Whisper")
        transcript = await asyncio.to_thread(transcribe.transcribe, wav, req.language)

        # 3. Find viral moments
        await report(Stage.analyzing, 0, "Scoring replay heatmap and audio peaks")
        energy = await asyncio.to_thread(signals.energy_per_second, wav)
        heat = signals.heat_per_second(info.heatmap, info.duration)
        cands = signals.candidates(
            transcript, heat, energy, req.min_duration, req.max_duration, limit=req.max_clips * 3
        )
        if not cands:
            # Music, performances, sparse speech: pick by replay heat and loudness instead.
            log.info("signals.audio_fallback", words=len(transcript.words))
            await report(Stage.analyzing, 0.2, "Little speech found, picking moments by sound")
            cands = signals.audio_candidates(
                heat, energy, info.duration, req.min_duration, req.max_duration,
                limit=req.max_clips * 3,
            )
        if not cands:
            raise RuntimeError(
                f"This video is shorter than the minimum clip length ({req.min_duration}s)."
            )
        await report(Stage.analyzing, 0.3, "Claude is picking the most viral moments")
        ranked = await asyncio.to_thread(
            scoring.rank, info, cands, req.max_clips, req.min_duration, req.max_duration
        )

        # 4 + 5. Reframe and render each clip
        clips: list[Clip] = []
        total = len(ranked)
        for i, r in enumerate(ranked):
            start, end = signals.snap_to_words(transcript.words, r.start, r.end)
            await report(Stage.reframing, i / total, f"Tracking speaker in clip {i + 1}/{total}")
            plan = await asyncio.to_thread(reframe.plan, info.path, start, end)

            await report(Stage.rendering, i / total, f"Rendering clip {i + 1}/{total}")
            ass_text = captions.build_ass(transcript.words, start, end, req.caption_style, r.hook)
            ass = captions.write_ass(workdir / f"clip_{i}.ass", ass_text)
            name = f"clip_{i + 1:02d}"
            mp4 = await asyncio.to_thread(
                render.render_clip, info.path, start, end, plan, ass, outdir / f"{name}.mp4"
            )
            await asyncio.to_thread(render.thumbnail, mp4, outdir / f"{name}.jpg")

            base = f"{settings.public_media_url}/{job_id}"
            clips.append(Clip(
                id=name, rank=i + 1, start=round(start, 2), end=round(end, 2),
                duration=round(end - start, 2), title=r.title, hook=r.hook, reason=r.reason,
                virality_score=r.virality_score, hashtags=r.hashtags,
                video_url=f"{base}/{name}.mp4", thumbnail_url=f"{base}/{name}.jpg",
            ))
            await store.update(job_id, clips=clips)

        clips.sort(key=lambda c: c.virality_score, reverse=True)
        clips = [c.model_copy(update={"rank": n + 1}) for n, c in enumerate(clips)]
        await store.update(
            job_id, status=JobStatus.succeeded, stage=Stage.done, progress=1.0,
            message=f"{len(clips)} Shorts ready", clips=clips,
        )
        log.info("job.succeeded", clips=len(clips))
    except Exception as e:  # noqa: BLE001 - every failure must reach the user
        log.exception("job.failed")
        await store.update(job_id, status=JobStatus.failed, error=_public_error(e),
                           message="Something went wrong")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
        structlog.contextvars.clear_contextvars()


def _public_error(e: Exception) -> str:
    if isinstance(e, download.DownloadError):
        msg = str(e)
        if "not a bot" in msg:
            return "YouTube is rate-limiting this server. Configure YTDLP_COOKIES_FILE (see docs/DEPLOYMENT.md)."
        if "Sign in" in msg or "private" in msg.lower():
            return "This video is private, age-restricted or region-locked."
        return msg.removeprefix("ERROR: ")[:300]
    if isinstance(e, render.RenderError):
        return "Video rendering failed. Please try another video."
    if type(e) is RuntimeError:  # raised by us with a user-facing message
        return str(e)[:300]
    return "Unexpected error while processing this video. Please try again."
