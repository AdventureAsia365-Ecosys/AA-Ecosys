# AA-995 — TripPlanner customer pages: brand reference + current state (research)

Session S252, 27/10/2026. Read-only research for the AA-995 redesign (friendlier, more polished customer pages,
motion allowed, e.g. the sideways-scrolling banner on adventure.asia). Inputs for the "3 directions → judge →
build" steps. Agent: Claude Code (subagent).

- Reference captures: `ref/` (adventure.asia: home, a destination, an itinerary at 1440 and 390, fold shots;
  `aa-home-1440-marquee.jpg`; `aa-home-motion-15s.webm`, 15 s at 1280×720: hero autoplay, then the photo marquee).
- Current TripPlanner: `before/`. **Only the home page (1440 and 390) was captured.** Vercel's bot challenge answered
  403 from the 3rd page load on (`/destinations/vietnam`), so per the run rules the probe stopped. The destination,
  tour and `/plan` findings below come from the code, not screenshots. Retake them in the build step when Vercel
  stops challenging this IP.
- Measured with Playwright 1.59 (headless Chromium), computed styles, `document.getAnimations()`, Swiper's live
  `params`, and a `PerformanceObserver` for LCP/CLS. **Lighthouse was not run** (no Vercel budget left), so the
  timings here are desktop numbers with no throttling, not Lighthouse mobile scores.

---

## 1. adventure.asia: what the brand site does today

**Context first: adventure.asia has turned into a B2B site.** Its title is "ADVENTURE ASIA — THE ADVENTURE
TRAVEL MARKETPLACE FOR AGENTS & OPERATORS". The CTAs are "Apply" and "Partner Login", and the itinerary page shows
"PARTNER LOGIN / APPLY" where you would expect a booking button. **Copy the visual language, not the copy.**
TripPlanner is B2C. Stack: Nuxt 2 (Vue) + Tailwind + Swiper 5/6. Images come from `admin.adventure.asia/storage/…?fm=webp&w=1600`.

### 1.1 The sideways-scrolling banner (marquee): exact mechanics

| Property | Value (measured) |
|---|---|
| What scrolls | **Photos only**: an Instagram-style strip of 19 square photos (`/images/instagram/image-N.jpeg`), headed by an Instagram icon + "adventureasia365" in gold. No text, chips or logos. |
| Where | The last section before the footer, on **every** page (home, destination, itinerary). Full-bleed, no gutters, no gaps or corners between tiles. |
| Component | Vue `vue-infinite-slide-bar` (`.vifnslb-container` > `.vifnslb-element` > 2 × `.vifnslb-bar`). The content is rendered **twice** back to back. |
| Animation | CSS `@keyframes { 100% { transform: translateX(-50%) } }`, `animation: 50s linear infinite`, `translateZ(0)` (GPU layer). Pure CSS transform, so no layout work and no CLS. |
| Direction | Right → left (content moves left). |
| Speed | One copy (4,750 px at ≥1280) per 50 s → **95 px/s at 1440** (measured: −95 px/s). Tiles are 150/200/250/300 px at base/lg/xl/2xl, so speed changes with the breakpoint: about **57 px/s at 390** (2,850 px / 50 s). |
| Pause on hover | **No** (measured −95 px/s while hovering; `animation-play-state` stays `running`). |
| Pause control | **None.** |
| `prefers-reduced-motion` | **Ignored** (still −95 px/s with `reducedMotion: 'reduce'`). |
| A11y | The `<img>` tags have **no `alt`**; the duplicate copy is not `aria-hidden`; nothing is focusable. |
| Loading | `loading="lazy"`. The images were still blank in a full-page screenshot until scrolled into view. |

So the brand banner is a slow, endless, full-bleed photo ribbon. It **fails WCAG 2.2.2** (moving content that runs
longer than 5 s must have a pause) and our AA-995 bars. Keep the look; build it correctly (see §4).

