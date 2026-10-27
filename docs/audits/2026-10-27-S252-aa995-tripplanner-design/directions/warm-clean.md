# AA-995: TripPlanner customer pages, design spec ("Golden Hour" direction)

Direction: warm, clean and trustworthy, built to convert. It keeps the Adventure Asia brand (navy `#1F2933`, gold `#DB9628`, cream `#F8F6F2`, Poppins, the Satisfy script for section titles, full-bleed photos) and softens it: more white space, rounded cards, a sand-coloured section surface and gentle motion. Each page has at most one element that moves by itself: the brand's sideways photo ribbon, rebuilt accessibly.

Sources: `docs/audits/2026-10-27-S252-aa995-tripplanner-design/research.md`, the TripPlanner code (`frontend/app/{page,destinations,tours}`, `ui/tokens.css`, `lib/catalogTypes.ts`, `backend/browse/catalog.py`) and the AA-994 ADR draft (`docs/audits/2026-10-27-S252-aa994-design-system/adr-draft.md`). This is a spec only: nothing was committed.

---

## 0. Principles

1. **Photo first, words second.** Every page opens on a real AA photo. A missing photo gets a designed placeholder, never the camera icon.
2. **One clear next step per screen.** "Plan my trip" / "Customise this trip" is the gold primary button; "Ask an advisor" is the secondary. They are on screen at both 390 and 1440.
3. **The script is for titles only.** Satisfy is used only for section titles (≥ 28 px, ≤ 6 words) and big numerals. Poppins is used for everything else. Inter and Fahkwang are dropped.
4. **Surfaces alternate:** cream → white → sand → navy band → photo ribbon → navy footer.
5. **Motion is calm.** Only transform and opacity are animated, plus colour. One auto-moving element per page. Everything is off under `prefers-reduced-motion`, and also when there is no JS.

---

## 1. Tokens: one file, `frontend/ui/tokens.css`

**Naming follows AA-994 / ADR 0016 §3–4:**
- Generic scales use `--aa-*`. Radius, space, type, shadow and motion are proposed for AA-994 slice 1 ("token chung") so they become core tokens.
- B2C-only surfaces use `--tp-*`. These are the sand surface, navy band, ribbon and script.
- Until `ui/core/tokens.css` exists, both blocks live in `ui/tokens.css`. Once core lands, the `--aa-*` block is deleted from it and nothing else changes.
- Tailwind 3 maps every token, for example:
  - `fontSize.display` → `var(--aa-text-display)`
  - `borderRadius.card` → `var(--aa-radius-lg)`
  - `boxShadow.md`
  - `transitionTimingFunction.out`
  - `transitionDuration.base`
  - `fontFamily.script`
- After that, inline `text-[13px]`, `rounded-2xl`, `duration-300` and raw `rgba()` shadows are banned (extend the `lib/contrast.test.ts` ban list).

### 1.1 Colour (light / dark). Contrast was computed, WCAG 2.x

| Token | Light | Dark | Use | Contrast check |
|---|---|---|---|---|
| `--aa-accent` | `#DB9628` | `#E8A838` | Primary fill, icons, active marks | Text on it is `--aa-on-accent #1A1206` (7.42:1) |
| `--aa-accent-deep` | `#875D12` | `#F0C070` | Gold text and links | 5.40 on cream, 5.00 on sand, 5.28 on tint |
| `--aa-accent-tint` | `#FBF3E3` | `#332814` | Chip/selected bg, day-number circles | — |
| `--aa-accent-border` | `#DDA64E` | `#6B531F` | Outline buttons, dividers | — |
| `--aa-ink` | `#1F2933` | `#EAEEF4` | Headings | 13.67 on cream |
| `--aa-body` | `#33363D` | `#D4DAE2` | Body | 10.39 on sand |
| `--aa-muted` | **`#5A6270`** (was `#656D7A`) | `#9099A6` | Secondary text | **Change required.** The old value is 4.48 on sand and fails; the new one is 5.28 on sand and 5.70 on cream. It is also the CIS AA-760 value, which removes the drift |
| `--aa-bg` | `#F8F6F2` | `#0F141B` | Page / cream surface | — |
| `--aa-card` | `#FFFFFF` | `#19212C` | Cards, white bands | — |
| `--aa-line` | `#E9E4DB` | `#2A3542` | Hairlines, card borders | — |
| `--aa-scrim` | `rgba(15,20,27,.55)` | `rgba(5,8,12,.62)` | Under text on photos (see note) | — |
| `--aa-hero-bg` | `#1F2933` | `#19212C` | Shown behind the hero while the photo loads | — |
| **`--tp-surface-sand`** (new) | `#F3EDE3` | `#151C25` | Alternate band (destinations, places) | Body 10.39 / muted 5.28 |
| **`--tp-band`** (new) | `#1F2933` | `#0A0E13` | Navy CTA band, header (solid state), footer | — |
| **`--tp-on-band`** (new) | `#F8F6F2` | `#EAEEF4` | Text on navy | 13.67 |
| **`--tp-on-band-muted`** (new) | `#C8D6E5` | `#B8C0CC` | Secondary text and links on navy | 9.98 |
| **`--tp-band-accent`** (new) | `#E8B865` | `#E8A838` | Satisfy titles and numerals on navy, focus ring on navy | 8.06 |
| **`--tp-hero-gradient`** (new) | `linear-gradient(180deg, rgba(15,20,27,.45) 0, rgba(15,20,27,0) 120px, rgba(15,20,27,0) 40%, rgba(15,20,27,.70) 100%)` | same, `.80` at the bottom | Top: header legibility. Bottom: hero text | — |

