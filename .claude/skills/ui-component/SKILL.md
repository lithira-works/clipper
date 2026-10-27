---
name: ui-component
description: Build or restyle Clipper web UI (Next.js 16 + Tailwind v4) so it matches the light paper / black ink / dark-yellow design system and stays accessible. Use for any change under apps/web/src/.
---

# UI component

Read `docs/DESIGN_SYSTEM.md` first. The tokens are in `apps/web/src/app/globals.css`.

## Rules

- **Tokens only.** Use `bg-paper`, `bg-surface`, `text-ink`, `text-ink-soft`, `text-muted`,
  `border-line`, `bg-gold`, `hover:bg-gold-strong`, `bg-gold-soft` and `text-gold-ink`. Never write raw hex in a
  component. If a new color is truly needed, add a token to `@theme` and document it.
- **Contrast.** Use black text on gold and never white. Never put `gold` text on paper; use `gold-ink`.
- **Primitives first.** Use `.btn-primary` (one per view), `.btn-ghost`, `.card` and `.eyebrow` before inventing new styles.
- **Server by default.** Add `"use client"` only to components with state, effects or event handlers.
  Keep data fetching in `src/lib/`.
- **Icons.** Use `lucide-react` with `aria-hidden`. Icon-only buttons need an `aria-label`. Don't use brand icons.
- **Video.** Use `aspect-[9/16]`, `playsInline`, `preload="metadata"` and a `poster`.
- **Responsive.** The layout must work at 360 px wide with no horizontal scroll. Containers use `mx-auto max-w-6xl px-4 sm:px-6`.
- **A11y.** Every element needs keyboard access and visible focus. Errors use `role="alert"`. Live regions use `aria-live="polite"`.
  Segmented controls use `aria-pressed`.
- **Motion.** Keep it subtle (150–700 ms). Everything is already disabled under `prefers-reduced-motion`.

## Verify

```bash
cd apps/web && npm run typecheck && npm run build
```

Then check `npm run dev` in a narrow (375 px) and a wide (1440 px) viewport.