### 1.2 Hero

- Full-bleed **photo carousel** (Swiper `effect: slide`, `loop`, `autoplay.delay 4000`, `speed 300`,
  `disableOnInteraction`, a11y module on). 4 slides. Height `calc(100vh − 60px)` on mobile and `70vh` from md
  (630 px at 1440×900).
- Each slide has a short line in a **gold pill** (`#DB9628` bg, white Poppins ~28 px, `rounded-full`), centred
  above the search box. Lines: "The best of Asia is hidden." / "Real trips. Check on the ground" / "No trips of our
  own. No selling around you." / "One curated source. Zero tabs open."
- A search bar sits centred over the photo: a white field + a square gold "Search" button (radius 0). At 390 the
  button stacks under the field at full width.
- Pagination: white 8 px dots; the active dot becomes a **20 px gold pill** (`transition .5s cubic-bezier(.4,0,.2,1)`).
- Under the hero, over the bottom of the photo: a translucent dark band (`rgba(21,23,39,.85)`-ish, 112 px) with 3
  links, each with a two-tone illustrated icon: "Quick search", "Map", "Featured trips". At 390 only 2 show.
- **Do not copy:** the hero slides are `loading="lazy"`. In the video the hero is **white for about a second**
  before the photo appears (`ref/aa-home-motion-15s.webm`, start), which means a slow LCP. The pill is white text on
  `#DB9628`, which is **2.5:1** and fails AA.

### 1.3 Navigation

- Sticky **dark navy header** `#1F2933`, 82 px (60 px mobile), small shadow (`0 1px 3px rgba(0,0,0,.1)`).
- Left: the gold mountain logo with the "Adventure Asia" wordmark. Right: white Poppins 600 ~15 px links
  "Destinations ▾", "Interest ▾", "About Us", "Blog", a search icon, "Partner Login", and an **outline gold pill**
  "APPLY" (gold border and text, transparent fill).
- Mobile: logo, search icon, gold hamburger.

### 1.4 Typography (from computed styles)

| Role | Family | Size / weight | Notes |
|---|---|---|---|
| Body, UI, cards, nav | **Poppins** (300/400/500/600 loaded) | 14–16 px; card summaries 14 px **300**; nav 600 | Fallback stack starts with "Averta". |
| **Section titles (h2)** | **Satisfy** (script), 400 | **50 px desktop / 40 px mobile**, line-height 1, `-1px` tracking on some | Centred. "Highlight Trips", "Explore Asia", "Top Destinations", "Region map", "Day by day Itinerary". The tour title (h1) on the itinerary page is Satisfy 50/40 too. |
| Destination hero h1 | Poppins 400, **UPPERCASE**, wide tracking | 64 px / 36 px | "VIETNAM" over the photo, colour `#F8F6F2`. |
| Card titles | Poppins 400–500 | 20 px | |
| Sub-heads on the itinerary page | Poppins 600 UPPERCASE | ~24 px | "SUMMARY", "HIGHLIGHTS". |
| **Fahkwang** | used on 1 element, **not even loaded** | — | The live site does **not** use Fahkwang for headings. Our CIS kit (`_brand/tokens.ts`: "Fahkwang headings") and the 14/09 brand note assumed it did. The live display voice is **Satisfy + Poppins**. |

### 1.5 Colour palette (sampled, by frequency)

