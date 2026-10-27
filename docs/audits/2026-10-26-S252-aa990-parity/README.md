# AA-990 item 1 — TripPlanner parity sample on the S1 v2 catalogue (Dev, $0)

Run: 26/10/2026 (S252), Claude Code. Host: <https://aa-tripplanner.vercel.app> (Dev TripPlanner, Vercel).
Goal: check that TripPlanner still works after all 892 active tours were rewritten (S1 v2) and re-atomized on 25/10/2026.

**Result: no 5xx, no 4xx, no console errors, and the v2 text renders on all 43 sampled tours in 14 countries.**
Every tour page loads (200). The day list matches the browse API's `duration_days` on 42 of 43 tours.
Every tour-route read answers 200. There are three findings: one is a real front-end bug (single-pin static
map) and two are about the data (see Findings).

## Method

1. **Catalogue**: the whole catalogue came from the public BFF
   `GET /api/browse?resource=catalog-tours&limit=60&offset=0..840` (15 pages): 892 tours, all `lifecycle_stage=active`.
   It has **14 countries, not 17** (see Finding 3).
2. **Selection**: for each country, up to 12 tours spread evenly over the list were checked with the planner's whole-route
   read `GET /api/browse?resource=tour-route&tour_id=…&source_id=…` (145 checks, all 200). The selection took 3 tours
   that have a route (`match` = `tour_graph` or `places`) first. Where the country also had a tour with no route
   (`match: "none"`, day list only), one of those was added. Countries with fewer than 3 routed tours were topped
   up with day-list-only tours. Vietnam has only 1 tour in the catalogue.
3. **Per tour** (Playwright Chromium from AA-CIS-App, one browser, run one at a time, light scheme, viewport 1440×900):
   - opened `/tours/<slug>` and recorded the document status and every response from the TP host, Mapbox and the CIS
     photo host. It also recorded console errors, page errors and failed requests;
   - from the DOM: the "Day by day" list (count, number, title, body length), summary, subtitle and highlights,
     the "Where you go" section (pins, lines), whether the static map `<img>` decoded (`naturalWidth > 0`),
     and the JSON-LD `TouristTrip` day count;
   - the tour-route read again: status, `match`, legs (= `segments`), `total_days`, or the fallback day list;
   - text check ("v2 text OK"): the summary is not empty, at least 1 day, every day has a title and a body, and no
     placeholder pattern (`lorem`, `TODO`, `TBD`, `placeholder`, `undefined`, `null`, `NaN`, `{{`, "being prepared").
4. **Country page**: `/destinations/<slug>` was opened once per country (status, tour links, console errors).
5. **Guards (no LLM, no writes)**: a `page.route` blocked any URL with `narrate`/`compose`, any non-GET
   `/api/trip`, `/api/browse?resource=search` (query embedding) and any non-GET `/api/auth`. **Nothing hit
   these routes:** the tour and country pages do not call narrate, compose or search on their own.
   The planner (`/plan?tour=…`) was **not opened**, because on load it calls apply-route, which creates a guest
   trip (a DB write). Its route data was read through the GET-only tour-route read instead.
6. **Screenshots**: one tour per country at 1440 and at 390 (light), clipped from the top of the page to the end
   of the map section, or the day list when the tour has no map. That makes 28 images in `shots/`, all under
   400 KB. A PNG over 400 KB was saved as JPEG (quality 70 or 55). On the 390 shots, the fixed mobile CTA bar
   shows part-way down the page. This comes from the full-page capture and is not a layout bug.

Raw results per tour are in `results.json`: `tours[]`, `countries{}`, and the selection checks under
`method.selection_probes`. Mapbox tokens are replaced with `REDACTED`. The file holds no cookies or session data.

## Per-country summary

"Pages OK" means the tour page returned 200, no 5xx, and the tour-route read returned 200. "Day match" means the
days shown equal the browse API's `duration_days`. "Map OK" counts tours with a "Where you go" section whose
map image loaded, out of the tours that have the section. Under "Route", G is `tour_graph`, P is `places` and
N is `none`. Legs: every routed tour is one segment (1 leg). The country page returned 200 for all 14 countries.

