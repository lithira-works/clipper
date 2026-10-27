from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from arq import create_pool
from arq.connections import RedisSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from redis.asyncio import Redis

from . import __version__
from .config import get_settings
from .log_config import configure_logging
from .routes import health, jobs
from .store import JobStore

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    app.state.store = JobStore(redis)
    app.state.queue = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    log.info("api.started", version=__version__, env=settings.env)
    yield
    await app.state.queue.aclose()
    await redis.aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Clipper API",
        version=__version__,
        description="Turn long YouTube videos into viral, captioned 9:16 Shorts.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(jobs.router, prefix="/v1")
    app.mount("/media", StaticFiles(directory=settings.media_root), name="media")
    return app


app = create_app()
