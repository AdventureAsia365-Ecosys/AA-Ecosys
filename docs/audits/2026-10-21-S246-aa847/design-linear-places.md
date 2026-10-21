# AA-847 — drawing linear places as lines (design, S246)

Agent: Claude Code (design only, nothing applied). Owner decision S246 (Nghiệp, 21/10/2026): linear places (rivers,
roads, trekking stretches) are **drawn correctly** on the TripPlanner map — not hidden, not a circle. This replaces the
"hidden" proposal on the validity branch (`LINEAR_FEATURES_HIDDEN`, `Located.hidden`), which is not deployed yet.

Read with: ADR 0007 (+ S246 amendment), CIS `docs/implementation-notes/AA-847.md` (validity branch), TripPlanner 6c
notes, `db-schema-reference.md` (verified 2026-10-20, CIS 251). Names below were checked there.

## 1. What is linear today

- **Flag:** `services/places/geomatch.feature_kind(name, result_type)` (validity branch) returns `linear` when the
  name has a word of `LINEAR_FEATURE_WORDS` (trail, river, road, highway, range, loop, railway, railroad, canal,
  route), or Geoapify `result_type='street'` + a street word; a word of `POINT_ON_FEATURE_WORDS` (bridge, falls,
  museum, village, …) keeps it a point ("River Kwai Bridge").
- **Effect on that branch:** `Located.hidden` → `shared.destinations.geo_status='suspect'`,
  `review_reason='linear_feature'`, `geo_precision='area'`; every catalog view drops it; flip gate reason
  `linear_feature`. Nothing stores a shape: the only geometry anywhere is `lat`/`lng` (+ `geocoder_place_id`,
  `geocoder_meta`).
- **No PostGIS** on the shared RDS (extensions: `pg_stat_statements`, `plpgsql`, `vector` 0.8.1).
- **How many** (offline count, `feature_kind` of the validity branch over the S234 atom dump of the 892 published
  tours, `.tmp-session/s234/aa772_probe.json`, 24,302 atoms, 11,877 distinct (place, country)):

  | | keys (name, country) | tours touched |
  |---|---|---|
  | linear, proper name ("Nam Ou River", "Karakoram Highway") | **317** | 285 |
  | linear, descriptive ("the river", "sandbank on Nam Ou River", "rocky section of trail") | 114 | — |
  | words the list misses, proper name (stream, creek, waterway, expressway, path, circuit) | ~25 | — |
  | area (national park, delta, gorge …) — not in scope here | 241 | — |

  By word (proper): river 197, trail 39, road 31, railway 12, route 11, highway 10, canal 9, range 9. By country:
  Thailand 39, India 39, Nepal 36, China 32, South Korea 29, Taiwan 29, Laos 29, Philippines 25, Japan 23, Sri Lanka
  14, Pakistan 11, Bhutan 9, Vietnam 2. **Planning number: ~340 linear destinations catalog-wide.** Dev today has only
  ~27 built tours; the exact Dev count is one read-only probe line (§9).

## 2. Classification changes (deterministic, no model)

| Change | Why |
|---|---|
| Add `stream`, `creek`, `waterway`, `expressway`, `path`, `circuit` to `LINEAR_FEATURE_WORDS` | ~25 proper names missed ("Cheonggyecheon Stream", "Yamuna Expressway", "Barkhor circuit"). Not `kora` ("Chorten Kora" is a temple), not `cruise` (an activity: "Yangtze Cruise" → §2 row 4). |
| `range` → area kind | A mountain range is not a line a traveller follows; OSM holds it as a node or polygon. Drawn with the area rule. |
| Descriptive phrase with a named feature inside ("sandbank on the Nam Ou River", "main road south from Luang Prabang toward Kuang Si", "Yangtze deluxe cruise") | Regex `(on|along|of|by|down|up)? (the)? <Proper words> (River|Road|Trail|Canal|Highway|…)` extracts the feature name; the component links to **that** feature's destination (a line). Keeps one destination per river. |
| Descriptive phrase with no proper noun ("the river", "the trail", "river valleys") | Already `is_generic_phrase` → not geocoded, the day's town point (ADR 0007 §9). Not a place, so no line; the text stays in the day. Unchanged. |
| Kind stored, not recomputed in readers | New `shared.destinations.geo_precision` value **`line`** (CHECK widened). TripPlanner reads `precision='line'`. |

## 3. Where the geometry comes from

Both sources are OpenStreetMap data, the attribution TripPlanner already shows (ADR 0007 §9) covers them.

