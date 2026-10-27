# AA-990: TripPlanner catalogue sweep, all 892 tours (Dev, HTTP only, $0)

Run: 27/10/2026 06:44–06:51 +07 (26/10 23:44–23:51 UTC), Claude Code subagent. Host: <https://aa-tripplanner.vercel.app>.
This is the follow-up of the 43-tour parity sample (`README.md`) and its F2/F3 investigation (`f2-f3-investigation.md`).
It checks every catalogue tour for the same defect classes, using HTTP only: no browser, no AWS, no DB, no LLM, no writes.
The raw per-tour results are in `catalogue-sweep.json`.

**Result: 892/892 tour pages answer 200, and 892/892 tour-route reads answer 200, with no retries. 422 tours (47%) are
OK. 294 have a route shorter than the tour, and in every one of them the missing days are only at the start or the
end. 162 have no route (61 of them are Pakistan/Philippines, explained by F3). 14 have a day list that does not
match `duration_days`. The F1 single-pin map bug is gone from the live pages.**

## Method

1. **Catalogue**: `GET /api/browse?resource=catalog-tours&limit=60&offset=0..840`, 15 pages, all 200. `total` is 892, and 892
   tours came back, all `lifecycle_stage=active`.
2. **Per tour** (one Python process, 4 threads, at least 100 ms between request starts across all threads,
   up to 3 retries with 1/2/4 s backoff on 429, 5xx or network errors; 1,800 requests, **0 retries needed**):
   - `GET /api/browse?resource=tour-route&tour_id=…&source_id=…`. A routed answer is `{tour_id, proposal:{…}}`. From it
     the script records `match`, `total_days`, `whole_tour`, the segment count, the `tour_day`s that `proposal.days`
     covers, **pinned days** (rows with a `component_id`) and **stop days** (rows with a `destination_id`).
     A no-route answer is `{match:"none", tour:{…}}`, and the script records the length of the fallback day list.
   - `GET /tours/<slug>` for the status, plus two cheap reads from the HTML (nothing is rendered): the JSON-LD
     `TouristTrip.itinerary` item count (the day list the page shows), and the Mapbox static-map URL form. A
     `lng,lat,zoom` centre with `padding=` is the F1 defect. Only booleans are stored; the token is never stored.
3. **Classes**: each tour gets one primary class, in this priority order:
   - **ERROR**: tour-route or tour page not 200 after retries.
   - **DAYS_MISMATCH**: the page day list (JSON-LD), or the fallback day list when `match: none`, differs from the
     catalogue's `duration_days`.
   - **SHORT_ROUTE**: `proposal.total_days` < `duration_days`. The missing tour days are split into leading, trailing and
     inner. **Inner gaps cannot happen in this answer**: the proposal always walks one contiguous span
     (first stop day..last stop day) and carries the previous stop into stop-less days inside it. So "inner" is 0 by
     construction. Holes inside the span show up only as unpinned days (see "pins < half").
   - **NO_ROUTE**: `match: none` (day list only) and the day list is complete.
   - **OK**: routed (`tour_graph` or `places`), covers days 1..`duration_days`, and the page day list equals `duration_days`.
   Extra flags: `LONG_ROUTE` (route longer than `duration_days`), `ZERO_PIN` (a routed tour with no pinned day),
   `PIN_BELOW_HALF` (pinned days < 50% of `duration_days`, the S236 places rule applied to every route),
   `F1_SINGLE_PIN_PADDING`, `PAGE_ERROR`.
4. **Explained by**: (a) F3 is a NO_ROUTE in Pakistan or Philippines. (b) F2 is a SHORT_ROUTE with edge-only missing days,
   split into b1 (at most 1 day at each end: the arrival/departure case, class A) and b2 (2+ days at one end: the
   same code gap, plus stop-less stretches that are probably unresolved places, F2 class B). (c) is everything else.
5. **Countries**: `GET /api/browse?resource=countries` compared with the catalogue's tour countries.

## Per-country summary

"match G/P/N" is `tour_graph` / `places` / `none`. "pins < half" counts tours of any class whose route pins fewer than
half of the tour days, and includes the one 0-pin route. ERROR and page non-200 are 0 everywhere.

| Country | Tours | OK | SHORT_ROUTE | of which 1-day edges | of which multi-day edge | NO_ROUTE | DAYS_MISMATCH | ERROR | match G/P/N | pins < half (any class) | page non-200 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Bhutan | 32 | 12 | 19 | 19 | 0 | 0 | 1 | 0 | 32/0/0 | 0 | 0 |
| China | 121 | 78 | 43 | 41 | 2 | 0 | 0 | 0 | 120/1/0 | 0 | 0 |
| India | 218 | 165 | 48 | 45 | 3 | 3 | 2 | 0 | 215/0/3 | 13 | 0 |
| Japan | 79 | 15 | 8 | 2 | 6 | 55 | 1 | 0 | 23/1/55 | 8 | 0 |
| Laos | 46 | 30 | 15 | 14 | 1 | 0 | 1 | 0 | 45/1/0 | 6 | 0 |
| Mongolia | 17 | 12 | 5 | 5 | 0 | 0 | 0 | 0 | 16/1/0 | 1 | 0 |
| Nepal | 85 | 26 | 52 | 45 | 7 | 5 | 2 | 0 | 77/3/5 | 26 | 0 |
| Pakistan | 18 | 0 | 0 | 0 | 0 | 18 | 0 | 0 | 0/0/18 | 0 | 0 |
| Philippines | 44 | 0 | 0 | 0 | 0 | 43 | 1 | 0 | 0/0/44 | 0 | 0 |
| South Korea | 30 | 11 | 16 | 14 | 2 | 2 | 1 | 0 | 28/0/2 | 6 | 0 |
| Sri Lanka | 122 | 46 | 68 | 45 | 23 | 5 | 3 | 0 | 116/1/5 | 57 | 0 |
| Taiwan | 36 | 10 | 4 | 2 | 2 | 22 | 0 | 0 | 12/2/22 | 7 | 0 |
| Thailand | 43 | 17 | 16 | 13 | 3 | 9 | 1 | 0 | 28/6/9 | 14 | 0 |
| Vietnam | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1/0/0 | 0 | 0 |
| **Total** | 892 | 422 | 294 | 245 | 49 | 162 | 14 | 0 | 713/16/163 | 138 | 0 |

Pinned share across all 729 routed tours: 4,016 pinned days out of 6,242 tour days (64%). The 138 "pins < half" tours
are 93 SHORT_ROUTE, 42 OK and 3 DAYS_MISMATCH. So 42 tours that count as OK still pin less than half their days.

### Other checks

- **F1 (single-pin static map)**: 747 tour pages have a "Where you go" static map, and 56 of them are single-pin
  (`lng,lat,8` centre). **None** of them carries `padding=` any more. The fix (TripPlanner #158,
  `fix: single-pin static map drops padding…`) is live, and no tour has the F1 defect now.
- **Countries**: `resource=countries` returns 14 countries: Bhutan, Cambodia, China, India, Japan, Kyrgyzstan, Laos, Mongolia,
  Nepal, South Korea, Sri Lanka, Taiwan, Thailand, Vietnam. The catalogue also has 14 countries. **Catalogue only:
  Pakistan (18 tours), Philippines (44).** **Planner only: Cambodia, Kyrgyzstan.** This is unchanged from F3 (the
  guard fix has not shipped or has not re-geocoded yet).
- **Cross-border routes**: 48 routed tours have stops in 2 or 3 countries, which is where Cambodia and Kyrgyzstan come from (by design, F3).
- Every routed answer is a single segment with `whole_tour: true`. `proposal.days` row count equals `total_days` on all 729.
- **Sample re-check**: all 43 sampled tours give the same numbers as the 27/10 F2 re-probe (`700044ca` 11/12,
  `7100f50c` now `tour_graph` 7/7 and OK, the other 10 short routes unchanged).

## Non-OK tours

Tour page links are `https://aa-tripplanner.vercel.app/tours/<slug>`; the link text is the source-id prefix. "Numbers": for
SHORT_ROUTE, `route days / duration_days`, which days are missing, and pinned days; for NO_ROUTE, the fallback day list
against `duration_days`; for DAYS_MISMATCH, the route or day list and the mismatch.


### (a) Explained by F3, the CIS place guard has no Pakistan or Philippines (61)

All Pakistan and Philippines tours: `match: none`, fallback day list complete. Philippines `41b138a1` is also a DAYS_MISMATCH and is listed under (c).

