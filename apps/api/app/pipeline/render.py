"""ffmpeg helpers: audio extraction and final 1080x1920 Shorts render."""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..config import get_settings
from .reframe import CropPlan


class RenderError(RuntimeError):
    pass


def _run(args: list[str]) -> None:
    proc = subprocess.run(args, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RenderError(proc.stderr[-2000:])


def extract_audio(video: Path, out: Path) -> Path:
    """16 kHz mono PCM WAV: what Whisper wants and cheap to analyse for loudness."""
    _run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000",
          "-c:a", "pcm_s16le", str(out)])
    return out


def _ass_path(p: Path) -> str:
    # ffmpeg filter args need ':' and '\' escaped (matters for Windows drive letters).
    return str(p).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def _video_filter(plan: CropPlan, ass: Path | None) -> str:
    s = get_settings()
    W, H = s.output_width, s.output_height
    if plan.mode == "track":
        chain = f"crop={plan.crop_w}:{plan.src_h}:'{plan.x_expr}':0,scale={W}:{H}:flags=lanczos"
    elif plan.mode == "native":
        chain = (f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos,"
                 f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black")
    else:  # fit: sharp 16:9 video centred over a blurred, zoomed copy of itself
        chain = (
            f"split=2[bg][fg];"
            f"[bg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
            f"gblur=sigma=40,eq=brightness=-0.08[bgb];"
            f"[fg]scale={W}:-2:flags=lanczos[fgs];"
            f"[bgb][fgs]overlay=(W-w)/2:(H-h)/2"
        )
    chain += f",fps={s.output_fps},format=yuv420p"
    if ass is not None:
        chain += f",ass='{_ass_path(ass)}'"
    return chain


def render_clip(
    src: Path, start: float, end: float, plan: CropPlan, ass: Path | None, out: Path
) -> Path:
    s = get_settings()
    _run([
        "ffmpeg", "-y", "-v", "error",
        "-ss", f"{start:.3f}", "-to", f"{end:.3f}", "-i", str(src),
        "-filter_complex", f"[0:v]{_video_filter(plan, ass)}[v]",
        "-map", "[v]", "-map", "0:a?",
        "-c:v", "libx264", "-preset", s.x264_preset, "-crf", str(s.x264_crf),
        "-profile:v", "high", "-level", "4.2",
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",  # YouTube's loudness target
        "-movflags", "+faststart",
        str(out),
    ])
    return out


def thumbnail(video: Path, out: Path, at: float = 1.0) -> Path:
    _run(["ffmpeg", "-y", "-v", "error", "-ss", f"{at:.2f}", "-i", str(video),
          "-frames:v", "1", "-q:v", "3", str(out)])
    return out
