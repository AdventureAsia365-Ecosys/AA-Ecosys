# AA-995 design spec: map-first explorer for the TripPlanner customer pages

Direction in one line: **make the product the hero.** Each customer page shows a route being drawn on a brand-coloured map, and a slow, accessible strip of destinations slides across the page. The tone stays warm, confident and plain, in brand colours (navy, gold, cream) with the Satisfy script for section titles.

Sources: `docs/audits/2026-10-27-S252-aa995-tripplanner-design/research.md`, `apps/AA-TripPlanner-Web/CONTEXT.md`, `frontend/ui/tokens.css`, `frontend/tailwind.config.ts`, `frontend/lib/staticMap.ts` and the page code. Nothing was committed and no code was written.

---

## 0. Principles

1. **The planner is the hero.** Every page leads to "Start planning" or "Plan this trip". On each page the map is the strongest visual, ahead of decoration.
2. **Motion explains the route.** Lines draw in the order of the trip, pins appear as the line reaches them, and the map follows the day you are reading. Nothing moves only to look busy.
3. **Only one thing moves on its own at a time.** The hero animation plays once and finishes in under 5 s. The one endless animation (the strip) can be paused and stops when it is off screen.
4. **Keep the brand.** Navy, gold and cream; Satisfy for short section titles; Poppins for everything else; full-bleed photos at the top of pages. We copy adventure.asia's look, not its B2B wording.
5. **CSS first.** No animation or carousel library. Small client pieces use IntersectionObserver, and the catalog pages stay Server Components with ISR.

---

## 1. Tokens: one file, `frontend/ui/tokens.css`, shaped for AA-994

`tokens.css` stays the only source. Tailwind maps every group (`colors.k`, `fontFamily`, `fontSize`, `spacing`, `borderRadius`, `boxShadow`, `transitionDuration`, `transitionTimingFunction`, `zIndex`). All names use the `--aa-*` prefix, so AA-994 can later replace the file without touching components.

Guards:
- extend `lib/contrast.test.ts` with the new text pairs (on-band, map labels, route against land);
- add `lib/tokens.test.ts`, which bans `text-[NNpx]`, raw hex values and raw `duration-NNN` / `ease-[…]` in `app/` and `components/site/`.

### 1.1 Colour

The existing values are kept (accent, semantic colours, neutrals, scrim, hero-bg). `muted` and `muted2` are aligned with the CIS AA-760 values (`#5A6270` / `#626A78`) under AA-994, provided the contrast test stays green. New tokens:

| Token | Light | Dark | Use |
|---|---|---|---|
| `--aa-band` | `#1F2933` | `#0B1016` | Navy bands: hero, CTA band, header, footer |
| `--aa-band-2` | `#2A333E` | `#141B24` | Raised surface on a band (plan card edge, chips) |
| `--aa-on-band` | `#F8F6F2` | `#EAEEF4` | Text on band (13.4:1 / 15:1) |
| `--aa-on-band-muted` | `#C8D6E5` | `#9FB0C4` | Secondary text on band (≈9.8:1) |
| `--aa-on-band-accent` | `#DB9628` | `#E8A838` | Satisfy titles and numerals on band (5.8:1 / 9.2:1) |
| `--aa-focus-on-band` | `#F8F6F2` | `#F8F6F2` | Focus ring on navy |
| `--aa-map-sea` | `#1F2933` | `#0B1016` | Hero map background (= band) |
| `--aa-map-land` | `#35495E` | `#1C2633` | Countries |
| `--aa-map-land-active` | `#4A5D73` | `#2A3A4D` | Countries that have tours |
| `--aa-map-land-hover` | `#DB9628` at 0.35 fill | `#E8A838` at 0.30 | Country highlighted from its chip |
| `--aa-map-border` | `#1F2933` | `#0B1016` | 0.75 px country borders |
| `--aa-route` | `#B5791F` | `#E8A838` | Route line on light Mapbox maps (≥ 3:1 against light-v11 land) |
| `--aa-route-on-band` | `#DB9628` | `#E8A838` | Route line on the navy hero map (3.7:1 on land) |
| `--aa-route-casing` | `#FFFFFF` | `#0B1016` | 2 px halo under the route |
| `--aa-route-muted` | `#C9B48C` | `#5A4A2A` | Route not yet reached (tour scroll-spy) |
| `--aa-pin` | `#1F2933` | `#EAEEF4` | Pin body |
| `--aa-pin-text` | `#F8F6F2` | `#0F141B` | Pin number |
| `--aa-pin-ring` | `#DB9628` | `#E8A838` | Pin ring and active ring |
| `--aa-scrim-bottom` | `linear-gradient(180deg, transparent 40%, rgba(15,20,27,.78))` | same, `.85` | Text over a photo |