Notes:
- **Text on a photo** always sits where the gradient is ≥ 0.55 opacity. 55 % black over pure white gives about `#737373`, which is about 4.7:1 for white text. That makes AA safe on any photo. Add `text-shadow: 0 1px 2px rgba(0,0,0,.35)` as a second guard.
- **Dark mode:** the navy band (`#0A0E13`) is close to the dark page bg (`#0F141B`), so bands get a 1 px `--aa-line` top and bottom border in dark mode.
- **White on gold is never allowed.** Gold buttons keep dark text, as today.
- **`lib/contrast.test.ts` gains these pairs:**
  - body/muted/accent-deep on sand;
  - on-band/on-band-muted/band-accent on band;
  - both themes for every pair.

### 1.2 Typography

Families:

| Token | Value | Use |
|---|---|---|
| `--aa-font-sans` | `var(--font-poppins), system-ui, -apple-system, "Segoe UI", sans-serif` | Body, UI, cards, headings h1/h3 |
| `--tp-font-script` | `var(--font-satisfy), "Poppins", cursive` | h2 section titles, big numerals, the hero kicker |

Loading:
- Poppins 400/500/600. Drop 700 unless a real use is found.
- Satisfy 400, latin subset, `preload: true`, `display: "optional"`. Swapping a large script on screen would shift layout; with `optional` a slow first view simply keeps Poppins, with no layout shift.
- Remove Inter (the `/plan` planner moves to Poppins) and Fahkwang. `--aa-font-display` points to sans until AA-994 decides on a display font.
- Raise to AA-994: the CIS kit's "Fahkwang headings" assumption is wrong (research §1.4).

Scale. All are fluid between 390 and 1440 (clamp is linear on vw; values checked at both widths):

| Token | 390 → 1440 | clamp() | Weight / line-height / tracking | Use |
|---|---|---|---|---|
| `--aa-text-display` | 32 → 52 | `clamp(2rem, 1.4rem + 2.6vw, 3.25rem)` | Poppins 600 / 1.1 / -0.015em | Home hero h1 |
| `--aa-text-h1` | 28 → 40 | `clamp(1.75rem, 1.35rem + 1.7vw, 2.5rem)` | 600 / 1.15 / -0.01em | Tour h1. Destination h1 is UPPERCASE with +0.08em tracking |
| `--tp-text-script` | 36 → 48 | `clamp(2.25rem, 1.9rem + 1.5vw, 3rem)` | Satisfy 400 / 1.05 / 0 | Section h2, centred |
| `--tp-text-script-sm` | 28 → 40 | `clamp(1.75rem, 1.45rem + 1.2vw, 2.5rem)` | Satisfy 400 / 1.1 | Hero kicker, CTA card heading |
| `--aa-text-h3` | 18 → 20 | `clamp(1.125rem, 1.08rem + .2vw, 1.25rem)` | 600 / 1.3 | Card titles, sub-heads |
| `--aa-text-lead` | 17 → 18 | — | 400 / 1.6 | Hero lede, section intros |
| `--aa-text-body` | 16 | — | 400 / 1.65 | Body (up from 13–15 px today: friendlier, easier to read) |
| `--aa-text-small` | 14 | — | 400 / 1.55 | Card summaries, meta |
| `--aa-text-caption` | 13 | — | 500 / 1.4 | Chips, photo credits |
| `--aa-text-kicker` | 12 | — | 600 / 1.2 / 0.16em, UPPERCASE | Country kicker on cards, eyebrow labels |

### 1.3 Radius, shadow, space, layout, z-index

| Token | Value |
|---|---|
| `--aa-radius-sm` | 6px (badges, small chips) |
| `--aa-radius-md` | 12px (inputs, thumbs, ribbon tiles) |
| `--aa-radius-lg` | 16px (cards, destination tiles, map card) |
| `--aa-radius-xl` | 24px (hero search card, gallery outer corners) |
| `--aa-radius-pill` | 999px (buttons, chips) |
| `--aa-shadow-sm` | `0 1px 2px rgba(31,41,51,.06), 0 1px 1px rgba(31,41,51,.04)` |
| `--aa-shadow-md` | `0 6px 16px -4px rgba(31,41,51,.10), 0 2px 4px rgba(31,41,51,.06)` (card hover) |
| `--aa-shadow-lg` | `0 18px 40px -12px rgba(31,41,51,.22)` (search card, sticky CTA card) |
| Dark shadows | Same geometry at `rgba(0,0,0,.45)`, always paired with a `--aa-line` border |
| `--aa-space-1…10` | 4, 8, 12, 16, 20, 24, 32, 48, 64, 96 px |
| `--tp-section-y` | `clamp(3rem, 2rem + 4vw, 6rem)` → 48 px at 390, ≈ 90 px at 1440 |
| `--tp-container` | 1248px. Gutter `--tp-gutter`: 16px (< 768), 32px (≥ 768) |
| `--tp-header-h` | 56px (< 1024), 64px (≥ 1024) |
| z-index | `--aa-z-header: 30`, `--aa-z-sticky-cta: 40`, `--aa-z-popover: 50` |

