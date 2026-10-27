---
name: add-api-endpoint
description: Add or change a Clipper HTTP endpoint end to end - Pydantic schema, FastAPI route, TypeScript type mirror, web API client, docs and tests. Use whenever apps/api/app/routes/ or apps/api/app/schemas.py changes.
---

# Add an API endpoint

Each step below has a reason. Skipping one causes drift between the API and the web app.

1. **Schema**: add request and response models in `apps/api/app/schemas.py`. Validate at the boundary
   with `Field(ge=, le=)`, `field_validator` and `model_validator`. Never trust client input downstream.
2. **Route**: add it to `apps/api/app/routes/jobs.py` (or a new router registered in
   `main.create_app` under `prefix="/v1"`). Follow these rules:
   - Set `response_model` and an explicit `status_code`.
   - Return 404 or 429 through `HTTPException`.
   - Keep it thin. Heavy work is enqueued with `request.app.state.queue.enqueue_job(...)`, never run inline.
   - Mutations that create work call `store.hit_rate_limit(ip)`.
3. **Worker** (only if the endpoint creates work): add an `async def` to `app/worker.py` and list it
   in `WorkerSettings.functions`.
4. **TypeScript mirror**: update `apps/web/src/lib/types.ts` to match field names exactly (snake_case).
5. **Client**: add a typed method to `api` in `apps/web/src/lib/api.ts`. Paths go through `/api/v1`.
6. **Docs**: add the endpoint to `docs/API.md` with a request example, a response example and error codes.
7. **Tests**: add schema validation tests in `apps/api/tests/`. For routes, use
   `fastapi.testclient.TestClient` with a fake store when needed.
8. **Changelog**: add a line under `[Unreleased]` in `CHANGELOG.md`.

## Verify

```bash
cd apps/api && uv run ruff check app tests && uv run pytest -q
cd apps/web && npm run typecheck
```
