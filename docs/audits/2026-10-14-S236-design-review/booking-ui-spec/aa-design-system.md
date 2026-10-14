# Adventure Asia ecosystem design system (S236 research draft)

Status: research draft for review, not yet in a repo. Date: 14/10/2026.
Evidence:
- The live site https://adventure.asia, fetched 14/10/2026 with curl. HTML is saved in `.tmp-session/s236/aa-site/*.html`,
  the extracted text in `*.txt` and all inline CSS in `all.css`. Screenshots (Playwright, desktop 1440 and mobile 390)
  are in `.tmp-session/s236/aa-site/shots/` (`*-full.png` is the whole page, `tiles/` holds 1800 px slices,
  and `menu-*`, `enquire.png` and `search-Map.png` show interactions).
- Pages read: home, `/destination/bhutan-must-know-before-travel`, `/destination/vietnam-adventure-tours`,
  `/interest/hiking` (it returns **HTTP 500** today), `/search`, `/about`, `/blog`, five posts (Paro, Nepal seasons,
  Phong Nha, the trekking-vs-hiking hub, and the newest one, South Korea soft adventure, dated 16/05/2026) and one tour,
  `/itinerary/beautiful-life-along-the-mekong-river-in-vietnam-and-cambodia-5`.
- Also read: the Figma shell spec `.tmp-session/s236/figma-spec/01-shell.md`; the CIS kit (`apps/AA-CIS-App/frontend/app/_kit/tokens.ts`,
  `_brand/tokens.ts`, `globals.css`); and the TripPlanner `frontend/tailwind.config.ts`.

The site is Nuxt 2 with Tailwind 2. Its custom colour scales are `gold-*`, `grey-*` and `navy-*`. Its font utilities
are `font-sans` (Poppins), `font-display` (Fahkwang) and `font-title` (Satisfy). Every hex value below was read from that
CSS, not sampled from images.

---

## 1. Brand essence and voice

### 1.1 Essence (what the brand says about itself)

- Positioning line, repeated on every page ("Why Adventure Asia", the footer and About): *"soft/medium vacation options
  to the experienced adventure customer seeking uniquely styled expeditions, rather than traditional tourist-oriented
  itineraries"*. **Soft-to-medium adventure for experienced travellers, custom and flexible, not mass tourism.**
- The new hero carousel (2026) carries four claims. These are the sharpest brand statements on the site and should
  become the ecosystem's pillars:
  1. *The best of Asia is hidden.* (discovery)
  2. *Real trips. Checked on the ground.* (trust: the H3 drops the "-ed", see §5)
  3. *No trips of our own. No selling around you.* (independence: a curator, not an operator pushing stock)
  4. *One curated source. Zero tabs open.* (convenience: the TripPlanner promise)
- Human proof: the About page features "expert adventure planner Leigh Wilson" (25 years in Asia). The enquiry promise
  is "a tailor-made price & itinerary proposal" "by phone or email within 24 to 48 hours".
- Range: 24 countries (Central, East, South and Southeast Asia) and 6 interests (Beach Retreat, Biking, Culture, Hiking,
  Water Activities, Wildlife). The site claims "more than 720 sample itineraries", while `/search` shows "1042 Trips".

### 1.2 Two voices on the site: pick the new one

| | Legacy voice (2022–2024 posts, destination guides, About) | New voice (2026: South Korea post, new hero, new tour summaries) |
|---|---|---|
| Example | "Nestled amidst the majestic peaks of the Himalayas, Paro Valley Bhutan unfolds like a breathtaking tapestry woven with vibrant culture…" | "Many destinations force a compromise. You either get beautiful active terrain with tiring transfer days, or excellent city infrastructure with outdoor experiences that feel bolted on." |
| Tone | SEO-flowery, superlatives ("breathtaking", "enchanting", "majestic", "unforgettable", "heart-pounding") | Plain, specific, honest, and the reader is assumed smart. It shows planning expertise. |
| Signature moves | "Unveiling…", "Delve into…", "Embark on…", "A Wanderer's Paradise" | "Honest caveat:", "Regional Proof Points, Not Generic Claims", "Build by Energy Arc", "Seasonal Reality and the Caveat Most Plans Miss" |
| Trust | none | an explicit disclaimer: "Travel details can shift by season and supplier availability. Confirm key logistics before booking." Byline: "Adventure Asia Editorial Team" |

**Rule: write in the new voice everywhere** (TripPlanner, CIS T-pipeline output, Booking customer emails). Keep the
legacy voice's *structure*: numbered sections, a table of contents and internal links. Drop its adjectives. This matches
the CIS writer policy (`writer-source-fidelity`): never promise views, services or times that the source lacks.

### 1.3 Headline patterns (from the blog and tour titles)

- `Place: Benefit/Angle` with a colon: "Phong Nha - Ke Bang National Park in Vietnam: The Splendid Cave Kingdom",
  "Wildlife in Vietnam: A Land of Majestic Animal Species".
- "Best time to … : A Season-by-Season Guide for Adventurers". "… – The ultimate guide for adventurers".
- "Why <Place> Is Asia's Hidden <Trip Style> Destination" (new; it echoes the "best of Asia is hidden" pillar).
- Numbered listicles: "Top 5 Bhutan Hiking and Trekking Tours", "Top 6 Must-See National Parks…", "Vietnamese caves: 10
  plus awesome places".
- Tour titles come in two styles. Legacy: "N Days <Festival> Tour", "Classic 22 days Laya Trek". New, descriptive:
  "A guided cycling journey along South Korea's Four Rivers route", "Dog sledding tour in Mongolia". **Prefer the
  descriptive style. The duration belongs in metadata, not in the title.**
- Section H2s inside posts are numbered: "1. Unveiling the Valley's Treasures", "1.1 Scaling the Heights: A Hike to…".
  They use a `Theme: Specific` sub-pattern.