| Country | Tour page | Class | Numbers | Extra flags |
|---|---|---|---|---|
| Pakistan | [52ca8bd5](https://aa-tripplanner.vercel.app/tours/baltistan-deosai-fairy-meadows-and-hunza-15-days-pakistan-52ca8bd5) | NO_ROUTE | none; day list 15/15 | — |
| Pakistan | [13e85c2d](https://aa-tripplanner.vercel.app/tours/china-border-to-islamabad-via-hunza-swat-and-taxila-8-days-pakistan-13e85c2d) | NO_ROUTE | none; day list 8/8 | — |
| Pakistan | [7391e677](https://aa-tripplanner.vercel.app/tours/concordia-and-k2-base-camp-trek-via-the-baltoro-glacier-return-via-jhola-and-ask-7391e677) | NO_ROUTE | none; day list 19/19 | — |
| Pakistan | [29393653](https://aa-tripplanner.vercel.app/tours/deosai-plains-expedition-7-days-pakistan-29393653) | NO_ROUTE | none; day list 7/7 | — |
| Pakistan | [45ee817f](https://aa-tripplanner.vercel.app/tours/fairy-meadows-and-nanga-parbat-trek-7-days-pakistan-45ee817f) | NO_ROUTE | none; day list 7/7 | — |
| Pakistan | [b6a594ae](https://aa-tripplanner.vercel.app/tours/fairy-meadows-k2-base-camp-and-concordia-trek-via-gondogoro-la-22-days-pakistan-b6a594ae) | NO_ROUTE | none; day list 22/22 | — |
| Pakistan | [da6b5194](https://aa-tripplanner.vercel.app/tours/fairy-meadows-rakaposhi-trek-hunza-14-days-pakistan-da6b5194) | NO_ROUTE | none; day list 14/14 | — |
| Pakistan | [14e34425](https://aa-tripplanner.vercel.app/tours/hunza-valley-tour-8-days-pakistan-14e34425) | NO_ROUTE | none; day list 8/8 | — |
| Pakistan | [80f92b21](https://aa-tripplanner.vercel.app/tours/islamabad-peshawar-swat-kalash-and-hunza-tour-14-days-pakistan-80f92b21) | NO_ROUTE | none; day list 14/14 | — |
| Pakistan | [23a61989](https://aa-tripplanner.vercel.app/tours/k2-base-camp-concordia-trek-gondogoro-la-crossing-20-days-pakistan-23a61989) | NO_ROUTE | none; day list 20/20 | — |
| Pakistan | [4734f92c](https://aa-tripplanner.vercel.app/tours/k2-base-camp-trek-16-days-pakistan-4734f92c) | NO_ROUTE | none; day list 16/16 | — |
| Pakistan | [81f0b32e](https://aa-tripplanner.vercel.app/tours/kalash-valley-cultural-tour-bumburet-rumbur-and-birir-8-days-pakistan-81f0b32e) | NO_ROUTE | none; day list 8/8 | — |
| Pakistan | [e3a274d8](https://aa-tripplanner.vercel.app/tours/karakoram-highway-jeep-safari-7-days-pakistan-e3a274d8) | NO_ROUTE | none; day list 7/7 | — |
| Pakistan | [5dca3b21](https://aa-tripplanner.vercel.app/tours/lahore-heritage-tour-4-days-pakistan-5dca3b21) | NO_ROUTE | none; day list 4/4 | — |
| Pakistan | [44f78259](https://aa-tripplanner.vercel.app/tours/sindh-and-punjab-along-the-indus-karachi-to-islamabad-15-days-pakistan-44f78259) | NO_ROUTE | none; day list 15/15 | — |
| Pakistan | [22c5f9f6](https://aa-tripplanner.vercel.app/tours/skardu-adventure-6-days-pakistan-22c5f9f6) | NO_ROUTE | none; day list 6/6 | — |
| Pakistan | [40621c3f](https://aa-tripplanner.vercel.app/tours/snow-lake-trek-via-the-biafo-and-hispar-glaciers-24-days-pakistan-40621c3f) | NO_ROUTE | none; day list 24/24 | — |
| Pakistan | [41c81746](https://aa-tripplanner.vercel.app/tours/swat-valley-mountains-rivers-buddhist-heritage-5-days-pakistan-41c81746) | NO_ROUTE | none; day list 5/5 | — |
| Philippines | [086213a8](https://aa-tripplanner.vercel.app/tours/arts-and-crafts-of-rizal-and-laguna-3-days-philippines-086213a8) | NO_ROUTE | none; day list 3/3 | — |
| Philippines | [1f97f431](https://aa-tripplanner.vercel.app/tours/banaue-batad-and-kalinga-trek-and-rafting-7-days-philippines-1f97f431) | NO_ROUTE | none; day list 7/7 | — |
| Philippines | [defe75c5](https://aa-tripplanner.vercel.app/tours/batanes-batan-itbayat-and-sabtang-islands-6-days-philippines-defe75c5) | NO_ROUTE | none; day list 6/6 | — |
| Philippines | [87500d17](https://aa-tripplanner.vercel.app/tours/batanes-island-tour-4-days-philippines-87500d17) | NO_ROUTE | none; day list 4/4 | — |
| Philippines | [5455d52f](https://aa-tripplanner.vercel.app/tours/bicol-express-naga-caramoan-legazpi-and-misibis-7-days-philippines-5455d52f) | NO_ROUTE | none; day list 7/7 | — |
| Philippines | [0b51b917](https://aa-tripplanner.vercel.app/tours/bicol-wakeboarding-donsol-and-sorsogon-tour-5-days-philippines-0b51b917) | NO_ROUTE | none; day list 5/5 | — |
| Philippines | [8146fcc3](https://aa-tripplanner.vercel.app/tours/birding-in-manila-mt-makiling-villa-escudero-and-cavite-5-days-philippines-8146fcc3) | NO_ROUTE | none; day list 5/5 | — |
| Philippines | [361b2054](https://aa-tripplanner.vercel.app/tours/birdwatching-in-cebu-sumilon-negros-oriental-and-bohol-10-days-philippines-361b2054) | NO_ROUTE | none; day list 10/10 | — |
| Philippines | [1a8f81ca](https://aa-tripplanner.vercel.app/tours/bohol-cebu-and-boracay-island-tour-7-days-philippines-1a8f81ca) | NO_ROUTE | none; day list 7/7 | — |
| Philippines | [7b368504](https://aa-tripplanner.vercel.app/tours/butanding-whale-shark-encounter-legazpi-and-donsol-4-days-philippines-7b368504) | NO_ROUTE | none; day list 4/4 | — |
| Philippines | [b1875b7a](https://aa-tripplanner.vercel.app/tours/candaba-bataan-subic-and-pangasinan-bird-watching-5-days-philippines-b1875b7a) | NO_ROUTE | none; day list 5/5 | — |
| Philippines | [31ab4c84](https://aa-tripplanner.vercel.app/tours/cebu-and-bohol-adventure-5-days-philippines-31ab4c84) | NO_ROUTE | none; day list 5/5 | — |
| Philippines | [e7341db9](https://aa-tripplanner.vercel.app/tours/coron-and-popototan-island-mangrove-kayaking-5-days-philippines-e7341db9) | NO_ROUTE | none; day list 5/5 | — |
| Philippines | [4facae84](https://aa-tripplanner.vercel.app/tours/coron-weekend-diving-4-days-philippines-4facae84) | NO_ROUTE | none; day list 4/4 | — |
| Philippines | [825beb68](https://aa-tripplanner.vercel.app/tours/dumaguete-balinsasayaw-and-siquijor-7-days-philippines-825beb68) | NO_ROUTE | none; day list 7/7 | — |
| Philippines | [144e6ddd](https://aa-tripplanner.vercel.app/tours/dumaguete-siquijor-and-bohol-adventure-8-days-philippines-144e6ddd) | NO_ROUTE | none; day list 8/8 | — |
| Philippines | [d9c3d13d](https://aa-tripplanner.vercel.app/tours/exotic-south-general-santos-lake-sebu-and-davao-7-days-philippines-d9c3d13d) | NO_ROUTE | none; day list 7/7 | — |
| Philippines | [f8b7f55b](https://aa-tripplanner.vercel.app/tours/fiesta-islands-philippines-7-days-philippines-f8b7f55b) | NO_ROUTE | none; day list 7/7 | — |
| Philippines | [b1774b6b](https://aa-tripplanner.vercel.app/tours/general-santos-lake-sebu-and-kidapawan-tour-5-days-philippines-b1774b6b) | NO_ROUTE | none; day list 5/5 | — |
| Philippines | [5c099dbf](https://aa-tripplanner.vercel.app/tours/highlands-to-islands-davao-and-mt-apo-6-days-philippines-5c099dbf) | NO_ROUTE | none; day list 6/6 | — |
| Philippines | [73440e76](https://aa-tripplanner.vercel.app/tours/ifugao-heritage-tour-banaue-bontoc-and-sagada-4-days-philippines-73440e76) | NO_ROUTE | none; day list 4/4 | — |
| Philippines | [31d7481c](https://aa-tripplanner.vercel.app/tours/mindanao-philippine-eagle-and-birding-tour-10-days-philippines-31d7481c) | NO_ROUTE | none; day list 10/10 | — |
| Philippines | [1f816967](https://aa-tripplanner.vercel.app/tours/north-luzon-baguio-sagada-banaue-and-batad-6-days-philippines-1f816967) | NO_ROUTE | none; day list 6/6 | — |
| Philippines | [139f1b4e](https://aa-tripplanner.vercel.app/tours/north-luzon-run-back-packing-trail-13-days-philippines-139f1b4e) | NO_ROUTE | none; day list 13/13 | — |
| Philippines | [8b4eb454](https://aa-tripplanner.vercel.app/tours/north-luzon-western-trail-8-days-philippines-8b4eb454) | NO_ROUTE | none; day list 8/8 | — |
| Philippines | [cbf5237f](https://aa-tripplanner.vercel.app/tours/northern-exposure-banaue-sagada-cagayan-and-batanes-7-days-philippines-cbf5237f) | NO_ROUTE | none; day list 7/7 | — |
| Philippines | [3eebc390](https://aa-tripplanner.vercel.app/tours/nueva-vizcaya-to-kalinga-caves-and-whitewater-rafting-5-days-philippines-3eebc390) | NO_ROUTE | none; day list 5/5 | — |
| Philippines | [44e58975](https://aa-tripplanner.vercel.app/tours/paddle-and-surf-pangasinan-to-pagudpud-10-days-philippines-44e58975) | NO_ROUTE | none; day list 10/10 | — |
| Philippines | [532cf597](https://aa-tripplanner.vercel.app/tours/palawan-birding-program-6-days-philippines-532cf597) | NO_ROUTE | none; day list 6/6 | — |
| Philippines | [a91dbbba](https://aa-tripplanner.vercel.app/tours/palawan-circuit-manila-coron-el-nido-and-puerto-princesa-15-days-philippines-a91dbbba) | NO_ROUTE | none; day list 15/15 | — |
| Philippines | [63b4d8e6](https://aa-tripplanner.vercel.app/tours/palawan-puerto-princesa-sabang-and-el-nido-7-days-philippines-63b4d8e6) | NO_ROUTE | none; day list 7/7 | — |
| Philippines | [f056b376](https://aa-tripplanner.vercel.app/tours/philippines-cordillera-rice-terraces-and-beach-stay-15-days-philippines-f056b376) | NO_ROUTE | none; day list 15/15 | — |
| Philippines | [b2b99bb4](https://aa-tripplanner.vercel.app/tours/philippines-highlands-to-islands-manila-banaue-palawan-cebu-and-boracay-24-days-b2b99bb4) | NO_ROUTE | none; day list 24/24 | — |
| Philippines | [d6b877c6](https://aa-tripplanner.vercel.app/tours/philippines-rock-and-surf-4-days-philippines-d6b877c6) | NO_ROUTE | none; day list 4/4 | — |
| Philippines | [924c7fc3](https://aa-tripplanner.vercel.app/tours/rafting-and-rappelling-in-cagayan-de-oro-and-camiguin-4-days-philippines-924c7fc3) | NO_ROUTE | none; day list 4/4 | — |
| Philippines | [2ea6d400](https://aa-tripplanner.vercel.app/tours/siargao-island-tour-6-days-philippines-2ea6d400) | NO_ROUTE | none; day list 6/6 | — |
| Philippines | [d308e781](https://aa-tripplanner.vercel.app/tours/southern-escapade-cagayan-de-oro-camiguin-and-butuan-7-days-philippines-d308e781) | NO_ROUTE | none; day list 7/7 | — |
| Philippines | [5e6cfb4a](https://aa-tripplanner.vercel.app/tours/taal-villa-escudero-and-pagsanjan-3-days-philippines-5e6cfb4a) | NO_ROUTE | none; day list 3/3 | — |
| Philippines | [20a57c8e](https://aa-tripplanner.vercel.app/tours/taal-volcano-and-mt-pinatubo-crater-treks-3-days-philippines-20a57c8e) | NO_ROUTE | none; day list 3/3 | — |
| Philippines | [52a75a31](https://aa-tripplanner.vercel.app/tours/the-cordillera-trail-baguio-sagada-and-banaue-5-days-philippines-52a75a31) | NO_ROUTE | none; day list 5/5 | — |
| Philippines | [8a94f617](https://aa-tripplanner.vercel.app/tours/tribes-of-the-north-clark-baguio-sagada-banaue-and-batad-7-days-philippines-8a94f617) | NO_ROUTE | none; day list 7/7 | — |
| Philippines | [000e3340](https://aa-tripplanner.vercel.app/tours/tropical-jewels-bohol-dumaguete-and-siquijor-6-days-philippines-000e3340) | NO_ROUTE | none; day list 6/6 | — |
| Philippines | [e66948be](https://aa-tripplanner.vercel.app/tours/visayan-charms-cebu-and-bohol-6-days-philippines-e66948be) | NO_ROUTE | none; day list 6/6 | — |

### (b1) Explained by F2 class A, the route stops at the first/last stop day; at most 1 day missing at each end (245)

These are the arrival and/or departure days with no stop. The TripPlanner fix (span the proposal over 1..N) closes all of them; no data work.

| Country | Tour page | Class | Numbers | Extra flags |
|---|---|---|---|---|
| Bhutan | [8ecd1233](https://aa-tripplanner.vercel.app/tours/best-of-bhutan-9-days-bhutan-8ecd1233) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 7 | — |
| Bhutan | [6ff4f5ea](https://aa-tripplanner.vercel.app/tours/bhutan-culinary-trail-east-to-west-10-days-bhutan-6ff4f5ea) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 8 | — |
| Bhutan | [f9eba2f0](https://aa-tripplanner.vercel.app/tours/bhutan-day-hike-tour-7-days-bhutan-f9eba2f0) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 5 | — |
| Bhutan | [7930c16a](https://aa-tripplanner.vercel.app/tours/bhutan-honeymoon-thimphu-punakha-and-paro-7-days-bhutan-7930c16a) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 5 | — |
| Bhutan | [f041c263](https://aa-tripplanner.vercel.app/tours/bhutan-mountain-biking-9-days-bhutan-f041c263) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 7 | — |
| Bhutan | [8577ac83](https://aa-tripplanner.vercel.app/tours/bhutan-spa-and-wellness-with-day-hikes-8-days-bhutan-8577ac83) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 6 | — |
| Bhutan | [a618b237](https://aa-tripplanner.vercel.app/tours/bhutan-walking-pilgrimage-7-days-bhutan-a618b237) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 5 | — |
| Bhutan | [cbe5c6d2](https://aa-tripplanner.vercel.app/tours/bhutanese-wildlife-expedition-royal-manas-national-park-to-paro-11-days-bhutan-cbe5c6d2) | SHORT_ROUTE | tour_graph 10/11; missing last 1; pins 9 | — |
| Bhutan | [252b1557](https://aa-tripplanner.vercel.app/tours/buddhist-retreat-and-meditation-in-bhutan-10-days-bhutan-252b1557) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 8 | — |
| Bhutan | [51b36891](https://aa-tripplanner.vercel.app/tours/bumthang-drup-festival-tour-bhutan-12-days-bhutan-51b36891) | SHORT_ROUTE | tour_graph 11/12; missing last 1; pins 11 | — |
| Bhutan | [c61e2458](https://aa-tripplanner.vercel.app/tours/dagala-thousand-lakes-trek-9-days-bhutan-c61e2458) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 5 | — |
| Bhutan | [82a9b1a1](https://aa-tripplanner.vercel.app/tours/glimpse-of-bhutan-thimphu-and-paro-5-days-bhutan-82a9b1a1) | SHORT_ROUTE | tour_graph 4/5; missing last 1; pins 3 | — |
| Bhutan | [f04640c7](https://aa-tripplanner.vercel.app/tours/history-tour-of-bhutan-jambay-lhakhang-tshechu-11-days-bhutan-f04640c7) | SHORT_ROUTE | tour_graph 10/11; missing last 1; pins 8 | — |
| Bhutan | [374e44f8](https://aa-tripplanner.vercel.app/tours/jomolhari-soi-yaksa-trek-11-days-bhutan-374e44f8) | SHORT_ROUTE | tour_graph 10/11; missing last 1; pins 6 | — |
| Bhutan | [4e0baa58](https://aa-tripplanner.vercel.app/tours/the-druk-path-trek-8-days-bhutan-4e0baa58) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 5 | — |
| Bhutan | [ce3e0d6c](https://aa-tripplanner.vercel.app/tours/thimphu-festival-bhutan-8-days-bhutan-ce3e0d6c) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 7 | — |
| Bhutan | [f8bff8a1](https://aa-tripplanner.vercel.app/tours/time-travel-samdrup-jongkhar-to-paro-bhutan-11-days-bhutan-f8bff8a1) | SHORT_ROUTE | tour_graph 10/11; missing last 1; pins 9 | — |
| Bhutan | [c58222c8](https://aa-tripplanner.vercel.app/tours/western-bhutan-highlights-7-days-bhutan-c58222c8) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 5 | — |
| Bhutan | [956c992a](https://aa-tripplanner.vercel.app/tours/western-bhutan-with-phobjikha-extension-9-days-bhutan-956c992a) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 7 | — |
| China | [45021768](https://aa-tripplanner.vercel.app/tours/beijing-hangzhou-and-shanghai-cultural-tour-7-days-china-45021768) | SHORT_ROUTE | tour_graph 5/7; missing first 1; last 1; pins 5 | — |
| China | [6ac53082](https://aa-tripplanner.vercel.app/tours/beijing-to-hong-kong-by-high-speed-train-14-days-china-6ac53082) | SHORT_ROUTE | tour_graph 13/14; missing first 1; pins 10 | — |
| China | [af5a6da3](https://aa-tripplanner.vercel.app/tours/beijing-to-hong-kong-route-13-days-china-af5a6da3) | SHORT_ROUTE | tour_graph 11/13; missing first 1; last 1; pins 11 | — |
| China | [af510009](https://aa-tripplanner.vercel.app/tours/beijing-to-kathmandu-overland-via-tibet-15-days-china-af510009) | SHORT_ROUTE | tour_graph 14/15; missing last 1; pins 10 | — |
| China | [a7268e14](https://aa-tripplanner.vercel.app/tours/beijing-to-kathmandu-via-lhasa-and-everest-15-days-china-a7268e14) | SHORT_ROUTE | tour_graph 14/15; missing last 1; pins 12 | — |
| China | [0b8fecd2](https://aa-tripplanner.vercel.app/tours/best-of-china-14-days-china-0b8fecd2) | SHORT_ROUTE | tour_graph 13/14; missing first 1; pins 11 | — |
| China | [7f094dbc](https://aa-tripplanner.vercel.app/tours/china-by-bike-16-days-china-7f094dbc) | SHORT_ROUTE | tour_graph 15/16; missing last 1; pins 12 | — |
| China | [382aa3d7](https://aa-tripplanner.vercel.app/tours/china-explorer-beijing-xi-an-huashan-luoyang-and-shanghai-11-days-china-382aa3d7) | SHORT_ROUTE | tour_graph 10/11; missing last 1; pins 9 | — |
| China | [ad844b71](https://aa-tripplanner.vercel.app/tours/china-express-beijing-xi-an-and-shanghai-8-days-china-ad844b71) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 7 | — |
| China | [73306106](https://aa-tripplanner.vercel.app/tours/china-golden-triangle-beijing-xi-an-and-shanghai-8-days-china-73306106) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 5 | — |
| China | [c3c3f17b](https://aa-tripplanner.vercel.app/tours/china-highlights-beijing-xi-an-shanghai-and-suzhou-9-days-china-c3c3f17b) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 7 | — |
| China | [520c9bd5](https://aa-tripplanner.vercel.app/tours/china-tibet-encompassed-16-days-china-520c9bd5) | SHORT_ROUTE | tour_graph 14/16; missing first 1; last 1; pins 12 | — |
| China | [190f0ac9](https://aa-tripplanner.vercel.app/tours/classic-china-tour-14-days-china-190f0ac9) | SHORT_ROUTE | tour_graph 13/14; missing last 1; pins 10 | — |
| China | [2529bae8](https://aa-tripplanner.vercel.app/tours/cycle-beijing-great-wall-trek-6-days-china-2529bae8) | SHORT_ROUTE | tour_graph 5/6; missing last 1; pins 5 | — |
| China | [741e63fa](https://aa-tripplanner.vercel.app/tours/cycle-xinjiang-13-days-china-741e63fa) | SHORT_ROUTE | tour_graph 12/13; missing last 1; pins 11 | — |
| China | [704a2e65](https://aa-tripplanner.vercel.app/tours/cycle-yunnan-14-days-china-704a2e65) | SHORT_ROUTE | tour_graph 13/14; missing last 1; pins 10 | — |
| China | [0790084d](https://aa-tripplanner.vercel.app/tours/cycle-yunnan-tibet-26-days-china-0790084d) | SHORT_ROUTE | tour_graph 25/26; missing last 1; pins 21 | — |
| China | [9103cace](https://aa-tripplanner.vercel.app/tours/eastern-china-tour-shanghai-suzhou-hangzhou-and-huangshan-8-days-china-9103cace) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 7 | — |
| China | [159bb30b](https://aa-tripplanner.vercel.app/tours/everest-base-camp-experience-lhasa-shigatse-and-rombuk-9-days-china-159bb30b) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 7 | — |
| China | [2a2fc5c4](https://aa-tripplanner.vercel.app/tours/gourmet-china-beijing-xi-an-chengdu-hangzhou-and-shanghai-11-days-china-2a2fc5c4) | SHORT_ROUTE | tour_graph 10/11; missing last 1; pins 8 | — |
| China | [a7993309](https://aa-tripplanner.vercel.app/tours/great-wall-hike-from-beijing-10-days-china-a7993309) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 7 | — |
| China | [ab3fb3a8](https://aa-tripplanner.vercel.app/tours/great-wall-trek-from-shanhaiguan-to-beijing-8-days-china-ab3fb3a8) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 7 | — |
| China | [15d9ba8e](https://aa-tripplanner.vercel.app/tours/guilin-and-yangshuo-tour-3-days-china-15d9ba8e) | SHORT_ROUTE | tour_graph 2/3; missing last 1; pins 2 | — |
| China | [39bb7911](https://aa-tripplanner.vercel.app/tours/guizhou-to-yangshuo-cycling-tour-12-days-china-39bb7911) | SHORT_ROUTE | tour_graph 11/12; missing last 1; pins 7 | — |
| China | [2ec16c65](https://aa-tripplanner.vercel.app/tours/hainan-cycling-tour-haikou-to-sanya-8-days-china-2ec16c65) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 5 | — |
| China | [9fc1a15f](https://aa-tripplanner.vercel.app/tours/highlights-of-china-shanghai-beijing-xi-an-chengdu-yangshuo-and-hong-kong-11-day-9fc1a15f) | SHORT_ROUTE | tour_graph 10/11; missing last 1; pins 8 | — |
| China | [faef1867](https://aa-tripplanner.vercel.app/tours/highlights-of-tibet-beijing-to-lhasa-13-days-china-faef1867) | SHORT_ROUTE | tour_graph 12/13; missing last 1; pins 12 | — |
| China | [554a7457](https://aa-tripplanner.vercel.app/tours/highlights-of-tibet-tour-beijing-xi-an-and-lhasa-13-days-china-554a7457) | SHORT_ROUTE | tour_graph 12/13; missing last 1; pins 8 | — |
| China | [fda5d19f](https://aa-tripplanner.vercel.app/tours/hike-and-bike-china-16-days-china-fda5d19f) | SHORT_ROUTE | tour_graph 15/16; missing last 1; pins 12 | — |
| China | [ebb9728e](https://aa-tripplanner.vercel.app/tours/hiking-the-great-wall-7-days-china-ebb9728e) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 5 | — |
| China | [927c5e70](https://aa-tripplanner.vercel.app/tours/hong-kong-to-beijing-bullet-train-journey-13-days-china-927c5e70) | SHORT_ROUTE | tour_graph 12/13; missing last 1; pins 8 | — |
| China | [96e2ebdd](https://aa-tripplanner.vercel.app/tours/lhasa-and-namtso-lake-tour-5-days-china-96e2ebdd) | SHORT_ROUTE | tour_graph 4/5; missing last 1; pins 3 | — |
| China | [15d13ec4](https://aa-tripplanner.vercel.app/tours/lhasa-highlights-potala-palace-jokhang-temple-and-yamdrok-lake-4-days-china-15d13ec4) | SHORT_ROUTE | tour_graph 3/4; missing last 1; pins 3 | — |
| China | [786a98e4](https://aa-tripplanner.vercel.app/tours/private-tour-lhasa-gyantse-and-shigatse-5-days-china-786a98e4) | SHORT_ROUTE | tour_graph 4/5; missing last 1; pins 3 | — |
| China | [c3cffa9f](https://aa-tripplanner.vercel.app/tours/running-on-the-wall-beijing-great-wall-and-xi-an-12-days-china-c3cffa9f) | SHORT_ROUTE | tour_graph 11/12; missing first 1; pins 9 | — |
| China | [6bc4ab33](https://aa-tripplanner.vercel.app/tours/shanghai-and-hangzhou-3-days-china-6bc4ab33) | SHORT_ROUTE | tour_graph 2/3; missing last 1; pins 2 | — |
| China | [24befdc9](https://aa-tripplanner.vercel.app/tours/silk-road-china-tour-15-days-china-24befdc9) | SHORT_ROUTE | tour_graph 14/15; missing last 1; pins 12 | — |
| China | [b478272c](https://aa-tripplanner.vercel.app/tours/silk-road-journey-beijing-to-dunhuang-and-jiayuguan-14-days-china-b478272c) | SHORT_ROUTE | tour_graph 13/14; missing last 1; pins 10 | — |
| China | [81f9ee29](https://aa-tripplanner.vercel.app/tours/tibet-beijing-to-kathmandu-21-days-china-81f9ee29) | SHORT_ROUTE | tour_graph 20/21; missing last 1; pins 17 | — |
| China | [72e4fd9f](https://aa-tripplanner.vercel.app/tours/tibet-encompassed-14-days-china-72e4fd9f) | SHORT_ROUTE | tour_graph 13/14; missing last 1; pins 11 | — |
| China | [312aff49](https://aa-tripplanner.vercel.app/tours/tibet-express-lhasa-gyantse-and-shigatse-7-days-china-312aff49) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 6 | — |
| India | [c763435b](https://aa-tripplanner.vercel.app/tours/best-of-southern-india-kerala-and-tamil-nadu-14-days-india-c763435b) | SHORT_ROUTE | tour_graph 13/14; missing last 1; pins 10 | — |
| India | [15ae3046](https://aa-tripplanner.vercel.app/tours/bijli-mahadev-trek-2-days-india-15ae3046) | SHORT_ROUTE | tour_graph 1/2; missing first 1; pins 1 | — |
| India | [7e746f2a](https://aa-tripplanner.vercel.app/tours/classic-rajasthan-15-days-india-7e746f2a) | SHORT_ROUTE | tour_graph 14/15; missing last 1; pins 13 | — |
| India | [5522b60c](https://aa-tripplanner.vercel.app/tours/classic-south-india-kochi-to-kovalam-9-days-india-5522b60c) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 5 | — |
| India | [bec33740](https://aa-tripplanner.vercel.app/tours/cycle-rajasthan-15-days-india-bec33740) | SHORT_ROUTE | tour_graph 14/15; missing last 1; pins 12 | — |
| India | [432a75a2](https://aa-tripplanner.vercel.app/tours/cycling-in-sattal-3-days-india-432a75a2) | SHORT_ROUTE | tour_graph 2/3; missing first 1; pins 2 | — |
| India | [f1e4900a](https://aa-tripplanner.vercel.app/tours/delhi-agra-jaipur-mughal-capitals-palaces-8-days-india-f1e4900a) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 6 | — |
| India | [56bb9527](https://aa-tripplanner.vercel.app/tours/delhi-dharamsala-and-amritsar-cultural-tour-10-days-india-56bb9527) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 6 | — |
| India | [540796dc](https://aa-tripplanner.vercel.app/tours/delhi-to-kathmandu-india-and-nepal-15-days-india-540796dc) | SHORT_ROUTE | tour_graph 14/15; missing last 1; pins 13 | — |
| India | [72b6d430](https://aa-tripplanner.vercel.app/tours/goa-honeymoon-tour-6-days-india-72b6d430) | SHORT_ROUTE | tour_graph 5/6; missing first 1; pins 3 | — |
| India | [684f0dfb](https://aa-tripplanner.vercel.app/tours/golden-triangle-cycling-tour-14-days-india-684f0dfb) | SHORT_ROUTE | tour_graph 13/14; missing last 1; pins 9 | — |
| India | [5122bd9b](https://aa-tripplanner.vercel.app/tours/golden-triangle-delhi-agra-and-jaipur-8-days-india-5122bd9b) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 7 | — |
| India | [e437bbf1](https://aa-tripplanner.vercel.app/tours/golden-triangle-delhi-agra-and-jaipur-8-days-india-e437bbf1) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 6 | — |
| India | [94069baf](https://aa-tripplanner.vercel.app/tours/golden-triangle-tour-with-ajmer-and-pushkar-7-days-india-94069baf) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 6 | — |
| India | [ff98ebb9](https://aa-tripplanner.vercel.app/tours/golden-triangle-tour-with-mandawa-7-days-india-ff98ebb9) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 6 | — |
| India | [ca2ca36a](https://aa-tripplanner.vercel.app/tours/golden-triangle-tour-with-mumbai-7-days-india-ca2ca36a) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 5 | — |
| India | [49e51439](https://aa-tripplanner.vercel.app/tours/golden-triangle-with-orchha-and-khajuraho-8-days-india-49e51439) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 6 | — |
| India | [1e0e7fa9](https://aa-tripplanner.vercel.app/tours/india-encompassed-28-days-india-1e0e7fa9) | SHORT_ROUTE | tour_graph 27/28; missing last 1; pins 21 | — |
| India | [be7b6725](https://aa-tripplanner.vercel.app/tours/india-experience-delhi-rajasthan-and-agra-13-days-india-be7b6725) | SHORT_ROUTE | tour_graph 12/13; missing last 1; pins 10 | — |
| India | [798fd092](https://aa-tripplanner.vercel.app/tours/india-s-golden-triangle-8-days-india-798fd092) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 6 | — |
| India | [17c4ecb0](https://aa-tripplanner.vercel.app/tours/india-s-golden-triangle-amritsar-8-days-india-17c4ecb0) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 6 | — |
| India | [711f1db9](https://aa-tripplanner.vercel.app/tours/india-snapshot-delhi-agra-and-jaipur-6-days-india-711f1db9) | SHORT_ROUTE | tour_graph 5/6; missing last 1; pins 4 | — |
| India | [90089969](https://aa-tripplanner.vercel.app/tours/india-women-s-expedition-13-days-india-90089969) | SHORT_ROUTE | tour_graph 12/13; missing last 1; pins 10 | — |
| India | [f414bd3e](https://aa-tripplanner.vercel.app/tours/ladakh-siachen-e-cycling-expedition-9-days-india-f414bd3e) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 6 | — |
| India | [b0ef3d56](https://aa-tripplanner.vercel.app/tours/luxury-north-india-with-kerala-16-days-india-b0ef3d56) | SHORT_ROUTE | tour_graph 15/16; missing last 1; pins 11 | — |
| India | [ac00fd71](https://aa-tripplanner.vercel.app/tours/meghalaya-cycling-tour-8-days-india-ac00fd71) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 2 | PIN_BELOW_HALF |
| India | [2a605c98](https://aa-tripplanner.vercel.app/tours/mountains-mystics-of-india-13-days-india-2a605c98) | SHORT_ROUTE | tour_graph 12/13; missing last 1; pins 11 | — |
| India | [2f134c99](https://aa-tripplanner.vercel.app/tours/north-india-delhi-to-varanasi-22-days-india-2f134c99) | SHORT_ROUTE | tour_graph 21/22; missing last 1; pins 20 | — |
| India | [ef40701b](https://aa-tripplanner.vercel.app/tours/north-india-highlights-delhi-agra-jaipur-and-pachewar-8-days-india-ef40701b) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 5 | — |
| India | [03ee66ab](https://aa-tripplanner.vercel.app/tours/northern-india-cultural-journey-delhi-varanasi-agra-rajasthan-15-days-india-03ee66ab) | SHORT_ROUTE | tour_graph 14/15; missing last 1; pins 11 | — |
| India | [6fcb4541](https://aa-tripplanner.vercel.app/tours/northern-india-family-holiday-10-days-india-6fcb4541) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 9 | — |
| India | [35f6b607](https://aa-tripplanner.vercel.app/tours/rajasthan-cultural-and-heritage-tour-22-days-india-35f6b607) | SHORT_ROUTE | tour_graph 21/22; missing last 1; pins 16 | — |
| India | [0fa0bbb7](https://aa-tripplanner.vercel.app/tours/rajasthan-cycling-expedition-11-days-india-0fa0bbb7) | SHORT_ROUTE | tour_graph 10/11; missing last 1; pins 6 | — |
| India | [a95de828](https://aa-tripplanner.vercel.app/tours/rajasthan-heritage-tour-19-days-india-a95de828) | SHORT_ROUTE | tour_graph 18/19; missing last 1; pins 13 | — |
| India | [97a1d818](https://aa-tripplanner.vercel.app/tours/rajasthan-laneways-local-villages-15-days-india-97a1d818) | SHORT_ROUTE | tour_graph 14/15; missing last 1; pins 13 | — |
| India | [5a711d53](https://aa-tripplanner.vercel.app/tours/rajasthan-palaces-forts-tiger-reserves-15-days-india-5a711d53) | SHORT_ROUTE | tour_graph 14/15; missing last 1; pins 13 | — |
| India | [b5194ba8](https://aa-tripplanner.vercel.app/tours/rajasthan-taj-mahal-delhi-to-khajuraho-temples-13-days-india-b5194ba8) | SHORT_ROUTE | tour_graph 12/13; missing first 1; pins 11 | — |
| India | [dd958ecf](https://aa-tripplanner.vercel.app/tours/rajasthan-tour-from-delhi-to-delhi-15-days-india-dd958ecf) | SHORT_ROUTE | tour_graph 14/15; missing last 1; pins 13 | — |
| India | [c4448ace](https://aa-tripplanner.vercel.app/tours/real-rajasthan-delhi-bikaner-jaisalmer-jodhpur-udaipur-jaipur-and-agra-16-days-i-c4448ace) | SHORT_ROUTE | tour_graph 15/16; missing last 1; pins 14 | — |
| India | [7ac63a1d](https://aa-tripplanner.vercel.app/tours/sikkim-honeymoon-tour-gangtok-lachung-and-pelling-6-days-india-7ac63a1d) | SHORT_ROUTE | tour_graph 5/6; missing last 1; pins 2 | PIN_BELOW_HALF |
| India | [5a32808b](https://aa-tripplanner.vercel.app/tours/sikkim-kangchenjunga-trek-21-days-india-5a32808b) | SHORT_ROUTE | tour_graph 20/21; missing last 1; pins 16 | — |
| India | [4ccf3346](https://aa-tripplanner.vercel.app/tours/south-india-revealed-kerala-karnataka-and-goa-16-days-india-4ccf3346) | SHORT_ROUTE | tour_graph 15/16; missing last 1; pins 13 | — |
| India | [8b33eed4](https://aa-tripplanner.vercel.app/tours/southern-india-kerala-karnataka-and-tamil-nadu-14-days-india-8b33eed4) | SHORT_ROUTE | tour_graph 13/14; missing last 1; pins 10 | — |
| India | [c3b6dff8](https://aa-tripplanner.vercel.app/tours/southern-india-kochi-to-kochi-15-days-india-c3b6dff8) | SHORT_ROUTE | tour_graph 14/15; missing last 1; pins 13 | — |
| India | [06eaf425](https://aa-tripplanner.vercel.app/tours/stok-kangri-expedition-9-days-india-06eaf425) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 4 | PIN_BELOW_HALF |
| Japan | [0079d599](https://aa-tripplanner.vercel.app/tours/okinawa-from-naha-history-coast-and-tokashiki-island-5-days-japan-0079d599) | SHORT_ROUTE | tour_graph 4/5; missing last 1; pins 3 | — |
| Japan | [0c35c80e](https://aa-tripplanner.vercel.app/tours/yanbaru-forest-and-okinawa-longevity-villages-4-days-japan-0c35c80e) | SHORT_ROUTE | tour_graph 3/4; missing last 1; pins 3 | — |
| Laos | [664086a9](https://aa-tripplanner.vercel.app/tours/classic-laos-10-days-laos-664086a9) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 6 | — |
| Laos | [7c14cb5d](https://aa-tripplanner.vercel.app/tours/classic-laos-6-days-laos-7c14cb5d) | SHORT_ROUTE | tour_graph 5/6; missing last 1; pins 4 | — |
| Laos | [4ca1193d](https://aa-tripplanner.vercel.app/tours/classic-laos-8-days-laos-4ca1193d) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 6 | — |
| Laos | [b9073577](https://aa-tripplanner.vercel.app/tours/impressions-of-laos-9-days-laos-b9073577) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 8 | — |
| Laos | [99c764d3](https://aa-tripplanner.vercel.app/tours/laos-and-vietnam-cycling-tour-from-luang-prabang-to-hanoi-16-days-laos-99c764d3) | SHORT_ROUTE | tour_graph 15/16; missing last 1; pins 9 | — |
| Laos | [292e525d](https://aa-tripplanner.vercel.app/tours/laos-cycling-tour-luang-prabang-vientiane-and-vang-vieng-14-days-laos-292e525d) | SHORT_ROUTE | tour_graph 13/14; missing last 1; pins 7 | — |
| Laos | [bd183835](https://aa-tripplanner.vercel.app/tours/laos-from-north-to-south-16-days-laos-bd183835) | SHORT_ROUTE | tour_graph 15/16; missing last 1; pins 11 | — |
| Laos | [274b546c](https://aa-tripplanner.vercel.app/tours/luang-prabang-cultural-tour-5-days-laos-274b546c) | SHORT_ROUTE | tour_graph 4/5; missing last 1; pins 2 | PIN_BELOW_HALF |
| Laos | [763e21cd](https://aa-tripplanner.vercel.app/tours/luang-prabang-to-vang-vieng-cycling-6-days-laos-763e21cd) | SHORT_ROUTE | tour_graph 5/6; missing first 1; pins 3 | — |
| Laos | [0cae3867](https://aa-tripplanner.vercel.app/tours/luang-prabang-to-vang-vieng-cycling-tour-4-days-laos-0cae3867) | SHORT_ROUTE | tour_graph 3/4; missing first 1; pins 3 | — |
| Laos | [a045779f](https://aa-tripplanner.vercel.app/tours/northern-laos-luang-prabang-nam-kat-and-the-nam-ou-8-days-laos-a045779f) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 4 | — |
| Laos | [edf3474f](https://aa-tripplanner.vercel.app/tours/northern-laos-mekong-namkat-resort-and-nam-ou-10-days-laos-edf3474f) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 6 | — |
| Laos | [b8ee3d60](https://aa-tripplanner.vercel.app/tours/pakse-to-siem-reap-cycling-tour-via-the-4000-islands-and-preah-vihear-14-days-la-b8ee3d60) | SHORT_ROUTE | tour_graph 13/14; missing last 1; pins 8 | — |
| Laos | [2eebd89e](https://aa-tripplanner.vercel.app/tours/yunnan-and-laos-cycling-and-trekking-14-days-laos-2eebd89e) | SHORT_ROUTE | tour_graph 13/14; missing last 1; pins 6 | PIN_BELOW_HALF |
| Mongolia | [6d841428](https://aa-tripplanner.vercel.app/tours/central-mongolia-7-days-6-nights-mongolia-6d841428) | SHORT_ROUTE | tour_graph 5/7; missing first 1; last 1; pins 5 | — |
| Mongolia | [e6b44b45](https://aa-tripplanner.vercel.app/tours/gobi-by-land-10-days-mongolia-e6b44b45) | SHORT_ROUTE | tour_graph 9/10; missing first 1; pins 6 | — |
| Mongolia | [13e0cc40](https://aa-tripplanner.vercel.app/tours/khustai-national-park-and-mongol-nomadic-camp-2-days-1-night-mongolia-13e0cc40) | SHORT_ROUTE | tour_graph 1/2; missing last 1; pins 1 | — |
| Mongolia | [0b472d81](https://aa-tripplanner.vercel.app/tours/trans-siberian-railway-tour-from-ulaanbaatar-to-sainshand-7-days-mongolia-0b472d81) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 4 | — |
| Mongolia | [7d0e01c8](https://aa-tripplanner.vercel.app/tours/trans-siberian-railway-ulaanbaatar-irkutsk-lake-baikal-and-listvyanka-12-days-mo-7d0e01c8) | SHORT_ROUTE | tour_graph 11/12; missing last 1; pins 2 | PIN_BELOW_HALF |
| Nepal | [bc372d03](https://aa-tripplanner.vercel.app/tours/annapurna-base-camp-trek-15-days-nepal-bc372d03) | SHORT_ROUTE | tour_graph 14/15; missing last 1; pins 9 | — |
| Nepal | [e847627a](https://aa-tripplanner.vercel.app/tours/annapurna-base-camp-trek-9-days-nepal-e847627a) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 5 | — |
| Nepal | [c0a184fc](https://aa-tripplanner.vercel.app/tours/annapurna-base-camp-trek-with-poon-hill-16-days-nepal-c0a184fc) | SHORT_ROUTE | tour_graph 15/16; missing first 1; pins 10 | — |
| Nepal | [f5aefe67](https://aa-tripplanner.vercel.app/tours/annapurna-base-camp-trek-with-poonhill-15-days-nepal-f5aefe67) | SHORT_ROUTE | tour_graph 14/15; missing last 1; pins 8 | — |
| Nepal | [dff72478](https://aa-tripplanner.vercel.app/tours/best-of-nepal-kathmandu-pokhara-and-chitwan-7-days-nepal-dff72478) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 5 | — |
| Nepal | [9de73f8e](https://aa-tripplanner.vercel.app/tours/bhutan-cultural-tour-9-days-nepal-9de73f8e) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 7 | — |
| Nepal | [368f3314](https://aa-tripplanner.vercel.app/tours/bhutan-nepal-and-tibet-tour-22-days-nepal-368f3314) | SHORT_ROUTE | tour_graph 21/22; missing last 1; pins 12 | — |
| Nepal | [6143e059](https://aa-tripplanner.vercel.app/tours/bird-watching-tour-in-nepal-10-days-nepal-6143e059) | SHORT_ROUTE | tour_graph 9/10; missing first 1; pins 3 | PIN_BELOW_HALF |
| Nepal | [0cb86a64](https://aa-tripplanner.vercel.app/tours/damodar-kunda-and-muktinath-trek-23-days-nepal-0cb86a64) | SHORT_ROUTE | tour_graph 21/23; missing first 1; last 1; pins 7 | PIN_BELOW_HALF |
| Nepal | [d8fe530a](https://aa-tripplanner.vercel.app/tours/damodar-kunda-trek-15-days-nepal-d8fe530a) | SHORT_ROUTE | tour_graph 14/15; missing last 1; pins 7 | PIN_BELOW_HALF |
| Nepal | [98624d92](https://aa-tripplanner.vercel.app/tours/everest-base-camp-lhasa-and-kailash-motorbike-tour-24-days-nepal-98624d92) | SHORT_ROUTE | tour_graph 23/24; missing last 1; pins 11 | PIN_BELOW_HALF |
| Nepal | [ac104e19](https://aa-tripplanner.vercel.app/tours/everest-base-camp-trek-14-days-nepal-ac104e19) | SHORT_ROUTE | tour_graph 13/14; missing last 1; pins 8 | — |
| Nepal | [dccab98d](https://aa-tripplanner.vercel.app/tours/everest-base-camp-trek-15-days-nepal-dccab98d) | SHORT_ROUTE | tour_graph 14/15; missing last 1; pins 10 | — |
| Nepal | [de1eea74](https://aa-tripplanner.vercel.app/tours/everest-base-camp-trek-15-days-nepal-de1eea74) | SHORT_ROUTE | tour_graph 13/15; missing first 1; last 1; pins 7 | PIN_BELOW_HALF |
| Nepal | [d43cd7c3](https://aa-tripplanner.vercel.app/tours/ghorepani-poonhill-trek-11-days-nepal-d43cd7c3) | SHORT_ROUTE | tour_graph 10/11; missing last 1; pins 6 | — |
| Nepal | [690d2fce](https://aa-tripplanner.vercel.app/tours/gokyo-lake-trek-13-days-nepal-690d2fce) | SHORT_ROUTE | tour_graph 12/13; missing last 1; pins 10 | — |
| Nepal | [709bd3db](https://aa-tripplanner.vercel.app/tours/gokyo-lakes-and-everest-base-camp-trek-16-days-nepal-709bd3db) | SHORT_ROUTE | tour_graph 15/16; missing last 1; pins 13 | — |
| Nepal | [334ef8ff](https://aa-tripplanner.vercel.app/tours/island-peak-gokyo-lake-and-everest-base-camp-22-days-nepal-334ef8ff) | SHORT_ROUTE | tour_graph 20/22; missing first 1; last 1; pins 15 | — |
| Nepal | [cadad720](https://aa-tripplanner.vercel.app/tours/jomsom-muktinath-poonhill-trek-13-days-nepal-cadad720) | SHORT_ROUTE | tour_graph 12/13; missing last 1; pins 8 | — |
| Nepal | [c158c6e3](https://aa-tripplanner.vercel.app/tours/kailash-inner-kora-from-kathmandu-13-days-nepal-c158c6e3) | SHORT_ROUTE | tour_graph 12/13; missing last 1; pins 9 | — |
| Nepal | [a5f30249](https://aa-tripplanner.vercel.app/tours/kailash-mansarovar-yatra-by-helicopter-11-days-nepal-a5f30249) | SHORT_ROUTE | tour_graph 10/11; missing last 1; pins 5 | PIN_BELOW_HALF |
| Nepal | [bc498fc5](https://aa-tripplanner.vercel.app/tours/kailash-mansarovar-yatra-via-lhasa-15-days-nepal-bc498fc5) | SHORT_ROUTE | tour_graph 14/15; missing last 1; pins 6 | PIN_BELOW_HALF |
| Nepal | [e0b0918c](https://aa-tripplanner.vercel.app/tours/kailash-mansarovar-yatra-with-saga-dawa-festival-fly-in-drive-out-16-days-nepal-e0b0918c) | SHORT_ROUTE | tour_graph 15/16; missing last 1; pins 7 | PIN_BELOW_HALF |
| Nepal | [116c1706](https://aa-tripplanner.vercel.app/tours/kailash-overland-tour-via-kerung-13-days-nepal-116c1706) | SHORT_ROUTE | tour_graph 12/13; missing last 1; pins 8 | — |
| Nepal | [beb84744](https://aa-tripplanner.vercel.app/tours/kathmandu-lhasa-everest-base-camp-and-kailash-parikrama-17-days-nepal-beb84744) | SHORT_ROUTE | tour_graph 16/17; missing last 1; pins 13 | — |
| Nepal | [aba6338a](https://aa-tripplanner.vercel.app/tours/khopra-danda-trek-10-days-nepal-aba6338a) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 4 | PIN_BELOW_HALF |
| Nepal | [40f96b68](https://aa-tripplanner.vercel.app/tours/langtang-and-gosaikunda-trek-15-days-nepal-40f96b68) | SHORT_ROUTE | tour_graph 14/15; missing last 1; pins 1 | PIN_BELOW_HALF |
| Nepal | [0b3b7a24](https://aa-tripplanner.vercel.app/tours/langtang-valley-trek-10-days-nepal-0b3b7a24) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 1 | PIN_BELOW_HALF |
| Nepal | [2211c7f0](https://aa-tripplanner.vercel.app/tours/lhasa-and-namtso-lake-5-days-nepal-2211c7f0) | SHORT_ROUTE | tour_graph 4/5; missing last 1; pins 2 | PIN_BELOW_HALF |
| Nepal | [1ef96951](https://aa-tripplanner.vercel.app/tours/lhasa-cultural-tour-5-days-nepal-1ef96951) | SHORT_ROUTE | tour_graph 3/5; missing first 1; last 1; pins 1 | PIN_BELOW_HALF |
| Nepal | [0f7ac225](https://aa-tripplanner.vercel.app/tours/lhasa-gyantse-and-shigatse-tour-7-days-nepal-0f7ac225) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 3 | PIN_BELOW_HALF |
| Nepal | [ac5b5b43](https://aa-tripplanner.vercel.app/tours/lhasa-kailash-and-everest-base-camp-overland-tour-17-days-nepal-ac5b5b43) | SHORT_ROUTE | tour_graph 16/17; missing last 1; pins 12 | — |
| Nepal | [3511d8ef](https://aa-tripplanner.vercel.app/tours/lhasa-kailash-guge-kingdom-and-everest-base-camp-tour-20-days-nepal-3511d8ef) | SHORT_ROUTE | tour_graph 19/20; missing last 1; pins 14 | — |
| Nepal | [d54db345](https://aa-tripplanner.vercel.app/tours/lhasa-mount-kailash-and-guge-kingdom-overland-tour-18-days-nepal-d54db345) | SHORT_ROUTE | tour_graph 17/18; missing last 1; pins 10 | — |
| Nepal | [481e3dab](https://aa-tripplanner.vercel.app/tours/lower-mustang-motorbike-tour-10-days-nepal-481e3dab) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 3 | PIN_BELOW_HALF |
| Nepal | [f964fe2d](https://aa-tripplanner.vercel.app/tours/maha-shivratri-tour-kathmandu-pokhara-and-muktinath-7-days-nepal-f964fe2d) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 5 | — |
| Nepal | [706bcdaa](https://aa-tripplanner.vercel.app/tours/mera-peak-climb-17-days-nepal-706bcdaa) | SHORT_ROUTE | tour_graph 16/17; missing last 1; pins 11 | — |
| Nepal | [2a943f95](https://aa-tripplanner.vercel.app/tours/motorbike-tour-to-kailash-and-lake-manasarovar-from-kathmandu-13-days-nepal-2a943f95) | SHORT_ROUTE | tour_graph 12/13; missing last 1; pins 5 | PIN_BELOW_HALF |
| Nepal | [7f07f4a7](https://aa-tripplanner.vercel.app/tours/mount-kailash-parikrama-and-saga-dawa-festival-14-days-nepal-7f07f4a7) | SHORT_ROUTE | tour_graph 13/14; missing last 1; pins 6 | PIN_BELOW_HALF |
| Nepal | [96b8d006](https://aa-tripplanner.vercel.app/tours/muktinath-overland-tour-from-pokhara-2-days-nepal-96b8d006) | SHORT_ROUTE | tour_graph 1/2; missing last 1; pins 1 | — |
| Nepal | [0d92d75e](https://aa-tripplanner.vercel.app/tours/nar-phu-valley-trek-18-days-nepal-0d92d75e) | SHORT_ROUTE | tour_graph 17/18; missing last 1; pins 13 | — |
| Nepal | [9ed6142e](https://aa-tripplanner.vercel.app/tours/nepal-and-bhutan-tour-8-days-nepal-9ed6142e) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 6 | — |
| Nepal | [b194bd6d](https://aa-tripplanner.vercel.app/tours/nepal-motorbiking-tour-12-days-nepal-b194bd6d) | SHORT_ROUTE | tour_graph 11/12; missing last 1; pins 7 | — |
| Nepal | [5a79408b](https://aa-tripplanner.vercel.app/tours/short-lower-dolpa-trek-nepal-13-days-nepal-5a79408b) | SHORT_ROUTE | tour_graph 12/13; missing last 1; pins 8 | — |
| Nepal | [a42bc61f](https://aa-tripplanner.vercel.app/tours/trishuli-river-rafting-2-days-nepal-a42bc61f) | SHORT_ROUTE | places 1/2; missing first 1; pins 1 | — |
| South Korea | [4012d8e3](https://aa-tripplanner.vercel.app/tours/cycle-south-korea-9-days-south-korea-4012d8e3) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 6 | — |
| South Korea | [db7c7eb6](https://aa-tripplanner.vercel.app/tours/hiking-trekking-and-temple-stay-in-south-korea-12-days-south-korea-db7c7eb6) | SHORT_ROUTE | tour_graph 11/12; missing last 1; pins 4 | PIN_BELOW_HALF |
| South Korea | [68b392ba](https://aa-tripplanner.vercel.app/tours/life-and-culture-of-south-korea-12-days-south-korea-68b392ba) | SHORT_ROUTE | tour_graph 10/12; missing first 1; last 1; pins 8 | — |
| South Korea | [8cfac543](https://aa-tripplanner.vercel.app/tours/namhae-island-sea-kayaking-hiking-and-village-home-stay-3-days-south-korea-8cfac543) | SHORT_ROUTE | tour_graph 2/3; missing first 1; pins 1 | PIN_BELOW_HALF |
| South Korea | [1362541b](https://aa-tripplanner.vercel.app/tours/seoul-to-busan-cycling-tour-8-days-south-korea-1362541b) | SHORT_ROUTE | tour_graph 7/8; missing first 1; pins 5 | — |
| South Korea | [d1c94102](https://aa-tripplanner.vercel.app/tours/seoul-to-jeju-cycling-tour-15-days-south-korea-d1c94102) | SHORT_ROUTE | tour_graph 14/15; missing last 1; pins 13 | — |
| South Korea | [d9b10288](https://aa-tripplanner.vercel.app/tours/south-korea-explorer-9-days-south-korea-d9b10288) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 6 | — |
| South Korea | [1f19cdf0](https://aa-tripplanner.vercel.app/tours/south-korea-guided-bike-tour-9-days-south-korea-1f19cdf0) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 4 | PIN_BELOW_HALF |
| South Korea | [d9e9ffa0](https://aa-tripplanner.vercel.app/tours/south-korea-heritage-bike-tour-seoul-to-andong-9-days-south-korea-d9e9ffa0) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 3 | PIN_BELOW_HALF |
| South Korea | [ab061445](https://aa-tripplanner.vercel.app/tours/south-korea-highlights-seoul-to-busan-walking-and-hiking-tour-8-days-south-korea-ab061445) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 7 | — |
| South Korea | [54b7d6b1](https://aa-tripplanner.vercel.app/tours/south-korea-seoul-gyeongju-and-busan-9-days-south-korea-54b7d6b1) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 6 | — |
| South Korea | [3750c4c2](https://aa-tripplanner.vercel.app/tours/south-korea-seoul-gyeongju-busan-and-jeju-9-days-south-korea-3750c4c2) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 8 | — |
| South Korea | [40769f2c](https://aa-tripplanner.vercel.app/tours/south-korea-seoul-hanok-villages-island-10-days-south-korea-40769f2c) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 9 | — |
| South Korea | [b01dd2a6](https://aa-tripplanner.vercel.app/tours/south-korea-seoul-seoraksan-andong-busan-and-jeju-14-days-south-korea-b01dd2a6) | SHORT_ROUTE | tour_graph 13/14; missing last 1; pins 9 | — |
| Sri Lanka | [ba7a93da](https://aa-tripplanner.vercel.app/tours/beach-and-wildlife-tour-in-sri-lanka-10-days-9-nights-sri-lanka-ba7a93da) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 4 | PIN_BELOW_HALF |
| Sri Lanka | [ea500c73](https://aa-tripplanner.vercel.app/tours/beach-and-wildlife-tour-of-sri-lanka-8-days-sri-lanka-ea500c73) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 2 | PIN_BELOW_HALF |
| Sri Lanka | [f32a8105](https://aa-tripplanner.vercel.app/tours/bentota-beach-yala-and-udawalawe-wildlife-tour-sri-lanka-10-days-sri-lanka-f32a8105) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 8 | — |
| Sri Lanka | [338fdd12](https://aa-tripplanner.vercel.app/tours/bird-watching-tour-of-sri-lanka-10-days-sri-lanka-338fdd12) | SHORT_ROUTE | tour_graph 8/10; missing first 1; last 1; pins 5 | — |
| Sri Lanka | [86e7574c](https://aa-tripplanner.vercel.app/tours/bird-watching-tour-of-sri-lanka-9-days-sri-lanka-86e7574c) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 3 | PIN_BELOW_HALF |
| Sri Lanka | [4ef4f182](https://aa-tripplanner.vercel.app/tours/birding-and-wildlife-tour-in-sri-lanka-7-days-sri-lanka-4ef4f182) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 3 | PIN_BELOW_HALF |
| Sri Lanka | [4b6224b9](https://aa-tripplanner.vercel.app/tours/delights-of-sri-lanka-7-days-sri-lanka-4b6224b9) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 5 | — |
| Sri Lanka | [b88aba4d](https://aa-tripplanner.vercel.app/tours/eco-rustic-explorer-sri-lanka-negombo-anamaduwa-and-sigiriya-7-days-sri-lanka-b88aba4d) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 1 | PIN_BELOW_HALF |
| Sri Lanka | [c93a4b34](https://aa-tripplanner.vercel.app/tours/endemic-bird-watching-tour-of-sri-lanka-15-days-sri-lanka-c93a4b34) | SHORT_ROUTE | tour_graph 14/15; missing last 1; pins 5 | PIN_BELOW_HALF |
| Sri Lanka | [829927a5](https://aa-tripplanner.vercel.app/tours/family-adventure-holiday-in-sri-lanka-12-days-sri-lanka-829927a5) | SHORT_ROUTE | tour_graph 11/12; missing last 1; pins 5 | PIN_BELOW_HALF |
| Sri Lanka | [da87e83b](https://aa-tripplanner.vercel.app/tours/family-adventure-holiday-in-sri-lanka-18-days-sri-lanka-da87e83b) | SHORT_ROUTE | tour_graph 17/18; missing last 1; pins 9 | — |
| Sri Lanka | [a7ee157f](https://aa-tripplanner.vercel.app/tours/family-adventure-in-sri-lanka-with-teenage-kids-18-days-sri-lanka-a7ee157f) | SHORT_ROUTE | tour_graph 17/18; missing last 1; pins 7 | PIN_BELOW_HALF |
| Sri Lanka | [b1c59f08](https://aa-tripplanner.vercel.app/tours/family-holiday-in-sri-lanka-15-days-sri-lanka-b1c59f08) | SHORT_ROUTE | tour_graph 14/15; missing last 1; pins 13 | — |
| Sri Lanka | [80477347](https://aa-tripplanner.vercel.app/tours/highland-colombo-sri-lanka-4-days-sri-lanka-80477347) | SHORT_ROUTE | tour_graph 3/4; missing last 1; pins 3 | — |
| Sri Lanka | [43b9e261](https://aa-tripplanner.vercel.app/tours/honeymoon-tour-in-sri-lanka-7-days-6-nights-sri-lanka-43b9e261) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 4 | — |
| Sri Lanka | [4aa09ab8](https://aa-tripplanner.vercel.app/tours/honeymoon-tour-in-sri-lanka-option-ii-10-days-9-nights-sri-lanka-4aa09ab8) | SHORT_ROUTE | tour_graph 8/10; missing first 1; last 1; pins 5 | — |
| Sri Lanka | [b14bd485](https://aa-tripplanner.vercel.app/tours/passikudah-beach-and-wilpattu-wildlife-tour-8-days-sri-lanka-b14bd485) | SHORT_ROUTE | tour_graph 7/8; missing last 1; pins 4 | — |
| Sri Lanka | [f9b54865](https://aa-tripplanner.vercel.app/tours/passikudah-beach-and-wilpattu-wildlife-tour-sri-lanka-10-days-sri-lanka-f9b54865) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 1 | PIN_BELOW_HALF |
| Sri Lanka | [bd1a1cb7](https://aa-tripplanner.vercel.app/tours/sri-lanka-beach-and-safari-bentota-mirissa-yala-and-udawalawe-10-days-sri-lanka-bd1a1cb7) | SHORT_ROUTE | tour_graph 8/10; missing first 1; last 1; pins 5 | — |
| Sri Lanka | [3887d68b](https://aa-tripplanner.vercel.app/tours/sri-lanka-beach-and-wildlife-tour-tangalle-yala-and-udawalawe-10-days-sri-lanka-3887d68b) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 4 | PIN_BELOW_HALF |
| Sri Lanka | [44b63c6a](https://aa-tripplanner.vercel.app/tours/sri-lanka-birding-tour-18-days-sri-lanka-44b63c6a) | SHORT_ROUTE | tour_graph 17/18; missing last 1; pins 11 | — |
| Sri Lanka | [a3e3a9ce](https://aa-tripplanner.vercel.app/tours/sri-lanka-colombo-kandy-sigiriya-hatton-yala-and-thalpe-10-days-9-nights-sri-lan-a3e3a9ce) | SHORT_ROUTE | tour_graph 8/10; missing first 1; last 1; pins 4 | PIN_BELOW_HALF |
| Sri Lanka | [87d77f66](https://aa-tripplanner.vercel.app/tours/sri-lanka-cultural-and-coastal-highlights-7-days-sri-lanka-87d77f66) | SHORT_ROUTE | tour_graph 6/7; missing first 1; pins 3 | PIN_BELOW_HALF |
| Sri Lanka | [8ae2ee73](https://aa-tripplanner.vercel.app/tours/sri-lanka-cultural-and-wildlife-journey-colombo-wilpattu-anuradhapura-kandy-nuwa-8ae2ee73) | SHORT_ROUTE | tour_graph 8/10; missing first 1; last 1; pins 5 | — |
| Sri Lanka | [b777cca6](https://aa-tripplanner.vercel.app/tours/sri-lanka-family-wildlife-and-village-tour-10-days-sri-lanka-b777cca6) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 4 | PIN_BELOW_HALF |
| Sri Lanka | [63d0fe36](https://aa-tripplanner.vercel.app/tours/sri-lanka-heritage-wildlife-and-beach-14-days-sri-lanka-63d0fe36) | SHORT_ROUTE | tour_graph 13/14; missing first 1; pins 7 | — |
| Sri Lanka | [2b0b0f3a](https://aa-tripplanner.vercel.app/tours/sri-lanka-highlights-and-local-experiences-14-days-sri-lanka-2b0b0f3a) | SHORT_ROUTE | tour_graph 13/14; missing first 1; pins 8 | — |
| Sri Lanka | [f2bdccc9](https://aa-tripplanner.vercel.app/tours/sri-lanka-highlights-anuradhapura-wilpattu-sigiriya-and-dambulla-7-days-sri-lank-f2bdccc9) | SHORT_ROUTE | tour_graph 6/7; missing first 1; pins 5 | — |
| Sri Lanka | [63d21f32](https://aa-tripplanner.vercel.app/tours/sri-lanka-honeymoon-tour-anuradhapura-kandy-and-negombo-10-days-sri-lanka-63d21f32) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 4 | PIN_BELOW_HALF |
| Sri Lanka | [0fa7b0ef](https://aa-tripplanner.vercel.app/tours/sri-lanka-honeymoon-tour-colombo-kandalama-kandy-bentota-and-galle-10-days-sri-l-0fa7b0ef) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 5 | — |
| Sri Lanka | [c7d92000](https://aa-tripplanner.vercel.app/tours/sri-lanka-honeymoon-tour-colombo-kandy-hatton-kitulgala-and-yala-10-days-9-night-c7d92000) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 4 | PIN_BELOW_HALF |
| Sri Lanka | [97b4b821](https://aa-tripplanner.vercel.app/tours/sri-lanka-honeymoon-tour-kandy-tea-country-and-negombo-beach-7-days-sri-lanka-97b4b821) | SHORT_ROUTE | tour_graph 5/7; missing first 1; last 1; pins 1 | PIN_BELOW_HALF |
| Sri Lanka | [b33281fc](https://aa-tripplanner.vercel.app/tours/sri-lanka-honeymoon-tour-tea-country-horton-plains-and-negombo-7-days-sri-lanka-b33281fc) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 1 | PIN_BELOW_HALF |
| Sri Lanka | [6830196b](https://aa-tripplanner.vercel.app/tours/sri-lanka-north-east-jaffna-trincomalee-passikudah-arugam-bay-and-udawalawe-14-d-6830196b) | SHORT_ROUTE | tour_graph 13/14; missing last 1; pins 3 | PIN_BELOW_HALF |
| Sri Lanka | [66e190db](https://aa-tripplanner.vercel.app/tours/sri-lanka-overland-adventure-wildlife-hill-treks-and-village-stays-20-days-sri-l-66e190db) | SHORT_ROUTE | tour_graph 19/20; missing last 1; pins 6 | PIN_BELOW_HALF |
| Sri Lanka | [6b390225](https://aa-tripplanner.vercel.app/tours/sri-lanka-self-guided-journey-by-public-transport-22-days-sri-lanka-6b390225) | SHORT_ROUTE | tour_graph 21/22; missing last 1; pins 10 | PIN_BELOW_HALF |
| Sri Lanka | [10098d76](https://aa-tripplanner.vercel.app/tours/sri-lanka-tea-wildlife-and-beach-6-days-sri-lanka-10098d76) | SHORT_ROUTE | tour_graph 5/6; missing last 1; pins 4 | — |
| Sri Lanka | [e8f3d0d3](https://aa-tripplanner.vercel.app/tours/sri-lanka-wildlife-big-4-photography-tour-9-days-sri-lanka-e8f3d0d3) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 7 | — |
| Sri Lanka | [f4da4a45](https://aa-tripplanner.vercel.app/tours/sri-lanka-wildlife-photography-tour-leopard-elephant-blue-whale-sloth-bear-and-b-f4da4a45) | SHORT_ROUTE | tour_graph 13/14; missing last 1; pins 10 | — |
| Sri Lanka | [48c299af](https://aa-tripplanner.vercel.app/tours/sri-lanka-wilpattu-anuradhapura-sigiriya-and-kandy-7-days-sri-lanka-48c299af) | SHORT_ROUTE | tour_graph 5/7; missing first 1; last 1; pins 3 | PIN_BELOW_HALF |
| Sri Lanka | [77278764](https://aa-tripplanner.vercel.app/tours/sri-lankan-classics-cultural-triangle-hill-country-yala-and-the-south-coast-16-d-77278764) | SHORT_ROUTE | tour_graph 15/16; missing last 1; pins 10 | — |
| Sri Lanka | [79de4d60](https://aa-tripplanner.vercel.app/tours/tangalle-yala-and-negombo-honeymoon-tour-7-days-sri-lanka-79de4d60) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 1 | PIN_BELOW_HALF |
| Sri Lanka | [97a60e0b](https://aa-tripplanner.vercel.app/tours/tea-wildlife-and-coast-in-sri-lanka-9-days-sri-lanka-97a60e0b) | SHORT_ROUTE | tour_graph 8/9; missing last 1; pins 3 | PIN_BELOW_HALF |
| Sri Lanka | [25e9e723](https://aa-tripplanner.vercel.app/tours/wildlife-bird-watching-tour-in-sri-lanka-7-days-sri-lanka-25e9e723) | SHORT_ROUTE | tour_graph 5/7; missing first 1; last 1; pins 4 | — |
| Sri Lanka | [cd8bc159](https://aa-tripplanner.vercel.app/tours/wilpattu-safari-and-negombo-beach-honeymoon-sri-lanka-7-days-sri-lanka-cd8bc159) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 2 | PIN_BELOW_HALF |
| Taiwan | [43446904](https://aa-tripplanner.vercel.app/tours/syakaro-historic-trail-and-smangus-giant-trees-2-days-taiwan-43446904) | SHORT_ROUTE | places 1/2; missing first 1; pins 1 | — |
| Taiwan | [c7cf9f1f](https://aa-tripplanner.vercel.app/tours/taiwan-bike-hike-and-river-adventures-11-days-taiwan-c7cf9f1f) | SHORT_ROUTE | tour_graph 10/11; missing last 1; pins 1 | PIN_BELOW_HALF |
| Thailand | [91a362f8](https://aa-tripplanner.vercel.app/tours/bangkok-to-the-golden-triangle-biking-hiking-and-kayaking-in-thailand-10-days-th-91a362f8) | SHORT_ROUTE | tour_graph 9/10; missing first 1; pins 6 | — |
| Thailand | [15a4ed31](https://aa-tripplanner.vercel.app/tours/central-and-northern-thailand-soft-adventure-10-days-thailand-15a4ed31) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 2 | PIN_BELOW_HALF |
| Thailand | [b3765df1](https://aa-tripplanner.vercel.app/tours/chiang-dao-trekking-and-village-homestay-2-days-thailand-b3765df1) | SHORT_ROUTE | places 1/2; missing first 1; pins 1 | — |
| Thailand | [27da7ebe](https://aa-tripplanner.vercel.app/tours/chiang-mai-hilltribe-mountain-villages-2-days-thailand-27da7ebe) | SHORT_ROUTE | places 1/2; missing first 1; pins 1 | — |
| Thailand | [9ad903f2](https://aa-tripplanner.vercel.app/tours/chiangdao-highlands-overnight-trek-2-days-thailand-9ad903f2) | SHORT_ROUTE | places 1/2; missing first 1; pins 1 | — |
| Thailand | [e53c44c6](https://aa-tripplanner.vercel.app/tours/cycle-bangkok-to-ho-chi-minh-city-thailand-cambodia-and-vietnam-14-days-thailand-e53c44c6) | SHORT_ROUTE | tour_graph 13/14; missing last 1; pins 9 | — |
| Thailand | [3606efc6](https://aa-tripplanner.vercel.app/tours/hilltribe-trek-from-chiang-mai-northern-thailand-5-days-thailand-3606efc6) | SHORT_ROUTE | tour_graph 4/5; missing last 1; pins 1 | PIN_BELOW_HALF |
| Thailand | [700044ca](https://aa-tripplanner.vercel.app/tours/northern-thailand-and-laos-cycling-tour-12-days-thailand-700044ca) | SHORT_ROUTE | tour_graph 11/12; missing last 1; pins 7 | — |
| Thailand | [f5512ffb](https://aa-tripplanner.vercel.app/tours/southern-thailand-coastal-cycle-tour-7-days-self-guided-thailand-f5512ffb) | SHORT_ROUTE | tour_graph 6/7; missing last 1; pins 3 | PIN_BELOW_HALF |
| Thailand | [6cb13a96](https://aa-tripplanner.vercel.app/tours/thailand-and-cambodia-multisport-tour-12-days-thailand-6cb13a96) | SHORT_ROUTE | tour_graph 11/12; missing last 1; pins 10 | — |
| Thailand | [45ee47ba](https://aa-tripplanner.vercel.app/tours/thailand-bangkok-chiang-mai-kanchanaburi-10-days-thailand-45ee47ba) | SHORT_ROUTE | tour_graph 9/10; missing last 1; pins 6 | — |
| Thailand | [fedaa700](https://aa-tripplanner.vercel.app/tours/thailand-discovery-12-days-thailand-fedaa700) | SHORT_ROUTE | tour_graph 11/12; missing last 1; pins 6 | — |
| Thailand | [8628ef79](https://aa-tripplanner.vercel.app/tours/thailand-north-and-koh-samui-bangkok-sukhothai-chiang-rai-chiang-mai-11-days-tha-8628ef79) | SHORT_ROUTE | tour_graph 10/11; missing first 1; pins 7 | — |

### (b2) Same F2 code gap, but 2+ days missing at one end (49)

Also edge-only (the route never has holes inside, see Method), so the F2 code fix would cover these days, but only as unpinned carry days. Two or more stop-less days at an end usually means those days' places did not resolve (F2 class B, data). In the sample there were 3 such tours; across the catalogue there are 49, 23 of them in Sri Lanka (Kalpitiya/Wilpattu/south-coast tours). 38 of the 49 also pin fewer than half of the tour days (one of them, `51285758`, pins none).

| Country | Tour page | Class | Numbers | Extra flags |
|---|---|---|---|---|
| China | [09b3c6b4](https://aa-tripplanner.vercel.app/tours/cultural-tour-of-kazakhstan-kyrgyzstan-and-china-19-days-18-nights-china-09b3c6b4) | SHORT_ROUTE | tour_graph 16/19; missing first 3; pins 13 | — |
| China | [66eb3286](https://aa-tripplanner.vercel.app/tours/cycle-guangdong-to-yangshuo-8-days-china-66eb3286) | SHORT_ROUTE | tour_graph 6/8; missing last 2; pins 5 | — |
| India | [3c271a1c](https://aa-tripplanner.vercel.app/tours/india-and-sri-lanka-experience-24-days-india-3c271a1c) | SHORT_ROUTE | tour_graph 22/24; missing last 2; pins 18 | — |
| India | [51285758](https://aa-tripplanner.vercel.app/tours/kullu-to-bir-billing-cycling-rafting-and-trekking-4-days-india-51285758) | SHORT_ROUTE | tour_graph 1/4; missing first 3; pins 0 | ZERO_PIN |
| India | [a5665631](https://aa-tripplanner.vercel.app/tours/sikkim-assam-and-nagaland-expedition-16-days-india-a5665631) | SHORT_ROUTE | tour_graph 7/16; missing first 1; last 8; pins 3 | PIN_BELOW_HALF |
| Japan | [a90ddcc5](https://aa-tripplanner.vercel.app/tours/nasu-to-nikko-gourmet-cycling-tour-6-days-japan-a90ddcc5) | SHORT_ROUTE | tour_graph 2/6; missing last 4; pins 1 | PIN_BELOW_HALF |
| Japan | [4246ce3f](https://aa-tripplanner.vercel.app/tours/northern-okinawa-experience-3-days-japan-4246ce3f) | SHORT_ROUTE | tour_graph 1/3; missing first 2; pins 1 | PIN_BELOW_HALF |
| Japan | [f364dfea](https://aa-tripplanner.vercel.app/tours/northern-okinawa-villages-and-yambaru-forest-4-days-japan-f364dfea) | SHORT_ROUTE | tour_graph 2/4; missing first 2; pins 2 | — |
| Japan | [5dc8b7f7](https://aa-tripplanner.vercel.app/tours/okinawa-coral-and-uminchu-fishing-culture-yanbaru-4-days-japan-5dc8b7f7) | SHORT_ROUTE | tour_graph 1/4; missing first 3; pins 1 | PIN_BELOW_HALF |
| Japan | [b2fe0d36](https://aa-tripplanner.vercel.app/tours/okinawa-island-hop-naha-kerama-islands-yomitan-and-izena-7-days-japan-b2fe0d36) | SHORT_ROUTE | tour_graph 5/7; missing last 2; pins 2 | PIN_BELOW_HALF |
| Japan | [a83cec93](https://aa-tripplanner.vercel.app/tours/tokyo-by-bicycle-20km-loop-through-temple-tower-park-japan-a83cec93) | SHORT_ROUTE | tour_graph 1/4; missing first 2; last 1; pins 1 | PIN_BELOW_HALF |
| Laos | [f63c3ce9](https://aa-tripplanner.vercel.app/tours/luang-prabang-temples-kuang-si-and-pak-ou-caves-4-days-laos-f63c3ce9) | SHORT_ROUTE | tour_graph 2/4; missing last 2; pins 2 | — |
| Nepal | [97998bbb](https://aa-tripplanner.vercel.app/tours/everest-base-camp-trek-15-days-nepal-97998bbb) | SHORT_ROUTE | tour_graph 12/15; missing first 1; last 2; pins 8 | — |
| Nepal | [8e6022ea](https://aa-tripplanner.vercel.app/tours/kailash-door-darshan-via-limi-valley-and-lapcha-la-nepal-7-days-nepal-8e6022ea) | SHORT_ROUTE | tour_graph 5/7; missing last 2; pins 2 | PIN_BELOW_HALF |
| Nepal | [346c2cfa](https://aa-tripplanner.vercel.app/tours/kailash-helicopter-tour-via-lucknow-9-days-nepal-346c2cfa) | SHORT_ROUTE | tour_graph 6/9; missing last 3; pins 4 | PIN_BELOW_HALF |
| Nepal | [2b9070e3](https://aa-tripplanner.vercel.app/tours/mardi-himal-trek-9-days-nepal-2b9070e3) | SHORT_ROUTE | tour_graph 6/9; missing first 2; last 1; pins 3 | PIN_BELOW_HALF |
| Nepal | [5190cf8f](https://aa-tripplanner.vercel.app/tours/mustang-muktinath-and-annapurna-cycling-expedition-9-days-nepal-5190cf8f) | SHORT_ROUTE | tour_graph 6/9; missing first 2; last 1; pins 4 | PIN_BELOW_HALF |
| Nepal | [fbfb8d1d](https://aa-tripplanner.vercel.app/tours/pikey-peak-trek-7-days-nepal-fbfb8d1d) | SHORT_ROUTE | tour_graph 4/7; missing first 3; pins 1 | PIN_BELOW_HALF |
| Nepal | [5952635b](https://aa-tripplanner.vercel.app/tours/tibet-overland-group-tour-from-kathmandu-to-lhasa-8-days-nepal-5952635b) | SHORT_ROUTE | tour_graph 5/8; missing first 2; last 1; pins 5 | — |
| South Korea | [7d7989ee](https://aa-tripplanner.vercel.app/tours/south-korea-family-adventure-tour-9-days-south-korea-7d7989ee) | SHORT_ROUTE | tour_graph 7/9; missing last 2; pins 4 | PIN_BELOW_HALF |
| South Korea | [f659eb87](https://aa-tripplanner.vercel.app/tours/south-korea-on-foot-10-days-south-korea-f659eb87) | SHORT_ROUTE | tour_graph 8/10; missing last 2; pins 5 | — |
| Sri Lanka | [507e5c10](https://aa-tripplanner.vercel.app/tours/beach-and-wildlife-tour-of-sri-lanka-10-days-9-nights-sri-lanka-507e5c10) | SHORT_ROUTE | tour_graph 3/10; missing first 6; last 1; pins 2 | PIN_BELOW_HALF |
| Sri Lanka | [e6696066](https://aa-tripplanner.vercel.app/tours/beach-and-wildlife-tour-of-sri-lanka-10-days-9-nights-sri-lanka-e6696066) | SHORT_ROUTE | tour_graph 3/10; missing first 6; last 1; pins 1 | PIN_BELOW_HALF |
| Sri Lanka | [1494f49c](https://aa-tripplanner.vercel.app/tours/beach-and-wildlife-tour-of-sri-lanka-8-days-7-nights-sri-lanka-1494f49c) | SHORT_ROUTE | tour_graph 5/8; missing first 2; last 1; pins 2 | PIN_BELOW_HALF |
| Sri Lanka | [584cad4f](https://aa-tripplanner.vercel.app/tours/beach-and-wildlife-tour-of-sri-lanka-kalpitiya-and-wilpattu-8-days-sri-lanka-584cad4f) | SHORT_ROUTE | tour_graph 4/8; missing first 4; pins 1 | PIN_BELOW_HALF |
| Sri Lanka | [b353b96d](https://aa-tripplanner.vercel.app/tours/kalpitiya-beach-and-wilpattu-wildlife-tour-10-days-sri-lanka-b353b96d) | SHORT_ROUTE | tour_graph 2/10; missing first 6; last 2; pins 1 | PIN_BELOW_HALF |
| Sri Lanka | [6cdd718e](https://aa-tripplanner.vercel.app/tours/knuckles-to-ella-trekking-tour-sri-lanka-6-days-sri-lanka-6cdd718e) | SHORT_ROUTE | tour_graph 3/6; missing first 3; pins 1 | PIN_BELOW_HALF |
| Sri Lanka | [24b88880](https://aa-tripplanner.vercel.app/tours/passikudah-beach-and-wilpattu-national-park-safari-10-days-sri-lanka-24b88880) | SHORT_ROUTE | tour_graph 7/10; missing last 3; pins 1 | PIN_BELOW_HALF |
| Sri Lanka | [f9d212e8](https://aa-tripplanner.vercel.app/tours/rustic-explorer-rural-lodges-wilpattu-and-kalpitiya-09-nights-sri-lanka-f9d212e8) | SHORT_ROUTE | tour_graph 6/10; missing first 4; pins 1 | PIN_BELOW_HALF |
| Sri Lanka | [82981be3](https://aa-tripplanner.vercel.app/tours/sinharaja-rain-forest-and-galle-fort-3-days-2-nights-sri-lanka-82981be3) | SHORT_ROUTE | tour_graph 1/3; missing first 2; pins 1 | PIN_BELOW_HALF |
| Sri Lanka | [35523b41](https://aa-tripplanner.vercel.app/tours/southern-sri-lanka-honeymoon-tour-tangalle-ahangama-and-galle-7-days-sri-lanka-35523b41) | SHORT_ROUTE | tour_graph 4/7; missing last 3; pins 1 | PIN_BELOW_HALF |
| Sri Lanka | [3ae3b34b](https://aa-tripplanner.vercel.app/tours/sri-lanka-beach-reefs-wilpattu-wildlife-8-days-sri-lanka-3ae3b34b) | SHORT_ROUTE | tour_graph 4/8; missing first 4; pins 3 | PIN_BELOW_HALF |
| Sri Lanka | [96576793](https://aa-tripplanner.vercel.app/tours/sri-lanka-colombo-nuwara-eliya-koslanda-and-kaleliya-7-days-6-nights-sri-lanka-96576793) | SHORT_ROUTE | tour_graph 3/7; missing last 4; pins 2 | PIN_BELOW_HALF |
| Sri Lanka | [8d800efd](https://aa-tripplanner.vercel.app/tours/sri-lanka-highlights-kalpitiya-wilpattu-jaffna-sigiriya-kandy-ella-and-galle-21-8d800efd) | SHORT_ROUTE | tour_graph 18/21; missing first 3; pins 8 | PIN_BELOW_HALF |
| Sri Lanka | [f558b8bc](https://aa-tripplanner.vercel.app/tours/sri-lanka-hill-country-yala-and-south-coast-10-days-sri-lanka-f558b8bc) | SHORT_ROUTE | tour_graph 8/10; missing last 2; pins 4 | PIN_BELOW_HALF |
| Sri Lanka | [ee8cc01f](https://aa-tripplanner.vercel.app/tours/sri-lanka-honeymoon-tour-14-days-13-nights-sri-lanka-ee8cc01f) | SHORT_ROUTE | tour_graph 9/14; missing first 1; last 4; pins 4 | PIN_BELOW_HALF |
| Sri Lanka | [d2cd9ed7](https://aa-tripplanner.vercel.app/tours/sri-lanka-honeymoon-tour-option-i-culture-tea-country-yala-and-thalpe-14-days-sr-d2cd9ed7) | SHORT_ROUTE | tour_graph 11/14; missing last 3; pins 5 | PIN_BELOW_HALF |
| Sri Lanka | [0913b37a](https://aa-tripplanner.vercel.app/tours/sri-lanka-honeymoon-tour-option-ii-14-days-13-nights-sri-lanka-0913b37a) | SHORT_ROUTE | tour_graph 7/14; missing first 6; last 1; pins 1 | PIN_BELOW_HALF |
| Sri Lanka | [0c7920bb](https://aa-tripplanner.vercel.app/tours/sri-lanka-honeymoon-tour-thalpe-yala-and-galle-7-days-sri-lanka-0c7920bb) | SHORT_ROUTE | tour_graph 3/7; missing first 3; last 1; pins 2 | PIN_BELOW_HALF |
| Sri Lanka | [301ff5bb](https://aa-tripplanner.vercel.app/tours/sri-lanka-leisure-tour-kotugoda-kalupahana-and-tangalle-12-days-sri-lanka-301ff5bb) | SHORT_ROUTE | tour_graph 9/12; missing first 2; last 1; pins 4 | PIN_BELOW_HALF |
| Sri Lanka | [fabba396](https://aa-tripplanner.vercel.app/tours/sri-lanka-luxury-holiday-option-i-14-days-sri-lanka-fabba396) | SHORT_ROUTE | tour_graph 11/14; missing first 1; last 2; pins 6 | PIN_BELOW_HALF |
| Sri Lanka | [b5e3e5c9](https://aa-tripplanner.vercel.app/tours/sri-lanka-luxury-holiday-option-ii-14-days-13-nights-sri-lanka-b5e3e5c9) | SHORT_ROUTE | tour_graph 11/14; missing first 1; last 2; pins 7 | — |
| Sri Lanka | [bbfd3cd1](https://aa-tripplanner.vercel.app/tours/sri-lanka-photography-tour-12-days-11-nights-sri-lanka-bbfd3cd1) | SHORT_ROUTE | tour_graph 10/12; missing last 2; pins 8 | — |
| Sri Lanka | [d63bb46e](https://aa-tripplanner.vercel.app/tours/sri-lanka-south-coast-and-yala-holiday-option-i-7-days-sri-lanka-d63bb46e) | SHORT_ROUTE | places 5/7; missing last 2; pins 4 | — |
| Taiwan | [175f7587](https://aa-tripplanner.vercel.app/tours/east-coast-cycling-tour-of-taiwan-8-days-taiwan-175f7587) | SHORT_ROUTE | tour_graph 1/8; missing last 7; pins 1 | PIN_BELOW_HALF |
| Taiwan | [74f84466](https://aa-tripplanner.vercel.app/tours/wheels-around-taipei-3-day-cycling-tour-taiwan-74f84466) | SHORT_ROUTE | tour_graph 1/3; missing first 2; pins 1 | PIN_BELOW_HALF |
| Thailand | [fdfa1b38](https://aa-tripplanner.vercel.app/tours/amphawa-to-ban-krut-cycling-tour-8-days-thailand-fdfa1b38) | SHORT_ROUTE | tour_graph 5/8; missing first 2; last 1; pins 2 | PIN_BELOW_HALF |
| Thailand | [cbfc127e](https://aa-tripplanner.vercel.app/tours/chiang-mai-to-chiang-rai-mountain-cycling-5-days-thailand-cbfc127e) | SHORT_ROUTE | tour_graph 2/5; missing first 3; pins 1 | PIN_BELOW_HALF |
| Thailand | [0d16c064](https://aa-tripplanner.vercel.app/tours/northern-thailand-and-laos-by-bike-chiang-mai-to-luang-prabang-10-days-thailand-0d16c064) | SHORT_ROUTE | tour_graph 8/10; missing last 2; pins 4 | PIN_BELOW_HALF |

### (c) Everything else: new findings (115)

DAYS_MISMATCH (14) first, then NO_ROUTE outside Pakistan/Philippines (101). The analysis is in "New findings" below.

| Country | Tour page | Class | Numbers | Extra flags |
|---|---|---|---|---|
| Bhutan | [97ccd551](https://aa-tripplanner.vercel.app/tours/jomolhari-trek-bhutan-bhutan-97ccd551) | DAYS_MISMATCH | tour_graph route 15; page day list 15 vs duration_days 14; route 15 days > duration_days 14; pins 11 | LONG_ROUTE |
| India | [81d4279c](https://aa-tripplanner.vercel.app/tours/bangalore-to-cochin-cycling-tour-15-days-india-81d4279c) | DAYS_MISMATCH | tour_graph route 13; page day list 14 vs duration_days 15; pins 10 | SHORT_ROUTE |
| India | [21f00fb2](https://aa-tripplanner.vercel.app/tours/north-india-s-imperial-triangle-delhi-agra-jaipur-then-udaipur-8-days-india-21f00fb2) | DAYS_MISMATCH | tour_graph route 9; page day list 9 vs duration_days 8; route 9 days > duration_days 8; pins 7 | LONG_ROUTE |
| Japan | [c90f78a6](https://aa-tripplanner.vercel.app/tours/trans-tohoku-bike-tour-nasu-to-aomori-japan-c90f78a6) | DAYS_MISMATCH | tour_graph route 4; page day list 4 vs duration_days 12; pins 3 | SHORT_ROUTE, PIN_BELOW_HALF |
| Laos | [0130f9a6](https://aa-tripplanner.vercel.app/tours/laos-central-vietnam-by-bike-luang-prabang-to-hoi-an-18-days-laos-0130f9a6) | DAYS_MISMATCH | tour_graph route 17; page day list 17 vs duration_days 18; pins 17 | SHORT_ROUTE |
| Nepal | [c476ddbf](https://aa-tripplanner.vercel.app/tours/annapurna-circuit-trek-14-days-nepal-c476ddbf) | DAYS_MISMATCH | tour_graph route 12; page day list 13 vs duration_days 14; pins 10 | SHORT_ROUTE |
| Nepal | [0a911b96](https://aa-tripplanner.vercel.app/tours/nepal-and-tibet-tour-20-days-nepal-0a911b96) | DAYS_MISMATCH | tour_graph route 19; page day list 19 vs duration_days 20; pins 13 | SHORT_ROUTE |
| Philippines | [41b138a1](https://aa-tripplanner.vercel.app/tours/luzon-s-heritage-laoag-vigan-and-bolinao-philippines-41b138a1) | DAYS_MISMATCH | none route 7; page day list 7 vs duration_days 3; fallback day list 7 vs duration_days 3 | NO_ROUTE |
| South Korea | [945ddd21](https://aa-tripplanner.vercel.app/tours/south-korea-palace-temple-island-13-days-south-korea-945ddd21) | DAYS_MISMATCH | tour_graph route 9; page day list 9 vs duration_days 13; pins 8 | SHORT_ROUTE |
| Sri Lanka | [3b3b4052](https://aa-tripplanner.vercel.app/tours/beach-and-wildlife-tour-of-sri-lanka-tangalle-mirissa-and-yala-sri-lanka-3b3b4052) | DAYS_MISMATCH | tour_graph route 7; page day list 8 vs duration_days 10; pins 2 | SHORT_ROUTE, PIN_BELOW_HALF |
| Sri Lanka | [1e5f891f](https://aa-tripplanner.vercel.app/tours/sri-lanka-and-maldives-by-rail-home-stay-and-island-guest-house-16-days-sri-lank-1e5f891f) | DAYS_MISMATCH | tour_graph route 11; page day list 13 vs duration_days 16; pins 7 | SHORT_ROUTE, PIN_BELOW_HALF |
| Sri Lanka | [31f1baac](https://aa-tripplanner.vercel.app/tours/sri-lanka-s-south-coast-yala-4-days-sri-lanka-31f1baac) | DAYS_MISMATCH | tour_graph route 2; page day list 3 vs duration_days 4; pins 2 | SHORT_ROUTE |
| Thailand | [4c41f401](https://aa-tripplanner.vercel.app/tours/thailand-by-water-rail-trail-9-days-thailand-4c41f401) | DAYS_MISMATCH | tour_graph route 9; page day list 10 vs duration_days 9; pins 5 | — |
| Vietnam | [ca1d7500](https://aa-tripplanner.vercel.app/tours/vietnam-the-ho-chi-minh-trail-by-bicycle-14-days-vietnam-ca1d7500) | DAYS_MISMATCH | tour_graph route 12; page day list 12 vs duration_days 14; pins 12 | SHORT_ROUTE |
| India | [489079d3](https://aa-tripplanner.vercel.app/tours/kilimanjaro-trek-via-the-machame-route-8-days-india-489079d3) | NO_ROUTE | none; day list 8/8 | — |
| India | [fbe37dd2](https://aa-tripplanner.vercel.app/tours/mount-kilimanjaro-trek-via-the-marangu-route-8-days-india-fbe37dd2) | NO_ROUTE | none; day list 8/8 | — |
| India | [278f88de](https://aa-tripplanner.vercel.app/tours/mountain-biking-workshop-shimla-and-kufri-3-days-india-278f88de) | NO_ROUTE | none; day list 3/3 | — |
| Japan | [1a353cb5](https://aa-tripplanner.vercel.app/tours/birdwatching-in-kin-town-okinawa-2-days-japan-1a353cb5) | NO_ROUTE | none; day list 2/2 | — |
| Japan | [635632c3](https://aa-tripplanner.vercel.app/tours/east-of-the-sumida-river-tokyo-kiyosumi-garden-and-fukagawa-half-day-japan-635632c3) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [b7188d60](https://aa-tripplanner.vercel.app/tours/edo-tokyo-culture-route-b-nihombashi-to-the-imperial-palace-half-day-japan-b7188d60) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [f4a313d0](https://aa-tripplanner.vercel.app/tours/higashi-agatsuma-cherry-blossoms-and-daffodils-half-day-japan-f4a313d0) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [d3e76297](https://aa-tripplanner.vercel.app/tours/higashi-agatsuma-highlights-1-day-japan-d3e76297) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [7cd67b6b](https://aa-tripplanner.vercel.app/tours/iriomote-mangrove-kayak-and-waterfall-trek-1-day-japan-7cd67b6b) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [c175f55e](https://aa-tripplanner.vercel.app/tours/iriomote-mangrove-kayak-and-waterfall-trek-1-day-japan-c175f55e) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [3bb94eae](https://aa-tripplanner.vercel.app/tours/iriomote-mangrove-river-stargazing-kayak-2-hours-japan-3bb94eae) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [d4963dd2](https://aa-tripplanner.vercel.app/tours/iriomote-mayagusuku-waterfall-trek-1-day-japan-d4963dd2) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [4b1d789d](https://aa-tripplanner.vercel.app/tours/iriomote-yutsun-3-steps-waterfall-trek-1-day-japan-4b1d789d) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [57fbb080](https://aa-tripplanner.vercel.app/tours/iwajuku-museum-to-ashio-copper-mine-day-trip-japan-57fbb080) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [a44bf9c4](https://aa-tripplanner.vercel.app/tours/jungle-river-trek-to-the-sea-japan-half-day-japan-a44bf9c4) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [1c84683b](https://aa-tripplanner.vercel.app/tours/kajikasou-people-s-inn-day-trip-japan-japan-1c84683b) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [56098381](https://aa-tripplanner.vercel.app/tours/kumano-kodo-pilgrimage-bike-and-hike-7-days-japan-56098381) | NO_ROUTE | none; day list 7/7 | — |
| Japan | [8650c2ca](https://aa-tripplanner.vercel.app/tours/marsh-plateau-circular-hike-japan-1-day-japan-8650c2ca) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [b5c3c908](https://aa-tripplanner.vercel.app/tours/masuya-meat-shop-ashio-nikko-day-trip-japan-b5c3c908) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [e864ec99](https://aa-tripplanner.vercel.app/tours/miyako-island-sea-colours-bridges-reef-and-beaches-3-days-japan-e864ec99) | NO_ROUTE | none; day list 3/3 | — |
| Japan | [0c608efd](https://aa-tripplanner.vercel.app/tours/mt-shibutsu-hiking-course-2-days-japan-0c608efd) | NO_ROUTE | none; day list 2/2 | — |
| Japan | [32160209](https://aa-tripplanner.vercel.app/tours/naha-city-by-bicycle-japan-32160209) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [7a3e71ce](https://aa-tripplanner.vercel.app/tours/nasu-highland-cycling-and-mt-nasu-hike-2-days-japan-7a3e71ce) | NO_ROUTE | none; day list 2/2 | — |
| Japan | [f807063c](https://aa-tripplanner.vercel.app/tours/nasu-to-shirakawa-e-bike-tour-5-days-japan-f807063c) | NO_ROUTE | none; day list 5/5 | — |
| Japan | [5a227f7e](https://aa-tripplanner.vercel.app/tours/nikko-e-bike-tour-5-days-japan-5a227f7e) | NO_ROUTE | none; day list 5/5 | — |
| Japan | [73dad072](https://aa-tripplanner.vercel.app/tours/nikko-to-midori-shrine-villa-park-mine-and-canyon-overnight-trip-japan-73dad072) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [645aa9ae](https://aa-tripplanner.vercel.app/tours/okinawa-canyoning-in-yanbaru-national-park-half-day-or-full-day-japan-645aa9ae) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [8b40853f](https://aa-tripplanner.vercel.app/tours/okinawa-island-hopping-nago-yagaji-beach-and-izena-island-3-days-japan-8b40853f) | NO_ROUTE | none; day list 3/3 | — |
| Japan | [a5eb7e29](https://aa-tripplanner.vercel.app/tours/okinawa-mangrove-and-ocean-kayak-private-tour-3-hours-japan-a5eb7e29) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [19b7e801](https://aa-tripplanner.vercel.app/tours/okinawa-mangrove-and-ocean-kayak-tour-private-2-hours-japan-19b7e801) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [043868cf](https://aa-tripplanner.vercel.app/tours/okinawa-mangroves-kayaking-in-gesashi-bay-japan-043868cf) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [bdde0ce8](https://aa-tripplanner.vercel.app/tours/okinawa-marine-activities-japan-bdde0ce8) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [6a50472e](https://aa-tripplanner.vercel.app/tours/okinawa-sup-and-snorkel-tour-full-or-half-day-japan-6a50472e) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [854d0e26](https://aa-tripplanner.vercel.app/tours/oze-katashina-sugenuma-and-nikko-activities-2-days-japan-854d0e26) | NO_ROUTE | none; day list 2/2 | — |
| Japan | [2020d00f](https://aa-tripplanner.vercel.app/tours/oze-katashina-to-nikko-waterfalls-marunuma-dam-and-senjogahara-walk-2-days-japan-2020d00f) | NO_ROUTE | none; day list 2/2 | — |
| Japan | [3eda85ad](https://aa-tripplanner.vercel.app/tours/private-bike-tour-in-tokyo-3-hours-japan-3eda85ad) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [ed920610](https://aa-tripplanner.vercel.app/tours/restored-brunat-engine-tomioka-silk-mill-japan-ed920610) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [bbc72094](https://aa-tripplanner.vercel.app/tours/sacred-sites-around-mt-iwabitsu-japan-1-day-japan-bbc72094) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [54b052bf](https://aa-tripplanner.vercel.app/tours/satoyama-and-craft-bike-tour-nasu-to-mashiko-7-days-japan-54b052bf) | NO_ROUTE | none; day list 7/7 | — |
| Japan | [03b17fb1](https://aa-tripplanner.vercel.app/tours/shima-onsen-by-rental-bicycle-2-days-1-night-japan-03b17fb1) | NO_ROUTE | none; day list 2/2 | — |
| Japan | [64f31e48](https://aa-tripplanner.vercel.app/tours/shirataki-shrine-and-houtokuji-temple-side-trip-kiryu-japan-64f31e48) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [b858703e](https://aa-tripplanner.vercel.app/tours/sumo-morning-practice-visit-and-cycling-in-tokyo-japan-b858703e) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [8f6d7604](https://aa-tripplanner.vercel.app/tours/sutra-tracing-in-nikko-1-day-japan-8f6d7604) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [a423e72e](https://aa-tripplanner.vercel.app/tours/the-tokyo-toilet-cycling-route-in-shibuya-half-day-japan-a423e72e) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [78831da8](https://aa-tripplanner.vercel.app/tours/time-travel-to-good-old-tokyo-guided-cycling-route-half-day-japan-78831da8) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [a7fb5257](https://aa-tripplanner.vercel.app/tours/tokyo-backstreets-asakusa-oshiage-by-bike-half-day-japan-a7fb5257) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [cfa16a4a](https://aa-tripplanner.vercel.app/tours/tokyo-bay-cycling-tour-half-day-japan-cfa16a4a) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [34e84f33](https://aa-tripplanner.vercel.app/tours/tokyo-central-bike-tour-3-hours-japan-34e84f33) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [5b7b47fa](https://aa-tripplanner.vercel.app/tours/tokyo-modern-architecture-tour-half-day-japan-5b7b47fa) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [b9b39260](https://aa-tripplanner.vercel.app/tours/tokyo-riverside-and-local-life-cycling-tour-half-day-japan-b9b39260) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [9e7643b8](https://aa-tripplanner.vercel.app/tours/tokyo-riverside-bike-tour-3-hours-japan-9e7643b8) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [269b6b09](https://aa-tripplanner.vercel.app/tours/tokyo-sumida-river-and-bayside-cycling-tour-half-day-japan-269b6b09) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [253c095c](https://aa-tripplanner.vercel.app/tours/tomioka-silk-mill-guided-visit-40-minutes-japan-253c095c) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [306c5f2f](https://aa-tripplanner.vercel.app/tours/yambaru-mangrove-kayaking-and-shikuwasa-park-1-day-japan-306c5f2f) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [ba4ad5c8](https://aa-tripplanner.vercel.app/tours/yanbaru-kayak-and-snorkel-private-tour-4-hours-japan-ba4ad5c8) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [28a7b883](https://aa-tripplanner.vercel.app/tours/yanbaru-mangrove-kayaking-night-walk-and-bird-watching-okinawa-japan-28a7b883) | NO_ROUTE | none; day list 2/2 | — |
| Japan | [d4d00218](https://aa-tripplanner.vercel.app/tours/yanbaru-national-park-hiking-okinawa-half-day-or-full-day-japan-d4d00218) | NO_ROUTE | none; day list 1/1 | — |
| Japan | [2b8dc3b1](https://aa-tripplanner.vercel.app/tours/yanbaru-national-park-river-trekking-okinawa-half-day-or-full-day-japan-2b8dc3b1) | NO_ROUTE | none; day list 1/1 | — |
| Nepal | [be1f2f6f](https://aa-tripplanner.vercel.app/tours/dakshinkali-temple-tour-1-day-nepal-be1f2f6f) | NO_ROUTE | none; day list 1/1 | — |
| Nepal | [43483a87](https://aa-tripplanner.vercel.app/tours/doleshwor-mahadev-temple-tour-1-day-nepal-43483a87) | NO_ROUTE | none; day list 1/1 | — |
| Nepal | [57f90d43](https://aa-tripplanner.vercel.app/tours/kathmandu-valley-cycling-tour-1-day-nepal-57f90d43) | NO_ROUTE | none; day list 1/1 | — |
| Nepal | [bf0cfb01](https://aa-tripplanner.vercel.app/tours/pikey-peak-trek-solu-khumbu-7-days-nepal-bf0cfb01) | NO_ROUTE | none; day list 7/7 | — |
| Nepal | [c99a1434](https://aa-tripplanner.vercel.app/tours/trishuli-river-rafting-3-days-nepal-c99a1434) | NO_ROUTE | none; day list 3/3 | — |
| South Korea | [3c406e5c](https://aa-tripplanner.vercel.app/tours/mokpo-to-yeosu-cycling-along-the-yeongsan-and-seomjin-rivers-6-days-south-korea-3c406e5c) | NO_ROUTE | none; day list 6/6 | — |
| South Korea | [90b88118](https://aa-tripplanner.vercel.app/tours/sunset-road-cycling-tour-seoul-to-busan-14-days-south-korea-90b88118) | NO_ROUTE | none; day list 14/14 | — |
| Sri Lanka | [375fbc8a](https://aa-tripplanner.vercel.app/tours/ahangama-cycling-tour-1-day-sri-lanka-375fbc8a) | NO_ROUTE | none; day list 1/1 | — |
| Sri Lanka | [1305e815](https://aa-tripplanner.vercel.app/tours/hikkaduwa-cycling-tour-1-day-sri-lanka-1305e815) | NO_ROUTE | none; day list 1/1 | — |
| Sri Lanka | [1e956eb0](https://aa-tripplanner.vercel.app/tours/hiyare-cycling-tour-galle-1-day-sri-lanka-1e956eb0) | NO_ROUTE | none; day list 1/1 | — |
| Sri Lanka | [87f57c16](https://aa-tripplanner.vercel.app/tours/kanneliya-rain-forest-cycling-tour-1-day-sri-lanka-87f57c16) | NO_ROUTE | none; day list 1/1 | — |
| Sri Lanka | [ec969e59](https://aa-tripplanner.vercel.app/tours/mirissa-cycling-tour-1-day-sri-lanka-ec969e59) | NO_ROUTE | none; day list 1/1 | — |
| Taiwan | [1c732b6f](https://aa-tripplanner.vercel.app/tours/alangyi-historic-trail-and-tjuvecekadan-village-2-days-taiwan-1c732b6f) | NO_ROUTE | none; day list 2/2 | — |
| Taiwan | [d8e5bda3](https://aa-tripplanner.vercel.app/tours/alishan-indigenous-culture-and-tea-tour-3-days-2-nights-taiwan-d8e5bda3) | NO_ROUTE | none; day list 3/3 | — |
| Taiwan | [ac1d5f9b](https://aa-tripplanner.vercel.app/tours/birds-of-central-taiwan-3-days-taiwan-ac1d5f9b) | NO_ROUTE | none; day list 3/3 | — |
| Taiwan | [b9f5f3af](https://aa-tripplanner.vercel.app/tours/coast-valley-cycling-tour-9-days-taipei-to-kenting-taiwan-b9f5f3af) | NO_ROUTE | none; day list 9/9 | — |
| Taiwan | [bde4c7a3](https://aa-tripplanner.vercel.app/tours/dabajianshan-hike-shei-pa-national-park-taiwan-3-days-2-nights-taiwan-bde4c7a3) | NO_ROUTE | none; day list 3/3 | — |
| Taiwan | [bb81b0c6](https://aa-tripplanner.vercel.app/tours/dabajianshan-trek-3-days-taiwan-bb81b0c6) | NO_ROUTE | none; day list 3/3 | — |
| Taiwan | [292b3ef2](https://aa-tripplanner.vercel.app/tours/dongyanshan-national-forest-guided-day-tour-1-day-taiwan-292b3ef2) | NO_ROUTE | none; day list 1/1 | — |
| Taiwan | [44e767ac](https://aa-tripplanner.vercel.app/tours/guanwu-national-forest-guided-day-tour-from-taipei-1-day-taiwan-44e767ac) | NO_ROUTE | none; day list 1/1 | — |
| Taiwan | [766361cd](https://aa-tripplanner.vercel.app/tours/hehuanshan-5-peaks-2-days-taiwan-766361cd) | NO_ROUTE | none; day list 2/2 | — |
| Taiwan | [0a5b343f](https://aa-tripplanner.vercel.app/tours/hehuanshan-north-peak-guided-day-tour-1-day-taiwan-0a5b343f) | NO_ROUTE | none; day list 1/1 | — |
| Taiwan | [adacd017](https://aa-tripplanner.vercel.app/tours/jiaming-lake-trek-4-days-taiwan-adacd017) | NO_ROUTE | none; day list 4/4 | — |
| Taiwan | [142074e2](https://aa-tripplanner.vercel.app/tours/mian-yue-line-guided-hike-from-chiayi-1-day-taiwan-142074e2) | NO_ROUTE | none; day list 1/1 | — |
| Taiwan | [f5a5aac8](https://aa-tripplanner.vercel.app/tours/mt-nanhuda-trek-5-days-taiwan-f5a5aac8) | NO_ROUTE | none; day list 5/5 | — |
| Taiwan | [56313361](https://aa-tripplanner.vercel.app/tours/snow-mountain-trek-shei-pa-national-park-3-days-taiwan-56313361) | NO_ROUTE | none; day list 3/3 | — |
| Taiwan | [cb334274](https://aa-tripplanner.vercel.app/tours/syakaro-historic-trail-hsinchu-1-day-guided-hike-taiwan-cb334274) | NO_ROUTE | none; day list 1/1 | — |
| Taiwan | [2218c3e3](https://aa-tripplanner.vercel.app/tours/taipei-night-safari-guided-night-wildlife-walk-1-day-taiwan-2218c3e3) | NO_ROUTE | none; day list 1/1 | — |
| Taiwan | [cea98ee8](https://aa-tripplanner.vercel.app/tours/taiwan-s-mountain-spine-555km-cycling-from-taipei-to-kenting-taiwan-cea98ee8) | NO_ROUTE | none; day list 8/8 | — |
| Taiwan | [f0eb0c29](https://aa-tripplanner.vercel.app/tours/taiwan-s-southern-coastline-east-rift-valley-8-days-by-bike-taiwan-f0eb0c29) | NO_ROUTE | none; day list 8/8 | — |
| Taiwan | [19879aac](https://aa-tripplanner.vercel.app/tours/taiwan-s-southern-rim-indigenous-trails-hot-springs-coastal-wilderness-5-days-ta-19879aac) | NO_ROUTE | none; day list 5/5 | — |
| Taiwan | [797070fa](https://aa-tripplanner.vercel.app/tours/tjuvecekadan-and-jinshuiying-national-trail-2-days-taiwan-797070fa) | NO_ROUTE | none; day list 2/2 | — |
| Taiwan | [71464667](https://aa-tripplanner.vercel.app/tours/tonghou-traversing-trail-day-hike-taiwan-1-day-taiwan-71464667) | NO_ROUTE | none; day list 1/1 | — |
| Taiwan | [8e5fa7f5](https://aa-tripplanner.vercel.app/tours/walami-trail-trek-yushan-national-park-2-days-taiwan-8e5fa7f5) | NO_ROUTE | none; day list 2/2 | — |
| Thailand | [ed647352](https://aa-tripplanner.vercel.app/tours/cha-am-bike-tour-with-wildlife-friends-foundation-thailand-1-day-thailand-ed647352) | NO_ROUTE | none; day list 1/1 | — |
| Thailand | [7d229e89](https://aa-tripplanner.vercel.app/tours/chiang-mai-private-bike-tour-half-day-thailand-7d229e89) | NO_ROUTE | none; day list 1/1 | — |
| Thailand | [8c0ccb8f](https://aa-tripplanner.vercel.app/tours/high-mountain-trek-mae-taeng-highlands-1-day-thailand-8c0ccb8f) | NO_ROUTE | none; day list 1/1 | — |
| Thailand | [56e78342](https://aa-tripplanner.vercel.app/tours/mae-taeng-and-chiang-dao-mountain-biking-3-days-thailand-56e78342) | NO_ROUTE | none; day list 3/3 | — |
| Thailand | [c6b24380](https://aa-tripplanner.vercel.app/tours/mae-taeng-highlands-jungle-trek-3-days-thailand-c6b24380) | NO_ROUTE | none; day list 3/3 | — |
| Thailand | [229f2c60](https://aa-tripplanner.vercel.app/tours/mae-taeng-highlands-trek-and-waterfalls-3-days-thailand-229f2c60) | NO_ROUTE | none; day list 3/3 | — |
| Thailand | [f40602e6](https://aa-tripplanner.vercel.app/tours/northern-thailand-chiang-mai-mae-hong-son-pai-4-days-thailand-f40602e6) | NO_ROUTE | none; day list 4/4 | — |
| Thailand | [a936d5bd](https://aa-tripplanner.vercel.app/tours/northern-thailand-hilltribes-trek-5-days-thailand-a936d5bd) | NO_ROUTE | none; day list 5/5 | — |
| Thailand | [2d9ccb23](https://aa-tripplanner.vercel.app/tours/northern-thailand-hmong-hilltribe-soft-adventure-3-days-thailand-2d9ccb23) | NO_ROUTE | none; day list 3/3 | — |

## New findings (bucket c) in short

**N1. 101 tours outside Pakistan/Philippines have no planner route** (`match: none`). The day list is complete on all of them.
By country: Japan 55 of 79 (70%), Taiwan 22 of 36 (61%), Thailand 9, Sri Lanka 5, Nepal 5, India 3, South Korea 2.
60 of the 101 are 1-day products (half-day city bike tours, kayak or hike outings, 2–4-hour activities). 41 are multi-day:
Taiwan 15, Japan 13, Thailand 6, India 3, Nepal 2 and South Korea 2. Examples are `90b88118` Seoul to Busan 14 days,
`b9f5f3af` / `cea98ee8` / `f0eb0c29` Taiwan 8–9-day cycling tours, and `56098381` Kumano Kodo 7 days.
Japan and Taiwan also have very few planner components (`resource=countries`: Japan 84, Taiwan 23, against Laos 468 or
Nepal 708). That points to places that did not resolve in those two countries (same mechanism as F2 class B,
but whole tours). **Not verified**: it needs the F2 Q8 per-day query (`geo.tour_day` / `geo.place_name`
status) on these tours. It may also be partly by design for single-spot activities.

**N2. Two Kilimanjaro treks are catalogued under India**: `489079d3` (Machame route, 8 days) and `fbe37dd2` (Marangu
route, 8 days). Tanzania is not an AA country, so the place guard rejects their places, and they have no route. This is
CIS catalogue data (wrong `country`, or a product that should not be in the catalogue). Also `278f88de` (Shimla
mountain-biking workshop, 3 days, India) has no route.

**N3. 14 tours where the page day list differs from `duration_days`** (CIS content or metadata, the same kind as the
Vietnam note in the sample):
- Fewer day blocks than `duration_days` (10): Japan `c90f78a6` **4/12**, South Korea `945ddd21` **9/13**,
  Sri Lanka `1e5f891f` 13/16, `3b3b4052` 8/10, `31f1baac` 3/4, Vietnam `ca1d7500` 12/14 (known), India `81d4279c` 14/15,
  Laos `0130f9a6` 17/18, Nepal `c476ddbf` 13/14, `0a911b96` 19/20.
- More day blocks than `duration_days` (4): Philippines `41b138a1` **7/3**, Bhutan `97ccd551` 15/14, India `21f00fb2` 9/8,
  Thailand `4c41f401` 10/9. On `97ccd551` and `21f00fb2` the route follows the page and is longer than `duration_days`.
- On 6 of the 14 the route is also shorter than the **page** day list, by the F2 edge gap: `81d4279c` 13/14,
  `c476ddbf` 12/13, `3b3b4052` 7/8, `1e5f891f` 11/13, `31f1baac` 2/3, `4c41f401` 9/10.
  These are new because the page days and the catalogue disagree, which the sample saw only on Vietnam.

**N4. 42 tours count as OK but pin fewer than half their days.** The route covers every day, but most days carry a stop
without a component. These are not in the non-OK lists. They would be affected by the "share rule for `tour_graph`"
part of the F2 fix (fall back to `places` or to the day list). The flag is `PIN_BELOW_HALF` in `catalogue-sweep.json`.

## What this means for the fixes

| Fix | Tours it closes |
|---|---|
| F3 CIS guard (PK/PH) + re-geocode | 61 NO_ROUTE (all of Pakistan and Philippines) |
| F2 TripPlanner span 1..N | 245 b1 completely; 49 b2 get full length, but with unpinned edge days |
| F2 data (resolve class B places) | the pinned share of the 49 b2 tours, and probably most of the 101 N1 tours (needs Q8) |
| CIS content/metadata | 14 N3 day-count mismatches, 2 N2 Kilimanjaro tours |
| F1 static map | already live (#158), 0 tours left |

## Not done

- No DB read: the per-day cause of the b2 stretches and N1 (unresolved vs unknown places) is inferred, not checked.
- No browser: the maps are not rendered and Mapbox was not called. F1 is checked only from the URL form in the HTML.
- `/plan`, apply-route, narrate and search were not called (writes and LLM calls).