1. **Geoapify Place Details** `GET /v2/place-details?id=<geocoder_place_id>&features=details` — the `details`
   feature's geometry is the place's own geometry (LineString / MultiLineString for a way / relation), 1 credit;
   `details.full_geometry` returns the original (unsimplified) geometry, +1 credit, asked only when `details` comes
   back as a Point or is cut. Used when `geocode` accepted a candidate (we hold its `place_id`).
2. **Overpass API** (public instance, fair use ≈ 10,000 requests / 1 GB a day; an offline job, never a request path)
   by name + OSM tag near the model / geocoder point, inside the country bbox (`guards.BBOX`):
   `waterway~"^(river|stream|canal)$"`, `highway`, `railway`, `route~"^(hiking|foot|road|bicycle|railway)$"`
   relations; name match = `geomatch.name_sim` = 1.0 (or ≥ 0.5 with ≥ 2 distinctive tokens), ways of the same
   name merged. Used when (1) has no place id or returns no line. $0.
3. **Manual** (`/admin/places`, admin pastes a GeoJSON LineString) — exception path for a feature OSM lacks.

Acceptance (pure function, `services/places/shape.py`, unit-tested on recorded responses): geometry type line,
≥ 2 vertices, inside (or crossing) the country bbox, ≤ 25 km from the model point (50 km for river / highway /
railway), length ≥ 1 km. Otherwise `not_found` (listed on `/admin/places`).

## 4. Storage (owner CIS, migration **255**, or the next free number at merge — the probe's 255+ follow-ups may take it)

New table **`geo.place_shape`** (internal like every `geo` table, granted to `cis_app` DML + `catalog_owner` SELECT):

| Column | Type | Note |
|---|---|---|
| `destination_id` | uuid PK → `shared.destinations(id)` | one shape per destination |
| `kind` | text CHECK `line` / `area` | `area` reserved for real polygons later (same table) |
| `status` | text CHECK `pending` / `ok` / `not_found` / `failed` / `manual` | job queue state (`pending` index) |
| `geom` | jsonb | GeoJSON (Multi)LineString, **clipped to the destination's country bbox**, Douglas–Peucker to ≤ 2,000 vertices, 5 decimals |
| `geom_mid` | jsonb | ≤ 300 vertices (map at zoom ≥ 7, trip panel) |
| `geom_lo` | jsonb | ≤ 60 vertices (zoom < 7, static maps) |
| `min_lat`, `min_lng`, `max_lat`, `max_lng` | double precision | bbox for tile intersection (no PostGIS) |
| `length_km` | numeric(8,1) | of the clipped line |
| `source` | text CHECK `geoapify_details` / `overpass` / `manual` | |
| `osm_type`, `osm_id` | text, bigint | identity of the feature (also a **same-place signal for the automatic duplicate merge**: two destinations on one `osm_id` are one place — input to problem 2) |
| `tries`, `next_retry_at`, `last_error`, `fetched_at`, `meta` jsonb | | as `geo.place_name` |

Per tour-day **stretch** on `geo.tour_place` (appended, nullable): `segment` jsonb (≤ 300 vertices), `segment_basis`
text (`day_anchors` / `feature`), `segment_from_destination_id`, `segment_to_destination_id` uuid. The same table
also gets `geo.geocode_call.endpoint text NOT NULL DEFAULT 'search'` so the Geoapify daily credit guard counts
details calls in the same 3,000/day pool. `shared.destinations` changes only its CHECK (`geo_precision` += `line`).

Why a `geo` table and not columns on `shared.destinations`: the golden record stays narrow (TripPlanner still holds
a direct SELECT grant on it), shapes are rebuildable derived data like the rest of `geo`, and one table serves lines
now and polygons later. Why no PostGIS: one more extension in the shared database (upgrade path, dump, every app),
for ~340 rows; clip / simplify / substring are ~150 lines of pure Python (no new dependency; shapely is not in CIS).

## 5. Pipeline (CIS)

- **`place_geocode`** stores a linear name as `geo_status='ok'`, `geo_precision='line'`, `review_reason` NULL, and
  inserts `geo.place_shape(status='pending')`. The `hidden` path goes (validity branch, before merge).
- **New job kind `place_shape`** (platform, debounced, `background=True`, cap 1; enqueued by `place_geocode` when it
  created a pending shape, and by `POST /admin/places/shapes/backfill` — dry run first, prints names + credits):
  fetch §3 → accept → clip / simplify (three levels) → write `geo.place_shape` → **snap** the destination's
  `lat`/`lng` to the point of the line nearest the old point (the label / tile anchor sits on the line) → enqueue
  one debounced `tour_graph_build`. Single writer of `geo.place_shape` (+ the admin manual action). Budget row
  `job:place_shape` in `shared.spend_budget`; Geoapify ≤ 5 req/s and the shared daily guard; Overpass ≤ 1 req / 2 s,
  backoff on 429 / 504.