### 1.4 Intro style

- Legacy: 3–5 sentences of scene-setting, ending with "Whether you seek X, Y, or simply Z, <place> promises…".
- New: the first H2 makes a claim ("What Korea Does Better Than Most Regional Alternatives") and then gives the
  trade-off. **Use this: open with the trade-off the traveller faces, then say why this place or route solves it.**
  No "nestled".

### 1.5 How they write about places

- Concrete anchors are good and should be kept: altitudes ("Lijiang at 2,412 meters", "3,000 feet above the valley floor"),
  dates ("built in 1352", "Ta Dzong, dating back to 1649"), durations ("The 4-hour trek"), counts ("850 ha eco-reserve,
  100 species of water birds"). Local terms are glossed in place: "dzongs (fortresses)", "Ema Datshi, the national dish
  featuring chili peppers and cheese".
- Seasonality is always present, as a season list (Spring/Summer/Autumn/Winter with months) plus a "best window"
  recommendation.
- Practical planning blocks: Seasonality, Accommodation, Permits, Guides, Respectful Exploration (dress codes).
- Pacing language (new): "lighter city adjustment first, higher-output middle, gentler cultural finish"; "Keep one
  major move per day". **This is the vocabulary TripPlanner should use when it explains a plan.**
- Fitness is stated plainly: "If you can walk 10 km comfortably and handle moderate hills…".

### 1.6 CTA wording seen

| Context | Live wording | Recommended wording |
|---|---|---|
| Header button | "ENQUIRE" | "Enquire" (keep it short) |
| Tour card | "EXPLORE" | "View trip" or "Explore" |
| Tour detail | "ENQUIRE" + "ADD TO WISHLIST" | keep |
| Enquiry submit | "Send Enquire" (wrong) | "Send enquiry" |
| Thank-you modal | "…you will be contected by our sales staff shortly" | "Thanks, we'll reply within 24–48 hours with a tailor-made proposal." |
| In-post links | ">>> Discover more:", ">>> Read more:", ">>> Explore further:", ">>> Continue reading:" | keep as a styled "Related" callout, without the `>>>` |
| Post closer | "Contact Adventure Asia today and let our <Country> experts design your dream <X> adventure" | new: "Share your dates and preferred activity level, and we will shape this into a practical, booking-ready route." |
| Post end buttons (new) | "Explore South Korea routes", "Request custom trip design", "Get the guide" | keep the wording, but fix the links (§5) |
| PDF capture | "Please leave your email, to get your perfect trip in PDF format" | "Email me this trip as a PDF" |
| Search panel | "FIND TOUR" / "CLEAR ALL" | "Find trips" / "Clear all" |

---

## 2. Tokens (site vs CIS kit, reconciled)

Legend: ✅ same value; ⚠️ differs (a decision is needed or proposed); ➕ exists on the site, missing in the kit.

### 2.1 Colour

| Role | Site class → hex | CIS kit (`globals.css` / `_brand/tokens.ts`) | Status / decision |
|---|---|---|---|
| Brand gold (primary button, price, active) | `gold-600` `#DB9628` (`.btn-primary`, price `text-gold-600`) | `--aa-accent` / `--brand-gold` `#DB9628` | ✅ |
| Gold hover / pressed / text on tint | `gold-700` `#9E6E16` (`.btn-primary:hover`, `.btn:focus`, day number) | `--aa-accent-deep` `#9E6E16`, **but** legacy `--brand-gold-dark` `#B87A1A` | ⚠️ Two hover golds are in use. TripPlanner `aa.gold-dark` is also `#B87A1A`. **Proposal: `#9E6E16` is the single hover/deep value.** Retire `#B87A1A`. |
| Outline border / soft gold | `gold-500` `#DDA64E` (`.btn-outline-primary` border) | `--aa-accent-border` `#DDA64E` | ✅ |
| Divider gold | `gold-400` `#E3BD7F` (included-list rule, icon ring stroke) | — | ➕ add `--aa-accent-line` |
| Gold tints | `gold-50` `#F5EBD9`, `gold-100` `#F0E3CE`, `gold-200` `#EEDBBD`, `gold-300` `#E9CEA3` | `--aa-accent-soft` `#F4E2C2`, `--aa-accent-tint` `#FBF3E3` | ⚠️ They are close but not equal. Keep the kit pair (soft and tint). The site scale is only for reference. |
| Darkest gold (text on cream) | `gold-800` `#633A00` | — | optional |
| Cream page background | `gold-0` `#F8F6F2` (Highlight Trips band, included box, search bg) | `--aa-bg` `#F8F6F2`, `--brand-offwhite` | ✅. Legacy `--bg-primary` `#F4F1EC` is a second cream (⚠️). The Figma header band uses cool `#F4F6F8` (C-12): use `#F8F6F2`. |
| Header / footer navy | `navy-800` `#1B232C` (header), `navy-700` `#1F2933` (footer) | `--aa-ink` / `--aa-side-bg` `#1F2933` | ✅ for `#1F2933`. `#1B232C` ➕ is the header-only shade, optional. |
| Overlay | `navy-transparent-85` `rgba(21,23,39,.85)` | kit Modal scrim | use the kit |
| Map land / light navy | `navy-200` `#C8D6E5` (map countries), `navy-50` `#F7F9FB` | — | ➕ map tokens for TripPlanner |
| Disabled button | `#98A9BB` | kit disabled | use the kit |
| Body text | `grey-800` `#33363D` | `--aa-body` `#33363D` | ✅ |
| Strong text | `grey-900` `#1C2027` (card titles) | `--aa-ink` `#1F2933` | ✅ (close enough; use the kit) |
| Secondary text | `grey-600` `#595C62` (itinerary body), `grey-500` `#6A6C72` | `--aa-muted` `#6B7380` | ✅ (close) |
| Muted / placeholder | `grey-400` `#88898E`, `grey-300` `#A6A7AA` | `--aa-muted2` `#9099A6` | ✅ (close) |
| Card divider | `grey-200` `#D3D3D4` (`.card-content` top and bottom) | `--aa-line` `#E9E4DB` (warm) | ⚠️ The site is a cool grey and the kit a warm beige. **Use the kit's warm line everywhere.** |
| Light fill | `grey-100` `#EDEDED`, `grey-50` `#FBFBFB` (post title band) | `--aa-line2` `#F0EBE0`, `--aa-panel-bg0` `#FAFAF8` | ✅ (close) |
| Slate secondary | `#35495E` (8× on home, SVG icon fills) | `--aa-slate` `#35495E` | ✅ |
| Danger | `#C20101` (required-fields note) | `--aa-red` `#C20101` | ✅. The Figma uses `#D9534F` (⚠️: use the kit). |
| Success | Tailwind `green-500` `#10B981` | `--aa-green` `#2E7D5B` | ⚠️ Use the kit. The Figma `#1F9D55` also maps to the kit. |
| Orange "primary" | `.text-primary` `#FF6F00`, `meta theme-color` `#E56400` | — | ⚠️ A leftover on the site, almost unused. **Do not adopt it.** Set the mobile `theme-color` to `#1F2933` or `#DB9628`. |

The dark theme exists only in the CIS kit (`[data-theme="dark"]`, gold lifted to `#E8A838`). Customer-facing surfaces
(TripPlanner and Booking customer pages) stay **light only**, as the live site and the CIS portal do.

### 2.2 Typography

| Family | Site role (observed) | CIS kit | Decision |
|---|---|---|---|
| **Poppins** 300/400/500/600/700 | All UI and body text, nav, buttons, card titles (20 px / 400), meta (12 px). Body is 16 px; post body 16–18 px; `body` goes to 20 px/28 at large breakpoints. Banner titles are uppercase Poppins with tracking ("VIETNAM", "BLOG", "ABOUT US": `.title-banner` 36→64 px, letter-spacing 3→5 px). | `FONT_SANS` Poppins (400–700, **no 300**) | ✅ Poppins is the ecosystem sans. ⚠️ TripPlanner uses **Inter** (`var(--font-inter)`): switch it to Poppins. Add weight 300 only if a light lead paragraph is needed. |
| **Satisfy** (script) | `font-title`: **every customer section heading** ("Highlight Trips", "Explore Asia", "Top Destinations", "Why Adventure Asia", "Region map", "Day by day Itinerary", "Weather and Climate", "Travel FAQs"), post and tour H1s, footer column titles, the modal title "Enquire adventure trips". Sizes: `text-section` 40→50 px, `text-modal` 32→40 px, `leading-none`. | **not loaded** | ⚠️ Missing in the kit. **Customer surfaces only**, for H1/H2 section titles of 32 px and up and at most one per screen section. Never for UI labels, tables, forms, numbers, buttons or long tour names on mobile (the 4-line mobile H1 on the tour page shows why). Not in admin. |
| **Fahkwang** | `font-display`, `.h1–.h5`, `.p1`, `.caption`, `.btn-lg`; visible as the gold "Table of contents" label. It is loaded but rarely seen. | `FONT_DISPLAY` Fahkwang 500–700 (titles, big numbers) | ✅ Keep it as the **admin display face** (page titles, KPI numbers) and for small gold eyebrow labels on customer pages. It is the "serious" brand face; Satisfy is the "holiday" face. |
| Mono | — | JetBrains Mono (IDs, codes) | admin only |

Proposed type scale (px, desktop / mobile):

| Token | Customer (TripPlanner, Booking customer) | Admin (CIS, Booking staff) |
|---|---|---|
| display-hero | Poppins 600 uppercase, tracking .08em, 64/36 (banner) | — |
| title-script | Satisfy 50/40, line-height 1 | — |
| title-script-sm | Satisfy 40/32 (modal, card group) | — |
| h1 | Poppins 600, 32/24 | Fahkwang 600, 28 (kit PageHeader 24, ⚠️ Figma 32: use 28) |
| h2 | Poppins 600, 24/20 (post H2, "SUMMARY" uppercase 24) | Poppins 500, 20 (Figma section 22) |
| h3 | Poppins 600, 20/18 | Poppins 600, 15–16 |
| card-title | Poppins 400, 20/14, 2-line clamp | Poppins 500, 14–15 |
| body | Poppins 400, 16 (post 16–17, line-height 1.6) | Poppins 400, 13–14 (kit) ⚠️ Figma draws 17–18 at 1920 width: keep the kit's 13–14 |
| meta / caption | Poppins 400, 12–13 | 12 |
| eyebrow | Fahkwang 600, 14, gold-600 ("Table of contents") or Poppins 500 uppercase 13 gold-700 ("DURATION") | Poppins 400 uppercase 11–12, tracking .04em (sidebar section labels) |
| price | Poppins 600, 20, gold-600, prefixed by "From" 14 black | Poppins 600 tabular |

### 2.3 Radius

| Element | Site | CIS kit | Figma (Booking) | Decision |
|---|---|---|---|---|
| Header CTA "ENQUIRE", tour-detail CTAs, hero tagline chip | pill (`rounded-full`) | `BTN_RADIUS` 999 (all buttons) | 8 | ⚠️ **Pill = primary CTA on customer surfaces.** |
| Card buttons ("EXPLORE", "See More", "Read More", "FIND TOUR"), tabs, search input, inputs, cards, images | **0 (square)** | `RADIUS` sm 6 / md 8 / lg 12 | inputs 8, cards 16 | ⚠️ The site is square-edged editorial. **Customer: cards, images and inputs at 0–4 px** (keep the editorial look). **Admin: kit md 8 for inputs and buttons, lg 12 for cards.** Do not adopt the Figma's 16 (it doubles the kit). |
| Icons (activity glyphs, slider arrows) | circle, 40 px with a 1 px ring | 50% | — | ✅ |

### 2.4 Shadow

| Use | Site | Kit / TripPlanner | Decision |
|---|---|---|---|
| Card hover, FAQ active | `0 0 20px rgba(0,0,0,.10)` (no resting shadow) | TP `aa-sm` `0 1px 2px rgba(31,41,51,.06), 0 2px 8px rgba(31,41,51,.07)` | Customer: no resting shadow; on hover use `0 0 20px rgba(0,0,0,.10)` and turn the title gold. |
| Cover card hover | `0 0 20px rgba(0,0,0,.30)` | — | destination cover cards only |
| Image text scrim | `.shadow-box` `linear-gradient(1turn,#000,transparent 90%)` | — | ➕ `--aa-scrim-bottom` for text over a photo |
| Popover / dropdown | Tailwind `shadow-lg` | Topbar `0 12px 32px rgba(0,0,0,.18)`, DataTable `0 10px 30px rgba(0,0,0,.12)` | Use the kit. |
| Modal | — | `0 20px 60px rgba(0,0,0,.25)` | Use the kit. The Figma "gold glow" around the modal is dropped. |

### 2.5 Spacing and layout

- Container: max **1280 px** (`.container`) with 16 px gutters below 992. Reading column: **906 px** (day-by-day
  itinerary, FAQs at 905 px). Tour sidebar: **405 px** (included/excluded box). Blog body is about 928 px with a 288 px
  sticky TOC rail.
- Header height: **60 px mobile, 82 px desktop** (`--header-height-sm/md`).
- Card grid: 1 / 2 / 3 columns (`md` / `lg`), gap **16 px mobile, 32 px desktop**. Card inner padding is 8 px on mobile
  and 20 px on desktop.
- Section rhythm: about 64–96 px vertical between sections, alternating white and cream (`#F8F6F2`) bands.
- Base unit: 4 px. The site uses Tailwind steps 2.5/3/4/5/8/14/16. The kit has `SPACE` 4/8/12/16/22 and the Figma uses
  8/16/24/32. **Use 4-px steps; prefer 8/16/24/32 for layout.**

---

## 3. Customer-facing patterns (from the live site)

### 3.1 Header and navigation

- A dark navy bar (`#1B232C`, 82 px). Left: logo (gold mountains + "Adventure Asia"). Right: **Interest ▾**,
  **Destinations ▾**, About Us, Blog, a search icon, a wishlist heart with a gold count badge, a gold **outline-pill
  "ENQUIRE"**, and Account ▾ (Login / Signup / My wishlist).
- **Interest mega menu**: a full-width dark panel with 6 round line icons (40 px, white ring) and a label under each:
  Beach Retreat, Biking, Culture, Hiking, Water Activities, Wildlife. Each links to `/interest/<slug>` (hiking returns
  500 today).
- **Destinations mega menu**: a dark panel. On the left is "ALL DESTINATION" (underlined) and a 4-column list of 24
  countries. On the right is a promo image card with the overlay text "Browse more than 720 sample itineraries across
  Asia".
- Active or hovered nav items turn gold. Mobile: logo, search, heart, then a gold hamburger opening a drill-down menu
  with "Back" rows.
- Breadcrumb sits under the hero title: Home › Destination › **Vietnam** (current page in gold).

### 3.2 Search panel (home): tabs Quick search / Map / Featured trips

- Hero: a full-bleed photo carousel (4 slides, dot pager with a gold active dash). Each slide has a **gold pill tagline**
  (one of the four pillars) above a white search bar "Search by destination, activities" with a gold square "Search"
  button.
- Under the hero is a dark translucent strip with 3 large icon tabs: **Quick search** (→ `/search`), **Map**
  (→ "Explore More Asia": an amCharts-style Asia map, served countries in gold, the rest light navy `#C8D6E5`,
  home/+/− controls, and a 2-column country list on the right), **Featured trips** (→ "Highlight Trips" carousel).
  Mobile shows only Quick search and Featured trips.
- "Explore Asia" filter panel: a white box on a photo background. A search input sits on top. Left are vertical
  region tabs (Central Asia / East Asia / South Asia / Southest Asia [sic]; the active tab is filled gold). Right is a
  grid of place chips (square, 1 px grey border) grouped under country headings in uppercase. Below is the "Activities"
  row of 6 round icons. The footer has two equal-width buttons, **CLEAR ALL** (grey) and **FIND TOUR** (gold).
- `/search`: a gold "Search by destination, activities" trigger, "Sort by" (Relevance, Price ↑↓, Duration ↑↓, Level
  ↑↓), activity icon toggles on the right, the count line "**1042** Trips match your search criteria", a "Highlight
  trips" checkbox, then the card grid on a cream background.

### 3.3 Tour card anatomy (`.card-box`)

```
┌──────────────────────────────┐
│ [photo 3:2, object-cover]  ♡ │  ← gold outline heart, top 15 / right 20 (wishlist)
├──────────────────────────────┤  white body, p 8 → 20
│ Card title, 20px, grey-900,  │  2-line clamp; turns gold #DB9628 on card hover
│ line-clamp-2                 │
│ ⦿ 9   ▣ 9 days 8 nights  ▮ Leisurely │ meta row 12px grey-800: pin = number of places (unlabelled ⚠️), calendar = duration, bars = level
├──────────────────────────────┤  1px grey-200 rule
│ (◯)(◯) activity icons 29px   │  round ring #E3BD7F, glyph #DB9628
│ Summary, 14px light, 3-line  │  hidden on mobile
│ clamp                        │
├──────────────────────────────┤  1px grey-200 rule
│ From $1,699        [EXPLORE] │  "From" 14 black + price 20/600 gold-600; square outline-gold button, uppercase 14
└──────────────────────────────┘
```
Behaviour: there is no resting shadow; hover adds `0 0 20px rgba(0,0,0,.1)` and turns the title gold. The grid is
3-up on desktop. On the home page it is a carousel with square white arrow buttons (48 px) outside the grid.
Destination "cover cards" are a different pattern: a tall portrait photo, a bottom black-gradient scrim, the country
name (Poppins 20, white) and a tagline (12 px), e.g. "Japan, Land Of The Rising Sun".

**Improve when reusing:** label the pin count ("9 places"); always show a level; hide the "From" row when there is no
price, or show "Price on request"; and show the duration in days only, consistently (the site mixes "8 DAYS",
"9 days 8 nights", "3 hours", "7").

### 3.4 Tour detail anatomy (`/itinerary/<slug>-<id>`)

1. **Gallery carousel**: a centred 16:10 photo (960 px) with neighbouring slides faded at the edges and square white
   arrows.
2. Breadcrumb: Home › Search › **Trip**.
3. **H1 in Satisfy** (about 50 px, centred).
4. Key facts row, 3 columns: **DURATION** "9 days 8 nights" · **DESTINATION** "Ho Chi Minh" (the start city only ⚠️)
   · **PRICE PER PERSON** "From $1,699". The labels are uppercase 13 px gold-700.
5. Activity icons (round).
6. CTA pair: **ENQUIRE** (gold filled pill) and **♡ ADD TO WISHLIST** (gold outline pill).
7. Section tabs (anchor): **OVERVIEW** (active: white with a gold border) | HOTELS | SIMILAR ITINERARIES | WHERE TO GO
   NEXT (inactive: filled gold). This inverted style also appears on destination pages (OVERVIEW / ITINERARIES /
   HOTELS).
8. Two columns. Left: **SUMMARY** (uppercase H3 24) paragraph and **HIGHLIGHTS** (gold-dot bullets). Right: a cream box
   405 px wide holding "What is included in this tour?" (subtitle "Items that are included in the cost of tour price.",
   a gold rule, ✓ gold ticks) and "What is not included…" (✕ gold crosses).
9. **Route map** (Mapbox) with numbered gold-brown pins per day.
10. **"Day by day Itinerary"** (Satisfy): an accordion of rows, `DAY 1` (gold-700, semibold) + `SAIGON - CAI BE - CAN THO`
    (uppercase bold grey-800), a chevron and a gold-700 bottom rule. Expanded: "LEVEL Leisurely", narrative paragraphs
    (16 px grey-600), then "Hotel options": hotel mini-cards (photo, name, LOCATION, HOTEL TYPE: Authentic, Resort,
    Luxury, Boutique) opening a hotel detail modal.
11. Instagram strip and footer. A hidden "Please leave your email, to get your perfect trip in PDF format" modal.

The level vocabulary seen is **Leisurely · Fairly Easy · Moderate · Strenuous**. The enquiry form offers only 3 of them
and misspells one (§5).

### 3.5 Destination guide anatomy (`/destination/<slug>`)

1. A full-bleed hero photo (630 px) with an uppercase tracked white title ("VIETNAM") and a breadcrumb.
2. Tabs: OVERVIEW | ITINERARIES | HOTELS.
3. **"Region map"**: an SVG country map with gold ring markers per place, map controls, and a 2-column list of places
   (each links to `/search?destination_ids=<id>`).
4. **"General information"**: a collapsed long-form text with a fade-out and an outline **See More** button. Today it
   leads with the 2022 COVID reopening notes (⚠️ stale).
5. "<Country> itineraries": the tour card grid (3-up).
6. Hotels: hotel cards.
7. **"<Country> goes well with"**: 4 portrait cover cards of neighbouring countries.
8. "Why Adventure Asia": the positioning paragraph over a misty-mountain image band.
9. **"Event Festival"**: "Browse a month-by-month breakdown…". A month header bar (gold-700 fill, white uppercase),
   then the festival name and description, and **Read More** (gold filled square).
10. **"Weather and Climate"**: image left, text right (justified ⚠️), See More.
11. **"Travel FAQs"**: a white accordion on cream. A plus icon turns into a gold minus; the active row is gold-bordered
    with a shadow. Fixed topics: Essential Information, Getting There, Getting Around, Visa and Permits, Local Customs,
    Events and Festivals, "What will it cost for a…?", credit cards, ATM, refund policy.

### 3.6 Blog layout

- **Index** (`/blog`): a hero image with a "BLOG" title. Category filter: a text row separated by pipes (All active in
  gold, then Vietnam, Nepal, Thailand, Cambodia, Laos, Bhutan, Everest, Trekking vs hiking, Adventure South Korea).
  Featured layout: 1 large post on the left plus 3 stacked small posts (thumbnail + gold category eyebrow + bold title
  + 2-line excerpt) on the right. Then a 3-up grid, "View more", and a **"Hot itineraries"** tour-card row.
- **Article**: a hero photo with a breadcrumb (Home › Blog › Country › Title). A cream title band with the H1 in Satisfy,
  centred. Two columns:
  - main (about 928 px): intro, numbered H2/H3, full-width images with captions, **inline tour cards** mid-article
    (image, title, duration, excerpt, "From $2,208", Explore), and ">>> Discover more:" internal links;
  - right rail (sticky, 288 px): "**Table of contents**" (Fahkwang, gold), "Share" (Facebook, LinkedIn, copy link as
    square grey buttons), and "Rating" (5 stars).
  - The end: "Posted date: 07/17/2024" (US format ⚠️), tag links, and "Related Posts". The new posts add an **FAQ**
    (H3 questions), a "Plan With Adventure Asia" closer with 2 buttons, an "Author: Adventure Asia Editorial Team" line
    and a disclaimer.

### 3.7 Enquiry form (modal "Enquire adventure trips", tabs ENQUIRE ONLINE / FIND US)

Intro: "Please fill in your details below and we will contact you by phone or email within 24 to 48 hours with a
tailor-made price & itinerary proposal. Required fields are marked with an asterisk (*)." (shown in red).

| # | Field (live label) | Type / options | Required |
|---|---|---|---|
| 1 | Your Name | text | ✔ |
| 2 | Email Address (We will not spam you) | text, placeholder "Where should we send confirmation email to?" | ✔ |
| 3 | Activity (multi selection) | checkboxes: Beach Retreat, Biking, Culture, Hiking, Water Activities, Wildlife | ✔ |
| 4 | How challenging would you like the tour? | select: Fairly Easy, Moderate, Strenuos [sic] | ✔ |
| 5 | Where would you like to visit? (multi selection) | multiselect of 24 countries | ✔ |
| 6 | How long would your trip be? | select: 5-7, 8-10, 11-14, 15-20 days | ✔ |
| 7 | When would you like to go? | select: Month (Jan–Dec) | – |
| 8 | How many people in your group? | select: 2-5, 6-10, 10-14 | ✔ |
| 9 | Style of accommodation would suite you [sic] | select: Luxury, Resort, Boutique, Authentic, Eco/homestay | – |
| 10 | Extra City Break | radio Yes / No | – |
| 11 | Is there anything else we need to know… | textarea | – |
| | Submit "Send Enquire" | gold | |

"FIND US" tab: Adventure Asia, Inc. (Brisbane, QLD, Australia 4000) and Adventure Asia (Vietnam) Co., Ltd (13 Hung Gia 4,
Tan Phong, District 7). Inputs are filled light grey (`#EDEDED`-ish), square and borderless; labels are 14/600 above.

**Gaps to fix in the ecosystem version** (it maps to Booking `customers` plus the `inquiry.submitted` v1.1 contract):
no phone or WhatsApp field even though "we will contact you by phone"; no country of residence; no exact dates or
flexible window; groups of 1 (solo) and 15+ are impossible and the ranges overlap (6-10 / 10-14); durations end at 20
days although 22–26 day trips are sold; the level list is missing "Leisurely" and "Strenuous" is misspelt; no
budget-per-person band; no consent checkbox (privacy, marketing). Add a "trip of interest" hidden field when the form is
opened from a tour.

### 3.8 Footer and trust

- An Instagram strip ("@adventureasia365" in gold over a 6-photo row), then a dark navy footer in 5 columns:
  1. logo plus Facebook, Instagram and YouTube round icons;
  2. **About us** (Satisfy title) with the positioning text (justified ⚠️);
  3. **Office – Vietnam**: "Open Hour: 9:30am – 6:00pm", the address "G floor, Building B, Incubition [sic] Tower,
     District 7, Ho Chi minh city", "Business Certificate(ABN): 68831347858";
  4. **Contact us**: ☎ +61 420 946 007, ✉ info@adventure.asia, 📍 Brisbane, QLD, Australia 4000;
  5. **Payment method**: logos for **VISA, Mastercard, PayPal, Maestro, Bank transfer** (`/images/{visa,mastercard,paypal,maestro,bank-transfer}.svg`).
- "© Copyright 2022 Adventure Asia". A floating "↑ Top" control at the bottom right.
- Trust signals that are missing today and worth adding in the ecosystem: licence and registration numbers per
  entity, real reviews (the star "Rating" widget has no count), the "Checked on the ground" proof (who checked, and
  when), and the payment protection or refund policy as a link rather than only a FAQ row.
- Two offices with different addresses appear (the form's "13 Hung Gia 4" and the footer's "Incubition Tower").
  Reconcile them before reuse.

---

## 4. Staff and admin patterns (Figma layouts on the same tokens)

The Booking staff Figma (`01-shell.md`) already uses the brand gold `#DB9628`, so it maps onto the CIS kit with few
changes. Rules:

- **Shell = the CIS kit** (`AdminShell`, `Sidebar`, `Topbar`, `PageHeader`, `Tabs`, `DataTable`, `Modal`, `Drawer`,
  `Toast`, `BottomNav`). The kit uses inline styles, `K` tokens and no Tailwind; Booking copies that convention or uses
  Tailwind with the same `--aa-*` variables. Pick one per repo and do not mix them.
- **Sidebar**: dark `--aa-side-bg` `#1F2933`. The Figma gradient `#18212A → #111820` is dropped (one flat navy, same as
  the site footer). Section labels are uppercase 11–12 px `--aa-side-text2`. The active item is a pill `#303941` with
  gold icon and text. Lucide icons, 20–24 px, stroke 1.5. The Figma "logo band gradient → gold" is **optional**; the
  site never fades navy into gold, so prefer a flat navy with the gold logo.
- **Page header band**: `--aa-bg` cream `#F8F6F2`, not the Figma cool `#F4F6F8` (C-12). Title in Fahkwang 600 at 24–28,
  subtitle in Poppins 13–14 muted, primary actions on the right.
- **Cards**: white, 1 px `--aa-line`, radius **12** (kit lg; the Figma says 16), 24 px padding, no "double border frame".
- **Buttons**: primary gold fill with white text. Hover `#9E6E16`. Height 36–40 admin (the Figma's 48 is at 1920 width).
  The kit pill vs the Figma radius 8 is an open point (⚠️). **Proposal: admin buttons at radius 8. Keep pills for
  customer CTAs and for status badges only.** The kit `BTN_RADIUS` would change for admin; this needs Nghiệp's
  decision because it touches every CIS page.
- **Badges**: soft pairs with a leading dot (kit `TONE`/`StatusBadge`). Map the Figma colours to kit tones: neutral,
  amber, orange→amber, info, success, danger. Audit actions are uppercase; everything else is Title Case.
- **Tables**: header row `--aa-panel-bg0`, 13 px uppercase muted header, 2-line cells (title + secondary), checkbox
  column, the footer "Showing 1–10 of N" with pagination (current page filled gold). Use the kit `TableSkeleton`,
  `EmptyState` and `ErrorState`. The Figma draws none of these.
- **Tabs**: gold text with a 2 px gold underline on a 1 px grey baseline (Figma = kit). **Do not** reuse the site's
  inverted filled-gold tab blocks in admin.
- **Forms**: label above (13–14 px, 500), inputs 36–40 px, radius 8, white with a 1 px line (not the Figma's filled grey),
  locked fields with a lock icon and "Managed in CIS" helper text (O1).
- **Gold usage in admin**: gold only for the primary action, the active nav, the active tab, links and the current page.
  Status colour comes from the semantic tones, never from gold. No Satisfy anywhere in admin.
- **Dark mode**: admin gets it via the kit `[data-theme]`; the sidebar stays dark in both themes.
- **Mobile**: the sidebar becomes a drawer plus the kit `BottomNav` (C-13), with a 16 px gutter.

---

## 5. Do / Don't

### Do

- Use Poppins for everything readable, Satisfy only for big customer section titles, and Fahkwang for admin titles,
  numbers and eyebrow labels.
- Use gold `#DB9628` for one primary action per view plus prices and active states. Hover `#9E6E16`.
- Alternate white and cream `#F8F6F2` section bands on customer pages; use the navy `#1F2933` header and footer.
- Use big, honest photography of the actual Asian place, with a bottom scrim when text sits on it.
- Write in the 2026 voice: concrete numbers (km, m, hours, months), trade-offs, pacing, an honest caveat, and a
  disclaimer that logistics shift by season and supplier.
- Show **trip level** (Leisurely, Fairly Easy, Moderate, Strenuous), duration in days, place count *with a label*, and
  "From $X per person".
- Put a TOC, numbered sections, FAQs and inline trip cards in long content.
- Date format: "17 Jul 2024" (the kit's `formatDate`, en-GB), not "07/17/2024".

### Don't

- Don't use the orange `#FF6F00` / `#E56400` (site leftovers) or a second gold-dark `#B87A1A`.
- Don't set Satisfy below 32 px, in buttons, labels, tables or admin, or on 3+-line titles on mobile.
- Don't justify body text (footer About and destination Weather): it makes "rivers".
- Don't bake text or watermarks into images (blog thumbnails carry burnt-in titles and "WWW.ADVENTURE.ASIA").
- Don't publish stale operational content (the 2022 COVID reopening blocks lead the Bhutan and Vietnam guides; Bhutan
  fee figures are dated). Every practical fact needs a "verified on" date.
- Don't use non-Asia stock imagery for an Asia brand (the About page appears to show a Canadian-style highway and a
  European castle).
- Don't contradict difficulty (e.g. a 26-day "Cycle Yunnan–Tibet" labelled "Fairly Easy") or counts (720 vs 1042 trips).
- Don't ship cards with an empty "From" price or unlabelled numbers.
- Don't link to the wrong target (the Paro post's "Bhutan must know before travel" points at the **Laos** page; the
  Korea post's "Request custom trip design" points at `www.adventure.asia` as a relative link; "Get the guide" opens an
  itinerary page; the Phong Nha post links `/destination/vietnam-must-know-before-travel`, which is not the live slug).
- Don't leave broken routes (`/interest/hiking` → HTTP 500) or empty SSR sections ("Highlight Trips: No results" in the
  server HTML; the "Explore More Asia" map renders blank until scripts load).
