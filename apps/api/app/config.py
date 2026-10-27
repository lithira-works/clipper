from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Every field maps to an env var of the same name (upper case)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    env: str = "development"
    log_level: str = "INFO"

    # Infrastructure
    redis_url: str = "redis://localhost:6379/0"
    media_root: Path = Path("./data/media")
    work_root: Path = Path("./data/work")
    public_media_url: str = "/media"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # AI
    anthropic_api_key: str | None = None
    claude_model: str = "claude-opus-5-5"
    claude_effort: str = "high"
    whisper_model: str = "large-v3-turbo"
    whisper_device: str = "auto"  # auto | cpu | cuda
    whisper_compute_type: str = "auto"  # auto | int8 | float16

    # Limits
    max_video_seconds: int = 3 * 60 * 60
    max_download_height: int = 1080
    # Netscape-format cookies.txt for YouTube's "confirm you're not a bot" check (optional).
    ytdlp_cookies_file: Path | None = None
    job_ttl_seconds: int = 7 * 24 * 60 * 60
    rate_limit_per_hour: int = 20

    # Rendering
    output_width: int = 1080
    output_height: int = 1920
    output_fps: int = 30
    x264_preset: str = "veryfast"
    x264_crf: int = 20
    face_model_path: Path = Path("./models/face_detection_yunet_2023mar.onnx")
    caption_font: str = "Montserrat"


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    s.media_root.mkdir(parents=True, exist_ok=True)
    s.work_root.mkdir(parents=True, exist_ok=True)
    return s
