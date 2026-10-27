"""Speaker-tracking 16:9 -> 9:16 reframe.

Samples frames, finds the dominant face with OpenCV's YuNet detector, smooths its x position,
and emits a piecewise-linear ffmpeg `crop` x-expression so the window glides with the speaker.
If no face is found consistently, the renderer falls back to a "fit + blurred background" layout.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
import structlog

from ..config import get_settings

log = structlog.get_logger()

SAMPLE_FPS = 2.0
MIN_FACE_COVERAGE = 0.25  # share of samples that must contain a face to use tracking
DEADZONE = 0.06  # ignore moves smaller than 6% of frame width (prevents jitter)


@dataclass(slots=True)
class CropPlan:
    mode: str  # "track" | "fit" | "native"
    src_w: int
    src_h: int
    crop_w: int = 0
    x_expr: str = "0"


@lru_cache(maxsize=1)
def _detector_model() -> str | None:
    p: Path = get_settings().face_model_path
    return str(p) if p.exists() else None


def plan(video: Path, start: float, end: float) -> CropPlan:
    cap = cv2.VideoCapture(str(video))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if w / max(h, 1) <= 9 / 16 + 0.01:
        cap.release()
        return CropPlan(mode="native", src_w=w, src_h=h)

    crop_w = int(round(h * 9 / 16)) // 2 * 2
    model = _detector_model()
    if model is None:
        log.warning("reframe.no_face_model", path=str(get_settings().face_model_path))
        cap.release()
        return CropPlan(mode="fit", src_w=w, src_h=h)

    # Detect on a downscaled frame for speed.
    scale = 640 / w
    det_w, det_h = 640, int(round(h * scale))
    detector = cv2.FaceDetectorYN.create(model, "", (det_w, det_h), 0.7, 0.3, 50)

    times: list[float] = []
    centers: list[float | None] = []
    t = start
    while t < end:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            break
        small = cv2.resize(frame, (det_w, det_h))
        _, faces = detector.detect(small)
        if faces is not None and len(faces):
            # Largest face = most likely the active speaker.
            fx, _, fw, _ = max(faces, key=lambda f: f[2] * f[3])[:4]
            centers.append(float(fx + fw / 2) / scale)
        else:
            centers.append(None)
        times.append(t - start)
        t += 1 / SAMPLE_FPS
    cap.release()

    found = [c for c in centers if c is not None]
    if not times or len(found) / len(times) < MIN_FACE_COVERAGE:
        return CropPlan(mode="fit", src_w=w, src_h=h)

    xs = _smooth(_fill_gaps(centers), w)
    lefts = np.clip(xs - crop_w / 2, 0, w - crop_w)
    return CropPlan(
        mode="track", src_w=w, src_h=h, crop_w=crop_w, x_expr=_lerp_expr(times, lefts.tolist())
    )


def _fill_gaps(centers: list[float | None]) -> np.ndarray:
    """Hold the last seen face position across gaps (back-fill the leading gap)."""
    first = next(c for c in centers if c is not None)
    out, last = [], first
    for c in centers:
        last = c if c is not None else last
        out.append(last)
    return np.asarray(out, dtype=np.float64)


def _smooth(xs: np.ndarray, frame_w: int) -> np.ndarray:
    # Median filter kills single-frame detector glitches; dead-zone + EMA gives calm camera moves.
    k = 5
    padded = np.pad(xs, (k // 2, k // 2), mode="edge")
    med = np.array([np.median(padded[i : i + k]) for i in range(len(xs))])
    out = np.empty_like(med)
    cur = med[0]
    for i, x in enumerate(med):
        if abs(x - cur) > DEADZONE * frame_w:
            cur = 0.6 * cur + 0.4 * x
        out[i] = cur
    return out


def _lerp_expr(times: list[float], lefts: list[float]) -> str:
    """Nested ffmpeg if() chain interpolating between keyframes. Drops redundant points."""
    pts = [(times[0], lefts[0])]
    for t, x in zip(times[1:], lefts[1:], strict=True):
        if abs(x - pts[-1][1]) >= 2:
            pts.append((t, x))
    if len(pts) == 1:
        return str(int(pts[0][1]))
    expr = f"{pts[-1][1]:.1f}"
    for (t0, x0), (t1, x1) in reversed(list(zip(pts[:-1], pts[1:], strict=True))):
        seg = f"{x0:.1f}+({x1 - x0:.1f})*(t-{t0:.2f})/{max(t1 - t0, 0.01):.2f}"
        expr = f"if(lt(t\\,{t1:.2f})\\,{seg}\\,{expr})"
    return f"if(lt(t\\,{pts[0][0]:.2f})\\,{pts[0][1]:.1f}\\,{expr})"