- Don't copy the Figma placeholders ("key System Metric", "Requires attentions", "Save Changs", Lorem ipsum, "African
  Savanna Experience").

### Typos and copy errors seen on the live site (never copy them)

| Seen | Correct | Where |
|---|---|---|
| "ADVENTURE AT IT'S BEST" | "Adventure at its best" | `<title>` |
| "Real trips. Check on the ground" | "Real trips. Checked on the ground." | hero H3 (the alt text is correct) |
| "Strenuos" / "Strenous" | "Strenuous" | enquiry form / search sort |
| "Style of accommodation would suite you" | "Which style of accommodation suits you?" | enquiry form |
| "Please seclect a style…" | "Please select…" | enquiry form |
| "Send Enquire" | "Send enquiry" | enquiry submit |
| "you will be contected by our sales staff" | "contacted" | thank-you modal |
| "Southest Asia" | "Southeast Asia" | Explore Asia tabs (and Central Asia lists Cambodia/Indonesia: wrong grouping) |
| "All Destination" | "All destinations" | mega menu |
| "Incubition Tower", "Ho Chi minh city" | "Incubation Tower" (verify), "Ho Chi Minh City" | footer |
| "Business Certificate(ABN)" | "ABN" (Australian Business Number) or the VN business registration no. | footer |
| "© Copyright 2022" | current year | footer |
| "We Cater to a Entire Family!" | "We cater to the entire family" | About |
| "KuChing", duplicate "Oudomxay" | "Kuching" | place chips |
| "Masutake Mushroom Festival" | "Matsutake" | Bhutan tours |
| "Punkha", "populutio", "contingency dy" | "Punakha", "population", "day" | Bhutan |
| "Tra Su mangrovie", "ncidental expenses", "Ho Chi Minch City", "Enjoyings", "Victoria Nui SAm" | "mangrove", "Incidental", "Minh", "Enjoy", "Sam" | Mekong tour |
| "3 days 2 night" | "3 days 2 nights" | search card |
| "traditional mark dances" | "mask dances" | Paro post card |
| "Lothse", "Ama Dalam", "Kyashar Kholar" | "Lhotse", "Ama Dablam", "Kyashar Khola" | Nepal post |
| "Table Contents" | "Table of contents" | post rail (inconsistent) |
| "The Enchanting of Paro Valley" | "The Enchantment of Paro Valley" | post title |
| two sections numbered "2.4" | renumber | Paro post |
| "Can I visit Vietnam without quarantine ?", "What's your refund policy ?" | no space before "?" | FAQs |