Rule: white or cream text on gold is never allowed. Text on gold is `--aa-on-accent #1A1206`.

### 1.2 Type

Families:
- `--aa-font-sans`: **Poppins** 400/500/600. Weight 700 is dropped.
- `--aa-font-script`: **Satisfy** 400.
- **Fahkwang and Inter are removed.** The planner moves to Poppins in its own slice (see risk R9).

All three are loaded with `next/font`, latin subset, `display: swap`, `adjustFontFallback`.

The scale is fluid, written as `clamp(min @390, …, max @1440)`:

| Token | 390 | 1440 | Weight / case | Use |
|---|---|---|---|---|
| `--aa-text-display` | 32/38 | 52/58 | 600, −0.01em | Home hero h1 |
| `--aa-text-script` | 36/40 | 48/52 | Satisfy 400 | Centred section titles, at most ~22 characters |
| `--aa-text-script-sm` | 26/30 | 32/36 | Satisfy 400 | Hero kicker, card-band kicker |
| `--aa-text-place` | 36/40 | 64/68 | 500, UPPERCASE, 0.08em | Destination hero h1 (brand style) |
| `--aa-text-h1` | 26/32 | 36/44 | 600 | Tour title, page h1 |
| `--aa-text-h2` | 22/28 | 28/36 | 600 | Poppins sub-sections (Included, Highlights) |
| `--aa-text-h3` | 18/24 | 20/28 | 500 | Card titles |
| `--aa-text-lede` | 16/26 | 18/30 | 400 | Hero lede |
| `--aa-text-body` | 15/24 | 16/26 | 400 | Body |
| `--aa-text-small` | 13/20 | 14/22 | 400 | Card summary, meta |
| `--aa-text-kicker` | 12/16 | 12/16 | 600, UPPERCASE, 0.12em | Overlines, country label |
| `--aa-text-caption` | 12/16 | 12/16 | 400 | Map captions; the current 11 px goes up to 12 |

Satisfy is used only at 26 px or larger, never for body text, buttons, labels or long tour titles.

### 1.3 Spacing, layout and radius

- **Space scale (4 px base):** `--aa-space-1..10` = 4, 8, 12, 16, 24, 32, 48, 64, 96, 128.
- **Layout:**
  - `--aa-container: 1248px`;
  - `--aa-gutter: 16px` (<768), `24px` (768+);
  - `--aa-section-y: clamp(48px, 5vw + 28px, 96px)`, which gives 48 at 390 and 96 at 1440;
  - `--aa-header-h: 56px` (390), `68px` (≥1024).
- **Radius:** `--aa-radius-sm 6`, `md 10`, `lg 16`, `xl 24`, `pill 999`. Cards, map frames and tiles use `lg`. Full-bleed heroes and the photo ribbon use 0 (brand style).
- **z-index:** `--aa-z-sticky-cta 30`, `header 40`, `popover 50`, `toast 60`.

### 1.4 Shadow

| Token | Light | Dark |
|---|---|---|
| `--aa-shadow-sm` | `0 1px 2px rgba(31,41,51,.06), 0 2px 8px rgba(31,41,51,.07)` | `0 1px 2px rgba(0,0,0,.4), 0 2px 8px rgba(0,0,0,.35)` |
| `--aa-shadow-md` | `0 1px 2px rgba(31,41,51,.06), 0 6px 20px rgba(31,41,51,.10)` | `0 2px 4px rgba(0,0,0,.45), 0 8px 24px rgba(0,0,0,.4)` |
| `--aa-shadow-lg` | `0 12px 32px rgba(31,41,51,.16)` | `0 16px 40px rgba(0,0,0,.5)` |
| `--aa-shadow-pin` | `0 0 0 4px rgba(219,150,40,.28)` | `0 0 0 4px rgba(232,168,56,.30)` |

### 1.5 Motion tokens

- **Durations:**
  - `--aa-dur-fast 160ms`, `--aa-dur-base 240ms`, `--aa-dur-slow 400ms`;
  - `--aa-dur-reveal 560ms`, `--aa-dur-draw 1600ms`;
  - `--aa-dur-kenburns 4500ms`, which ends under the 5 s limit in WCAG 2.2.2.
- **Easings:**
  - `--aa-ease-std cubic-bezier(.4,0,.2,1)`;
  - `--aa-ease-out cubic-bezier(.2,.7,.2,1)`;
  - `--aa-ease-draw cubic-bezier(.65,0,.35,1)`;
  - `--aa-ease-pop cubic-bezier(.34,1.56,.64,1)` (a small overshoot, the "playful" part);
  - linear for the strip.
