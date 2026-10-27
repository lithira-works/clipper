# API reference

The base URL is `http://localhost:8000` in development. The web app proxies it at `/api/v1/*`.
Interactive OpenAPI docs are at `/docs`, and the schema is at `/openapi.json`.

## `POST /v1/jobs`

Creates a clipping job.

```json
{
  "url": "https://www.youtube.com/watch?v=XXXXXXXXXXX",
  "max_clips": 5,
  "min_duration": 20,
  "max_duration": 55,
  "caption_style": "bold",
  "language": null
}
```

| Field | Type | Default | Rules |
|---|---|---|---|
| `url` | string | — | youtube.com/watch, /shorts, /live, /embed, or youtu.be |
| `max_clips` | int | 5 | 1–12 |
| `min_duration` | int (s) | 20 | 10–60, must be less than `max_duration` |
| `max_duration` | int (s) | 55 | 15–180. Keep ≤ 60 for classic Shorts. |
| `caption_style` | `bold` \| `minimal` \| `none` | `bold` | |
| `language` | ISO-639-1 \| null | null | null means auto-detect |

**202** response:

```json
{ "id": "3f2c…", "status": "queued" }
```

**422** is returned for a validation error. **429** is returned when the per-IP hourly limit (`RATE_LIMIT_PER_HOUR`) is reached.

## `GET /v1/jobs/{id}`

Returns the full `Job`, or **404** if the job does not exist.

```json
{
  "id": "3f2c…",
  "status": "running",
  "stage": "rendering",
  "progress": 0.82,
  "message": "Rendering clip 3/5",
  "request": { "...": "..." },
  "source": { "id": "XXXXXXXXXXX", "title": "…", "channel": "…", "duration": 3621.0,
              "thumbnail": "https://i.ytimg.com/…", "has_heatmap": true },
  "clips": [
    {
      "id": "clip_01", "rank": 1, "start": 812.4, "end": 851.9, "duration": 39.5,
      "title": "The one habit that doubled his revenue",
      "hook": "Nobody talks about this",
      "reason": "Clear setup and a surprising payoff in under 40 seconds.",
      "virality_score": 88,
      "hashtags": ["shorts", "business", "habits"],
      "video_url": "/media/3f2c…/clip_01.mp4",
      "thumbnail_url": "/media/3f2c…/clip_01.jpg"
    }
  ],
  "error": null,
  "created_at": "2026-10-08T12:00:00Z",
  "updated_at": "2026-10-08T12:03:10Z"
}
```

`status`: `queued` → `running` → `succeeded` | `failed`.
`stage`: `queued`, `downloading`, `transcribing`, `analyzing`, `reframing`, `rendering`, `done`.

## `GET /v1/jobs/{id}/events`

This endpoint is a Server-Sent Events stream. Each `job` event carries a full `Job` JSON snapshot. The
stream closes after a terminal status.

```
event: job
data: {"id":"3f2c…","status":"running","stage":"transcribing","progress":0.31,...}
```

```js
const es = new EventSource("/api/v1/jobs/" + id + "/events");
es.addEventListener("job", (e) => render(JSON.parse(e.data)));
```

## `GET /media/{job_id}/{file}`

Serves the rendered MP4s and JPG thumbnails as static files.

## `GET /healthz` · `GET /readyz`

`/healthz` is the liveness check. `/readyz` is the readiness check and also pings Redis.