| Hex | Use on adventure.asia | TripPlanner token today |
|---|---|---|
| `#DB9628` | Gold: buttons, prices, icons, map fill, active dot | `--aa-accent` ✅ same |
| `#C6932D` / `#DDA64E` | Gold variant fills; gold borders (outline buttons, dividers) | `--aa-accent-border #DDA64E` ✅ |
| `#9E6E16` (and ~`#A06A16`) | Dark gold text; month bars on the "Event Festival" accordion | `--aa-accent-deep #875D12` (darkened for AA) |
| `#1F2933` / `#1B232C` | **Navy**: header, "No trips…" band, footer, CTA bands | `--aa-ink #1F2933` (text only today, never a surface) |
| `#F8F6F2` | Cream section bg (`bg-gold-0`) | `--aa-bg` ✅ |
| `#FFFFFF` | Alternate section bg, cards | `--aa-card` ✅ |
| `#595C62`, `#33363D`, `#474A50`, `#6A6C72` | Body and secondary text greys | `--aa-body #33363D` ✅; muted differs |
| `#C8D6E5` | Footer link text on navy; light blue-grey map land | — |
| `#E5E7EB`, `#D3D3D4`, `#EDEDED` | Hairlines, "Clear all" button | `--aa-line #E9E4DB` (warmer) |
| `#C20101` | Rare alert red | `--aa-red` ✅ |

No dark mode on adventure.asia.

### 1.6 Imagery

- Photo-led everywhere. Full-bleed heroes, **no corner rounding**, no filters or duotone, `object-fit: cover`.
- Text on photos uses a bottom **black gradient** (destination tiles) or a dark band. The destination hero has a
  soft dark vignette at the bottom behind the uppercase name and breadcrumb.
- The itinerary hero is a **peek carousel**: the centre photo at 960 px, neighbours faded at the edges, square
  white arrow buttons.
- Maps: the home "Explore More Asia" map fills countries in gold `#DB9628` on blue-grey; the destination "Region
  map" shows gold ring pins; the itinerary page has a Mapbox Streets map with a dotted gold route.

### 1.7 Buttons and cards

- Buttons are **mixed**. In-content buttons are **square** (radius 0): solid gold "Search", "FIND TOUR" and tab
  buttons; outline gold "EXPLORE". The header and the CTAs on the itinerary and CTA bands are **pills**: outline
  "APPLY", solid "APPLY", outline "PARTNER LOGIN". All are Poppins 500, uppercase on the big ones, white text on
  gold (fails contrast; TripPlanner already uses dark text on gold).
- **Trip card** (Highlight Trips): white, square corners, no shadow. 3:2 photo with a gold outline heart (save)
  top-right. Title Poppins 20 px. Meta row with small icons: places count · days · difficulty ("Leisurely",
  "Moderate"). Hairline, then circled line-icons for activity types, then a 3-line summary in Poppins 300 14 px.
  Hairline, then "From **$2,340**" in gold and an outline "EXPLORE" button. Desktop: 3 per view with square white
  arrow buttons outside the row. Mobile: 1.15 per view, swipe, autoplay 3 s.
- **Destination tile** (Top Destinations): tall photo, square corners, bottom gradient, white name in Poppins 20 px
  and a one-line tagline ("Japan, Land Of The Rising Sun"). 4.2 per view, swipe.
- **Feature tiles** ("Everything to sell more…"): flat cream boxes with centred 600-weight text.

### 1.8 Section rhythm (home at 1440)