- **Strip speed:** `--aa-marquee-speed-sm 36px/s`, `--aa-marquee-speed-lg 48px/s`. The brand site runs at 57 and 95 px/s; ours is calmer. The CSS duration is worked out on the server (§3).
- `--aa-stagger 60ms`, with at most 6 items per group.

---

## 2. Motion

### 2.1 How it is switched on

- The existing inline restore script (`ui/restoreTheme.ts`) also sets `<html data-motion="ok">`, but only when `matchMedia('(prefers-reduced-motion: reduce)')` is false. It listens for `change` and removes the flag live.
- Every keyframe and transform transition is scoped under `[data-motion="ok"]`.
- Safety net: `@media (prefers-reduced-motion: reduce) { *, ::before, ::after { animation: none !important; transition-property: color, background-color, border-color, opacity, box-shadow !important } }`.
- With no JS, the flag is never set, so everything shows in its final, static state.
- Only `transform`, `opacity` and `stroke-dashoffset` are animated. Nothing animates layout.

### 2.2 Catalogue of animations

| # | Element | Trigger | Property | Duration / easing | Reduced-motion fallback |
|---|---|---|---|---|---|
| M1 | Home hero route draws itself | First paint, 300 ms delay (the hero is in view) | SVG `stroke-dashoffset` 1→0 (`pathLength="1"`) | 1600 ms, `ease-draw`, **once** | Line fully drawn |
| M2 | Hero pins appear | When the line reaches each pin: delay = the pin's share of the path × 1600 ms, worked out on the server | `transform: scale(0→1)`, `opacity 0→1` | 320 ms, `ease-pop` | Pins shown, no scale |
| M3 | Hero day steps (itinerary card) | Same delays as M2 | Day row background → `accent-tint`, 3 px gold left border | 240 ms `ease-std` | Every day row shown in its final state |
| M4 | "Replay route" button (hero) | Click | Restarts M1 to M3 (class toggle) | as M1 | Button hidden |
| M5 | Country highlight from a chip | Chip `:hover` / `:focus-visible` (CSS `:has()`, no JS) | Country fill → `map-land-hover` | 160 ms `ease-std` | Same: a colour change is not motion |
| M6 | Destination strip | In view (IntersectionObserver adds `data-running`) | Rail `translate3d(0→-50%)` | Server-computed (≈48 px/s at 1440, 36 at 390), linear, infinite | No animation. A swipeable row with scroll snapping and prev/next buttons |
| M7 | Photo ribbon (destination and tour pages, above the footer) | In view | Same as M6 | Same | Same as M6 |
| M8 | Section titles and card groups fade in | IntersectionObserver, once, 15% visible; only for elements **below the fold at load** | `opacity 0→1`, `translateY(12px→0)` | 560 ms `ease-out`, 60 ms stagger, at most 6 | Visible at once |
| M9 | Card hover/focus | `:hover` / `:focus-visible` | Card `translateY(-2px)` + `shadow-sm→md`; photo `scale(1→1.04)` | 240 ms `ease-std` (card), 400 ms `ease-out` (photo) | Shadow only |
| M10 | Route mark on a card | Card hover/focus | Mark `stroke-dashoffset 1→0` | 600 ms `ease-draw` | Drawn and static |
| M11 | "How it works" dotted connector | In view | `stroke-dashoffset` (dotted line drawn as a mask) | 1200 ms `ease-draw` | Static |
| M12 | Destination hero slow zoom (Ken Burns) | Image `load` (class added) | `scale(1→1.04)` | 4500 ms `ease-out`, once, `forwards` | None |
| M13 | Destination map pins drop in | In view | `translateY(-8px→0)`, `opacity` | 320 ms `ease-pop`, 40 ms stagger (25 pins at most, about 1 s) | Static |
| M14 | Place list ↔ map pin | List item hover/focus, or pin hover | Pin `scale(1→1.25)` + `shadow-pin` ring | 160 ms `ease-std` | Ring only, no scale |
| M15 | Tour route follows reading (scroll-spy) | The day section crosses the middle of the viewport | Route up to that day: `stroke-dashoffset` → that day's share of the line; pin *n* ring on | 400 ms `ease-out` | State changes at once (it is information, so it stays) |
| M16 | Header on scroll | Scroll-driven CSS (`animation-timeline: scroll()`); no JS, unsupported browsers keep the shadow-free header | `box-shadow` 0 → `shadow-sm` over the first 8 px | Linked to scroll | Same (not motion) |
| M17 | Primary button arrow | Hover/focus | Arrow icon `translateX(0→3px)` | 160 ms `ease-std` | No movement, colour change only |
| M18 | Theme switch | Toggle | Transitions **turned off** for one frame (`data-theme-switching`) so the page does not flash | — | — |

