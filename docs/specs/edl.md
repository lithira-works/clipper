# Spec: Edit Decision List (EDL) v1

**Status:** Proposed. Implemented by CLP-160. Decision: [ADR-0002](../adr/0002-edit-decision-list.md).

An EDL is the complete, declarative description of one Short. AI stages and human edits
produce it, and the renderer consumes it. The renderer must produce byte-identical output for
an identical EDL and source file, which means no randomness and no network calls.

## Rules

1. **Times are seconds relative to the clip start**, except `source.start` / `source.end`, which are
   absolute positions in the source video.
2. **Every field has a default**, so a minimal EDL is just `source` plus `captions.words`.
3. **Versioned.** `version` is bumped on breaking change. The renderer rejects unknown major versions.
4. **Validated** by Pydantic (`apps/api/app/edl.py`). The TypeScript mirror is in `apps/web/src/lib/edl.ts`.
5. **Sanitized.** All text passes through `captions._clean` before reaching ASS.

## Schema

```jsonc
{
  "version": 1,
  "source": { "video_id": "dQw4w9WgXcQ", "start": 812.40, "end": 851.90 },
  "output": { "width": 1080, "height": 1920, "fps": 30 },

  "frame": {
    "mode": "track",                      // track | fit | native | split
    "keyframes": [                        // crop window left edge in source px (track mode)
      { "t": 0.0, "x": 640 }, { "t": 6.5, "x": 702 }
    ],
    "cuts": [12.3, 27.8],                 // hard re-centre points (scene changes)
    "zooms": [                            // punch-ins on emphasis words
      { "t": 4.20, "dur": 0.6, "scale": 1.12, "ease": "out" }
    ]
  },

  "captions": {
    "template": "bold-gold",              // see Templates
    "position": "lower-third",            // lower-third | center | upper-third
    "max_words": 3,
    "uppercase": true,
    "words": [
      { "t": 0.00, "end": 0.28, "text": "this" },
      { "t": 0.31, "end": 0.70, "text": "changed", "emphasis": { "color": "gold", "emoji": "🤯" } }
    ]
  },

  "hook": { "text": "Nobody talks about this", "start": 0.0, "end": 2.6, "style": "banner" },

  "overlays": [                           // optional extras
    { "type": "progress_bar", "color": "gold" },
    { "type": "emoji", "t": 0.31, "dur": 0.8, "char": "🤯", "anchor": "above-caption" }
  ],

  "audio": {
    "loudness_lufs": -14,
    "sfx": [ { "t": 0.31, "kind": "pop", "gain_db": -8 } ],
    "music": null                         // { "track_id": "...", "gain_db": -22, "duck": true }
  },

  "package": {                            // publishing metadata, not rendered
    "titles": ["The habit that doubled his revenue", "..."],
    "description": "...",
    "hashtags": ["shorts", "business", "habits"],
    "pinned_comment": "Would you try this?",
    "thumbnail_t": 3.4
  }
}
```

## Templates

Templates are named presets in `apps/api/app/pipeline/templates.py` (CLP-170). The EDL references them by name
and may override individual fields.

| Name | Look |
|---|---|
| `bold-gold` (default) | Montserrat ExtraBold, white text with a 7 px black outline, active word `#E0A800` with a 112% pop |
| `minimal` | 64 px white, light outline, no highlight |
| `boxed` | Words on a black rounded box, active word gold |
| `none` | No captions (the hook is still shown) |

## Renderer mapping

| EDL | ffmpeg / libass |
|---|---|
| `frame.mode=track` + `keyframes` | `crop=w:h:x(t)` piecewise-linear expression |
| `frame.mode=fit` | `split` → blurred bg + scaled fg → `overlay` |
| `frame.zooms` | `zoompan`, or a `scale`+`crop` expression on `t` |
| `captions`, `hook` | Generated `.ass` → `ass=` filter |
| `overlays.emoji` | Twemoji PNG → `overlay=enable='between(t,a,b)'` (libass has no color-emoji support) |
| `overlays.progress_bar` | `drawbox` with width `iw*t/duration` |
| `audio.loudness_lufs` | `loudnorm` |
| `audio.sfx` | `amix` with `adelay` per cue (bundled CC0 SFX pack) |