### 1.4 Motion tokens

| Token | Value |
|---|---|
| `--aa-dur-instant` | 100ms |
| `--aa-dur-fast` | 160ms |
| `--aa-dur-base` | 240ms |
| `--aa-dur-slow` | 420ms |
| `--aa-dur-reveal` | 560ms |
| `--aa-ease-std` | `cubic-bezier(.4,0,.2,1)` (colour/state) |
| `--aa-ease-out` | `cubic-bezier(.22,.61,.36,1)` (entrances, lifts) |
| `--aa-ease-in` | `cubic-bezier(.4,0,1,1)` (exits) |
| `--tp-kenburns-dur` | 16s |
| `--tp-ribbon-s-per-tile` | 4.15s (< 768: tile 160 + gap 6 at 40 px/s), 4.96s (≥ 768: tile 240 + gap 8 at 50 px/s) |
| `--tp-stagger` | 60ms |

**Motion gate.** The existing inline restore script (`ui/restoreTheme.ts`, runs before paint) also sets `<html data-motion="ok|reduce">`:
- the value comes from `matchMedia('(prefers-reduced-motion: reduce)')`, with a live `change` listener;
- optionally a footer "Reduce motion" toggle stored in `localStorage` key `tp_motion` (wrapped in try/catch, as `tp_theme` is).

Every keyframe animation is declared only under `html[data-motion="ok"]`. Under `reduce`, all `--aa-dur-*` become `0.01ms`. Without JS there is no `data-motion`, so the page is static and fully visible.

---

## 2. Motion language

| # | Element | Trigger | Property | Duration / easing | Reduced-motion fallback |
|---|---|---|---|---|---|
| M1 | Buttons, links, chips | hover / focus / press | bg, border, colour; press: `translateY(1px)` | fast, std; press instant | Colour change only, no translate |
| M2 | Text-link underline (e.g. "Explore trip →") | hover / focus | `background-size` 0 → 100 % gold underline; arrow `translateX(4px)` | base, out | Underline shown at once, no arrow move |
| M3 | Card lift (tour card, destination tile) | hover, only `@media (hover:hover) and (pointer:fine)` | card `translateY(-4px)` + shadow sm → md; image `scale(1.04)` | card base/out; image slow/out | Shadow change only |
| M4 | Header state | IO sentinel at the hero's bottom edge leaves view | bg transparent → `--tp-band`, shadow none → sm | base, std | Same change, instant |
| M5 | Hero Ken Burns | Hero image `load` (class added; never delays paint) | `transform: scale(1) → scale(1.05)`, once, `forwards` | 16s, out | None, image static |
| M6 | Scroll reveal (section titles, card groups) | IO, threshold 0.15, rootMargin `0 0 -10% 0`, fires once | opacity 0 → 1, `translateY(16px) → 0`; stagger 60 ms, max 6 children | reveal, out | Visible, no animation |
| M7 | Featured carousel step | Prev / next button | Native `scrollBy({behavior:'smooth'})`, scroll-snap `x mandatory` | Browser smooth scroll | `behavior:'auto'` (jump) |
| M8 | Carousel progress dot | Active slide changes (IO on slides) | Active dot `scaleX(1) → scaleX(2.5)` (8 → 20 px, a nod to the brand), colour line → gold | base, std | Instant |
| M9 | Photo ribbon | In view (IO) and not paused | Track `translate3d(0,0,0) → translate3d(-50%,0,0)`, linear, infinite. Duration = `calc(var(--tp-ribbon-count) * var(--tp-ribbon-s-per-tile))` | ≈ 40 px/s at 390, 50 px/s at 1440 | No animation; a static row the user can swipe (see §3.6) |
| M10 | Search duration chips | Select | bg/border colour; check icon `scale(.8 → 1)` + opacity | fast, out | Colour only |
| M11 | Day-by-day accordion | `<details>` toggle | Chevron `rotate(180deg)`; body height through `::details-content` + `interpolate-size: allow-keywords` where supported (progressive) | base, std | Instant open / close |
| M12 | Focus ring | `:focus-visible` | None (2 px solid ring) | — | — |

