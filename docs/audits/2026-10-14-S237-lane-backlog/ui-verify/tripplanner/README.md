# UI verify — S237 TripPlanner (15/10/2026)

Read-only verification. No data written: "Send to an advisor" was never clicked, and a Playwright route guard
aborted every non-GET call to the app's own `/api/*` (it caught the 2 automatic `POST /api/trip` apply-route
calls that "Customise this trip" fires, see D2). Filters, the Map/List toggle and the month/sort selects were used.
No login is needed on the public site; the preview was opened with a Vercel share link (token scrubbed, not saved).

Tooling: Playwright (headless Chromium) from the scratch folder, axe-core `color-contrast` rule, curl, Vercel
runtime-errors API. One browser at a time, no Lighthouse.

## Targets

- **Production** `https://aa-tripplanner.vercel.app` — after TP #77 (AA-812: photo fallback, WCAG AA contrast,
  month filter) and #78 (AA-712 slice 6b, `PLACES_SOURCE` default `legacy`).
- **PR #78 preview** `https://aa-tripplanner-git-feat-aa-7-67b7ca-…vercel.app` — head `cf4ed03`, contains #77
  (GitHub compare: ahead 2, behind 0). Vercel-protected, opened with a share link.
- Pages: `/`, `/destinations/laos`, `/destinations/vietnam` (prod only), `/tours/laos-north-to-south-16-days-laos-bd183835`,
  `/tours/vietnam-the-ho-chi-minh-trail-by-bicycle-14-days-vietnam-ca1d7500` (prod only), `/plan` (map + List).
  "Customise this trip" was also tried on the S236 tours Sri Lanka `63d21f32` and Kailash `98624d92`.

## Summary