---

## 6. Guidance per app

### 6.1 AA-TripPlanner-Web (customer front door, map-first)

- **Fonts**: replace Inter with **Poppins** (`next/font/google`, weights 400/500/600/700). Add **Satisfy** for the
  2–3 marketing headings only (landing hero subtitle, "Your trip" panel title, empty state). Planner UI text stays
  Poppins.
- **Tokens**: rename the `aa.*` Tailwind colours to the shared names, set `gold-dark` to `#9E6E16` (it is `#B87A1A`
  today), add `line` `#E9E4DB`, `map-land` `#C8D6E5` and `navy` `#1F2933`. Keep the TP shadows (`aa-sm`), which fit.
- **Header**: the navy bar as on the site (logo, Interests, Destinations, Wishlist, a gold pill **Enquire**). TP is
  the "One curated source. Zero tabs open." pillar, so use that as the hero line.
- **Map**: style it like the site's "Explore More Asia" (served countries gold `#DB9628` at about 70%, others
  `#C8D6E5`, white borders). Day-route pins are numbered gold-brown teardrops, as on the tour map.
- **Trip panel cards**: reuse §3.3, but **square images, gold title on hover, a labelled meta line ("9 places · 9 days
  · Moderate"), and the price row "From $X pp"**. Activity glyphs come from the same 6-icon set (circle ring
  `#E3BD7F`).