**Rules:**
- Never animate layout properties (width, height, top, margin).
- No entrance animation on hero content or anything in the first viewport. Elements at opacity 0 delay LCP, and the hero h1 or image is the LCP. Reveals (M6) are added on the server only to sections after the first.
- No autoplay anywhere except the ribbon.
- No parallax and no scroll-jacking.

---

## 3. Shared components

### 3.1 Header (`SiteHeader`)

- Height `--tp-header-h`.
- **Over a photo hero** (home, destination): transparent, with the top part of `--tp-hero-gradient` behind it and white text. It turns `--tp-band` solid after the hero (M4). **On the tour page:** solid `--tp-band` from the start.
- **Left:** the logo. The PNG is all gold and reads at 5.9:1 on navy. Plan an SVG trace later for sharpness at 32–36 px. Next to it the AI label (AA-805/819 disclosure, **must stay visible**), restyled as a ghost chip: `--tp-on-band-muted` text, 1 px `rgba(255,255,255,.28)` border.
- **Right:**
  - 1440: "Destinations", "Tours", "How it works" (Poppins 500, 15 px, `--tp-on-band`; hover goes gold-light), then the account link, the theme toggle and the "Plan a trip" primary pill.
  - 390: logo, the "AA AI" chip, the theme toggle and a "Plan a trip" small pill. Nav links stay hidden, as today: no hamburger, sections are reachable on the page.
- Focus ring on navy: `--tp-band-accent`.

### 3.2 Hero

- Full-bleed photo with `--aa-hero-bg` underneath and `--tp-hero-gradient` on top.
- Content is anchored bottom-left inside the container.
- The photo is chosen per page (§4). Each curated image carries an `object-position` focal point.

### 3.3 Section title

- Centred Satisfy h2 (`--tp-text-script`, `--aa-ink`; `--tp-band-accent` on navy).
- Optional 1-line Poppins lead under it (`--aa-text-lead`, muted, max 56ch).
- A 40 × 2 px gold rule, 16 px below.
- Optional "See all →" link (M2): right-aligned in the title row at 1440, under the lead at 390.

### 3.4 Tour card (`TourCard`)

Structure:
- **Shell:** `--aa-card` bg, 1 px `--aa-line` border, `--aa-radius-lg`, `--aa-shadow-sm`, full height (flex column, footer pinned with `mt-auto`). The whole card is one link, with `prefetch={false}` (AA-833).
- **Photo:** 4:3, top corners rounded, small variant (600 w), `loading=lazy`, except the first visible 3 on desktop / 1 on mobile, which are `eager`.
- **On the photo:**
  - duration pill, top left: "8 days", `--aa-scrim` bg, white, caption size;
  - when `cover_source ≠ "tour"`, a caption bottom left: "Photo: {cover_place}" (required by AA-812 D4/D5).
- **Body,** 20 px padding:
  - country kicker (`--aa-text-kicker`, accent-deep);
  - title (`--aa-text-h3`, 2-line clamp);
  - summary (small, muted, 2-line clamp);
  - meta row with icons: "Best Oct–Apr" (when `best_time_to_go` is set) and the number of highlights.
- **Footer:** hairline, then "Explore trip →" (accent-deep, M2).
- **Hover:** M3.
- **Duplicate covers:** if a cover URL already appeared earlier in the same list, the card shows the **no-photo tile** (§3.5) in the photo slot rather than repeating the picture. Fixes for the Bhutan and Sri Lanka repeats.

### 3.5 No-photo tile

- Used wherever a photo is missing.
- `--tp-band` bg with the logo's mountain lines as an inline SVG: gold at 18 % opacity, bottom-right, 60 % of the tile width.
- The country (or place) name in Satisfy (`--tp-band-accent`, 30–40 px), plus a Poppins caption on `--tp-on-band-muted` ("{n} tours").
- Never the bare camera icon on customer pages.

### 3.6 Photo ribbon (`PhotoRibbon`): the brand's sideways banner, done right

**Markup:**
- `<section aria-labelledby>` holding a header row and a viewport.
- **Header row,** inside the container:
  - Satisfy title, sm size: "From our trips" or "Around {country}";
  - to its right, a 44 × 44 round **pause/play button** (outline, `--aa-accent-border`). Its label switches between "Pause moving photos" and "Play moving photos", and it shows a pause/play icon.
- **Viewport:** full-bleed, `overflow:hidden`, `contain: layout paint`.
- **Track:** `display:flex; width:max-content; gap:var(--gap)`.
  - Copy A is a `<ul aria-label="Photos from our trips">`.
  - Copy B is identical with `aria-hidden="true"` and `inert`, so it is out of the tab order and out of the a11y tree.

**Tiles:**
- Square, 160 px with a 6 px gap below 768 px, 240 px with an 8 px gap at 768 px and up. `--aa-radius-md`.
- Each tile is a link to its destination or tour, and its image has a real `alt` (place label or tour title).
- A caption chip shows on hover and focus (`--aa-scrim`, white, caption size: "Punakha · Bhutan"). It fades in with opacity at fast speed; under reduced motion it is always visible.

