# ADR-0001: ffmpeg + libass as the renderer

- **Status:** Accepted
- **Date:** 2026-10-08
- **Tickets:** CLP-160, CLP-170

## Context
Each Short needs a 9:16 crop that follows the speaker, animated word-level captions, a hook
banner, zooms, emoji and normalized audio. Rendering runs once per clip, about 5 clips per job,
on CPU or GPU workers.

## Options
1. **ffmpeg + libass (ASS subtitles).**
   - Pros: one process, one pass, no extra runtime, every effect we need (karaoke color,
     transforms, fades, boxes), NVENC available later, and it is already in the image.
   - Cons: no color emoji in libass (we overlay PNGs instead), and complex animation is verbose.
2. **Remotion (React → video).**
   - Pros: any CSS or React animation, and the editor preview equals the render.
   - Cons: headless Chromium per render (slow and memory-heavy), a company license is needed above a
     small team size, and a second runtime in workers.
3. **MoviePy or a custom OpenCV compositor.**
   - Pros: Python-native.
   - Cons: slow frame-by-frame Python loops and weaker text rendering.

## Decision
ffmpeg + libass, driven entirely by the EDL. Emoji and stickers are PNG overlays.

## Consequences
- Renders are fast and deterministic. The web editor previews with CSS approximations of
  templates, so small visual drift between preview and render is accepted.
- If we later need motion-graphics templates that ASS can't express, revisit Remotion for
  *overlay layers only* (render a transparent ProRes or WebM overlay and composite it in ffmpeg).