Rules:
- No auto-advancing hero or card carousels.
- No parallax.
- No animated number counters (they are noisy for screen readers).
- Never animate the element that is the page's largest paint (LCP).

---

## 3. The sliding strip component (`Ribbon`)

This is our version of the adventure.asia banner, built to the AA-995 bars. The markup is a Server Component; a client piece of about 1.5 KB gzip handles pause, the in-view check and prev/next.

### 3.1 Variants

| Variant | Where | Tile | Content |
|---|---|---|---|
| `destinations` | Home | 4:5, 220 px (1440) / 168 px (390), gap 16/12, radius `lg` | **Link** to `/destinations/<slug>`: photo + scrim, name (Poppins 600, 20/18, on-band), "12 tours · 5–14 days" (small, on-band-muted). No photo → **silhouette tile** (§3.5) |
| `photos` | Destination page ("From our tours in X"), tour page ("More from X") | Square, 240 px (1440) / 160 px (390), **no gap, no radius** (the brand ribbon) | `<img alt>` taken from the photo caption or place. Destination variant: tiles are not links. Tour "More from X" variant: tiles link to tours |

### 3.2 Markup

```
section[aria-labelledby=ribbon-h]
  header (container): h2.script "Where will you go?" · subline · [Pause] button · "All destinations →" link
  div.viewport  (full-bleed, overflow:hidden, mask-image edge fade 48px both sides)
    div.rail (display:flex; width:max-content)
      ul[role=list][aria-label="Destinations"]  → copy A (focusable)
      ul[aria-hidden=true][inert]               → copy B (duplicate, out of tab order and hidden from screen readers)
```

### 3.3 How it moves

- `@keyframes aa-marquee { to { transform: translate3d(-50%,0,0) } }` on `.rail`, `animation: aa-marquee var(--dur) linear infinite`.
- **The duration is worked out on the server.** The server knows the tile count *n* and each breakpoint's tile width plus gap, so `--dur-sm = n·(168+12)/36 s` and `--dur-lg = n·(220+16)/48 s` are written inline and a media query picks one. No JS measuring.
- **Fill rule:** if one copy is narrower than 2,400 px, the server repeats the item set inside copy A until it is wide enough (repeats are marked `aria-hidden` after the first set). Duplicate photo URLs are removed first, and the same photo is never placed next to itself.
- **Running:** `animation-play-state: paused` unless `[data-running]`. IntersectionObserver sets it when the strip is in view and clears it when it leaves the screen or the tab is hidden. `will-change: transform` is on only while running.
- **Pause sources:**
  - the button (`aria-pressed`, label "Pause moving destinations" / "Play moving destinations", 44×44 px, visible pause/play icon, the choice saved per viewer in `localStorage` key `tp_ribbon_paused` inside try/catch);
  - `:hover`.
- **Focus:** `:focus-within` switches the strip to **static mode** (`animation: none` + `overflow-x: auto` on the viewport), so the browser scrolls the focused tile into view. This avoids hiding focus (WCAG 2.4.11).

### 3.4 Static mode

Static mode applies under reduced motion, without JS, or on focus:
- `overflow-x: auto`, `scroll-snap-type: x mandatory`, tiles `scroll-snap-align: start`;
- `scroll-padding-inline: var(--aa-gutter)`;
- the scrollbar is hidden visually but swiping and the keyboard still work;
- copy B is `display: none`.

Prev/next round buttons (44 px, `aria-label="Previous destinations"` / `"Next destinations"`) appear at ≥768 px and scroll by 80% of the viewport (`scroll-behavior: smooth`, or `auto` under reduced motion). At 390 the row is swiped by touch. The page itself never overflows sideways; only the strip's own viewport scrolls.

### 3.5 Silhouette tile (no-photo fallback; 8 of 14 destinations today)

- Navy `--aa-band` background.
- The country outline in a 1.5 px gold line (from the same Natural Earth data as the hero map, §4.1), centred at 60% width.
- The country name in Satisfy 28 px `on-band`, and the tour count in small `on-band-muted`.
- It looks deliberate rather than broken, and it replaces the camera icon on every customer page (tour cards too: there, the route mark on navy).

---

## 4. Pages

Common frame on every page:
- **Header:** navy `--aa-band`, sticky, 56 / 68 px.
  - Contents: logo (switch to an SVG, `logo.png` is blurry at 32 px), links Destinations · Tours · Sign in in on-band 15 px 500, theme toggle, and a gold "Plan a trip" pill.
  - The "AI" pill moves to the footer, next to the "How we use AI" link.
  - At 390: logo, "Plan a trip" pill (small), and a menu button that opens a full-height sheet.