- **Explaining a plan**: use the new-voice pacing vocabulary ("energy arc", "one major move per day", "buffer day
  before departure") and the caveat line. Never invent services (CIS source-fidelity policy).
- **Enquire (hand-off to Booking)**: the improved §3.7 form, split into 2 steps (1: trip shape: interests, countries,
  level, dates/window, length, group size, budget; 2: contact: name, email, phone/WhatsApp, country of residence,
  consent). It pre-fills from the plan. The confirmation copy promises the 24–48 h reply.
- **Wishlist heart** top right on every card, with a gold count badge in the header (same as the site).
- **Light theme only**. Mobile: a bottom-sheet trip panel over the map, a 16 px gutter, and Satisfy capped at 32 px.

### 6.2 AA-Booking staff admin

- **Copy the CIS kit** (the shell spec §4 build order) and re-skin only the nav. No new colours: the Figma maps 1:1
  onto `--aa-*`, apart from the four resolved conflicts: cool grey header → cream; card radius 16 → 12; the sidebar
  gradient → flat `#1F2933`; danger `#D9534F` → `#C20101`.
- Page titles in Fahkwang; KPI numbers in Fahkwang 600 with tabular figures; everything else in Poppins 13–14.
- Trip-case status badges use the kit tones mapped to the 13-value enum groups (shell C-6). Money uses tabular Poppins
  600, with the currency code always shown (ADR 0005, USD base).
- Content that belongs to CIS (countries, destinations, activities) is shown read-only, with an "Edit in CIS" link and
  a muted "Managed in CIS" chip.
- Microcopy follows the new voice: short and literal ("3 rate sheets awaiting publish", not "Requires attentions").

### 6.3 AA-Booking customer pages (proposal view, payment, my trip)

- These are **customer-facing**, so they use the site look, not the admin kit: navy header, cream/white bands, Poppins,
  and a Satisfy title for the proposal ("Your Mekong journey").
- **Proposal page** = the tour detail anatomy (§3.4) driven by the trip case. The key facts row (Duration, Route,
  Price per person, Valid until), "What's included / not included" box, day-by-day accordion with hotel options, route
  map, and a gold pill **Accept & pay deposit** next to an outline **Ask a question**.
- **Payment page**: a summary card (square, 1 px line), a payment schedule table (due date, amount, status badge), the
  payment-method logos (Visa, Mastercard, PayPal, Maestro, Bank transfer) as on the site footer, and a trust line
  (refund policy link, the legal entity per payment).
- **Emails and PDF** (the "perfect trip in PDF format"): gold `#DB9628` accents on white, Poppins (fallback Arial), a
  Satisfy wordmark-style title as an image only if needed, and the footer with both offices and the ABN.
- Light theme only, with mobile first: CTAs full-width on mobile, as the site's mobile Search button already is.

### 6.4 AA-CIS admin and tenant portal

- **Admin**: already on the kit. Actions:
  1. Unify the hover gold: map `--brand-gold-dark` `#B87A1A` → `#9E6E16`.
  2. Unify the cream: legacy `--bg-primary` `#F4F1EC` vs `--aa-bg` `#F8F6F2`. Migrate to `#F8F6F2` when the login pages
     are next touched.
  3. Decide the admin button radius (pill vs 8; §4). Same decision as Booking, so the two admin apps match.
  4. No Satisfy in admin.
- **Tenant portal** (`T` object, light): this is the closest surface to customers. It may use Satisfy for the portal
  welcome and section titles (≥ 32 px). Content previews of T-pipeline outputs (T2/T9) should render in the **customer
  look** (§3.3 card, §3.4 tour anatomy) so tenants see what travellers will see.
- **T-pipeline writing guidance** (writer prompts): use the §1 new-voice rules, the headline patterns in §1.3 (no "Nestled",
  "Unveiling", "tapestry", "Embark") and concrete numbers. Seasonality goes with a "verified" date and the practical
  block (Seasonality / Permits / Guides / Respectful exploration). Never claim what the source lacks.

---

## Open decisions for Nghiệp

1. **Admin button radius**: kit pill (999) vs Figma 8. The proposal is 8 in admin and pill for customer CTAs.
2. **Satisfy**: adopt it as the customer heading face (proposed), or drop it ecosystem-wide for a cleaner look.
3. **Card radius in admin**: 12 (kit lg, proposed) vs 16 (Figma).
4. Whether to send the live-site typo and broken-link list (§5) to chị Thư / the site owner. The site itself is not in
   our repos.
