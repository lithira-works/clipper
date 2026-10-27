# Design system

Clipper uses a light theme only: warm paper, black ink and a dark-yellow accent. The look is
editorial and confident, with chunky "pressable" primary buttons that echo the bold captions
burned into every Short.

All tokens live in `apps/web/src/app/globals.css` (`@theme`). Components use only these
tokens and never raw hex values.

## Color

| Token | Hex | Use |
|---|---|---|
| `paper` | `#FAF8F2` | Page background |
| `surface` | `#FFFFFF` | Cards, inputs |
| `ink` | `#0B0B0A` | Primary text, borders on primary controls |
| `ink-soft` | `#3A3833` | Body copy |
| `muted` | `#6B675E` | Meta text, placeholders |
| `line` / `line-strong` | `#E8E4D8` / `#D6D0BF` | Dividers / control borders |
| **`gold`** | **`#C99700`** | Primary accent: buttons, progress, active states |
| `gold-strong` | `#A67C00` | Hover and pressed state |
| `gold-soft` | `#FFF3C4` | Tints, chips, selection |
| `gold-ink` | `#6B5000` | Gold-colored text on paper (passes AA) |
| `success` / `danger` | `#1F7A3D` / `#B42318` | Status |

### Contrast rules

- Use **black text on `gold`**, never white. Ink on gold is about 9:1.
- Never use `gold` as text on paper, because its contrast is too low. Use `gold-ink`.
- In video captions, the active word is `#E0A800` with a 7 px black outline.

## Typography

| Role | Font | Style |
|---|---|---|
| UI and headings | Geist (next/font) | Headings `font-semibold tracking-tight`, h1 is 5xl–7xl |
| Labels and data | Geist Mono | `.eyebrow`: 12 px uppercase, tracking 0.18em, `gold-ink` |
| Burned-in captions | Montserrat ExtraBold | Uppercase, 96 px at 1080×1920 |

## Shape and depth

- Cards use `--radius-card` (20 px), a 1 px `line` border and the soft `--shadow-card`.
- Primary buttons have a 2 px ink border and a hard 4 px offset shadow (`--shadow-press`). On
  press, the button moves 2 px and the shadow disappears.

## Components

| Class / component | Notes |
|---|---|
| `.btn-primary` | Gold, ink border, press shadow. Use one per view. |
| `.btn-secondary` | Ink-filled. A repeatable action (one per card, e.g. Download), so it never competes with the single gold primary. |
| `.btn-ghost` | White with a hairline border that turns ink on hover |
| `.card` | Surface container |
| `.eyebrow` | Section kicker above headings |
| `.container-page` | The page width and gutter used by every route and by the header and footer (`max-w-6xl`, `px-4 sm:px-6 lg:px-8`) |
| `.chip` | Small rounded metadata pill (duration, settings) |
| `.skeleton` | Shimmer placeholder. Same size as the real element, so nothing reflows when data arrives. |
| `UrlForm` | Hero input, inline validation, and an always-visible options card (captions switch, length, Shorts stepper) |
| `JobView` | Source header card with status pill and settings chips, progress panel (bar, elapsed time, 5-step stepper), and a fixed clip grid with skeleton cards for Shorts still rendering |
| `ClipCard` | 9:16 player, rank, viral-score badge (gold at 80 or above), 2-line title and reason, hashtags, Download (secondary) and copy |
| `PhonePreview` | Static mockup of the output style |

## Layout

- The page shell is a flex column: a sticky header, a flexible main area, and a footer pinned to the bottom on short pages.
- Section rhythm: `py-20 sm:py-24` for home sections, `py-8 sm:py-10` for app pages.
- The clip grid is fixed: 1 column, then 2 from 520 px, 3 from `lg`, 4 from `xl`. Real and skeleton cards share it.

## Motion

The rules for motion are:
- Transitions take 150–700 ms with ease-out.
- Spinners appear only on active work.
- `prefers-reduced-motion` turns all motion off.

## Accessibility checklist

- Every interactive element is reachable by keyboard, with a visible gold `:focus-visible` outline.
- Icons are `aria-hidden`. Icon-only buttons have an `aria-label`.
- The progress bar uses `role="progressbar"` with values. Clip results use `aria-live="polite"`.
- Errors use `role="alert"` and are linked to their form with `aria-describedby`.
- Layout works from 360 px wide, with no horizontal scroll.
