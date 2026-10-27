"""Job state in Redis. One JSON document per job plus a pub/sub channel for live progress."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from redis.asyncio import Redis
from redis.asyncio.client import PubSub

from .config import get_settings
from .schemas import Job, JobCreate, JobStatus, Stage

_KEY = "clipper:job:{}"
_CHANNEL = "clipper:job:{}:events"


def _now() -> datetime:
    return datetime.now(UTC)


class JobStore:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis
        self.ttl = get_settings().job_ttl_seconds

    async def create(self, job_id: str, request: JobCreate) -> Job:
        job = Job(
            id=job_id,
            status=JobStatus.queued,
            stage=Stage.queued,
            progress=0.0,
            message="Waiting for a worker",
            request=request,
            created_at=_now(),
            updated_at=_now(),
        )
        await self._save(job)
        return job

    async def get(self, job_id: str) -> Job | None:
        raw = await self.redis.get(_KEY.format(job_id))
        return Job.model_validate_json(raw) if raw else None

    async def update(self, job_id: str, **fields: Any) -> Job:
        job = await self.get(job_id)
        if job is None:
            raise KeyError(job_id)
        job = job.model_copy(update={**fields, "updated_at": _now()})
        await self._save(job)
        await self.redis.publish(_CHANNEL.format(job_id), job.model_dump_json())
        return job

    async def next_update(self, pubsub: PubSub, wait_s: float) -> str | None:
        """Wait up to `wait_s` seconds for the next published snapshot."""
        msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=wait_s)
        if msg is None:
            return None
        data = msg["data"]
        return data if isinstance(data, str) else data.decode()

    async def open_channel(self, job_id: str) -> PubSub:
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(_CHANNEL.format(job_id))
        return pubsub

    async def _save(self, job: Job) -> None:
        await self.redis.set(_KEY.format(job.id), job.model_dump_json(), ex=self.ttl)

    async def hit_rate_limit(self, client_ip: str) -> bool:
        """Fixed-window limiter: N job submissions per IP per hour."""
        key = f"clipper:rl:{client_ip}:{int(_now().timestamp() // 3600)}"
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, 3600)
        return count > get_settings().rate_limit_per_hour
