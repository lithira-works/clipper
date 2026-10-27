# ADR-0004: Redis + arq for queue and live job state

- **Status:** Accepted
- **Date:** 2026-10-08
- **Tickets:** —

## Context
Jobs run for minutes on heavy workers. The UI needs live progress, and the API must stay thin.

## Options
1. **Celery + Redis/RabbitMQ.** Mature, but sync-first, heavier configuration, and a second broker if RabbitMQ.
2. **arq + Redis.** asyncio-native, tiny API, and the same Redis serves state and pub/sub.
3. **Temporal.** Durable workflows and retries per step, but a big operational footprint for v0.x.

## Decision
Use arq on Redis. Job state is one JSON document per job, and progress is the full snapshot published on change.

## Consequences
- One dependency covers queue, state, pub/sub and rate limiting.
- arq is in maintenance mode. The orchestrator is queue-agnostic (`run_job(store, job_id)`), so
  moving to Temporal later is mechanical. Revisit when per-stage retries or multi-hour workflows are
  needed (for example, batch channel imports).
- Redis is not the system of record. Durable data moves to Postgres (CLP-101).
