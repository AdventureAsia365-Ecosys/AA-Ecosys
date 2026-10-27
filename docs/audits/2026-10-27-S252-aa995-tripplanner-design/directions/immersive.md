# AA-995: TripPlanner customer pages design spec, direction "Field Journal" (immersive travel magazine)

This spec builds on `docs/audits/2026-10-27-S252-aa995-tripplanner-design/research.md`, the AA-994 ADR draft (`docs/audits/2026-10-27-S252-aa994-design-system/adr-draft.md`) and the current code (`frontend/ui/tokens.css`, `tailwind.config.ts`, `app/page.tsx`, `app/destinations/[country]/page.tsx`, `app/tours/[slug]/page.tsx`, `components/site/SiteHeader.tsx`, `ui/Photo.tsx`, `lib/catalogTypes.ts`). No code or commits came out of this step.

## 0. Direction in one paragraph

The pages take the brand's own look and make it bigger:
- **Photos:** full-width, square-edged photos at the top of every customer page.
- **Type:** Satisfy script for section titles and Poppins for everything else, at magazine sizes.
- **Bands:** cream, white and navy alternate down the page.
- **Banner:** a slow sideways photo ribbon, the adventure.asia banner, built properly.

**Motion rules:**
- Nothing in the first screen waits on an animation.
- Only one thing moves on its own in any viewport.
- Every looping motion has a pause control and stops under `prefers-reduced-motion`.
- All motion is CSS (transform and opacity). JavaScript only adds classes from an IntersectionObserver, in three tiny client components. No animation library.

**Brand rules kept:**
- Gold `#DB9628`, navy `#1F2933`, cream `#F8F6F2`.
- The gold mountain logo. `logo.png` is all gold on a transparent background, so it works on navy and on a photo with a top scrim. Add an SVG export so it stays sharp.
- Short two-beat copy, no exclamation marks.
- The AI label from AA-805/AA-819 stays. It is a disclosure requirement, so it is restyled, not removed.

---

## 1. Tokens

**Where they live.** All tokens go in `frontend/ui/tokens.css`. Tailwind maps them (`k-*` colours, plus new `borderRadius`, `spacing`, `fontSize`, `boxShadow`, `transitionDuration` and `transitionTimingFunction` entries). Pages never write raw px, hex, rgba or cubic-bezier values.

**Naming follows ADR 0016 §3–4.** There are two groups:
- **Core candidates (`--aa-*`).** These go to `core/tokens.css` in the AA-994 token PR. Until then TripPlanner defines them, and later the file is swapped for the core copy.
- **TripPlanner-only (`--tp-*`).** These stay local, because ADR 0016 forbids defining `--aa-*` outside core.

### 1.1 Colour

