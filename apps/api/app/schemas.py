from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator

YOUTUBE_URL_RE = re.compile(
    r"^https?://(www\.|m\.|music\.)?(youtube\.com/(watch\?v=|shorts/|live/|embed/)|youtu\.be/)"
    r"[A-Za-z0-9_-]{11}"
)


class JobStatus(StrEnum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"


class Stage(StrEnum):
    queued = "queued"
    downloading = "downloading"
    transcribing = "transcribing"
    analyzing = "analyzing"
    reframing = "reframing"
    rendering = "rendering"
    done = "done"


class CaptionStyle(StrEnum):
    bold = "bold"  # big word-by-word karaoke, dark-yellow active word
    minimal = "minimal"  # smaller, white, no highlight
    none = "none"


class JobCreate(BaseModel):
    url: str = Field(description="Public YouTube video URL")
    max_clips: int = Field(default=5, ge=1, le=12)
    min_duration: int = Field(default=20, ge=10, le=60, description="Seconds")
    max_duration: int = Field(default=55, ge=15, le=180, description="Seconds")
    caption_style: CaptionStyle = CaptionStyle.bold
    language: str | None = Field(default=None, description="ISO-639-1; auto-detect if null")

    @field_validator("url")
    @classmethod
    def _youtube_only(cls, v: str) -> str:
        v = v.strip()
        if not YOUTUBE_URL_RE.match(v):
            raise ValueError("Only youtube.com / youtu.be video URLs are supported")
        return v

    @model_validator(mode="after")
    def _durations(self) -> JobCreate:
        if self.min_duration >= self.max_duration:
            raise ValueError("min_duration must be less than max_duration")
        return self


class Clip(BaseModel):
    id: str
    rank: int
    start: float
    end: float
    duration: float
    title: str
    hook: str
    reason: str
    virality_score: int = Field(ge=0, le=100)
    hashtags: list[str] = []
    video_url: str
    thumbnail_url: str


class SourceVideo(BaseModel):
    id: str
    title: str
    channel: str | None = None
    duration: float
    thumbnail: str | None = None
    has_heatmap: bool = False


class Job(BaseModel):
    id: str
    status: JobStatus
    stage: Stage
    progress: float = Field(ge=0, le=1)
    message: str = ""
    request: JobCreate
    source: SourceVideo | None = None
    clips: list[Clip] = []
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class JobAccepted(BaseModel):
    id: str
    status: JobStatus