Hero 630 (photo) → Highlight Trips 789 (cream) → proof line 222 (cream: script title + gold stats "100 suppliers ·
14 core destinations · 1,000+ trips live today") → Explore More Asia map 1137 (white, `py-32`) → Explore Asia 844
(photo bg + white search card: regions → country → place chips + activity icons) → Top Destinations 675 (white) →
feature grid 442 (white) → **navy band** 446 (Satisfy title, big gold Satisfy numerals 1/2/3, outline pill CTA) →
photo marquee 366 → navy footer (Satisfy headings "About us", "Offices", "Contact us"). Mostly `py-16` (64 px) bands
with Satisfy titles centred. The container is about 1248 px (96 px side gutters at 1440). The bands alternate
cream / white / navy / photo.

### 1.9 Motion inventory (complete)

| Element | Mechanics |
|---|---|
| Hero carousel | Slide, 300 ms, autoplay 4 s, loop. Stops after user interaction. |
| Pagination dot | Width 8 → 20 px with a gold colour change, 500 ms `cubic-bezier(.4,0,.2,1)`. |
| Trip / destination sliders | Slide 300 ms. Desktop: arrows, no autoplay. Mobile: autoplay 3 s (Highlight Trips). |
| Photo marquee | 50 s linear infinite `translateX(-50%)`, 95 px/s at 1440, no pause, ignores reduced motion. |
| Buttons and links | Tailwind default `transition 150ms cubic-bezier(.4,0,.2,1)` on colour/bg/border. |
| Scroll reveals | **None** (no AOS, no `opacity:0` waiting for an IntersectionObserver). |
| Parallax / Ken Burns | None. |

The brand's motion is restrained: two auto-advancing photo things and one endless ribbon, nothing on scroll.

### 1.10 Tone of copy

Short, declarative two-beat lines: "The best of Asia is hidden." "Real trips. Checked on the ground." "Small
operators the big aggregators won't take. Hand-selected, vetted in person." Destination taglines: "Thailand, land of
smiles", "Laos, Land of Millions Of Elephants". The footer still carries the B2C positioning: "soft/medium vacation
options to the experienced adventure customer seeking uniquely styled expeditions, rather than traditional
tourist-oriented itineraries". The voice is confident and plain with a bit of insider "hidden Asia" mystique, and no
exclamation marks. The B2B lines (agents, earning, partner tiers) do not apply to TripPlanner.

### 1.11 Perf and quality note on the reference

0 console errors on home and destination. 1 on the itinerary page (a Permissions-Policy notice). No horizontal
overflow at 390 or 1440. The itinerary page never reached `networkidle` within 60 s (long-polling or many
requests). Lazy hero images cause a visible white hero on load. **The reference is not a performance model.**

---

## 2. TripPlanner today (code + home captures)

### 2.1 Stack and structure

- Next.js **16.4.2**, React 19.2, Tailwind **3.4.14**, mapbox-gl 3.7. **No animation library** (no motion or
  framer-motion, no Swiper or Embla). `package.json` has 5 runtime deps.
- `frontend/app`: `page.tsx` (home), `destinations/[country]/page.tsx`, `tours/[slug]/page.tsx` (Server
  Components, ISR 1800 s), `plan/` (client map planner), `sign-in`, `trips`, `privacy`, `terms`, `api/*` (BFF).
- `frontend/ui`: kit primitives (`tokens.css`, `Button` (pill; primary = gold + dark text, uppercase on md/lg),
  `Badge`, `Photo`, `Icon`, `States`, `ThemeToggle`, `theme.ts`, `restoreTheme.ts`).
- `frontend/components/site/*`: `SiteHeader`, `SiteFooter`, `TrustStrip`, `HomeSearch`, `TourCard`, `StaticMap`
  (server-rendered Mapbox Static `<img>`), `LegalPage`, `JsonLd`. `frontend/components/*`: planner pieces
  (`Header`, `MapView` 1,025 lines, `TripPanel` 754, `FilterChips`, `TourListPane`, …).

### 2.2 Tokens: where they live today

- **Colour: one place already.** `frontend/ui/tokens.css` defines `--aa-*` for light (`:root,[data-theme=light]`)
  and dark (`[data-theme=dark]`), copied from the CIS kit with 3 light values darkened for AA. Tailwind exposes them
  as `k-*` (`tailwind.config.ts`). `lib/contrast.test.ts` guards the text pairs (≥ 4.5:1, both themes) and bans
  raw palette classes in planner files.
- **Not tokenised:** radius (`rounded-2xl`/`rounded-xl`/`rounded-full` written inline), spacing, the type scale
  (inline `text-[11px]`, `text-[13px]`, `text-[15px]`, `text-[28px]`, `text-[44px]` everywhere), shadows
  (hard-coded `rgba(31,41,51,…)` in `tailwind.config.ts`), motion durations and easings (`duration-300`, the
  `aaFadeInUp .18s` keyframe in `globals.css`), z-index, and the container width (`max-w-6xl` repeated).
- **Drift from the CIS kit (AA-994 should settle it):** CIS `BRAND.muted` is now `#5A6270` and `muted2` `#626A78`
  (AA-760), while TripPlanner has `#656D7A` / `#9099A6`. TripPlanner also has `--aa-scrim`, `--aa-hero-bg` and
  `--aa-on-solid`, which are its own.

### 2.3 Fonts

`next/font/google` in `app/layout.tsx` loads **three** families: Inter (variable; the `body` default and the whole
`/plan` planner), Poppins 400/500/600/700 (`--font-poppins`, kit pages via `.aa-site`), and Fahkwang 500/600
(`--font-fahkwang`, kit-page h1/h2 and `font-display`). All use `display: swap`. Measured on home: h1 Fahkwang 600
44/30 px, h2 Fahkwang 28/24 px. **No Satisfy.** So the planner (Inter) and the site pages (Poppins + Fahkwang) look
like two products, and neither matches the brand's Satisfy + Poppins voice.

### 2.4 Images

- `ui/Photo.tsx` renders a plain `<img>` with `object-cover`, `loading=lazy` (eager for the first 3 cards or
  hero), `decoding=async`, and no `width`/`height`, `srcset`/`sizes` or `fetchpriority`. When there is no URL it
  shows a cream tile with a camera icon. This was a deliberate choice: "photos come from the CIS API already
  sized; `next/image` would add a second resize hop".
- Photo URLs are `https://api-cis…/content/photos/<id>?size=small|large`. That endpoint answers **302** (≈1.4–1.5 s
  through API Gateway, measured from this machine) to `https://img.lumiguides…/<country>/<id>-600.webp`
  (CloudFront hit, `max-age=31536000`, ≈1.3 s here). small = 600 px (≈46 KB), large ≈193 KB.
  **Every photo costs an extra API Gateway round-trip before the image request even starts.**
- Measured LCP on home at 1440 with no throttling: **4.56 s**. The LCP element is a featured-tour card image through
  that 302. At 390 the LCP was the h1 text (1.78 s) because no image is in the first viewport. CLS 0.0005 (1440) /
  0.0017 (390). Aspect-ratio boxes keep it stable. **A photo hero (which the redesign needs) will make the LCP an
  image, so the 302 hop must go or the LCP ≤ 2.5 s bar will not be met.**

### 2.5 Motion today

Card image `group-hover:scale-[1.03–1.04]` (300 ms); the `aa-animate-in` 180 ms fade-up for planner popovers;
`<details>` chevron rotate; Tailwind `transition` on buttons. `document.getAnimations()` on home = 0.
**`prefers-reduced-motion` is not handled anywhere** (grep for `prefers-reduced-motion`, `motion-reduce`,
`motion-safe` in app/components/ui finds nothing). It has to be added before any new motion lands.

### 2.6 What the pages look like (home captured; others from code)

- **Home** (`before/tp-home-*.png`): a **white** sticky 56 px header (small logo, "ADVENTURE ASIA AI ⓘ" outline
  pill, Destinations / Tours / Sign in / theme toggle / gold "Plan a trip" pill). The hero is **text only** on a
  cream→bg gradient: a small gold kicker, a Fahkwang h1 "Plan your Asia adventure, tailor-made with an advisor", a
  grey lede, and a white search card (Where to / Days / Travellers + "PLAN MY TRIP" + 5/7/10/14-day chips). Then
  "Featured tours" (3-col cards, rounded-2xl, day pill on the photo, country badge, Fahkwang title, 2-line summary,
  "VIEW ITINERARY →"), "Destinations" (4-col 4:5 tiles with a bottom gradient), "How it works" (3 numbered cards),
  and a footer trust strip. Every section sits on the same cream bg with left-aligned 28 px heads. No bands, no
  navy, no photo surface. 0 horizontal overflow at 390 and 1440. 0 app console errors. (The 4 console 403s at 390
  were Vercel's challenge on the `<Link>` RSC prefetches of `/plan`, `/sign-in`, `/privacy`, `/terms`, not an app
  bug. Those prefetches do add 4 requests per page view.)
- **Destination** (code): a photo hero (`bg-k-hero-bg` + `--aa-scrim` + Fahkwang h1 white + "Plan a trip to X"),
  "Tours in X" grid, "Places our tours visit" (static Mapbox map + numbered list with 56 px thumbs), and a
  "From our tours in X" photo grid. **This photo grid is the natural source for a marquee.**
- **Tour** (code): breadcrumb, a gallery (1 big + 2 small at sm, horizontal snap list on mobile), badges, Fahkwang
  h1, AI labels, Highlights, "Day by day" `<details>` accordion, "Where you go" static map, Included / Not included,
  a sticky CTA card at lg, and a sticky bottom CTA bar on mobile. No price (no price source, ADR 0005).
- **/plan** (code): Inter, its own `Header` with the tagline "Discreet executive adventures, crafted day by day",
  Mapbox GL full-height, `FilterChips`, `TripPanel`, and a Map | List toggle.

### 2.7 Already on-brand

Gold `#DB9628`, cream `#F8F6F2`, ink `#1F2933`, the gold border `#DDA64E` and red `#C20101` match the live site
exactly. Poppins body matches. The real logo is used (`/public/brand/logo.png`, 752×481 PNG shown at 32 px; an SVG
would be sharper). The brand icon SVGs (`public/brand/icons/plan-color.svg`, `map-color.svg`,
`direction-color.svg`, `instagram-gold.svg`, …) are already in the repo, the same illustrated icons as the
adventure.asia "Quick search / Map / Featured trips" band. Primary buttons pass contrast (dark text on gold),
which is better than the reference. Light/dark theme, the contrast test, JSON-LD and ISR are all in place.

### 2.8 Biggest gaps (ranked)

1. **No photography above the fold on home.** The brand opens on a full-bleed photo with a search box over it. Ours
   is a cream gradient with text, which is the main reason it feels "plain".
2. **No section rhythm or brand surfaces.** Every section is cream with a left-aligned 28 px heading. The brand
   alternates cream / white / **navy** bands with centred script titles. Our header is white; the brand's is navy.
3. **Display type is off-brand.** We use Fahkwang (not used on adventure.asia) and Inter (planner). The brand's
   signature is **Satisfy** for section titles with Poppins for everything else. There is no script accent at all.
4. **Missing and repeated photos (data, not design).** 8 of 14 destination tiles show the camera placeholder (India,
   Nepal, Japan, Laos, Philippines, Thailand, Pakistan, Vietnam). The 6 featured tours reuse 2 images (both Sri
   Lanka cards share one; all four Bhutan cards share one). Any design needs a good-looking no-photo fallback
   (navy or gold typographic tile, or a map silhouette) and must avoid placing duplicates next to each other. The
   real fix is more CIS cover photos, a separate issue.
5. **Image delivery is slow.** The 302 hop through API Gateway, no `fetchpriority`, no `srcset`, and no preconnect
   to the image host. LCP 4.56 s on desktop already, before any hero photo.
6. **No motion system and no reduced-motion guard.** There are no motion tokens, and nothing honours
   `prefers-reduced-motion`.
7. **Tone inconsistencies.** The planner tagline "Discreet executive adventures" matches neither the brand voice nor
   the site pages. The AI pill sits prominently next to the logo on every page.
8. **Tokens beyond colour are inline values,** which blocks AA-994 (shared radius, space, type, shadow and motion).

---

## 3. Constraints the build must respect (from AA-995 + repo rules)

- Lighthouse mobile perf ≥ 85, **LCP ≤ 2.5 s**, **CLS ≤ 0.05**, motion respects `prefers-reduced-motion`, an
  **accessible carousel** (pause, labels, keyboard), 390 and 1440, no page-level horizontal overflow, 0 console errors.
- `lib/contrast.test.ts` must stay green in both themes. Any new text-on-photo needs a scrim token. White on gold is
  not allowed.
- ISR catalog pages stay Server Components. Keep the client JS of motion pieces tiny (CSS-first). Do not add
  `prefetch` on card grids (AA-833).
- Dark theme must work on every new surface (navy bands need a dark-theme value too, e.g. `--aa-band` = `#1F2933`
  light / `#0B1016` dark).
- Do not copy B2B copy, and do not take photos from adventure.asia (brand-sync note: only official AA assets).

## 4. Implications and recommendations for the design directions

**Tokens (one place, ready for AA-994).** Keep `ui/tokens.css` as the only source and extend it with:

- `--aa-radius-{sm,md,lg,pill}`;
- `--aa-space-section` (64 px, 48 px mobile) and `--aa-container` (1248 px);
- type tokens `--aa-font-script` (Satisfy), `--aa-text-{display,h1,h2,h3,body,small,kicker}`;
- `--aa-shadow-{sm,md}`;
- surface tokens `--aa-band` and `--aa-on-band`;
- motion tokens `--aa-ease-out: cubic-bezier(.2,.7,.2,1)`, `--aa-ease-std: cubic-bezier(.4,0,.2,1)`,
  `--aa-dur-{fast:150ms, base:300ms, slow:600ms}` and `--aa-marquee-speed`.

Then map them in `tailwind.config.ts` (`borderRadius`, `fontFamily.script`, `boxShadow`, `transitionTimingFunction`)
and replace the inline `text-[..px]` values with the scale. Use the same names AA-994 plans to share, so the later
switch is a file swap. Reconcile `muted`/`muted2` with the CIS AA-760 values at the same time.

**Marquee (the thing Nghiệp asked for), built correctly:**

- **Content:** a full-bleed ribbon of real AA tour photos (from destination `photos` / featured tour covers, deduped
  by URL, only tiles that have a photo). Each tile links to its destination or tour, with an optional caption chip
  ("Bhutan · Punakha"). A lighter variant is a **text ribbon** of destination names and activity types in Satisfy or
  Poppins uppercase with gold separators, which needs no images and adds no LCP risk.
- **Mechanics:** CSS `transform: translate3d` keyframes on a duplicated track (same idea as the brand), linear,
  ≈40–60 px/s (the brand's 95 px/s feels fast on a phone). Set it with a CSS custom property, computed from the
  track width.
- **Accessibility:**
  - a visible **pause/play button** (`aria-pressed`, labelled) before the track;
  - pause on `:hover` and `:focus-within`;
  - the duplicate copy `aria-hidden="true"` with its links `tabindex="-1"`;
  - the list labelled (`aria-label="Photos from our tours"`);
  - `alt` on every image;
  - keyboard: the first copy is focusable, and focus pauses the ribbon.
- **`prefers-reduced-motion: reduce`:** no animation. Show a static horizontally scrollable row (`overflow-x: auto`,
  `scroll-snap`) inside its own container, so the page itself gets no overflow.
- **Performance:** the ribbon sits **below the fold** (never the LCP). Tiles have fixed size and `loading=lazy`, and
  the container is `overflow: hidden` so there is no page overflow. Start the animation only when it is in view
  (IntersectionObserver toggles a class) to save CPU on mobile.

**Hero.**

- Use a **single** full-bleed photo with a Satisfy kicker and a Poppins h1 over a scrim, and the existing search card
  overlapping the bottom edge. This beats a 4 s carousel for LCP and accessibility.
- If slides are wanted, crossfade only **after** LCP, pause on hover and focus, offer a pause control, and turn off
  under reduced motion. A subtle **Ken Burns** effect (scale 1 → 1.06 over ~12 s, ease-out, once) is a cheap way to
  get "motion" with no layout work; turn it off under reduced motion.
- The hero image must be `fetchpriority="high"`, `loading="eager"`, and served **without the 302**. Either the
  catalog payload returns the final `img.…/…-1600.webp` URL (best: a CIS/browse change), or the page adds
  `<link rel="preload" as="image">` for the resolved URL. In either case add `preconnect` to the image host. Also
  consider `srcset` with the 600 and large variants.
- Choose the hero image statically: a curated, known-good photo per page, never a random catalog item that may be a
  duplicate.

**Rhythm and surfaces.**

- Use centred Satisfy section titles (≈44/36 px; Satisfy is legible only at large sizes, so never use it for body or
  UI), Poppins for everything else, and drop Fahkwang and Inter.
- Alternate cream / white / navy bands (`--aa-band`). Make the header navy, or transparent over the hero and turning
  navy on scroll.
- Add a proof line in gold Poppins 600 ("N tours · 14 countries · every trip checked by an advisor"; counts from the
  catalog).
- Use the brand's illustrated icon trio (`public/brand/icons/*-color.svg`) for "How it works".
- Navy CTA band before the footer, then the photo marquee, then the navy footer. This copies the brand order.

**Cards.**

- Keep the rounded kit cards (the kit and AA-994 favour them; the brand's square corners are older).
- Add the brand's meta row (days · places · activity icons). Show "From $X" only when a real price source exists
  (not now).
- Use a typographic **no-photo tile**: navy or gold-tint background with the country name in Satisfy, plus a
  mountain-line motif from the logo. Never the bare camera icon on customer pages.

**Scroll reveals (optional, small).**

- Fade-up of 12–16 px over 400–600 ms (`--aa-ease-out`) on section headings and card groups, staggered 60 ms, via one
  tiny IntersectionObserver client component that adds a class.
- Content must be visible without JS: start from `opacity:1`, and only animate when a `data-motion="ok"` flag is set
  on `<html>` by the theme restore script after checking reduced motion. This avoids CLS and invisible content.
  The brand itself has no reveals, so keep them subtle.

**Copy.** Write in the brand's two-beat voice, aimed at travellers:

- "The Asia few people see. Planned with someone who's been there."
- "Real tours. Shaped by you. Checked by an advisor."

Retire "Discreet executive adventures" in the planner header.

**Verify in the build step:**

- before/after screenshots of all 4 pages at 390 and 1440, light and dark;
- reduced-motion screenshots;
- Lighthouse mobile on a preview (budget the Vercel loads: about 40 per session);
- an axe pass;
- a keyboard walk through the marquee pause control.

---

## Files

- `ref/aa-home-1440-fold.jpg`, `ref/aa-home-1440-marquee.jpg`, `ref/aa-home-390-fold.png`
- `ref/aa-destination-vietnam-1440-fold.jpg`, `ref/aa-destination-vietnam-390-fold.png`
- `ref/aa-itinerary-beijing-hongkong-1440-fold.jpg`, `ref/aa-itinerary-beijing-hongkong-390-fold.png`
- `ref/aa-home-motion-15s.webm`: 0–8 s hero autoplay (note the blank white hero while the lazy image loads), then the
  photo marquee above the footer.
- `before/tp-home-{1440,390}-fold.png` (destination, tour and `/plan` not captured: Vercel 403 challenge).
- Probe scripts (throwaway, not committed): `.tmp-session/s252/aa995/probe-*.cjs`. Raw JSON: `home-1440.json`,
  `motion.json`, `pages.json`, `tp.json`.

Size note: the captures came to about 23 MB, mostly full-page PNGs. The root repo keeps only the fold shots, the
marquee shot and the video (S252 close): the full-page PNGs were left out, and fold PNGs over 400 KB were saved as
JPEG (quality 70).