**Motion (M9):**
- runs only when `html[data-motion=ok]`, the section is in view and it is not paused;
- `animation-play-state: paused` on `:hover`, on `:focus-within`, on `[data-paused]` (button) and on `[data-offscreen]` (IO);
- `will-change: transform` only while running.

**Reduced motion / no JS:**
- the track gets `overflow-x:auto; scroll-snap-type:x mandatory`;
- copy B and the pause button are hidden;
- tiles snap to the start;
- the scroll is inside the section, so the page never overflows horizontally.

**Content rules (server-side):**
- dedupe by photo id or URL; skip null URLs;
- ≥ 8 unique photos: animate;
- 4–7: static swipe row;
- < 4: the section is not rendered.

**JS:** one client island of about 0.8 KB gz (button + IO), no library.

### 3.7 Featured carousel (`TourCarousel`): the gentle carousel

- **User-driven, no autoplay,** so there is nothing to pause. This keeps the ribbon as the only thing that moves by itself.
- **Scroller:** a `<ul>` with `display:grid; grid-auto-flow:column`, `scroll-snap-type:x mandatory`, `scroll-padding-inline: var(--tp-gutter)`, `overscroll-behavior-x: contain` and a hidden scrollbar. It sits in its own container with `overflow-x:auto`, so the page does not overflow.
- **Columns:**
  - 1440: 3 full cards plus a 0.25 peek (column ≈ 372 px, gap 24); prev/next round buttons (44 px) in the title row.
  - 390: column `calc(100% - 56px)`, 1.15 per view (the brand's mobile rhythm), gap 12; swipe; buttons hidden below 768 px.
- **Progress:** dots under it (M8). Dots are buttons labelled "Go to tour 4 of 9" at ≥ 768 px; decorative (`aria-hidden`) on mobile.
- **A11y:**
  - `<section aria-roledescription="carousel" aria-label="Featured tours">`;
  - each `<li aria-roledescription="slide" aria-label="3 of 9">`;
  - buttons with `aria-controls` and `aria-disabled` at the ends;
  - tabbing to a card scrolls it into view (`scroll-padding`), and arrow keys need no special handling, since this is not a roving widget;
  - the scroller gets `tabindex=0` only when it has no focusable children.
- **JS:** about 1.5 KB gz (buttons + IO for the active index).

### 3.8 Navy CTA band

- `--tp-band` bg, `--tp-section-y` padding, centred.
- **Text:**
  - Satisfy title in `--tp-band-accent`: "Talk it through with an advisor";
  - one line of `--tp-on-band-muted`: "Start from a real tour, change what you like on the map, and an Adventure Asia advisor prices and confirms it with you.";
  - three reassurances in a row (stacked at 390), each with a gold check: "Real Adventure Asia tours", "Change days and stops yourself", "No payment to send a draft".
- **Buttons:**
  - primary gold "Plan my trip";
  - outline light "Ask an advisor": `--tp-on-band` text, 1 px `rgba(255,255,255,.4)` border, which goes gold on hover.
- Do not claim response times or prices we cannot back up.

### 3.9 Footer

- `--tp-band` bg, `--tp-on-band-muted` links.
- Satisfy column titles: "Explore", "Adventure Asia", "Legal".
- The TrustStrip stays.
- Legal links get `prefetch={false}`. This drops the 4 RSC prefetches per view noted in research §2.6.

---

## 4. Pages

### 4.1 Home (`/`)

| # | Section | Surface | 390 | 1440 |
|---|---|---|---|---|
| 1 | Header | Transparent over the hero → navy | §3.1 | §3.1 |
| 2 | **Hero** | Photo | Height `min(88svh, 560px)`, portrait 4:5 art-directed crop. Bottom-left: Satisfy kicker "Asia, the way few see it" (`--tp-text-script-sm`, `#E8B865`), h1 display "Plan a tailor-made Asia trip with someone who's been there" (white, 3 lines max). No lede. | Height `clamp(560px, 68vh, 680px)`. Text column max 640 px: kicker, h1, lede 18 px white/90 "Start from a real Adventure Asia route, shape it on the map, and an advisor makes it yours." |
| 3 | **Search card** (`HomeSearch`, restyled) | White, `--aa-radius-xl`, `--aa-shadow-lg` | Overlaps the hero by −48 px. Full width inside 16 px gutters. Stacked: "Where to" select, "How long" chips 5/7/10/14 (own horizontal scroll), "Travellers" stepper, "Plan my trip" primary, full width, 52 px. | Overlaps the hero by −56 px, max-width 1040. One row: Where to · How long (chips) · Travellers · [Plan my trip]. Vertical hairlines between fields. |
| 4 | **Ways in** (the brand's "Quick search / Map / Featured trips" trio) | Cream | 3 compact columns: 32 px brand icon + 13 px label | 3 columns: 48 px icon + label + 1-line text: "Find by destination" (`#destinations`), "Explore on the map" (`/plan`), "Start from a tour" (`#tours`). Uses `public/brand/icons/*-color.svg` |
| 5 | **Featured tours** | White | Carousel 1.15/view, swipe, dots | Carousel 3 + peek, arrows in the title row, "See all on the map →". Title "Trips to start from". Fetch `limit: 9`. |
| 6 | **Proof line** | Cream, compact (32 px y-padding) | Wraps onto 2 lines | Centred, gold-deep Poppins 600 18 px: "{Σ tour_count} tours · {countries} countries · every trip checked by an advisor". Counts come from `getCountries()`; no count-up animation. |
| 7 | **Destinations** | Sand | 2-column grid, 4:5 tiles, gap 12 | 4-column grid, 4:5 tiles, gap 20. Title "Where to go". Tiles with a photo come first, then by `tour_count` desc; missing photos use the no-photo tile (§3.5). The tile label sits on a bottom gradient: name (h3 white) and "{n} tours · 5–14 days". M3 on hover. |
| 8 | **How it works** | White | Stacked, centred | 3 columns joined by a static dotted gold line. Each step has a Satisfy numeral (48 px gold), a brand illustrated icon (`plan-color`, `map-color`, `direction-color`), a title and 2 lines of text (existing STEPS copy, tightened). |
| 9 | **Navy CTA band** | Navy | Buttons stacked, full width | Buttons in a row |
| 10 | **Photo ribbon** "From our trips" | Full-bleed | 160 px tiles, 40 px/s | 240 px tiles, 50 px/s. Content: featured tour covers + country covers, deduped |
| 11 | Footer | Navy | | |

### 4.2 Destination (`/destinations/[country]`)

| # | Section | 390 | 1440 |
|---|---|---|---|
| 1 | Header | Transparent → navy | Same |
| 2 | **Hero** (country cover, else the no-photo hero: navy + mountain motif) | Height 420. Breadcrumb 13 px white/85. h1 UPPERCASE `--aa-text-h1` (+0.08em, the brand's destination style). Meta line "{n} tours · {min–max} days". Up to 3 top-activity chips (`--aa-scrim` bg). Primary "Plan a trip to {country}", full width. | Height 520. The same, left column max 720. Primary + outline-light "See the tours" (anchor). |
| 3 | **Tours in {country}** (white) | Carousel when > 2 tours, else a 1-column list | Carousel when > 3, else a 3-column grid. "See them all in the planner →" |
| 4 | **Places our tours visit** (sand) | Static map 4:3 full width (`--aa-radius-lg`), then the first 8 places (56 px thumb, number, name, activities) + `<details>` "Show all {n}" | 12-column grid. Map cols 1–7 (sticky inside the section, top = header + 24). List cols 8–12 in its own scroll area, max-height 560 px |
| 5 | **Navy CTA band**: "Make {country} yours" | Stacked | Row |
| 6 | **Photo ribbon** "Around {country}" from `d.photos` (captions = `place_label`) | Replaces the current static "From our tours in X" grid. When there are < 4 photos, the old grid is dropped and nothing is shown | |
| 7 | Footer | | |

### 4.3 Tour (`/tours/[slug]`)

| # | Section | 390 | 1440 |
|---|---|---|---|
| 1 | Header | Solid navy | Same |
| 2 | Breadcrumb (cream) | 13 px, truncates the middle | Same |
| 3 | **Gallery** (LCP) | Snap-scroll strip, full-bleed, height 260, slides 88 % wide. A static "{photo_count} photos" chip. Image 1 eager + `fetchpriority=high` | Mosaic, height 440: 1 large (2fr) + 2 stacked (1fr), outer corners `--aa-radius-xl`. "View all {n} photos" jumps to the photo section or ribbon |
| 4 | **Title block** | Badges (country → destination link, "{n} days"), h1 `--aa-text-h1` in Poppins (titles are too long for script), subtitle lead, AI labels as today | Main column cols 1–8 |
| 5 | **Key facts row** | 2×2 grid of icon facts | One row: duration · places ({unique places}) · best time · group size. Then up to 5 activity chips (accent-tint) |
| 6 | **Highlights** | 1 column, gold check icons | 2 columns |
| 7 | **Day by day** | Timeline: a 2 px dotted gold line on the left, day circles (36 px, accent-tint, Poppins 600). Each day is a `<details>`, day 1 open. An "Expand all" text button (small JS, optional) | Same, max 72ch |
| 8 | **Where you go** | Static route map card (sand bg, `--aa-radius-lg`) | Same |
| 9 | **Included / Not included** | Stacked cards | 2 columns |
| 10 | **CTA card** | **Sticky bottom bar** (exists; restyled): `--aa-card` bg, top hairline + `--aa-shadow-lg`, `padding-bottom: env(safe-area-inset-bottom)`, buttons "Customise" (primary) + "Ask an advisor" (secondary), each 50 %. The page gets bottom padding equal to the bar height so the footer is not covered | **Sticky aside**, cols 9–12, `top: calc(var(--tp-header-h) + 24px)`. White, `--aa-radius-xl`, `--aa-shadow-lg`. Satisfy "Make it yours", the 3 reassurances (§3.8), primary "Customise this trip", secondary "Ask an advisor" |
| 11 | **Navy CTA band** | Only when the page is longer than 3 viewports; otherwise skipped (the sticky CTA already does the job) | Same rule |
| 12 | **Photo ribbon** "More from this trip" | Only when the photos after the first 3 number ≥ 8; otherwise the static gallery is enough | Same |
| 13 | Optional, behind a decision: **"Similar tours in {country}"** carousel | Needs one extra cached browse read per tour page (`getTours({country})`, ISR). Check browse Lambda load first (AA-833) | |

### 4.4 `/plan` (tokens only in AA-995)

- Inter → Poppins and the new type tokens.
- The header tagline "Discreet executive adventures, crafted day by day" becomes "Real tours. Shaped by you. Checked by an advisor."
- No layout change.
- Screenshot `TripPanel` and `FilterChips` at 390: Poppins is wider than Inter (risk R10).

---

## 5. Accessibility

- **WCAG 2.2.2:**
  - the ribbon has a visible pause button, pauses on hover and focus, and pauses when off-screen;
  - the featured carousel never autoplays;
  - the hero does not rotate.
- **Reduced motion:** handled by the global gate (§1.4), with an optional user toggle in the footer. Screenshots in `reduce` mode are part of verification.
- **Carousel semantics** as in §3.7. Ribbon copy B is `aria-hidden` and `inert`. Every image has a real `alt` (tour title, place label, or `alt=""` when the image sits next to the same text in a link).
- **Focus:** a 2 px ring with 2 px offset, `--aa-accent` on light and `--tp-band-accent` on navy and photos. Tab order: header → hero → search → content. In the DOM, the sticky CTA bar on mobile comes after main.
- **Targets ≥ 44 × 44:** chips, carousel buttons, the pause button, the stepper.
- **Headings:** one h1 per page; the Satisfy titles are real `<h2>` text (no images of text); h3 for cards.
- **Contrast:** pairs added to `lib/contrast.test.ts` (§1.1); text on photos only over ≥ 0.55 scrim.
- **Script legibility:** Satisfy only at ≥ 28 px and ≤ 6 words, never for body, buttons or data.
- **Forced colours:** buttons and chips keep a 1 px border so they stay visible in Windows High Contrast.
- **Language:** `lang="en"`; English is the default (memory: pages default to English).

---

## 6. Performance plan

**Budgets, Lighthouse mobile:**
- perf ≥ 85;
- LCP ≤ 2.5 s;
- CLS ≤ 0.05;
- TBT < 200 ms;
- new client JS ≤ 5 KB gz in total;
- first-view weight at 390 ≤ 600 KB.

**1. Hero image (the LCP):**

The home hero is a **curated static asset** in `public/hero/`:
- the photo is taken from AA's own CIS catalog, never from adventure.asia;
- built as AVIF + WebP at 640 / 960 / 1280 / 1920 / 2560 w;
- `<picture>` with an art-directed portrait `<source media="(max-width:767px)">`, `sizes="100vw"`, `width`/`height` attributes, `fetchpriority="high"`, `loading="eager"`;
- a matching `<link rel="preload" as="image" imagesrcset imagesizes fetchpriority="high">` through React 19 `preload()`;
- budget ≤ 90 KB for the 960 w AVIF (390 @2x) and ≤ 220 KB for 1920 w.

Destination and tour heroes come from the catalog, through **the 302 hop**:
- **Phase 1** (TripPlanner only): a server-side `resolvePhotoUrl()` runs `fetch(url, {redirect:"manual"})`, reads `Location`, and is cached with the catalog ISR tag. Only the LCP image uses the resolved CDN URL. Add `<link rel="preconnect">` to the image CDN host.
- **Phase 2** (cross-repo): the CIS `catalog.*` contract exposes the CDN path (a minor contract version), and `photo_url()` in `backend/browse/catalog.py` emits it directly. That removes the hop for every image. Needs a CIS issue.

Do not use `next/image` for catalog photos: it adds a second resize hop, and the Hobby image-optimisation quota is low.

**2. Other images:**
- `loading=lazy`, `decoding=async`;
- aspect-ratio boxes or width/height attributes, so no CLS;
- the small (600 w) variant for cards, tiles and the ribbon; large only for heroes and the gallery's main image at ≥ 1024 px, through `srcset` with both variants.

**3. Fonts:**
- 2 families instead of 3: Poppins 400/500/600 + Satisfy 400, latin only;
- next/font self-hosted, `adjustFontFallback`;
- Satisfy `display: optional` (no swap shift);
- Inter and Fahkwang removed, about −60–90 KB.

**4. JS:**
- no animation or carousel libraries (no Swiper, Embla or framer-motion);
- four tiny client islands: `RevealObserver` (one shared IO, ≈ 0.6 KB), `TourCarousel` controls (≈ 1.5 KB), `RibbonControl` (≈ 0.8 KB), `HeaderScrollState` (IO sentinel, ≈ 0.4 KB);
- the motion gate goes into the existing inline restore script;
- all pages stay Server Components with ISR 1800.

**5. CSS:**
- keyframes in `globals.css`;
- only transform and opacity animated;
- `contain: layout paint` on the ribbon and carousel;
- `content-visibility: auto` + `contain-intrinsic-size` on below-fold sections (verify that the `#tours` / `#destinations` anchor jumps still land correctly).

**6. Network:**
- `prefetch={false}` stays on card grids (AA-833) and is added to footer legal links;
- keep the number of browse calls per page unchanged, except the optional "Similar tours" (R11).

---

## 7. Risks

| # | Risk | Impact | Mitigation |
|---|---|---|---|
| R1 | Catalog photos go through a ≈ 1.4 s API Gateway 302 before the image request | Destination and tour heroes miss LCP ≤ 2.5 s (home is already 4.56 s on desktop) | Phase 1: server-side resolve + preconnect + fetchpriority. Phase 2: CDN path in the CIS contract (cross-repo issue). Home uses a static asset |
| R2 | Not enough photos: 8 of 14 countries have no cover, and featured tours reuse 2 images | A photo-led design looks patchy | Designed no-photo tile, duplicate-cover rule, sort tiles with a photo first, ribbon minimum counts. The real fix (more CIS covers) is a separate data issue |
| R3 | Choosing hero photos | Wrong picture, or one AA does not own | Only AA catalog photos; the agent picks the best per page with a focal point and records the photo ids in the PR |
| R4 | Satisfy legibility and font loading | Hard-to-read titles, or a swap shift | ≥ 28 px, ≤ 6 words, titles only; `display: optional`; Poppins fallback |
| R5 | AA-994 token ownership | After ADR 0016, defining `--aa-*` outside `core/tokens.css` is a lint error | Propose the new generic `--aa-*` scales for AA-994 slice 1; keep B2C-only tokens as `--tp-*`; one file, so the later switch is a delete |
| R6 | `--aa-muted` changes to `#5A6270` | Small visible change in the planner; possible contrast-test churn | Needed anyway (4.48 on sand fails); matches CIS AA-760; the test proves it |
| R7 | Motion discomfort and distraction | Vestibular issues, cheap feel | One auto-moving element per page, slow speed (40–50 px/s), pause button, everything off under reduced motion and without JS |
| R8 | Transparent header over bright photos | White nav unreadable | Top part of `--tp-hero-gradient` (0.45) + solid navy after the hero |
| R9 | Dark mode: the navy band blends into the dark bg | Sections run together | 1 px `--aa-line` borders on bands in dark mode; screenshots in both themes |
| R10 | Planner font change (Inter → Poppins, wider) | Overflow in `TripPanel` / `FilterChips` | Check with screenshots at 390; if it breaks, ship the planner font change as its own small slice |
| R11 | "Similar tours" adds a browse read per tour page | Browse Lambda load after deploy or ISR expiry (AA-833) | Optional; ISR-cached by country; decide in the tour slice |
| R12 | Features with partial browser support (`::details-content`, `interpolate-size`) | Accordion animates only in Chromium | Progressive enhancement; instant open elsewhere |
| R13 | Verification budget: Vercel 403-challenges this IP after about 40 automated loads | Lighthouse and screenshots incomplete | Plan the loads: per page × 2 widths × 2 themes + reduced motion + 3 Lighthouse runs; prefer a CI screenshot job (AA-994 plan) on the preview |
| R14 | `content-visibility` interfering with anchors and IO reveals | Wrong scroll position, reveal not firing | Keep the first two sections off it; test `/#tours` and `/#destinations` |
| R15 | The AI label is less prominent on the navy header | Weaker AA-805 disclosure | Keep the chip next to the logo on every page with the same explanation popover; only the colour changes |

---

## 8. Suggested build slices

All PRs carry `Refs AA-995`. Each slice ends with screenshots at 390/1440, light/dark, reduced motion.

1. **Tokens + fonts + motion gate:** `tokens.css` scales, Tailwind mapping, Satisfy in / Inter and Fahkwang out, `data-motion` in the restore script, contrast-test pairs. No layout change.
2. **Header + home hero + search card:** curated static hero asset, preload.
3. **Cards:** tour card, destination tile, no-photo tile, `TourCarousel`, scroll-reveal observer.
4. **`PhotoRibbon`, navy CTA band, footer** and the section order on home.
5. **Destination page:** includes the server-side photo resolve for the hero.
6. **Tour page:** gallery, facts, timeline, sticky CTA card and bar. Decide on "Similar tours" here.
7. **Verification:**
   - Lighthouse mobile on the preview for the home, destination and tour pages;
   - axe;
   - a keyboard walk of the carousel and the ribbon pause;
   - a horizontal-overflow check at 390;
   - 0 console errors.

Then a CIS issue for phase 2 (CDN photo path in the catalog contract) and a data issue for the missing country and tour cover photos.