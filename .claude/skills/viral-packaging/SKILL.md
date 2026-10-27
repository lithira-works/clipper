---
name: viral-packaging
description: Build or tune what makes a Clipper Short go viral - the hook text, titles, description/hashtags/pinned comment, caption emphasis (color, emoji, punch-in zoom), caption templates, and the EDL builder (direct.py). Use for package.py, direct.py, templates.py, edl.py, the packaging prompt, or "make the shorts look better / more engaging".
---

# Viral packaging

Packaging turns a good moment into a Short people stop scrolling for. It produces two things:
- the **publishing package**: titles, description, hashtags, pinned comment, thumbnail time
- the **visual treatment**: hook banner, emphasis words, zooms, emoji, template

Both flow into the **EDL** ([docs/specs/edl.md](../../../docs/specs/edl.md)), which is the only input to
the renderer.

Read first:
1. `docs/VIRAL_PLAYBOOK.md`. It is the source of truth for every editorial rule.
2. `docs/specs/edl.md`. Field names and renderer mapping.
3. `docs/adr/0002-edit-decision-list.md`. Why the AI writes data and does not call ffmpeg.

## Where things live

| Concern | Module (🔨 = create it if it doesn't exist yet; ticket in TODO.md) |
|---|---|
| EDL contract (Pydantic, `version: 1`) | `apps/api/app/edl.py` 🔨 CLP-160 |
| TypeScript mirror | `apps/web/src/lib/edl.ts` 🔨 |
| Claude packaging call | `apps/api/app/pipeline/package.py` 🔨 CLP-150 |
| EDL assembly (cut + crop + captions + package) | `apps/api/app/pipeline/direct.py` 🔨 CLP-160 |
| Caption templates | `apps/api/app/pipeline/templates.py` 🔨 CLP-170 |
| ASS generation | `apps/api/app/pipeline/captions.py` ✅ |
| ffmpeg graph | `apps/api/app/pipeline/render.py` ✅ |

## The packaging call

The packaging call is one call per finalist clip. Run calls concurrently with a small semaphore (3) to respect rate limits.

```python
response = client.beta.messages.create(
    model=settings.claude_model,               # claude-opus-5-5
    max_tokens=16000,
    betas=["server-side-fallback-2026-07-01"],
    fallbacks="default",
    thinking={"type": "adaptive"},
    output_config={"effort": "medium", "format": {"type": "json_schema", "schema": PACKAGE_SCHEMA}},
    system=[{"type": "text", "text": PACKAGING_SYSTEM, "cache_control": {"type": "ephemeral"}}],
    messages=[{"role": "user", "content": clip_prompt}],  # transcript with word indices, video context
)
if response.stop_reason == "refusal": ...      # heuristic package
package = Package.model_validate_json(text)    # then enforce limits in code
```

- Give Claude the transcript as **indexed words** (`[12]changed`). Emphasis then refers to indices, not
  timestamps, and the server maps indices back to times. This avoids hallucinated timings.
- `effort: "medium"` is usually enough for packaging. Raise it only if the eval shows a gain.
- Without `cache_control` on the system prompt, every clip re-bills the playbook.

## Enforce in code, not only in the prompt

After validation, clamp everything. Models drift and the renderer must never break:

| Field | Server-side rule |
|---|---|
| `hook_text` | ≤ 8 words, `_clean`. Must not equal the first 8 spoken words. Fall back to the ranking hook. |
| `titles` | 1–3 items, each ≤ 60 chars, emoji and `#` stripped |
| `hashtags` | 3–5, lowercase, no `#`, `shorts` added if missing |
| `emphasis` | Indices in range, at most 1 per 3 s, none in the first 0.5 s (the hook owns it) |
| `zooms` | Scale 1.05–1.15, duration 0.4–0.8 s, never crossing `frame.cuts` |
| `thumbnail_t` | Inside the clip. Snap to a sampled frame where a face was detected. |

## Heuristic fallback (no key or failure)

- Hook: the ranking hook, or the first 6 words of the strongest sentence.
- Emphasis: numbers, ALL-CAPS words, and words followed by `!`.
- Titles: the ranking title. Hashtags: `["shorts"] +` the top 2 nouns from the transcript.

## Verify

1. Unit tests in `apps/api/tests/test_package.py` and `test_direct.py`:
   - The clamps work.
   - Index-to-time mapping is correct.
   - The EDL round-trips through JSON.
2. Golden render test (CLP-004) for any visual change.
3. `make check`.
4. Run a real job and watch the result on a phone. Check:
   - The hook is readable in < 1 s.
   - Emphasis lands on the right word.
   - Nothing covers the face or the Shorts UI.
5. For prompt changes, run the `eval-moments` skill and compare before and after.