| Country | Tours | Pages OK | 5xx | Day match | Map OK | Route (G/P/N) | v2 text OK | Console errors |
|---|---|---|---|---|---|---|---|---|
| Bhutan | 3 | 3 | 0 | 3/3 | 3/3 | 3/0/0 | 3 | 0 |
| China | 3 | 3 | 0 | 3/3 | 3/3 | 3/0/0 | 3 | 0 |
| India | 3 | 3 | 0 | 3/3 | 3/3 | 3/0/0 | 3 | 0 |
| Japan | 4 | 4 | 0 | 4/4 | **2/3** | 2/1/1 | 4 | 0 |
| Laos | 3 | 3 | 0 | 3/3 | 3/3 | 3/0/0 | 3 | 0 |
| Mongolia | 3 | 3 | 0 | 3/3 | 3/3 | 3/0/0 | 3 | 0 |
| Nepal | 3 | 3 | 0 | 3/3 | 3/3 | 3/0/0 | 3 | 0 |
| Pakistan | 3 | 3 | 0 | 3/3 | — (no map) | 0/0/3 | 3 | 0 |
| Philippines | 3 | 3 | 0 | 3/3 | — (no map) | 0/0/3 | 3 | 0 |
| South Korea | 4 | 4 | 0 | 4/4 | 3/3 | 3/0/1 | 4 | 0 |
| Sri Lanka | 3 | 3 | 0 | 3/3 | 3/3 | 3/0/0 | 3 | 0 |
| Taiwan | 3 | 3 | 0 | 3/3 | **1/2** | 2/0/1 | 3 | 0 |
| Thailand | 4 | 4 | 0 | 4/4 | **3/4** | 3/0/1 | 4 | 0 |
| Vietnam | 1 | 1 | 0 | **0/1** | 1/1 | 1/0/0 | 1 | 0 |
| **Total** | **43** | **43** | **0** | **42/43** | **31/34** | **32/1/10** | **43** | **0** |

Places built: 34 of the 43 tours show a "Where you go" map from catalog places. 33 have a planner route: 32 from
the Tour Graph and 1 from places. The other 10 have only a day list. The 145 selection checks show the same
split by country. Bhutan, China, India, Laos, Nepal and Sri Lanka had a route on 12/12; Mongolia on 12/12
(1 from places). Japan had 3/12, Taiwan 2/12, Thailand 3/8 and South Korea 3/4. **Pakistan and Philippines
had 0/12.**

### Per tour

The tour page is `https://aa-tripplanner.vercel.app/tours/<slug>`; the full slugs are in `results.json`. In
"Days shown / API", API is `duration_days`. "Route days" is the tour-route `total_days`, or the length of the
fallback day list when there is no route. "Map pins/lines" is the page's "Where you go" list.