- **Footer:** navy, Satisfy column titles, a gold hairline at the top, links in `on-band-muted`, and Mapbox / Natural Earth credits.
- **Section rhythm:** bands alternate cream (`bg`) → white (`card`) → navy (`band`). Section titles are Satisfy and centred, with a one-line Poppins subline under them in muted grey (on-band-muted on navy).

### 4.1 Home

**Hero, the "living map" (navy band)**

Layout at 1440:
- 12-column container, gap 32, padding 64 top / 48 bottom, min-height 600 px (content-driven, not `vh`).
- **Left, columns 1–5:**
  - Satisfy kicker in gold: "Asia, off the usual path";
  - h1 (`display`, on-band): "Plan your Asia trip, day by day.";
  - lede (on-band-muted): "Pick the places, shape the days, and an Adventure Asia advisor checks every detail.";
  - the **plan card** (white `card`, radius `lg`, `shadow-lg`, padding 24):
    - "Where to" select;
    - days chips 5 / 7 / 10 / 14 (radio group);
    - travellers stepper;
    - full-width gold button "Start planning →" going to `/plan?dest=&days=&pax=`;
    - text link "or browse all tours".
- **Right, columns 6–12, bleeding to the right edge of the viewport:**
  - Inline SVG map of Asia, about 760×560, with `role="img"` and an aria-label that describes the route (example: "Map of Asia showing a 10-day route through Vietnam: Hanoi, Ha Long Bay, Hue, Hoi An").
  - **Route:** one real featured itinerary. The first featured tour with 3 or more exact pins, fetched on the server at ISR time and projected into the map's coordinates. Fallback: a curved gold line hopping between 3 countries that have tours.
  - **Itinerary card:** a floating `band-2` card at the top right of the map, listing up to 4 rows ("Day 1 · Hanoi"…), lit in turn by M3.
  - **Postcard:** a floating card at the bottom left of the map. Photo 240×160 (radius `md`), the tour title in h3, and "View itinerary →".
  - A small "Replay route" text button sits at the bottom right of the map (M4).
- **Chips row** across the bottom of the hero, full container width:
  - "Where to?" label, then destination chips (`band-2`, on-band, 40 px tall; 44 px touch area);
  - hover or focus on a chip lights up that country on the map (M5, CSS only);
  - each chip links to its destination page.

At 390:
- Padding 32/16.
- Order: kicker (26 px) → h1 32/38 → lede → plan card full width → chips row (scrolls sideways inside its own container) → map full-bleed at 4:3 (the route draws when it scrolls into view, since it starts below the fold) → postcard overlapping the bottom of the map by 24 px.
- The itinerary card is hidden; its days show in the postcard as "Hanoi → Ha Long → Hoi An".

Largest paint (LCP): the h1 text at both sizes.

**Proof line (cream, about 120 px)**
- Centred: "**N tours** · **14 countries** · every trip checked by an advisor".
- The numbers are gold-deep Poppins 600, counted from the catalog on the server.
- At 390 it breaks into 3 stacked lines.

**"Where will you go?" (white): the destination strip** (`Ribbon` variant `destinations`, §3)
- About 14 destinations. Those with photos and those without are mixed so that no two silhouette tiles sit next to each other.
- "All destinations →" link.

**"Featured tours" (cream)**
- 1440: 3 columns, gap 24. 768: 2 columns. 390: a sideways scroller at 85% card width, gap 12, snap start, no autoplay, then a "See all tours" button.
- Card:
  - radius `lg`, border `line`, `shadow-sm`; M9 on hover;
  - photo at 3:2 with a day pill at the top left (`band` background, on-band 12/16 600: "10 DAYS");
  - optional **route mark** at the bottom right: a 56 px cream disc with a mini SVG of the tour's pin order (M10), only when route points are in the payload;
  - body: kicker country (accent-deep), h3 title (2-line clamp), meta row (icons: days · places · activity icons from `ActivityIcon`), summary on 2 lines in small muted text, a hairline, then "View itinerary →" (accent-deep, M17);
  - the whole card is one link with `prefetch={false}` (AA-833);
  - no price (ADR 0005);
  - the same cover photo is never shown next to itself; if two tours share a cover, the second uses its next photo, otherwise the route-mark navy tile.

**"How it works" (white)**
- Three steps with the brand's illustrated icons (`plan-color`, `map-color`, `direction-color`, 72 px): "Pick places" / "Shape your days" / "An advisor checks it".
- A gold dotted connector between the steps (M11): horizontal at 1440, vertical at 390.