| Area | Verdict |
|---|---|
| Preview: S237 env vars (browse/trip API + Mapbox token) | **PASS with defects**: data renders; the Mapbox token refuses the preview host (403), so there is no base map |
| Prod: home, destinations, tour pages (1440/390 × light/dark) | **PASS** |
| Prod: AA-812 WCAG AA contrast (#77) | **PASS** on public pages (axe 0); `/plan` still has 7 violations (out of scope, AA-674) |
| Prod: AA-812 destination-photo fallback (#77) | **NOT VERIFIABLE**: 0 of 892 live tours get a fallback, so no caption or fallback photo shows anywhere |
| Prod: List view month filter (#77) | **PASS with defects**: the count changes per month; uncached calls are slow, and the browse Lambda 503s under bursts (D9) |
| Prod: #78 slice 6b is a no-op | **PASS**: every browse call 200, same counts as S236 (892 tours); `x-places-source` is not visible through the Next proxy |
| S236 D1, tile-request storm on `/plan` | **FIXED** |
| S236 D2, "Customise this trip" never applies the tour | **PARTLY FIXED**: graph/places tours now return a route and the planner tries to apply it; tours with no planner places still 404, but the fallback is now graceful |

## Per page — production (`prod-<page>-<w>-<scheme>.jpg`)

| Page | HTTP | Console errors | `/api` | Overflow @390 | Images (visible loaded/total) | Theme | Verdict |
|---|---|---|---|---|---|---|---|
| `/` | 200 ×4 | 0 | — | 0 | 13/13 | follows scheme | PASS |
| `/destinations/laos` | 200 ×4 | 0 | — | 0 | 2/2 (hero has no photo, static map 200) | follows scheme | PASS |
| `/destinations/vietnam` | 200 ×4 | 0 | — | 0 | 2/2 | follows scheme | PASS |
| `/tours/…laos…bd183835` | 200 ×4 | 0 | — | 0 | 2/2 (camera placeholder hero) | follows scheme | PASS (no photo, see D8) |
| `/tours/…vietnam…ca1d7500` | 200 ×4 | 0 | — | 0 | 2/2 (camera placeholder hero) | follows scheme | PASS (no photo, see D8) |
| `/plan` | 200 ×4 | 0 | 17 calls at 1440, 11 at 390, all 200 (15/9 tiles) | 0 | Mapbox 200 ×38/×26, 0 errors | pinned light (by design) | PASS |
| `/plan` List | — | 0 (rerun) | `catalog-tours` 200 | 0 | many placeholder thumbnails | light | PASS with defects |

Real data: List shows **892** tours (S236: 892); `/destinations/laos` shows "46 tours in Laos" with 12 cards and
12 place cards; the tour pages show the full day-by-day itinerary (16 and 12 days), highlights, inclusions and the
route map with numbered stops.

## Per page — PR #78 preview (`preview-<page>-<w>-<scheme>.jpg`)

| Page | HTTP | Console errors | `/api` | Mapbox | Overflow @390 | Verdict |
|---|---|---|---|---|---|---|
| `/` | 200 ×4 | 0 | — | — | 0 | PASS (13/13 images) |
| `/destinations/laos` | 200 ×4 | 0 | — | static map `ERR_BLOCKED_BY_ORB` | 0 | PASS, map image missing |
| `/tours/…laos…bd183835` | 200 ×4 | 0 | — | static map `ERR_BLOCKED_BY_ORB` | 0 | PASS, map image missing |
| `/plan` | 200 ×4 | 18–40 (`[mapbox error]`, 403) | `countries` 200, `tiles` 200 ×15, `/api/trip` GET 200 | vector tiles **403** `{"message":"Forbidden"}` (6–20 per run); style JSON 200 | 0 | **Defect D7**: no base map |
| `/plan` List | — | — | `catalog-tours` 200 | — | — | PASS: 892 tours (`preview-plan-list-1440-light.jpg`) |

- The S237 env vars work. Browse data (clusters, countries, list of 892, SSR destination and tour pages) and the
  trip API GET all return 200 on the preview.
- `NEXT_PUBLIC_MAPBOX_TOKEN` is present: the style JSON loads with 200 and the map canvas draws. But Mapbox
  returns **403 Forbidden** for every vector tile, and static map images are blocked. The token is URL-restricted
  and does not allow the preview hostname. The planner shows the AA clusters on a blank globe
  (`preview-plan-1440-light.jpg`). This is the same as S236 D7, and the prod alias is fine.
  Fix: add `https://*-pqnghiep1354-5974s-projects.vercel.app` (or the branch-alias pattern) to the token's
  URL restrictions, or use a separate preview token.

## Feature checks

### AA-812 contrast (#77) — axe `color-contrast`, 1440, prod

| Page | light | dark |
|---|---|---|
| `/` | 0 | 0 |
| `/destinations/laos` | 0 | 0 |
| `/tours/…laos…` | 0 | 0 |
| `/plan` (pinned light) | 7 | 7 |

- The live tokens match the PR. Light: `--aa-accent-deep #875d12`, `--aa-muted #656d7a`, `--aa-on-accent #1a1206`.
  `--aa-hero-bg` is `#1f2933` in light and `#19212c` in dark.
- The destination hero is now a solid dark band with white text (`prod-dest-laos-1440-light.jpg`).
- `/plan` still fails on the planner's own `aa-*` palette. For example, `#db9628` on white is 2.49:1 (the
  "TRIP PLANNER" label), the AI-ASSISTED badge is 3.59:1, and `#6b7280` on `#f8f6f2` is 4.47:1. PR #77 says this
  belongs to AA-674, so it is known and out of scope.

### AA-812 destination-photo fallback (#77) — NOT VERIFIABLE on live data

- The new fields are deployed: every `catalog-tours` item has `cover_source` and `cover_place`.
- A census of all **892** tours (14 countries) gives `cover_source`: `tour` 161, `null` 731,
  `destination` **0**, `country` **0**.
- None of the destination pages' place cards has a photo either (e.g. Laos: 12/12 camera placeholders).
- So `catalog.v_destination` has no usable cover today, and the fallback never fires: no "Destination photo · …"
  caption and no fallback alt on any page checked. Tours without their own photo (all of Laos, India, Nepal, Japan,
  Thailand…) still show the camera placeholder hero, card and List thumbnail.
- The code path was proven only on fixtures (PR #77 evidence in `../tp-812/`). Live, it waits for CIS photo
  matching (AA-708).

### List view month filter (#77)

| Month | Count (all countries) |
|---|---|
| Any | 892 |
| October | 874 |
| January | 828 |
| July | 842 |
| March (sort Longest first) | 850 |
| December (sort Longest first) | 831 |

- `catalog-tours&month=N` returns 200 every time. The count and cards follow the filter at 390 and 1440 ("Show more" was not exercised).
- Screenshots: `prod-plan-list-{any,october,july}-{1440,390}-light.jpg`.
- In the first 1440 run, uncached month calls took more than 2.5 s. October and January came back without a count,
  and July was still on "Loading tours…" (`prod-plan-list-july-1440-light.jpg`). That run also logged 5 console
  500s. The 1440 rerun was clean. In a second rerun with an uncached sort, the August call was still loading after 6 s.
- During that rerun, the List's Next.js prefetch of `/tours/<slug>?_rsc=` returned **500** for 2 India tours. Both
  were 200 on a later curl, so the 500s were transient. See D9.

### #78 slice 6b — no visible change

- Every browse resource used (`countries`, `tiles`, `catalog-tours`, `tour-route`) returned 200, or the expected
  404 for tour-route.
- Counts match S236: 892 tours, and the same cluster numbers on the globe.
- The `x-places-source` response header is not visible in the browser, because the Next.js `/api/browse` proxy does
  not forward it. To check `legacy`, call the Lambda directly; that was not done here.

### S236 D1 — tile-request storm on `/plan` — FIXED

Prod, 1440: load + 12 s, zoom ×2, pan, zoom ×3 (`prod-d1-plan-after-zoom-pan-1440.jpg`).

| Measure | S236 | Now |
|---|---|---|
| `/api` calls | about 10,200 in about 8 s | **38** in total, all 200 |
| Tile calls | — | 36 |
| 503 / `ERR_INSUFFICIENT_RESOURCES` | 1,050 / 8,900 | 0 / 0 |
| Console errors | — | 0 |

Calls after each step (cumulative): 17 after load, 32 after zoom-in, 32 after pan, 38 after more zoom. Mapbox
returned 85×200 and 4×204. The base map, clusters and single pins render. `prod-plan-1440-*.jpg` and
`prod-plan-390-*.jpg` show the same: 15 or 9 tile calls on load, all 200.

### S236 D2 — "Customise this trip" — PARTLY FIXED

| Tour | `tour-route` | What the planner did |
|---|---|---|
| Laos North to South `bd183835` | **200**, `match: tour_graph`, 16 days | Pre-filled Laos / 16 and fired the apply-route `POST /api/trip` (blocked by the read-only guard) |
| Kailash `98624d92` (S236: 404) | **200**, `match: places`, 21 days | Fired the apply-route POST (blocked) |
| Sri Lanka `63d21f32` (S236: 404) | 404 `no planner route for this tour` + tour info | Graceful fallback: "…isn't on the planner map yet. We've set Sri Lanka and 10 days in the route finder…", with the 10 days listed |
| Vietnam HCM Trail `ca1d7500` | 404 + tour info | Same graceful fallback, the tour days listed |

- Graph and places tours now get a route, and the planner tries to apply it. Kailash, which was a 404 in S236, now
  resolves through places.
- Tours with no planner places still cannot be applied. They now get a clear message and a pre-filled route finder
  instead of a bare "not on the map".
- The final step (stops appearing in "Your trip") was **not observed**, because the apply is a server write (POST
  `/api/trip`) and this run is read-only. Screenshots: `prod-d2-customise-{laos,kailash,srilanka,vietnam}-1440.jpg`.
  With the POST blocked, "Your trip" stays empty; that comes from the guard, not from a defect.
- Minor: the expected 404 shows as a red console error ("Failed to load resource: 404").

## Defects

| # | Sev | Page | Description | Evidence |
|---|---|---|---|---|
| D7 | Medium (preview only) | Preview `/plan`, destination and tour maps | The Mapbox token refuses the preview hostname: vector tiles 403 `{"message":"Forbidden"}`, static maps `ERR_BLOCKED_BY_ORB`. No base map on any preview, so preview reviews of the map stay impossible (carried over from S236 D7). | `preview-plan-*.jpg`, `results.json › preview_plan.mapbox_first_error` |
| D8 | Medium (data) | Prod tour pages, cards, List | AA-812 photo fallback never fires on live data: 0/892 tours get a destination or country cover, and 731/892 still show a camera placeholder. Waits on CIS photo matching (AA-708). | `results.json › prod_cover_source_census`, `prod-dest-laos-1440-light.jpg`, `prod-plan-list-october-390-light.jpg` |
| D9 | Medium | Prod SSR tour/destination pages, List | The browse Lambda returns 503 when pages are rendered in bursts. Vercel logged "tour read failed (503)" ×40 on `/tours/[slug].rsc` and "destination read failed (503)" ×30 on `/destinations/[country]`, including `/destinations/laos`, between 04:41 and 06:25Z. The List's prefetch of 24 tour links triggers it (2 RSC 500s seen). Uncached month and sort calls also took more than 6 s at times. | `results.json › vercel_runtime_errors_last_3h`, `prod_list_month_filter_*` |
| D10 | Low | Prod `/plan` | 7 axe contrast violations in the planner palette (2.49:1 gold label, 3.59:1 badge, 4.47:1 muted text). Out of scope for #77; tracked under AA-674. | `results.json › prod_contrast_axe` |
| D11 | Low | Prod `/plan` Customise | Tours with no planner places still cannot be applied (tour-route 404), and the expected 404 is logged as a console error. | `prod-d2-customise-srilanka-1440.jpg` |
| D12 | Low | Prod List | "1 DAYS" plural on one-day tours. | `prod-plan-list-october-390-light.jpg` |

## Hygiene

- No share token, `_vercel_jwt` or password is saved in this folder; the share URL was used only from a scratch
  file, which was deleted after the run. Mapbox token values are redacted in recorded URLs.
- Scripts are in `.tmp-session/s237/uiv/tripplanner/` (scratch). The browser was closed after each run.
