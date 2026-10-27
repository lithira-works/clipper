# syntax=docker/dockerfile:1.7
# One image, two roles: API (uvicorn) and worker (arq). Role is chosen by the compose command.
FROM python:3.12-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg fontconfig curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Caption font (SIL OFL). Not packaged in Debian bookworm, so fetch from the upstream repo.
RUN mkdir -p /usr/local/share/fonts/montserrat \
    && for w in Bold ExtraBold Black; do \
         curl -fsSL -o /usr/local/share/fonts/montserrat/Montserrat-$w.ttf \
           https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-$w.ttf; \
       done \
    && fc-cache -f

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /usr/local/bin/uv
# yt-dlp needs a JS runtime to solve YouTube player challenges.
COPY --from=denoland/deno:bin /deno /usr/local/bin/deno

WORKDIR /srv
COPY pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --no-dev --no-install-project

# Face detector for speaker tracking (OpenCV Zoo, Apache-2.0)
RUN mkdir -p models && curl -fsSL -o models/face_detection_yunet_2023mar.onnx \
    https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx

COPY app ./app

# Pre-create the Whisper cache dir so the mounted volume inherits non-root ownership.
RUN useradd --create-home --uid 10001 clipper \
    && mkdir -p data /home/clipper/.cache/huggingface \
    && chown -R clipper /srv /home/clipper/.cache
USER clipper

ENV PATH="/srv/.venv/bin:$PATH" \
    MEDIA_ROOT=/srv/data/media \
    WORK_ROOT=/srv/data/work \
    FACE_MODEL_PATH=/srv/models/face_detection_yunet_2023mar.onnx

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD curl -fs http://localhost:8000/healthz || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