**CTA band (navy)**
- Satisfy gold: "Your Asia, day by day."
- One line of on-band-muted text, a gold "Start planning" pill, and an outline cream "Browse tours" pill.
- Then the footer.

### 4.2 Destination `/destinations/<slug>`

**Hero (full-bleed photo)**
- Height 560 at 1440, 440 at 390. `hero-bg` navy underneath, so the white text is readable before the photo loads.
- Photo:
  - a curated cover, served at its resolved image URL (§6), with `fetchpriority="high"`, `loading="eager"`, width and height set, and `srcset` 600w/1600w with `sizes="100vw"`;
  - `scrim-bottom` gradient; M12 slow zoom.
- Bottom-left text:
  - breadcrumb (on-band-muted 13);
  - h1 `--aa-text-place`, UPPERCASE, on-band: "VIETNAM";
  - Satisfy gold tagline when one exists, otherwise "Discover {Country}";
  - chips: "12 tours · 5–14 days";
  - CTAs: gold "Plan a trip to Vietnam" and an outline cream "See tours".
- At 390 the CTAs stack at full width.
- No photo: a navy hero with the country silhouette drawn as a large gold line (M1 style, once).

**"Places our tours visit" (cream)**
- 1440: map in 7 columns + numbered list in 5 columns (the list scrolls inside a box as tall as the map).
- 390: map full width at 4:3, list below.
- **Map:**
  - The static Mapbox basemap (light-v11 / dark-v11 swapped by `data-theme`; only the visible `<img>` loads, because both are lazy and the hidden one is `display:none`).
  - Pins and any route move out of the Mapbox URL into an **SVG layer that lines up exactly with the image**: `lib/staticMap.ts` computes the centre and fractional zoom itself instead of `auto`, and the same Web-Mercator maths (512 px tiles, @2x) places the pins.
  - Pins: navy body, cream number, gold ring; M13 when in view, M14 linked to the list.
  - Rivers, roads and trails stay in the Mapbox overlay.
  - The caption stays (12 px).
- **List rows:** a number disc that matches the pin, the place name (body 500), "in 4 tours" (small muted), and a 56 px thumbnail (the silhouette when there is no photo).

**"Tours in Vietnam" (white)**
- Same card as on home. Grid of 3 / 2 / 1 columns; at 390 the cards stack, since this is the page's main content.

**"From our tours in Vietnam"**
- `Ribbon` variant `photos`, full-bleed. Shown only when there are 6 or more unique photos; otherwise a static grid.

**CTA band:** "Ready to shape your Vietnam trip?", then "Start planning".

### 4.3 Tour `/tours/<slug>`

**Gallery hero**
- 1440: a mosaic of one large photo (8 columns) and two stacked (4 columns), 480 px tall, radius `lg`, inside the container, with a "View all N photos" button that opens a native `<dialog>` lightbox.
- 390: full-bleed sideways snap row, 1 photo per view at 4:3, a "1 / 6" counter pill, no autoplay.
- The first photo is the LCP image: resolved URL, `fetchpriority=high`, eager.

**Title block**
- Badges: country, N days, the AI labels (kept as they are).
- h1 in Poppins `--aa-text-h1` (long titles; Satisfy is not legible enough for them).
- Meta row with icons.

**Body**
- 1440: main area in 8 columns + an aside in 4 columns that sticks at `top: header-h + 20`. 390: one column.
- Main sections, in order: Highlights (2-column check list) → **"Day by day"** (Satisfy title) → Included / Not included (2 columns, 1 at 390) → AI disclosure.
- **Day by day is a timeline:**
  - a 2 px dotted vertical line in `accent-border`;
  - 40 px day discs (navy with a cream number, gold ring when active) that match the map pins;
  - each day stays a native `<details>` with the summary "Day 3 · Hoi An" plus its places; day 1 opens by default.
- **Aside, the "Your route" card:**
  - map at 4:3 with the SVG route layer;
  - a live legend: "Day 3 of 10 · Hoi An";
  - gold "Plan this trip" and outline "Ask an advisor" buttons.
  - Scroll-spy (M15): IntersectionObserver on the day sections moves the gold line forward and rings the current pin. Opening a day also sets the active pin.
- **390:**
  - The "Your route" card is placed inline after Highlights and does not stick. Scroll-spy still runs when the map is in view.
  - The existing sticky bottom CTA bar becomes navy: 64 px, padding for the phone's safe area, a gold "Plan this trip" button and a ghost "Ask".

**"More from Vietnam"**
- `Ribbon` variant `photos` using covers of other tours in the country, with linked tiles. Falls back to the `destinations` variant when there are fewer than 6.