Existing tokens stay as they are: accent, accent-deep, accent-soft, accent-tint, accent-border, ink, body, bg, card, line, scrim, hero-bg and the rest. `muted` and `muted2` take whatever canonical value AA-994 settles (the stricter of CIS AA-760 `#5A6270` and TripPlanner's `#656D7A`). Do not hand-tune them here.

New tokens:

| Token | Light | Dark | Use / contrast |
|---|---|---|---|
| `--aa-band` | `#1F2933` | `#0A0E13` | Navy band surface (How it works, CTA band) |
| `--aa-band-deep` | `#1B232C` | `#06090D` | Footer |
| `--aa-on-band` | `#F8F6F2` | `#EAEEF4` | Text on the band, ≈14:1 |
| `--aa-on-band-muted` | `#C8D6E5` | `#B8C0CC` | Secondary text on the band, ≈10:1 |
| `--aa-accent-on-band` | `#DB9628` | `#E8A838` | Gold text or numerals on navy, 5.9:1 (light). Gold is **never** text on cream or white; use `accent-deep` there. |
| `--aa-band-line` | `#2F3A46` | `#1A222C` | Hairlines on navy; in dark mode it also separates the band from `bg` |
| `--tp-scrim-bottom` | `linear-gradient(180deg, rgba(15,20,27,0) 30%, rgba(15,20,27,.74) 100%)` | same with `.80` | Photo hero and tile captions. White text must sit where the scrim is ≥ .65: white under .65 over a white pixel ≈ 6.8:1, while .55 is only 4.2:1, which fails. |
| `--tp-scrim-top` | `linear-gradient(180deg, rgba(15,20,27,.50) 0, rgba(15,20,27,0) 120px)` | `.60` | Keeps the transparent header readable over bright skies |

Add every new text/background pair to `lib/contrast.test.ts`, which moves to CIS under AA-994. That covers on-band, on-band-muted and accent-on-band on band and band-deep, and white on the scrim worst case.

### 1.2 Type

- **Families:** Poppins 400/500/600/700 and Satisfy 400, both through `next/font`, latin subset only.
- **Fahkwang is dropped** from site pages. The live brand site does not use it.
- **Inter** moves out of the root layout into `app/plan/layout.tsx`, so site pages stop downloading it. Moving the planner to Poppins is a later slice.

| Token | Value | Notes |
|---|---|---|
| `--aa-font-sans` | `var(--font-poppins, "Poppins"), system-ui, sans-serif` | Body, UI, all h1 and h3 |
| `--aa-font-script` | `var(--font-satisfy, "Satisfy"), cursive` | Propose to core (Booking already loads Satisfy, so the promotion rule is met). Flag to AA-994 that the core `--aa-font-display` = Fahkwang does not match the live brand. |
| `--aa-text-display` | `clamp(2.25rem, 1.4rem + 3.6vw, 4.5rem)`, 600, lh 1.05, tracking −0.02em | Home hero h1: 36 px at 390, 72 px at 1440 |
| `--aa-text-place` | `clamp(2.5rem, 1.2rem + 5.4vw, 6rem)`, 500, UPPERCASE, tracking .12em, lh 1 | Destination hero name, the brand pattern: 40 px at 390, 96 px at 1440 |
| `--aa-text-script` | `clamp(2.25rem, 1.7rem + 2.2vw, 3.5rem)`, 400, lh 1.05 | Section titles (h2): 36 px at 390, 56 px at 1440. Never below 32 px, never in caps, never for body, buttons or tour titles. |
| `--aa-text-h1` | `clamp(1.75rem, 1.3rem + 1.9vw, 3.25rem)`, 600, lh 1.12 | Tour h1 (long titles): 28 px at 390, 52 px at 1440 |
| `--aa-text-h2` | `clamp(1.375rem, 1.15rem + .9vw, 2rem)`, 600, lh 1.2 | In-content Poppins h2 (tour sections) |
| `--aa-text-h3` | `clamp(1.125rem, 1.05rem + .3vw, 1.25rem)`, 600, lh 1.3 | Card titles: 18 px at 390, 20 px at 1440 |
| `--aa-text-lede` | `clamp(1.0625rem, 1rem + .3vw, 1.25rem)`, 400, lh 1.55 | Hero lede, tour overview |
| `--aa-text-body` | 1rem, 400, lh 1.6 | |
| `--aa-text-small` | .875rem, 400/500, lh 1.5 | Card summary and meta |
| `--aa-text-kicker` | .75rem, 600, UPPERCASE, tracking .16em | Eyebrow above titles, chips |
| `--aa-text-stat` | the script face at `clamp(2.75rem, 2rem + 3vw, 4rem)` | Step numerals 1/2/3 and proof numbers, on navy only |

Section header pattern, centred: a kicker (Poppins caps, `accent-deep`, or `accent-on-band` on navy), then the h2 in Satisfy, then a lede at most 640 px wide. Inline `text-[NNpx]` values go away and are replaced by this scale.

### 1.3 Spacing and layout (4 px base)

- **Spacing scale:** `--aa-space-{1..10}` = 4, 8, 12, 16, 24, 32, 48, 64, 96, 128.
- **Section padding:** `--aa-section-y: clamp(56px, 4vw + 40px, 112px)`, which gives 56 px at 390 and 96 px at 1440.
- **Container:** `--aa-container: 1248px`. The gutter is `--aa-gutter: clamp(16px, 4vw, 32px)`, centred, so you get 16 px at 390 and 96 px of effective margin at 1440. `--aa-measure: 680px` caps text columns.
- **Full-bleed:** photos and the ribbon ignore the container, but always stay inside `overflow-x: clip` on their own wrapper. The page itself never scrolls sideways.
- **Header height:** `--tp-header-h` = 56 px (390) / 72 px (≥1024).

### 1.4 Radius

| Token | Value | Use |
|---|---|---|
| `--aa-radius-none` | 0 | Full-bleed photos and bands (brand square edges) |
| `--aa-radius-sm` | 6px | Ribbon tiles, chips, inputs inside the search card |
| `--aa-radius-md` | 12px | Cards, card photos, map frame |
| `--aa-radius-lg` | 20px | Search card, sticky CTA card, quick-facts card |
| `--aa-radius-pill` | 999px | Buttons (the kit `Button` stays a pill), badges, the pause button |

### 1.5 Shadows

| Token | Light | Dark |
|---|---|---|
| `--aa-shadow-sm` | `0 1px 2px rgba(31,41,51,.06), 0 2px 8px rgba(31,41,51,.07)` | `0 1px 2px rgba(0,0,0,.4), 0 2px 8px rgba(0,0,0,.3)` |
| `--aa-shadow-md` | `0 1px 2px rgba(31,41,51,.06), 0 6px 20px rgba(31,41,51,.10)` | `0 2px 4px rgba(0,0,0,.45), 0 8px 24px rgba(0,0,0,.35)` |
| `--aa-shadow-lg` | `0 2px 4px rgba(31,41,51,.06), 0 16px 40px rgba(31,41,51,.16)` | `0 4px 8px rgba(0,0,0,.5), 0 20px 48px rgba(0,0,0,.45)` |

These replace the hard-coded `aa` and `aa-sm` entries in `tailwind.config.ts`.

### 1.6 Motion tokens

- **Durations:** `--aa-dur-fast` 150ms, `--aa-dur-base` 250ms, `--aa-dur-slow` 500ms, `--aa-dur-reveal` 600ms.
- **Easings:** `--aa-ease-std: cubic-bezier(.4,0,.2,1)`, `--aa-ease-out: cubic-bezier(.2,.7,.2,1)`, `--aa-ease-inout: cubic-bezier(.65,0,.35,1)`.
- **TripPlanner-only:**
  - `--tp-reveal-shift: 16px`
  - `--tp-reveal-stagger: 60ms`, capped at index 5, so 300 ms at most
  - `--tp-settle-dur: 4.8s`
  - `--tp-marquee-sec-per-tile`: 3.8s at <1024 and 5.75s at ≥1024. That is about 48 px/s at both sizes, half the brand's 95 px/s.
- **Global guard:** `@media (prefers-reduced-motion: reduce)` sets every `--aa-dur-*` to `0.01ms` and switches off all keyframe classes listed below.

---

## 2. Motion language

**The gate.** The theme-restore script in `layout.tsx` already runs before paint. It also sets `<html data-motion="ok">` when JavaScript is on and `matchMedia('(prefers-reduced-motion: reduce)')` is false, and updates the flag when the media query changes. Every "hide then reveal" style is scoped under `[data-motion="ok"]`. Without JavaScript, or with reduced motion on, all content is visible and still.

| # | Element | Trigger | Property | Duration / easing | Reduced-motion fallback |
|---|---|---|---|---|---|
| M1 | **Hero "settle"** (all photo heroes) | Page load, CSS only, runs once | `transform: scale(1.06) → scale(1)` on the hero `<img>`, `transform-origin` = focal point | `--tp-settle-dur` 4.8s, `--aa-ease-out`, `fill: both`; `will-change` removed on `animationend` (CSS `animation-fill-mode` only, no JS) | Static at scale 1. Kept ≤ 5 s on purpose so WCAG 2.2.2 does not require a pause control. No looping and no Ken Burns pan. |
| M2 | Header: transparent → navy | IntersectionObserver on a 1 px sentinel at the hero's bottom minus the header height (no scroll listener) | `background-color` transparent → `--aa-band`, `box-shadow` none → sm, `--tp-scrim-top` fades out | `--aa-dur-base`, `--aa-ease-std` | Same state change, applied instantly. Height never changes (no CLS). |
| M3 | Scroll reveal: section header and card groups below the fold | IO (`threshold .15`, `rootMargin 0 0 -10% 0`), once, then unobserve. Elements already in view on the first callback get no animation. | `opacity 0 → 1`, `translateY(16px) → 0`, children staggered by `--i × 60ms` (max 300 ms) | `--aa-dur-reveal`, `--aa-ease-out` | Not hidden, not moved. Only the opacity-0 start state is scoped under `[data-motion="ok"] [data-reveal="pending"]`. |
| M4 | **Ribbon marquee** (§3.1) | IO adds `.is-running` when ≥10 % is visible and removes it when out of view; `document.hidden` pauses it natively | `@keyframes tp-marquee { to { transform: translate3d(-50%,0,0) } }` on a track with two identical lists, `linear infinite` | `calc(var(--n) * var(--tp-marquee-sec-per-tile))` (≈48 px/s) | No animation. The track renders as a native `overflow-x:auto` scroll-snap row (the "still" mode). |
| M5 | Ribbon pause on hover | `:hover` (only `@media (hover:hover)`) | `animation-play-state: paused` | instant | n/a |
| M6 | Ribbon still mode | Pause button pressed, `:focus-within` from a keyboard (`:has(:focus-visible)`), or reduced motion | Animation removed; the track becomes a swipeable scroll-snap row; the duplicate list is `hidden` | instant (no position tween) | Already the default |
| M7 | Card hover (tour cards, destination tiles) | `@media (hover:hover)` `:hover` / `:focus-visible` | Card `translateY(-2px)`, shadow md → lg; photo `scale(1) → scale(1.04)` inside `overflow:hidden` | Lift `--aa-dur-base` std; photo `--aa-dur-slow` ease-out | Shadow change only; no lift, no zoom |
| M8 | Destination tile caption | hover / focus | Gradient deepens (.74 → .85), the "Explore →" line goes `opacity 0 → 1`, `translateY(6px) → 0` | `--aa-dur-base` ease-out | Line always visible, no shift |
| M9 | Text links and CTAs | hover / focus | Colour and background (`--aa-dur-fast` std). Inline text links get a gold underline `background-size 0% → 100%`. | `--aa-dur-base` ease-out | Colour change only; underline always shown |
| M10 | Day-by-day `<details>` | open / close | Chevron `rotate(0 → 180deg)`. Content height uses `interpolate-size: allow-keywords` + `::details-content` `block-size` where supported (progressive enhancement), otherwise instant. | `--aa-dur-base` inout | Instant |
| M11 | Mobile sticky CTA bar (tour, <1024) | IO: the hero CTA leaves the viewport | `translateY(100%) → 0` (fixed position, so no CLS) | `--aa-dur-base` ease-out | Appears instantly |
| M12 | Gallery row (tour) | User only (buttons / swipe) | `scroll-behavior: smooth` on `scrollBy` | browser | `scroll-behavior: auto` |

**Rejected, with reasons:**
- Rotating hero carousel: hurts LCP and needs a pause control.
- Count-up numbers: need JavaScript, screen readers read changing values, and they are gimmicky.
- Parallax: needs a scroll handler and jank on mobile.
- View Transitions (React `<ViewTransition>` is still experimental in Next 16; revisit later).
- Any autoplay slider apart from the ribbon.

---

## 3. Components

### 3.1 `Ribbon`: the sideways photo banner

**Files:**
- `components/site/Ribbon.tsx`: server markup, rendered by the page.
- `components/site/RibbonControls.tsx`: `"use client"`, about 1.5 KB. It holds the IntersectionObserver, the pause toggle and the stored preference.

**Props:** `items: RibbonItem[]` (photo tile or typographic tile), `label`, `heading`, `kicker?`, `href?` (a "see all" link).

**Item kinds:**
- **Photo tile.** `<a>` to the destination or tour. `<img>` with `alt` = "`place_label`, `country`". Caption chip at bottom-left: place name in Poppins 12/600 white on `--tp-scrim-bottom`, always visible.
- **Typographic tile**, for a country without a cover photo:
  - background alternates between `--aa-band` and `--aa-accent-tint`;
  - the country name in Satisfy 32/28 (`on-band` or `accent-deep`);
  - a mountain-line motif from the logo, as inline SVG at 12 % opacity;
  - "N tours" in Poppins small. It contains no `<img>`.

**Data rules:**
- Deduplicate by `photo_id` and by URL.
- Interleave typographic tiles so two never sit side by side.
- Animate only when `n ≥ 10` unique items (a track of 10 × 272 px is wider than 1440 px, so the loop has no visible gap).
- With 4–9 items, render the still row only. Under 4 items, omit the section.

**Size and layout:**

| | 390 | 1440 |
|---|---|---|
| Tile (4:5) | 176 × 220 | 264 × 330 |
| Gap | 8 | 12 |
| Radius | `--aa-radius-sm` | same |
| Section | Full-bleed, cream (home) or white (destination) band, `--aa-section-y` | same |
| Header row | Centred kicker + Satisfy h2; pause button right-aligned under the title | Header in the container; pause button at the container's right edge on the title baseline |
| Below the track | "All destinations" wrap-chip list (home) or "See all photos" (destination) | same |

**Markup and accessibility:**
- `<section aria-labelledby="ribbon-h">`
- The pause button **comes before** the track in DOM order. It is `<button type="button" aria-pressed="false">`, its visible text and accessible name is "Pause moving photos", it shows a pause/play icon and has a 44 × 44 hit area.
- The track wrapper is `<div class="overflow-x-clip">`.
- List A is `<ul aria-label="{label}">` with focusable links.
- List B is `<ul aria-hidden="true" inert>` with the same items. It is rendered only while animating (`hidden` in still mode), so it is never focused or announced.
- Keyboard: Tab into list A switches to still mode (M6), so a focused tile scrolls into view natively. Leaving the ribbon resumes the animation, unless the user pressed Pause.
- The pause preference is stored per viewer in `localStorage['tp_motion_paused']` (inside try/catch) and applies to every ribbon.
- Links use `prefetch={false}` (AA-833).

**Performance:**
- Always below the fold, so it can never be the LCP element.
- `loading="lazy"`, `decoding="async"`, `width`/`height` set, `sizes="(min-width:1024px) 264px, 176px"`, `src` = `url_small` (600 w).
- List B reuses the same URLs, so it costs no extra bytes.
- `will-change: transform` only while `.is-running`.
- `content-visibility: auto` with `contain-intrinsic-size: auto 420px` on the section.

**Where it appears:**
- **Home:** "Where we go". Destination items, all countries with `tour_count > 0`.
- **Destination:** "From our tours in {X}", items from `d.photos`. This replaces today's photo grid.
- **Tour:** "On this trip", only when the tour has ≥ 10 photos (otherwise left out; the gallery covers it).

### 3.2 `PhotoHero`

**Props:** `photo` (final CDN URL + `srcSet` + `width`/`height` + focal `object-position` + `alt`), `variant: home | place | tour`, `children` (the text block), `priority` (always true).

**Layers, bottom to top:**
1. `--aa-hero-bg` solid colour (so there is no white flash, and it doubles as the no-photo fallback);
2. the `<img>` (M1);
3. `--tp-scrim-top`;
4. `--tp-scrim-bottom`;
5. the content, inside the container and bottom-aligned.

**Without a photo:** a navy hero with the mountain-line SVG motif at 8 % and the name in the script face as a large watermark. The LCP is then the text.

**Heights:**

| Variant | 390 | 1440 |
|---|---|---|
| home | `min(78svh, 680px)`, min 520 | `min(86svh, 820px)`, min 600 |
| place | `min(64svh, 560px)`, min 440 | `min(72svh, 720px)`, min 520 |
| tour | `min(56svh, 480px)`, min 400 | `min(64svh, 640px)`, min 480 |

The heights deliberately leave the next band peeking in the first screen, as a cue to scroll.

### 3.3 Cards

**`TourCard`, restyled:**
- Card: `--aa-card` background, `--aa-radius-md`, `--aa-shadow-sm`, M7.
- Photo: 3:2 at the top, square on the inside edge (radius only on the outer corners).
- Day badge: pill top-left, `--aa-card` background, ink text.
- Country kicker: Poppins caps 12 px `accent-deep`, then the title in h3 Poppins 600, clamped to 2 lines.
- Meta row with icons: days · places count (when the API provides it) · top 3 activities as small line icons with `title`. Then a 2-line summary in small `muted`.
- Footer: hairline, then "View itinerary →" as a text link (M9).
- The whole card is one link (stretched `::after` on the title link; no nested links).
- No price (ADR 0005).
- **Duplicate cover rule:** in any one grid or row, a `cover_url` already used earlier renders the typographic treatment (navy + country in Satisfy) instead of the same photo again.

**`DestinationTile`:**
- 4:5 photo, `--aa-radius-md`, `--tp-scrim-bottom`.
- Name: Poppins 600 22 px white. Then "N tours · X–Y days" small. Then "Explore →" (M8).
- Without a photo, use the typographic tile from §3.1.

### 3.4 Header and footer

**`SiteHeader`:**
- Transparent over a photo hero, navy otherwise or after scroll (M2).
- Logo: an SVG version of the gold logo, 36 px tall at 1440 and 28 px at 390.
- The AI label is restyled as an outline pill: `--aa-on-band` text and `--aa-band-line` border on dark, the current style on light pages.
- Links: Destinations, Tours, My trips/Sign in. White Poppins 500 15 px, with a gold 2 px underline on hover and on the current page.
- Theme toggle, then a gold "Plan a trip" pill (dark text).
- At 390: logo + AI short label + "Plan" pill + a 44 px menu button that opens a `<dialog>` sheet. The sheet has the links and the theme toggle, a focus trap from the native dialog, and closes on Esc.
- On pages without a hero (`/plan`, sign-in, legal): solid navy from the start.

**`SiteFooter`:**
- `--aa-band-deep` background, `--aa-band-line` top hairline.
- Column headings in Satisfy 28 px: "Explore", "Trip planner", "Adventure Asia". Links in `on-band-muted`.
- Social icons (the existing `*-circle.svg` files).
- A small "Every itinerary checked by an advisor" line, then legal links.

### 3.5 Bands

| Band | Surface | Text |
|---|---|---|
| cream | `--aa-bg` | ink / body |
| white | `--aa-card` | ink / body |
| navy | `--aa-band` | on-band, numerals and kickers `accent-on-band` |
| photo | `PhotoHero` or a full-bleed `<img>` with scrim | white |

Rule: two bands next to each other never share a surface.

---

## 4. Page layouts

### 4.1 Home `/`

| # | Section | 1440 | 390 |
|---|---|---|---|
| 1 | Header | Transparent over the hero | same |
| 2 | **Hero** (photo, `home`) | Centred text block, max 880 px: kicker in the script face, `on-band` colour, 28 px ("The Asia few people see"); h1 display, white (keep the SEO h1 "Plan your Asia adventure, tailor-made with an advisor"); lede, 85 % white. The **search card** (`--aa-radius-lg`, `--aa-shadow-lg`, `--aa-card`, 960 px wide) overlaps the hero's bottom edge by 50 % of its height. Fields stay in one row (Where to · Days · Travellers · gold "Plan my trip"), with the day chips below. | Text left-aligned, 16 px gutters. The search card sits **after** the hero, pulled up 32 px into it. Fields stack; the button is full width. |
| 3 | Proof strip (cream) | One centred line: **{N} tours · {M} countries · every itinerary checked by an advisor**. Numbers in Poppins 700 `accent-deep`, text in body. Counts come from `getCountries()`. | Wraps to 2 lines |
| 4 | **Featured tours** (white) | Kicker "Hand-picked" + Satisfy h2 "Trips worth the detour" + lede. **Magazine grid:** card 1 is the lead (spans 2 columns × 2 rows, 16:10 photo, title `--aa-text-h2`). Cards 2–5 sit in a 2 × 2 grid beside it, card 6 below. "See all tours" secondary pill, centred. | Lead card full width. The rest go in a horizontal scroll-snap row (`overflow-x:auto` inside its own wrapper, ~1.15 cards per view, `scroll-padding: 16px`, no autoplay, visible scrollbar hidden but still keyboard-scrollable). The CTA follows. |
| 5 | **Destination ribbon** (cream, full-bleed) | §3.1, kicker "14 countries", h2 "Where we go". Wrapped chip list of all destinations under it. | same, smaller tiles |
| 6 | **How it works** (navy) | 3 columns: brand illustrated icon (`plan-color`, `map-color`, `direction-color`, 64 px), numeral 1/2/3 in `--aa-text-stat` gold, step title in Poppins 600 `on-band`, 2-line text `on-band-muted`. Centred gold "Plan a trip" pill. | Stacked; the icon sits left of the text |
| 7 | **Advisor split** (white) | 50/50: a full-bleed photo bleeding to the left viewport edge (curated, lazy) and text on the right in the container: kicker "Checked on the ground", Satisfy h2 "Real trips, shaped by you", 2 short paragraphs (the TrustStrip content moves here), "Talk to an advisor" secondary pill to `/plan`. | Photo on top (16:10), text below |
| 8 | Footer | §3.4 | same |

### 4.2 Destination `/destinations/[country]`

| # | Section | 1440 | 390 |
|---|---|---|---|
| 1 | **Hero** (photo, `place`) | Breadcrumb (Home / Destinations / X, white 80 %) at the top of the content block. Name in `--aa-text-place`, cream. Meta line "{N} tours · {min}–{max} days". Buttons: primary "Plan a trip to {X}" and ghost "See tours" (white outline on the scrim, jumps to #tours). | Same, left-aligned; buttons stack full width |
| 2 | **Quick facts card** (white, overlaps the hero by 40 px, `--aa-radius-lg`, shadow md) | One row: Tours · Trip length · Top activities (up to 5 chips with icons) · Places. | 2 × 2 grid, chips wrap |
| 3 | Tours in {X} (cream) | Kicker + Satisfy h2 "Tours in {X}". 3-column `TourCard` grid with the duplicate cover rule. "Show more" when there are more than 9. | 1 column |
| 4 | Places our tours visit (white) | Split 7/5: `StaticMap` (`--aa-radius-md`, frame `--aa-line`) left, numbered list right (56 px thumbs `--aa-radius-sm`, name, "in N tours"). The list scrolls inside a box of max map height. | Map, then the list |
| 5 | **Photo ribbon** "From our tours in {X}" | §3.1 | same |
| 6 | CTA band (navy) | Satisfy h2 "Shape your own {X} trip", one line, gold "Plan a trip" pill. | same, centred |
| 7 | Footer | | |

### 4.3 Tour `/tours/[slug]`

| # | Section | 1440 | 390 |
|---|---|---|---|
| 1 | **Hero** (photo, `tour`, photo 1) | Breadcrumb; badges (days, country, difficulty when present) as on-photo pills; h1 `--aa-text-h1` white, max 900 px; the subtitle as lede. Primary "Plan this trip" pill (this is the IO anchor for M11). | Left-aligned; the CTA is full width |
| 2 | Gallery row (white) | Photos 2…n in a scroll-snap row, 320 × 240 tiles, `--aa-radius-md`, with prev/next 44 px buttons (`aria-controls`, disabled at the ends). "N photos" label. No autoplay. | Swipe row, 1.3 per view, no buttons |
| 3 | Body (cream), 12-column grid | **Main 8 columns:** Overview (summary in lede size, max 680 px) → Highlights (2-column list with gold check icons) → **Day by day**: a vertical timeline with a 2 px `accent-border` rail and gold day dots, one `<details>` per day (day 1 open), summary "Day N · title" (M10) → Where you go (`StaticMap` route) → Included / Not included (two cards side by side, `--aa-radius-md`) → Good to know (best time, group size). **Aside 4 columns:** sticky (top = header + 24) CTA card, `--aa-radius-lg`, `--aa-shadow-md`: "{N} days in {X}", a "Tailor-made with an advisor" line, primary "Plan this trip", secondary "Ask an advisor", the AI label explanation. | 1 column; the aside is replaced by the **sticky bottom CTA bar** (M11): `--aa-card`, top hairline, shadow lg, "Plan this trip" full width; the page reserves its height in the bottom padding |
| 4 | "On this trip" ribbon | Only with ≥ 10 photos (§3.1) | same |
| 5 | More tours in {X} (white) | Kicker + Satisfy h2 "More in {X}", 3 cards, using data the page already has, or one extra ISR-cached `getTours({country, limit:3})` call | Snap row |
| 6 | CTA band (navy) + footer | | |

---

## 5. Accessibility

- **WCAG 2.2.2:** the ribbon is the only auto-moving loop. It has a visible pause control placed before it in DOM order, pauses on hover, switches to still mode on keyboard focus, and turns off under reduced motion. The hero settle is ≤ 5 s and plays once. Nothing else moves on its own.
- **Ribbon semantics:** the labelled section, the inert/`aria-hidden` duplicate, `alt` on every image, the typographic tiles' text as their accessible name, 44 px targets. It is not a "carousel" widget, so there is no `aria-roledescription` or `aria-live` rotation noise.
- **Contrast:**
  - Every new pair goes into the contrast test.
  - Text on photos sits only on the bottom scrim (≥ .65 where the text is).
  - Gold text only on navy (5.9:1).
  - Gold buttons keep dark text (`--aa-on-accent`).
  - The script face is only used at ≥ 32 px (large text, 3:1 minimum, yet every use passes 4.5:1).
- **Structure:**
  - One h1 per page.
  - Script h2s are real `<h2>`s, and their text is plain words (no decorative glyphs).
  - Landmarks: header, nav "Main", main, footer, plus a "Skip to content" link that becomes visible on focus.
  - Card links are not nested.
  - The breadcrumb is `<nav aria-label="Breadcrumb">`.
- **Keyboard:**
  - Gallery buttons have `aria-controls` and `aria-label` "Previous photos"/"Next photos".
  - The menu `<dialog>` closes on Esc and returns focus to its button.
  - The focus ring is the existing 2 px gold outline. On navy it is `--aa-on-band`, because gold on navy is 5.9:1 but this is clearer.
- **Zoom and reflow:** the type scale is in rem plus clamp, so 200 % text zoom works. At 320 px wide there is no sideways scroll; scroll rows live inside their own clipped wrappers.
- **No-JS and reduced motion:** all content is visible, the ribbon is a static scroll row, and the header is solid navy once past the hero (no-JS falls back to a solid header with `position: sticky`).
- **Dark theme:** every band, scrim and tile has a dark value (§1). Photos are unchanged. Dark bands use `--aa-band-line` hairlines so they read apart from `bg`.

---

## 6. Performance plan

1. **Hero LCP: remove the 302 hop.**
   - **Slice 0:** add `lib/heroes.ts`, a curated map for home and the 14 destinations: `{ photo_id, src (final CDN URL), srcSet, width, height, focal, alt }`. The CDN hostname is fine in the public repo; no IDs or ARNs. Tours use their own cover, falling back to the API URL.
   - **Follow-up (CIS + Browse):** the catalog returns the final CDN URLs (`url_final`, `url_small_final`) plus a width set, ideally adding a ~1024 w variant. That needs a CIS issue.
   - Until the follow-up lands, a tour hero still pays the hop, but tour pages at 390 usually have the h1 text as LCP. Measure it.
2. **Priority hints:**
   - Hero `<img fetchpriority="high" loading="eager" decoding="sync">` with `srcSet` (600 w / large) and `sizes="100vw"`.
   - `preload()` from `react-dom` in the server component with `imageSrcSet`/`imageSizes`.
   - `<link rel="preconnect">` to the image CDN, `dns-prefetch` to the API host.
   - Every other image is `loading="lazy"`.
3. **No layout shift:** every `<img>` gets `width`/`height` (`CatalogPhoto.width`/`height` are available) or an aspect-ratio box. The search card overlap uses a fixed negative margin. Motion is transform/opacity only. The header never changes height. `next/font` fallbacks are metric-adjusted. Target CLS ≤ 0.05.
4. **Fonts:**
   - Poppins 400/500/600/700 and Satisfy 400, latin, `display: swap`. Preload only Poppins 400 and 600 (h1); Satisfy is below the fold, so `preload: false`.
   - Drop Fahkwang.
   - Move Inter into `app/plan/layout.tsx`. That is −2 to −3 font files on every site page.
5. **JavaScript:** no new dependencies. The client pieces are three leaf components, ≈ 4 KB gz total: `MotionReveal` (one shared IO), `RibbonControls`, `HeaderState`. The menu dialog's open/close is a small client button. Pages stay Server Components with ISR 1800. Card and ribbon links keep `prefetch={false}`.
6. **Below the fold:** `content-visibility: auto` with `contain-intrinsic-size` on the ribbon, Places and the advisor split. Ribbon tiles use `url_small` (600 w, ≈ 46 KB); list B adds no bytes.
7. **Budgets per page at 390:**

   | Budget | Target |
   |---|---|
   | First-screen image bytes | ≤ 250 KB |
   | Total transferred on first load | ≤ 1.2 MB |
   | Added JS | ≤ 5 KB gz |
   | LCP | ≤ 2.5 s |
   | CLS | ≤ 0.05 |
   | Lighthouse mobile perf | ≥ 85 |
   | Console errors | 0 |
   | Page-level horizontal overflow at 390 and 1440 | none |

8. **Verify** on the Vercel preview, within about 40 page loads:
   - Lighthouse mobile on home, one destination and one tour, run from the GitHub Actions preview job rather than this machine, to avoid Vercel's bot challenge;
   - Playwright 390/1440 × light/dark × reduced motion;
   - a horizontal overflow check;
   - an axe pass;
   - a keyboard walk: pause button, Tab into the ribbon, the menu dialog.

---

## 7. Risks

| # | Risk | Effect | Mitigation |
|---|---|---|---|
| R1 | The 302 hop through the CIS API on every photo (≈1.4 s) | A photo hero misses LCP ≤ 2.5 s | Curated final URLs (slice 0), preload, preconnect; CIS issue for final URLs in the catalog |
| R2 | Photo coverage: 8 of 14 countries have no cover, featured tours repeat 2 images | The magazine look falls apart with placeholders | Typographic tiles and navy hero designed in as first-class; duplicate cover rule; curated heroes; a separate CIS issue for more cover photos |
| R3 | The "large" image variant may be narrower than 1600 px | Soft hero at 1440 on DPR 2 | Check widths before choosing heroes; ask for a 1920 w variant in the CIS issue |
| R4 | Font conflict with AA-994 (core `--aa-font-display` = Fahkwang; the live brand uses Satisfy) | Token drift right after unification | Propose `--aa-font-script` into core (Booking already uses Satisfy) and record the live-site finding in the AA-994 PR. TripPlanner never relies on the display token. |
| R5 | Too much motion or vestibular discomfort | Feels gimmicky, a11y complaints | One self-moving element per viewport, 48 px/s, pause control, reduced motion respected, settle ≤ 5 s once, no parallax |
| R6 | Scroll reveal hides content (JS error, IO not firing, crawlers) | Blank sections, SEO loss | Hidden state only under `[data-motion="ok"]` and only for elements below the fold on first observation; SSR HTML fully visible |
| R7 | The ribbon causes page-level horizontal overflow | Fails the bar, sideways wobble on mobile | `overflow-x: clip` wrapper on every full-bleed and scroll row; Playwright overflow assertion at 390/1440 |
| R8 | Transparent header over a bright photo | Nav text unreadable | `--tp-scrim-top` plus the M2 switch to navy; checked on the 15 curated heroes in both themes |
| R9 | Curated `heroes.ts` drifts from CIS (photo deleted or replaced) | Broken hero | Fall back to the catalog cover, then the navy typographic hero; a unit test checks that every entry has `alt`, width, height and a focal point |
| R10 | Vercel bot challenge limits verification from this IP | Cannot prove the Lighthouse and screenshot bars | Run Lighthouse and screenshots in GitHub Actions against the preview; keep local loads ≤ 40 |
| R11 | `/plan` still uses Inter and its own header | Two products feel different | Out of scope for this slice; the planner restyle is a follow-up slice that uses the same tokens |
| R12 | Visible change for returning users (header turns navy, Fahkwang removed) | Sign-off needed | Before/after shots of all 4 pages at 390/1440, light/dark, in the PR (AA-994 decision 9 style) |

**Suggested slice order:**
1. Tokens + fonts + reduced-motion gate (no visual change beyond type).
2. Header, footer, bands + `PhotoHero` + `heroes.ts` (home and destination).
3. `Ribbon` (home, destination).
4. Cards + home magazine grid.
5. Tour page.
6. CIS follow-up for final image URLs.