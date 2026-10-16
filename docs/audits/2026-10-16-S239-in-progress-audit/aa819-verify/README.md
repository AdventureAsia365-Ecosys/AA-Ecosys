# AA-819 verify: TripPlanner #86 + #87 on Dev (S239, Claude Code)

Live check on https://tripplanner.lumiguides.it.com, 16/10/2026 ~02:10–02:25 UTC. No login, no secrets.
Exactly **one** narrate call in the whole run (Playwright route guard aborts any second one; the follow-up run aborts all).
Server-side writes: only the anonymous trips the planner creates when `/plan?tour=…` pins a route (2: main run + follow-up).

Scripts (not committed): `.tmp-session/s239/aa819v/verify.mjs`, `followup.mjs`; raw output `verify_out.json`, `followup_out.json`.

## Deployed build

| Item | Evidence |
|---|---|
| #86 `5420863` (labels + D1 resolver) | merged 01:36Z; CI success; **Deploy Lambdas success** (`5420863`) |
| #87 `6feb8f6` ("Adventure Asia AI" / "AA AI") | merged 01:43Z; CI success; Vercel serves it |
| Pre-check | `curl` `/`, `/plan`, `/tours/<slug>` → 200; HTML contains "Adventure Asia AI" (6/3/9 hits); "AI-assisted" only inside the site explanation text. No wait needed. |

## Steps and results

### 1. Planner: `/plan?tour=78c5f4b7-5648-40ca-8d01-2474d785148a&source=a4966d23`, Compose once
- Pins: Day 1 Fatehpur Sikri (component `13520c53…`, tour `fbadec01…`, source day 16); Day 2 Amber Fort (component `2f11a430…`, tour `e716b1eb…`, source_day_index 5).
- `POST /api/trip` op=narrate → **200**, `source=master`, `ai_generated=true`, `cached=false`, 2 days. Narrate calls in total: **1**.
- **Day 2 now reads "Jaipur: Amber Fort, City Palace & Hawa Mahal"** ("Visit Amber Fort, City Palace, and the well-known Hawa Mahal … Overnight in Jaipur."). Before (S239 audit, same URL): "Khimsar to Jaisalmer". PASS.
- Day titles on their own line: each day block has 2 `<p>` (title `font-semibold`, then prose), title top 377/680 px, prose top 397/700 px. PASS (`05-plan-1440-narration-block.png`).
- Badge at 1440 renders **"AA itinerary · Adventure Asia AI"**; tap → `aria-expanded=true` + panel visible, tap again → closed; focus + **Enter** → open; Escape → closed. No clipping, no page overflow. PASS (`06-…-tap-open.png`, `06-…-enter-open.png`).
- Badge at 390 (same page, no second call) renders **"AA itinerary · AA AI"**; tap / Enter / Escape all PASS, panel inline at x 29–361 (`08-plan-390-narration-badge-*.png`).
- Header pill: "Adventure Asia AI" at 1440, "AA AI" at 390; tap/Enter/Escape PASS (`02-*`, `07-*`, `13-plan-1440-header-pill-open-viewport.png`).

### 2. Tour page `/tours/delhi-agra-jaipur-three-capitals-in-2-days-india-a4966d23` (1440 + 390, light + dark)
- All 4 variants → **200**, theme applied (`data-theme` light/dark; body bg `rgb(248,246,242)` / `rgb(15,20,27)`), 0 console errors, 0 HTTP ≥ 400.
- Labels present on **summary, Highlights, Day by day** in every variant: "Adventure Asia AI" at 1440, "AA AI" at 390. Header pill same.
- Explanation opens by tap and by Enter, closes by second tap / Escape: PASS on all 3 labels + header pill, all 4 variants (24 label exercises + 4 header).
- Dark panel uses theme tokens (bg `rgb(25,33,44)`, text `rgb(212,218,226)`); light panel white / `rgb(51,54,61)`.
- **Defect D-A** at 390 (light + dark): see below. 1440 and the 390 summary label do not overflow.
- Screenshots: `2x-tour-<w>-<theme>-{top,full}.png`, `2x-tour-<w>-<theme>-<i>-<section>-{tap,enter}-open.png`, `2x-tour-<w>-<theme>-header-pill-*.png`, `11-tour-390-<theme>-label{1,2}-viewport.png`.

### 3. Map popup + stop activity list (planner)
- Stop activities (Fatehpur Sikri, "Activities here"): label "Adventure Asia AI" (1440) / "AA AI" (390) under the list; tap/Enter/Escape PASS; explanation opens inline, inside its scroll box, no clipping (`03-*`, `09-*`).
- Map popup (opened via the "+ Hawa Mahal" suggestion = focusDestination, no trip change): label "Adventure Asia AI" (1440) / "AA AI" (390, Explore tab); tap/Enter/Escape PASS; inline panel at x 689–1007 (1440) and 39–357 (390), no clipping ancestor, no page overflow (`04-*`, `10-*`, `12-*`).

## Verdict per Done-when bullet (AA-819)

| Done-when bullet | Verdict |
|---|---|
| Notice visible in portal review/publish | Not in this task (PASS earlier, S237 `ui-verify/`) |
| T9 testimonial prompt blocked/rewritten | Not in this task (separate `aa819-f19/`) |
| 21st publish returns a clear limit error | Not in this task (PASS S238, 429 evidence) |
| **TripPlanner badge audit screenshots** (scope 4: badge on every AI-written block, mobile) | **PASS with one defect (D-A)**: labels present and honest on header, tour summary/Highlights/Day by day, narration, map popup, stop activities; open by tap and keyboard at 1440 + 390, light + dark; D1 narration fixed live. Share/export: the planner has no share/export control (S239 audit), nothing to label. |

## Defects

- **D-A (layout/a11y, low–medium): tour page at 390, the Highlights and Day by day explanations run off the right edge.** Panel rect right = 400 px (Highlights) and 408 px (Day by day) on a 390 px viewport; `document.scrollWidth` becomes 400 / 408, so the page scrolls sideways and the last ~10–18 px of each line is cut (`11-tour-390-light-label2-viewport.png`, same in dark). Cause: `AiLabel` popover is `absolute left-0 w-64 max-w-[calc(100vw-2rem)]`, anchored at a label that sits right of the heading (x 144 / 152); the max-width ignores the left offset. Fix options: `placement="inline"` for the heading-row labels (or below sm), or right-align / clamp the popover to the viewport.
- **D-B (copy, minor):** the site pill explanation still says "Trip narration is AI-written or AI-assisted, as its label says", but after #87 no label says "AI-assisted" (they say "AA itinerary · Adventure Asia AI" / "Adventure Asia AI narration").

## Observations (not AA-819 defects)
- The route card still shows "Rajasthan: Forts, Havelis & Desert — 22 Days · tour day 5" for Amber Fort, and the narrate response keeps `source_day_index: 5`: the frozen `itinerary_components` row is unchanged by design (#86 fixes the resolver, not the row). The narration is right; the card's "tour day 5" is still the Khimsar→Jaisalmer day.
- The Hawa Mahal map popup lists 6 identical "Hawa Mahal — visit" experiences (catalog duplication).
- 📍 / ✈️ render as boxes in headless Chromium (missing emoji font in the test machine, not the product).
