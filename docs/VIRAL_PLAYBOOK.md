# Viral Shorts playbook

This playbook is the editorial knowledge Clipper encodes. `scoring.SYSTEM_PROMPT` and the packaging
prompt (CLP-150) are derived from it. Change a rule here first, then update the prompt and the eval.

## What the algorithm rewards

YouTube Shorts distribution is driven by these signals:
- **Viewed vs swiped away.** Did people stop scrolling?
- **Average percentage viewed.**
- **Rewatches and loops.**
- **Engagement**: likes, comments and shares.

Every rule below serves one of these signals.

## 1. Moment selection

| Rule | Why |
|---|---|
| Open on the **most interesting sentence**, not the start of the topic | The first 1–2 s decide swipe-away |
| The clip must **pay off**: punchline, reveal, answer or strong opinion | Unresolved clips get swiped before the end |
| **Stand-alone**: zero context needed, with no "as I said", "he", or "that thing" without a referent | Viewers have never seen the long video |
| **Emotion**: surprise > humor > controversy > inspiration > relatability > information | Emotion drives shares and comments |
| Prefer **20–45 s**. Use up to 60 s only if the payoff needs it | Shorter means a higher % viewed |
| **High replay heat** is strong evidence, but content judgment wins | Heat can come from visuals, music or ads |
| Avoid moments that are only good visually when the speaker is off-screen | Crop can't save them |

## 2. The hook (first ~2.5 s)

- On-screen hook text is **≤ 8 words** and creates a curiosity gap. It must not repeat the first spoken line.
- Patterns that work:
  - "Nobody talks about this"
  - "This is why X fails"
  - "He wasn't ready for this"
  - "The $1 mistake that cost $1M"
- Never lie. The clip must deliver what the hook promises, because broken promises kill retention.
- Cut the dead lead-in. The first word should land within 0.3 s of frame 1.

## 3. Captions (speech text)

- Show every spoken word, **1–3 words at a time**, uppercase, with a heavy outline. They must be readable muted,
  because most Shorts start muted.
- **Highlight the active word** in the accent color with a slight scale pop. This creates rhythm.
- **Emphasis words** get extra treatment: color, an emoji or a punch-in zoom. These are numbers, names,
  emotional words and the payoff word. Use at most one emphasis every ~3 s, or it becomes noise.
- Placement: the lower third, above the bottom ~22% (YouTube UI) and clear of the right ~12% (action
  buttons). Never cover the speaker's mouth.

## 4. Visual pacing

- Keep the speaker's face in the upper-middle third.
- Add a punch-in zoom (1.08–1.15×) on emphasis words or at least every 6–8 s to reset attention.
- On scene cuts, hard-cut the crop. Don't pan across a cut.
- An optional progress bar (thin, accent color) increases completion on longer clips.

## 5. Ending and loop

- End right after the payoff. No outros, no "subscribe".
- When possible, make the last frame flow into the first, so the loop feels seamless and rewatches count.

## 6. Packaging

| Field | Rules |
|---|---|
| Title | ≤ 60 chars, curiosity plus a specific detail, no clickbait lies, no emojis, no hashtags. Produce 3 variants. |
| Description | 1–2 sentences of context, then a credit line to the original video/channel, then hashtags |
| Hashtags | 3–5, lowercase, specific to the clip, always including `shorts` |
| Pinned comment | A question that invites opinions (drives comments) |
| Thumbnail frame | A clear face, an expressive moment, no motion blur |

## 7. Audio

- Loudness −14 LUFS integrated, true peak −1.5 dBTP.
- Optional SFX: a subtle *pop* on emphasis words and a *whoosh* on zooms, at −8 to −12 dB under speech.
- Music only if it is licensed. It is off by default and ducked under speech.

## 8. Ethics

- Clip only content the user owns or has permission to reuse. Always credit the source channel.
- Don't reframe content so it changes the speaker's meaning. Don't add fabricated quotes.