**CTA band, then the footer.**

### 4.4 `/plan` (light touch in this issue)

- Header becomes navy, the font becomes Poppins, and the tagline "Discreet executive adventures…" is retired in favour of "Your Asia trip, day by day".
- The MapView route uses `--aa-route` / `--aa-route-casing`.
- Optional later slice: when a stop is added, animate mapbox-gl `line-trim-offset` (needs `lineMetrics`) once, for 600 ms, and skip it under reduced motion.

---

## 5. Accessibility

- **WCAG 2.2.2 (pause, stop, hide):** the strip has a visible pause button and also pauses on hover and focus. The hero animation and the slow zoom finish in under 5 s. There are no other auto-moving items.
- **Reduced motion:** the `data-motion` flag together with the media query safety net (§2.1). Everything is checked by screenshots taken under `reducedMotion: 'reduce'`.
- **Keyboard:**
  - the strip's copy A is tabbable, and copy B is `inert`;
  - focusing a tile switches the strip to static mode, so focus stays visible;
  - chips, cards and pins are reachable through their links or list rows (the SVG pins are `aria-hidden`; the numbered list and day timeline are what screen readers and keyboards use);
  - the gallery dialog traps focus and Esc closes it.
- **Labels:**
  - each strip is a `section` named by its heading, and the list is labelled;
  - every `img` has an `alt` (decorative scrims and silhouettes use `alt=""`);
  - the hero map is `role="img"` and its label describes the route;
  - static maps keep "Map: {title}";
  - the pause button uses `aria-pressed` and a label that changes with its state.
- **Focus:** a 2 px `accent` outline with 2 px offset on light surfaces, and `--aa-focus-on-band` on navy. Never removed.
- **Contrast:**
  - every new text pair goes into `contrast.test.ts` and must reach at least 4.5:1, or 3:1 for text ≥ 24 px and Satisfy titles;
  - the route line and pins must reach 3:1 against the land they sit on (WCAG 1.4.11): `--aa-route` on the light basemap and `--aa-route-on-band` on the navy map were chosen for this;
  - text on photos always sits on `scrim-bottom` or the navy `hero-bg`.
- **Touch targets:** at least 44×44 px (chips, pause, prev/next, CTA bar).
- **Screen-reader noise:** the scroll-spy and the hero day steps are visual only, with no `aria-live`. Any repeated item sets after the first are `aria-hidden`.
- **Language:** English by default (`lang="en"`). Satisfy has latin glyphs only (see R7).

---

## 6. Performance plan

| Item | Plan |
|---|---|
| **The 302 hop on photos** (this blocks LCP) | Slice 0. Preferred: the CIS catalog returns final image URLs plus size variants. Fallback that needs only TripPlanner: `resolvePhotoUrl()` on the server at ISR time (`fetch(…, { redirect: 'manual' })`, read `Location`, cached with the page for 1,800 s). This applies to every image above the fold and to all strip images. |
| Preconnect | `<link rel="preconnect" crossorigin>` to the image host (from config) in `app/layout.tsx`. Mapbox gets `dns-prefetch` only, since its maps are below the fold. |
| LCP images | Destination hero and tour gallery photo 1: `fetchpriority="high"`, `loading="eager"`, width/height set, `srcset` 600w + 1600w. Ask CIS for a ~1000w variant (about 90 KB), so phones do not pull 193 KB. Home: the LCP is the h1 text; the postcard image is 600w and eager. |
| Images below the fold | `loading="lazy"`, `decoding="async"`, aspect-ratio boxes. Strip tiles use the 600w variant today; ask CIS for a 300w thumbnail. |
| Hero map | Inline SVG, made by `tools/gen-asia-map.mjs` from Natural Earth 1:50m (public domain), simplified with mapshaper, cropped to longitude 60–150°E and latitude −12–45°N, Web Mercator. Budget **≤ 20 KB raw / ≤ 8 KB gzip**, home page only. The same script outputs each country's silhouette path (≤ 1.5 KB each) for the fallback tiles. |
| Static maps | The centre and zoom are calculated in the code instead of `auto`. Pins and route move to SVG, so the URLs get shorter. Lazy-loaded, below the fold, 800×480@2x. |
| Fonts | Poppins 400/500/600 + Satisfy, latin subset, preloaded by `next/font`. **Fahkwang and Inter removed**, so fewer font files than today. `adjustFontFallback` on. |
| JS | **No new dependencies.** Client pieces: `MotionReveal` (~1 KB), `RibbonControls` (~1.5 KB), `RouteSpy` (~1.5 KB), `ReplayRoute` (<0.5 KB). Country highlighting and the header shadow are CSS only (`:has()` and scroll-driven animation). Budget: **≤ 5 KB gzip of client JS added per page.** |
| CLS | All heights reserved (aspect boxes, fixed header, hero min-height). Fade-ins use transform and opacity only. Satisfy titles are kept short with a reserved line box. No content is inserted above content already on screen. Target **≤ 0.02**. |
| Off-screen work | IntersectionObserver pauses strips off screen. `will-change` only while running. |
| Prefetch | `prefetch={false}` on every card and strip link (AA-833). The strip alone has about 28 links. |
| Targets | Lighthouse mobile ≥ 90 on home, ≥ 85 on destination and tour pages. LCP ≤ 2.0 s on home, ≤ 2.5 s on destination and tour. TBT ≤ 150 ms. 0 console errors. No page-level horizontal overflow at 390 or 1440. |
| Verification within the Vercel load budget | Run Lighthouse and the 390/1440 × light/dark × reduced-motion screenshots in GitHub Actions (the AA-994 screenshot job), not from this machine. Locally, keep to at most about 40 page loads per session. |