| Country | Slug suffix | Days shown / API | Route | Legs | Route days | Map pins/lines | Map img |
|---|---|---|---|---|---|---|---|
| Bhutan | 4a2411b2 | 7 / 7 | tour_graph | 1 | 7 | 10/0 | ok |
| Bhutan | 8b6ce67b | 7 / 7 | tour_graph | 1 | 7 | 15/0 | ok |
| Bhutan | c58222c8 | 7 / 7 | tour_graph | 1 | **6** | 14/0 | ok |
| China | feb7e25f | 1 / 1 | tour_graph | 1 | 1 | 3/0 | ok |
| China | 93876fba | 1 / 1 | tour_graph | 1 | 1 | 5/0 | ok |
| China | 38df34c0 | 1 / 1 | tour_graph | 1 | 1 | 3/0 | ok |
| India | 51285758 | 4 / 4 | tour_graph | 1 | **1** | 4/0 | ok |
| India | 5122bd9b | 8 / 8 | tour_graph | 1 | **7** | 18/0 | ok |
| India | a38a5206 | 1 / 1 | tour_graph | 1 | 1 | 7/0 | ok |
| Japan | a90ddcc5 | 6 / 6 | tour_graph | 1 | **2** | 2/0 | ok |
| Japan | a9999de7 | 1 / 1 | places | 1 | 1 | 1/0 | **broken** |
| Japan | f3ab0cf2 | 8 / 8 | tour_graph | 1 | 8 | 7/0 | ok |
| Japan | b5c3c908 | 1 / 1 | none | — | 1 | — | — |
| Laos | 62b2895e | 7 / 7 | tour_graph | 1 | 7 | 8/2 | ok |
| Laos | 9149a7e8 | 14 / 14 | tour_graph | 1 | 14 | 35/2 | ok |
| Laos | 2f81b1e4 | 8 / 8 | tour_graph | 1 | 8 | 6/1 | ok |
| Mongolia | fba51164 | 2 / 2 | tour_graph | 1 | 2 | 4/0 | ok |
| Mongolia | 939e6241 | 12 / 12 | tour_graph | 1 | 12 | 22/0 | ok |
| Mongolia | 2b6b4d11 | 1 / 1 | tour_graph | 1 | 1 | 3/0 | ok |
| Nepal | de1eea74 | 15 / 15 | tour_graph | 1 | **13** | 16/0 | ok |
| Nepal | 2b9070e3 | 9 / 9 | tour_graph | 1 | **6** | 3/0 | ok |
| Nepal | c1d380d9 | 1 / 1 | tour_graph | 1 | 1 | 4/0 | ok |
| Pakistan | 44f78259 | 15 / 15 | none | — | 15 | — | — |
| Pakistan | 22c5f9f6 | 6 / 6 | none | — | 6 | — | — |
| Pakistan | 40621c3f | 24 / 24 | none | — | 24 | — | — |
| Philippines | f056b376 | 15 / 15 | none | — | 15 | — | — |
| Philippines | 87500d17 | 4 / 4 | none | — | 4 | — | — |
| Philippines | 000e3340 | 6 / 6 | none | — | 6 | — | — |
| South Korea | 739802f5 | 3 / 3 | tour_graph | 1 | 3 | 4/0 | ok |
| South Korea | d9b10288 | 9 / 9 | tour_graph | 1 | **8** | 27/0 | ok |
| South Korea | 745da9ab | 9 / 9 | tour_graph | 1 | 9 | 8/0 | ok |
| South Korea | 3c406e5c | 6 / 6 | none | — | 6 | — | — |
| Sri Lanka | 28e22489 | 3 / 3 | tour_graph | 1 | 3 | 7/0 | ok |
| Sri Lanka | cd8bc159 | 7 / 7 | tour_graph | 1 | **6** | 4/0 | ok |
| Sri Lanka | 5eeb8288 | 3 / 3 | tour_graph | 1 | 3 | 7/0 | ok |
| Taiwan | 74f84466 | 3 / 3 | tour_graph | 1 | **1** | 1/0 | **broken** |
| Taiwan | 3c9c5570 | 1 / 1 | tour_graph | 1 | 1 | 2/0 | ok |
| Taiwan | 766361cd | 2 / 2 | none | — | 2 | — | — |
| Thailand | e53c44c6 | 14 / 14 | tour_graph | 1 | **13** | 20/0 | ok |
| Thailand | 6dd98049 | 11 / 11 | tour_graph | 1 | 11 | 2/0 | ok |
| Thailand | 700044ca | 12 / 12 | tour_graph | 1 | **4** | 2/1 | ok |
| Thailand | 7100f50c | 7 / 7 | none | — | 7 | 1/0 | **broken** |
| Vietnam | ca1d7500 | **12 / 14** | tour_graph | 1 | 12 | 25/1 | ok |

## Findings

### F1 — Single-pin static map is broken (front-end bug, 3/43 sampled tours)

When a tour has exactly one map pin and no line, the "Where you go" map image does not load. The browser blocks
the response (`net::ERR_BLOCKED_BY_ORB`) and the page shows the broken image with its alt text. The same URL,
fetched with the page as Referer, answers **422** `{"message":"Padding cannot be used without the auto parameter
or without a provided bounding box."}`.

Cause: `apps/AA-TripPlanner-Web/frontend/lib/staticMap.ts:44-46`. A single pin uses a fixed `lng,lat,8`
center and zoom, but the URL always adds `?padding=48`, and Mapbox accepts `padding` only with `auto` or a
bounding box. Fix: drop `padding` when the position is `center,zoom`. A multi-pin map (`auto`) answers 200 (checked).

Affected sampled pages (document status 200; the map image request failed):
- <https://aa-tripplanner.vercel.app/tours/family-trip-to-northern-okinawa-japan-a9999de7>
- <https://aa-tripplanner.vercel.app/tours/wheels-around-taipei-3-day-cycling-tour-taiwan-74f84466>
- <https://aa-tripplanner.vercel.app/tours/thailand-to-cambodia-cycle-tour-coast-villages-and-angkor-temples-7-days-thailan-7100f50c>

The same `staticMapUrl` probably also serves other single-pin maps, such as a country page with one place.
That was not checked.

