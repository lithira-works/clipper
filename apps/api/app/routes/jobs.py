from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, status
from sse_starlette.sse import EventSourceResponse

from ..schemas import Job, JobAccepted, JobCreate, JobStatus
from ..store import JobStore

router = APIRouter(tags=["jobs"])

_TERMINAL = {JobStatus.succeeded, JobStatus.failed}


def _store(request: Request) -> JobStore:
    return request.app.state.store  # type: ignore[no-any-return]


@router.post("/jobs", status_code=status.HTTP_202_ACCEPTED, response_model=JobAccepted)
async def create_job(body: JobCreate, request: Request) -> JobAccepted:
    store = _store(request)
    ip = request.client.host if request.client else "unknown"
    if await store.hit_rate_limit(ip):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Hourly job limit reached")

    job_id = uuid4().hex
    await store.create(job_id, body)
    await request.app.state.queue.enqueue_job("process_job", job_id, _job_id=job_id)
    return JobAccepted(id=job_id, status=JobStatus.queued)


@router.get("/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str, request: Request) -> Job:
    job = await _store(request).get(job_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")
    return job


@router.get("/jobs/{job_id}/events")
async def job_events(job_id: str, request: Request) -> EventSourceResponse:
    """Server-Sent Events stream of full Job snapshots until the job finishes."""
    store = _store(request)
    job = await store.get(job_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")

    async def stream() -> AsyncIterator[dict[str, str]]:
        yield {"event": "job", "data": job.model_dump_json()}
        if job.status in _TERMINAL:
            return
        pubsub = await store.open_channel(job_id)
        try:
            while not await request.is_disconnected():
                data = await store.next_update(pubsub, wait_s=5)
                if data is None:
                    # Re-read the snapshot so a missed pub/sub message never stalls the client.
                    current = await store.get(job_id)
                    if current is None:
                        break
                    data = current.model_dump_json()
                yield {"event": "job", "data": data}
                if Job.model_validate_json(data).status in _TERMINAL:
                    break
        finally:
            await pubsub.unsubscribe()
            await pubsub.aclose()

    return EventSourceResponse(stream())