- **`tour_graph_build`** is the single writer of `geo.tour_place.segment*` (pure Python, no call): for each
  component on a `line` destination, anchors = previous day's overnight destination and this day's overnight
  destination (`geo.tour_day.overnight_destination_id`), plus the day's other component points; project them onto
  the line; when two anchors project ≤ 15 km from the line and ≥ 2 km apart along it → `segment` = the substring
  between them, `basis='day_anchors'` (Huay Xai → Pak Beng on the Mekong, not 4,900 km of Mekong). Otherwise
  `segment` = NULL, `basis='feature'` (the reader draws the country-clipped feature). Recomputed on every build, so
  re-extracts and merges keep it right. `component_id` (uuid5, no geometry) does not change → no id-map impact.
- **Graph:** a `line` destination is not a graph node / stop (`tour_stop` source `component` skips it; nodes are
  towns). Routes and the AA-674 planner are unchanged.
- **Validity / flip gate:** `linear_feature` stops being a gate reason; new gate reason **`linear_without_shape`**
  (a live component on a `line` destination whose shape is not `ok` / `manual`). The flip waits for it to be 0 on
  every country, like `near_duplicate`.

## 6. Read model (catalog views, appended columns only — 253 rule)

- `catalog.v_destination` += `shape_kind`, `shape_status`, `shape_mid` (jsonb), `shape_lo` (jsonb), `min_lat`,
  `min_lng`, `max_lat`, `max_lng`, `length_km`, `shape_source` (LEFT JOIN `geo.place_shape`; point rows: NULL shape,
  bbox = the point). The ≤ 2,000-vertex `geom` is **not** exposed (CIS-internal for substrings).
- `catalog.v_tour_place` and `catalog.v_tour_component` += `segment` (jsonb: the stretch, else NULL),
  `segment_basis`, `precision` (component view only). Careful: `v_tour_component` ends with the optional
  `embedding` column (`%s` in 253) — the new columns go after it in both branches of the format.