### F2 — The planner route covers fewer days than the tour (data, 12/32 Tour Graph routes)

The tour page shows the full v2 day list. But the planner's whole-route read (`tour-route`, `match: tour_graph`)
returns a proposal with fewer days than the tour on 12 of the 32 Tour Graph tours. Clicking "Customise this
trip" would therefore pin only part of the tour. The worst cases:

| Tour page | Route days / tour days |
|---|---|
| /tours/northern-thailand-and-laos-cycling-tour-12-days-thailand-700044ca | 4 / 12 |
| /tours/nasu-to-nikko-gourmet-cycling-tour-6-days-japan-a90ddcc5 | 2 / 6 |
| /tours/kullu-to-bir-billing-cycling-rafting-and-trekking-4-days-india-51285758 | 1 / 4 |
| /tours/wheels-around-taipei-3-day-cycling-tour-taiwan-74f84466 | 1 / 3 |
| /tours/mardi-himal-trek-9-days-nepal-2b9070e3 | 6 / 9 |

The other 7 are short by 1 or 2 days (see the per-tour table). The tour-route answers come from the browse
API, for example
`/api/browse?resource=tour-route&tour_id=335c1a57-9e06-4e1c-8b89-22669993ab63&source_id=700044ca-18e8-405a-b9af-54739cd6c0c8`
→ 200, `total_days: 4`, `whole_tour: true`, one segment covering days 1–4.

The S236 rule ("a places route must pin at least half the days") applies only to `match: places`; Tour Graph
routes are not checked. This may be a Tour Graph extracted before the v2 rewrite (the re-extract step in the
ecosystem wave order). That was not verified: it needs a DB read of the graph build time, which is outside
this $0 scope.

### F3 — The catalogue has 14 countries, not 17. Pakistan and Philippines have no map or route

- The live catalogue (`catalog-tours`, 892 tours) has **14 countries**: India 218, Sri Lanka 122, China 121,
  Nepal 85, Japan 79, Laos 46, Philippines 44, Thailand 43, Taiwan 36, Bhutan 32, South Korea 30, Pakistan 18,
  Mongolia 17, Vietnam 1. The brief's "17" is either out of date or counts countries that have no active tour.
- The planner's place list (`/api/browse?resource=countries`) has 14 countries too, but a different set. It
  includes **Cambodia and Kyrgyzstan**, which have no catalogue tour, and leaves out **Pakistan and
  Philippines**, which have 18 and 44 tours.
- So on all 24 checked Pakistan and Philippines tours, tour-route answers `match: "none"` (12/12 each) and the
  tour page has no "Where you go" map. The day list still shows correctly, and the fallback day list equals
  the page. Japan (9/12 none) and Taiwan (10/12 none) are mostly days-only too.

### Smaller notes

- **Vietnam, 12 days shown vs `duration_days` 14**:
  <https://aa-tripplanner.vercel.app/tours/vietnam-the-ho-chi-minh-trail-by-bicycle-14-days-vietnam-ca1d7500>.
  The title says 14 Days, but `catalog.v_tour_day` has 12 day blocks (1–12) and the route has 12 days. The
  v2 text compresses the itinerary (or the source has only 12 day blocks). This is a CIS content issue, not a
  TripPlanner issue.
- **No tour photo**: 26 of the 43 sampled pages show the "no photo yet" placeholder. In the whole catalogue,
  730 of 892 cards have `cover_url = null`. The placeholder is by design, but the catalogue looks bare.
- Next.js RSC prefetches of `/plan?tour=…` and `/sign-in` show as `net::ERR_ABORTED` when the page closes.
  This is benign: they are aborted prefetches with no error status. A prefetch does not run the planner's
  apply-route (that runs only after navigation).

## Not tested

- **Narration / compose** (`POST /api/trip` op `narrate`, either mode) and **search** (query embedding): these
  call an LLM and the budget is frozen until 01/11. They were blocked and never triggered.
- **The planner UI** (`/plan`, Mapbox GL map, legs drawn on the live map, apply-route, add/remove/reorder,
  send-to-advisor): apply-route writes a guest trip. Only its read-side input (`tour-route`) was checked.
- Sign-in, the trips page, dark mode, and tours outside the 43-tour sample (849 tours not opened).
- Whether the Tour Graph and places were re-extracted after the v2 rewrite (needs a DB read; see F2).
