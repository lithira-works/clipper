"""Fetch the source video and YouTube's "Most replayed" heatmap with yt-dlp."""

from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yt_dlp

from ..config import get_settings


class DownloadError(RuntimeError):
    pass


@dataclass(slots=True)
class HeatPoint:
    start: float
    end: float
    value: float  # 0..1, YouTube's normalized replay intensity


@dataclass(slots=True)
class SourceInfo:
    video_id: str
    title: str
    channel: str | None
    duration: float
    thumbnail: str | None
    description: str
    chapters: list[dict[str, Any]] = field(default_factory=list)
    heatmap: list[HeatPoint] = field(default_factory=list)
    path: Path | None = None


def _base_opts(workdir: Path, use_cookies: bool = False) -> dict[str, Any]:
    settings = get_settings()
    height = settings.max_download_height
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,  # progress bars flood the JSON worker logs
        "noplaylist": True,
        "outtmpl": str(workdir / "source.%(ext)s"),
        "format": f"bv*[height<={height}][ext=mp4]+ba[ext=m4a]/b[height<={height}]/b",
        "merge_output_format": "mp4",
        "retries": 5,
        "fragment_retries": 5,
        "concurrent_fragment_downloads": 4,
    }
    if use_cookies:
        # yt-dlp rewrites its cookie file on exit; work on a copy so the read-only mount
        # (and the user's original) is never touched.
        workdir.mkdir(parents=True, exist_ok=True)
        copy = workdir / "cookies.txt"
        shutil.copyfile(_cookie_file(), copy)  # type: ignore[arg-type]
        opts["cookiefile"] = str(copy)
    return opts


def _cookie_file() -> Path | None:
    path = get_settings().ytdlp_cookies_file
    return path if path and path.exists() else None


def _with_cookie_fallback[T](workdir: Path, action: Callable[[yt_dlp.YoutubeDL], T]) -> T:
    """Try anonymously first; use cookies only when YouTube's bot check blocks us.

    Stale or rejected cookies make YouTube fail requests that work anonymously, so cookies
    must never be the first attempt.
    """
    try:
        with yt_dlp.YoutubeDL(_base_opts(workdir)) as ydl:
            return action(ydl)
    except yt_dlp.utils.DownloadError as e:
        if "not a bot" not in str(e) or _cookie_file() is None:
            raise DownloadError(str(e)) from e
    try:
        with yt_dlp.YoutubeDL(_base_opts(workdir, use_cookies=True)) as ydl:
            return action(ydl)
    except yt_dlp.utils.DownloadError as e:
        raise DownloadError(str(e)) from e


def probe(url: str, workdir: Path) -> SourceInfo:
    """Metadata only. Fails fast on private, live or too-long videos before downloading."""
    info = _with_cookie_fallback(workdir, lambda ydl: ydl.extract_info(url, download=False))
    if info is None:
        raise DownloadError("Video not found")
    if info.get("is_live"):
        raise DownloadError("Live streams are not supported; wait until the stream ends")
    duration = float(info.get("duration") or 0)
    if duration <= 0:
        raise DownloadError("Could not read video duration")
    if duration > get_settings().max_video_seconds:
        raise DownloadError("Video is longer than the allowed maximum")

    return SourceInfo(
        video_id=info["id"],
        title=info.get("title") or "Untitled",
        channel=info.get("channel") or info.get("uploader"),
        duration=duration,
        thumbnail=info.get("thumbnail"),
        description=(info.get("description") or "")[:4000],
        chapters=info.get("chapters") or [],
        heatmap=[
            HeatPoint(float(h["start_time"]), float(h["end_time"]), float(h["value"]))
            for h in (info.get("heatmap") or [])
        ],
    )


def download(url: str, workdir: Path, info: SourceInfo) -> SourceInfo:
    workdir.mkdir(parents=True, exist_ok=True)
    _with_cookie_fallback(workdir, lambda ydl: ydl.download([url]))
    files = sorted(workdir.glob("source.*"))
    video = next((f for f in files if f.suffix == ".mp4"), files[0] if files else None)
    if video is None:
        raise DownloadError("Download finished but no file was written")
    info.path = video
    return info