- Size limits (asserted by the migration's closing check and a unit test of the simplifier): `shape_mid` ≤ 300
  vertices and ≤ 12 KB, `shape_lo` ≤ 60 vertices, `segment` ≤ 300 vertices. Worst tile (5° cell, ~10 lines × lo)
  ≈ 15 KB extra, CDN-cached 30 min.
- Contracts: `catalog.tour.v1.2` / `catalog.graph.v1.2` (additive), Infra byte copy + contract pins as for 253.
- No change to `v_component_embedding` (search ranks components; the line comes with the destination row).

## 7. TripPlanner rendering (slice 6d, after the CIS migration is applied)

- **Browse map (`MapView.tsx`):** tiles select destinations whose **bbox** intersects the cell (point rows behave
  as today); `geo_fields` adds `shape` (`shape_lo` for tile sizes ≥ 5°, else `shape_mid`), `shape_kind`,
  `length_km`. A `line` destination is **not** put in the clustered point source; it goes to a new unclustered
  source `destination-lines`, deduped by id across tiles. Layers: white casing + line; colour by feature
  (water: river / stream / canal = `#3B82C4`; trail / path / circuit = ink `#1F2933` dashed `[2,1.5]`; road /
  highway / railway / route = ink solid), width by zoom (2 → 5 px); `symbol-placement: line` label with the name
  and halo; a transparent 14 px hit layer for click / hover → the same `DestinationPopup` as a pin (components,
  photos), popup anchored at the click point. Attribution unchanged (OSM line ⇒ show "© OpenStreetMap
  contributors"; "Powered by Geoapify" when `shape_source='geoapify_details'`).
- **Trip / itinerary on the map:** the assembly day row carries `segment` (else the destination `shape_mid`) and
  `precision='line'`. The day's line is drawn gold (`#B87A1A`, 5 px, white casing) in a `trip-feature-line`
  source; the numbered day marker sits at the stretch's **entry end** (the end nearer the previous stop); the trip
  path joins previous stop → entry end and exit end → next stop (Directions / flight logic as today, so a river
  day adds at most one Directions request). Clicking the row fits the map to the stretch bbox, not a fly-to point.
- **Itinerary list (`TripPanel.tsx`):** a line glyph instead of the pin dot; subtitle "Along the Mekong River ·
  Huay Xai → Pak Beng · ≈ 150 km" (`segment_from/to` names, length of the stretch) or "Mekong River · ≈ 1,800 km in
  Laos" when only the feature is known.
- **Search:** keyword and vector results return the destination row with its shape; the result list shows the
  line glyph + kind + length; the result map draws the line (not a pin) and fits all results' bboxes.
- **Static maps (`StaticMap.tsx`, tour and destination pages):** a `path-4+3b82c4-0.9(<polyline5 of shape_lo>)`
  overlay per line (gold for the tour's stretches), at most 3 lines, numbered pin at the entry end; URL kept
  < 8,192 chars by the 60-vertex cap. Destination page top places: line glyph.
- Types: `GeoPrecision` += `"line"`; `DestinationPin` / `ItineraryDay` += `shape?`, `shape_kind?`, `length_km?`.

## 8. Missing geometry (until the shape is fetched)

- New tour: geocode and `place_shape` run in the same debounced chain, so the gap is minutes; the flip gate holds
  the cut-over until `linear_without_shape = 0` for the backfill.
- While `shape_status` is `pending` / `failed` / `not_found`: TripPlanner draws a **provisional dashed line** between
  the day's anchors (previous overnight → this overnight; the trip leg geometry already computed for that day),
  labelled with the feature name and "approximate route", the same line glyph in the list. No circle, no pin, never
  hidden. With no anchors at all (a one-day mention without overnights) the name stays in the list only, flagged
  on `/admin/places` (`linear_without_shape`).
- `not_found` after 3 tries → `/admin/places` "Lines" tab: name, country, tours, tried sources, actions "retry with
  another name" (alias) or "paste GeoJSON" (manual). Exception path, counted in the gate.

## 9. Read-only checks for the probe (orchestrator, `run-script`, no write)

```sql
-- Dev count of linear candidates now (names; feature_kind runs offline on the output)
SELECT d.name, d.country, d.located_by, d.geo_status, d.review_reason, (d.geocoder_place_id IS NOT NULL) AS has_place_id
  FROM shared.destinations d
 WHERE d.duplicate_of IS NULL
   AND d.name ~* '\m(trail|river|road|highway|range|loop|railway|railroad|canal|route|stream|creek|waterway|expressway|path|circuit)\M';
```

## 10. Cost (design; no call made)

| Item | Calls | USD |
|---|---|---|
| Geoapify Place Details backfill, ~340 lines × (1 `details` + ≤ 1 `full_geometry`) + ≤ 1 re-search where no `place_id` | ≤ 1,020 credits, one day under the 2,500/day guard (not on a paid place-run day) | **$0** (Free plan 3,000 credits/day) |
| Overpass fallback (lines Geoapify cannot give) | ≤ 340 queries | $0 |
| LLM | 0 (classification, name extraction, stretches are deterministic) | $0 |
| Steady state | ~0.4 linear place per new tour × ≤ 3 credits | $0 |
| Storage | ~340 × 5–50 KB jsonb ≈ 2–17 MB on RDS | ≈ $0 |
| Mapbox | no new API; ≤ +1 Directions request per linear trip day (free tier 100k/month) | $0 |
| Paid fallback if the Geoapify Free plan changes | Geoapify API 10, one month | $59 |

## 11. Slices

1. **CIS (validity branch, before it merges):** drop `LINEAR_FEATURES_HIDDEN` / `Located.hidden`; `precision='line'`;
   word list (§2); descriptive-name extraction; gate reason `linear_without_shape`. Unit tests on the pair set +
   the 25 extra names.
2. **CIS 255 (new branch):** `geo.place_shape`, `geo.tour_place.segment*`, `geocode_call.endpoint`, CHECK widen,
   view columns, closing size checks; Infra byte copy; contract pins v1.2.
3. **CIS job `place_shape` + `shape.py`** (clip / simplify / substring / accept, recorded Geoapify + Overpass
   fixtures, no network in tests), graph build stretches, `/admin/places` Lines tab, backfill dry run.
4. **Trial:** 3 rivers (Mekong / Nam Ou in Laos, Li River in China) + 1 trail + 1 road: Free-plan credits only, then
   the Laos + Vietnam backfill, then the rest by country (≤ 50 names per batch, as ADR 0007 §8).
5. **TripPlanner 6d:** tiles bbox, line layers, trip stretches, list / search / static maps, types. Screenshots of
   the HCM Trail tour (Vietnam / Laos), a Mekong slow-boat tour and the Kuang Si tour after the flip.