---

## 7. Build order (each slice is one PR)

1. **S0:** photo URL resolution and preconnect, then measure LCP on the destination and tour pages.
2. **S1:**
   - tokens (all groups) and the Tailwind mapping;
   - font swap (Poppins + Satisfy; Fahkwang and Inter removed from site pages);
   - the `data-motion` flag and safety net;
   - navy header and footer;
   - the new guard tests.
3. **S2:** `Ribbon` and silhouette tiles: the home destination strip, plus the photo ribbons on the destination and tour pages.
4. **S3:** the home "living map" hero (map generator script, route projection, M1–M5, chips, postcard) and the section rhythm.
5. **S4:** the SVG layer on the static map (centre and zoom maths, pins, M13/M14) and the destination page layout.
6. **S5:** tour page: gallery, timeline, "Your route" card with scroll-spy (M15), navy CTA bar.
7. **S6:** `/plan` header, font and route colours (Poppins pass across the planner panels).

---

## 8. Risks

| # | Risk | Effect | Mitigation |
|---|---|---|---|
| R1 | The photo 302 stays (about 1.4 s through API Gateway) | Destination and tour heroes miss LCP ≤ 2.5 s | S0 resolves URLs on the server at ISR time. The longer-term fix is final URLs from the CIS catalog (a CIS change, separate issue) |
| R2 | 8 of 14 destinations have no photo, and covers are repeated | The strip and grids look thin or repetitive | Silhouette tiles; duplicates removed and never adjacent. Real fix: more CIS cover photos (data issue) |
| R3 | The SVG layer does not line up with the Mapbox image | Pins land off target | Never use `auto`. Our own centre and zoom (512 px tiles, @2x) with a unit test against a fixture with known pixel positions, and a visual check in the build. Accepted error ≤ 2 px |
| R4 | Mapbox terms | Storing static images is not allowed | Live Mapbox URLs only. The hero uses Natural Earth (public domain), credited in the footer |
| R5 | Too much motion for a B2C brand whose own motion is restrained | Feels gimmicky or tiring | Only one endless animation per page, the hero plays once, everything can be turned off, and no count-ups or parallax |
| R6 | Font swap reflows Satisfy titles | Layout shift at 390 | Titles of ~22 characters at most, reserved line box, `adjustFontFallback`; CLS checked in CI |
| R7 | Satisfy covers latin only | A future Vietnamese UI would show diacritics in a fallback font | Pages are English by default. If a Vietnamese UI ships, script titles fall back to Poppins 600 under `:lang(vi)` |
| R8 | The featured itinerary used for the hero changes or has too few exact pins | Weak or broken hero route | Pick the first tour with ≥ 3 exact pins; otherwise the curved line between countries. The route is computed at ISR time, so it never fails at request time |
| R9 | Poppins is wider than Inter in the dense planner panels | Text wraps or overflows in `/plan` | Kept in its own slice (S6) with screenshots of the planner at 390 and 1440 |
| R10 | AA-994 shared token names may differ | Rework when switching to the shared set | `--aa-*` names that follow the CIS kit prefix, one file, Tailwind reads only CSS variables; the switch is a file swap |
| R11 | `:has()` and scroll-driven animations not supported in an older browser | Lost chip highlight or header shadow | Both are extras only; the content works without them |
| R12 | Vercel's bot challenge (403) | Too few preview loads to verify | Lighthouse and screenshots run in GitHub Actions; local Playwright limited to a few loads |
| R13 | More inline HTML on home (map + doubled strip) | Heavier HTML | Map ≤ 8 KB gzip; strip tiles are light markup; home HTML budget +25 KB gzip at most |