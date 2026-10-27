"""arq worker entrypoint:  arq app.worker.WorkerSettings"""

from __future__ import annotations

from typing import Any

from arq.connections import RedisSettings
from redis.asyncio import Redis

from .config import get_settings
from .log_config import configure_logging
from .pipeline.orchestrator import run_job
from .store import JobStore


async def startup(ctx: dict[str, Any]) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    ctx["store"] = JobStore(Redis.from_url(settings.redis_url, decode_responses=True))


async def shutdown(ctx: dict[str, Any]) -> None:
    await ctx["store"].redis.aclose()


async def process_job(ctx: dict[str, Any], job_id: str) -> None:
    await run_job(ctx["store"], job_id)


class WorkerSettings:
    functions = [process_job]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)
    max_jobs = 2  # video work is heavy; scale out with more worker replicas instead
    job_timeout = 60 * 60
    max_tries = 1
