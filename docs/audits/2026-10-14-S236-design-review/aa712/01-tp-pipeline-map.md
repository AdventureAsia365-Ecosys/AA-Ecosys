# 01 — TripPlanner place pipeline map (AA-712 input, S236, read-only)

Source: `apps/AA-TripPlanner-Web` @ 6523816 (main). Row counts = `pg_class.reltuples` from
`docs/architecture/db-schema-reference.md` (verified 2026-10-14, S235; approximate).
Note: TP migrations exist only for **001–009** (no 010). Place-relevant: 001, 002, 003, 004, 005.

## 0. Status / ownership context
- ADR 0002 (Accepted 01/10, S207): only CIS writes content (places, tour itinerary places, tour graph).
  The TP writers below are **frozen** until AA-712 moves the place pipeline into CIS job kinds
  (run after A3 atomize per wave; Mapbox key moves to CIS secrets; TP reads through views).
- CIS migration 201 removed `tripplanner` role write on `shared.destinations` (AA-731 notes): `components`
  and `tour_days` still call `locate.upsert` for new places -> would fail for new names today.
- CIS 216 grants `tripplanner` column read on `acp_contract.v_active_tour_atoms`.
- Catalog reads (`published_tours`, `raw_tours`, the atom view) need tenant RLS: `tour_days.fetch_catalog`
  does `SET LOCAL app.tenant_id = MASTER_CONTENT_TENANT_ID` in a transaction.

## 1. Tables (place pipeline) and rows

| Table | Mig | Key / notable cols | ~rows | Writer(s) |
|---|---|---|---|---|
| `shared.destinations` | 002, 005 | id uuid, name, country, lat, lng, cover_image_url, located_by ('mapbox'/'llm'), located_at; UNIQUE lower(name) | 1,178 | geocode.py, locate.py (upsert), regeocode_outliers.py, backfill_country.py, run_deterministic.py |
| `tripplanner.itinerary_components` | 001 | id, source_tour_id text, source_day_index, destination_id FK, name, activity (8 enum), intensity_level (4), season_months int[], duration_hint (4), text_extract, embedding vector(1536) HNSW cosine | 3,972 | components.py (op components), run.py (legacy LLM), run_deterministic.py (legacy), backfill_embeddings.py (UPDATE embedding) |
| `tripplanner.tour_day` | 003 | PK (source_tour_id, day_index); title, start/end/overnight_place, overnight_destination_id FK, places text[], extracted_by (rule/llm/rule+llm), source_hash (sha256 aa_itineraries), extracted_at | 650 | tour_days.py (op tour_days, relink, prune) |
| `tripplanner.tour_stop` | 004 | PK (tour, day); destination_id, country, source (overnight/component) | 622 | tour_graph.py |
| `tripplanner.tour_graph_node` | 004 | destination_id PK, name/country/lat/lng, tour_ids[], stop_count, activities[], intensity_min/max, season_months[] | 299 | tour_graph.py |
| `tripplanner.tour_graph_edge` | 004 | PK (from,to); tour_count, tour_ids[], km | 379 | tour_graph.py |
| `tripplanner.tour_leg` | 004 | PK (tour, day_from, day_to); days, start/end_destination_id, destination_ids[], countries[] (GIN), activities[] | 3,871 | tour_graph.py |
| `tripplanner.tour_junction` | 004 | PK (a,b), km, cross_border; both directions, <= junction_km (150) | 3,496 (=1,748 pairs) | tour_graph.py |
| `tripplanner.tour_graph_build` | 004 | params jsonb, stats jsonb, built_at (one row per rebuild) | n/a (small) | tour_graph.py |
| `tripplanner.trip_events` | 001, 006 | event log; payload.component_id references components **without FK** | 51 | assembly (not pipeline) |
| `tripplanner.trip_drafts` | 001 | | 21 | assembly |

CIS inputs: `acp_contract.tour_atoms` ~32,019 rows; view `v_active_tour_atoms` (gated on master_status);
`gold_aa_internal.published_tours` ~886 rows (121 active at 29/09 measurement); `silver_aa_internal.raw_tours.country`.
Logging: `shared.llm_call_log` ~244k rows (all CIS+TP).

Observations: tour_day 650 rows vs 1,489 days measured on 121 tours (29/09) -> current tour_day covers a
subset (first run stopped at 56 tours on purpose; ADR 0002 froze further waves). itinerary_components 3,972
includes the 1,081 legacy rows of unpublished tours unless pruned (prune of components is opt-in).

## 2. Runtime entry points
- **Assembly Lambda `aa-tripplanner-dev-assembly`**, direct invoke only, payload `{"extraction": {op...}}`
  (`lambda_entry.run_extraction_event`; API GW events never reach it). 60 s timeout -> one tour per invoke.
  Has Bedrock satellite role (tp_extract), DB secret, Mapbox secret (`MAPBOX_GEOCODING_TOKEN_ARN`).
- **Operator script** `invoke_tour_days.py` (laptop, aa365-admin, `lambda:InvokeFunction` only): loops
  `list` -> per tour `tour_days` (or `components` with `--components`; or paged `relink`), then `tour_graph`
  unless `--no-graph`. Flags: --only-stale, --force, --country, --limit, --pages, --junction-km.
- Ops: `list`, `tour_days`, `components`, `relink`, `tour_graph`, `neighbours`, `prune`, `orphans`.

## 3. Steps

### Step A — `tour_days` (AA-675) — tour_days.py, op `tour_days`
- **Input:** `published_tours.tour_id, aa_name, aa_itineraries` JOIN `raw_tours.country` WHERE master_status='active'
  (ACTIVE_TOURS_SQL, tenant RLS). Reads `tour_day.min(source_hash)` per tour.
- **Skip/idempotency:** sha256(aa_itineraries) == stored source_hash -> skip (unless `force`). Upsert per
  (tour, day); DELETE days > max day.
- **Logic:** parse "Day N — title" blocks (ranges expand) -> regex rules (A to B, "overnight/stay in X") ->
  `needs_model` only if some non-last day lacks an overnight from rules -> **1 tp_extract call per tour**
  (max 4000 tokens out, body truncated 900 chars/day) -> `ground_llm_day` drops any place not in that day's
  own text -> merge (model wins when grounded). Model failure -> rules only.
- **Anchor:** `anchor_place(overnight, end)`: skip transit (train/sleeper/flight/bus/ferry), lodging
  (hotel/lodge/camp except base camp/guesthouse/homestay/resort/...) -> fall back to end place.
- **Link (`_linker`):** anchors already in `shared.destinations` with `located_by IS NOT NULL` reuse id; new
  or legacy -> `locate.locate_many` (**+1 tp_extract call per 40 new names**) + Mapbox per name.
- **Output:** `tripplanner.tour_day` (all cols), `shared.destinations` upsert (new places).
- **Per-tour calls:** 0–1 tp_extract (day extraction) + 0..ceil(new/40) tp_extract (locate) + 1 Mapbox
  request per newly located name. No embeddings.
- **Runtime:** fits 60 s Lambda per tour (no per-tour seconds documented; the script prints `seconds`).
  Cost documented: first 56-tour run = **$0.89 tp_extract** (~$0.016/tour).

### Step B — `relink` — tour_days.relink, op `relink`
- **Input:** all `tour_day` rows of active tours; groups by lower(anchor).
- **Logic:** re-locates every anchor from scratch (ignores existing rows), page of 40 anchor names per invoke
  (= **1 tp_extract call + up to 40 Mapbox calls per page**); first page nulls `overnight_destination_id`
  on unanchored nights.
- **Output:** `shared.destinations` upsert (overwrites lat/lng/country/located_by), `tour_day.overnight_destination_id`.
- **Documented:** ~13 model calls for ~500 anchors of 56 tours.

### Step C — `components` (AA-674 step 1, AA-731) — components.py, op `components`
- **Input:** `acp_contract.v_active_tour_atoms` (atom_id, itinerary_day, place, activity_type, text) for one
  tour, place/day NOT NULL (tenant RLS); tour meta from ACTIVE_TOURS_SQL.
- **Logic:** deterministic, **no model for categorizing**: 1 atom -> 1 component via `categorize_atom`
  (activity_type map: trek/culture/food/bike/stay; 'other' by keywords; 'transit' skipped; lodging/transit
  places skipped via anchor_place). Defaults: duration full_day, season 1–12, intensity by activity,
  text_extract = atom text[:280].
- **Link:** unique places -> `_linker` (known located names reuse; new -> tp_extract per 40 names + Mapbox).
  Components whose place cannot be located are dropped.
- **Embed:** `tp_component_embed` (Cohere Embed v4, 1536-d, `input_type=search_document`, direct on acc2),
  **96 texts per call** -> ceil(components/96) calls per tour (typ. 1).
- **Output:** DELETE + INSERT all `itinerary_components` of the tour in one transaction (new ids every
  rebuild -> saved trips referencing old component ids lose those pins; no FK).
- **Skip/idempotency:** **none** (no hash; always full replace of the tour's rows). Re-running costs embed
  calls every time.
- **Per-tour calls:** 0..ceil(new places/40) tp_extract + ceil(n/96) tp_component_embed + Mapbox per new place.

### Step D — `tour_graph` (AA-673) — tour_graph.py, op `tour_graph`
- **Input:** active tour ids (catalog), `tour_day` (overnight_destination_id), `itinerary_components`
  (destination per tour-day, activity, intensity, season), `shared.destinations` (lat/lng/country).
- **Logic:** stop per (tour, day) = overnight destination, else the component destination with most
  components that day. Nodes, edges (consecutive distinct stops), legs (every span i<j per tour, O(n²)
  per tour), junctions (all destination pairs <= 150 km, haversine, both directions).
- **Output:** DELETE all + INSERT `tour_stop`, `tour_graph_node`, `tour_graph_edge`, `tour_leg`,
  `tour_junction`, one `tour_graph_build` row — one transaction, whole graph.
- **Calls:** none (no model, no external API). Refuses if 0 active tours visible.
- **Runtime:** single invoke for whole catalog (~1.5k stops, ~100k haversines); seconds reported in response,
  not documented.

### Step E — maintenance ops
- `prune` — DELETE tour_day (and optionally itinerary_components) of non-active tours; refuses if active set empty.
- `orphans` — read-only counts of rows of non-active tours.
- `neighbours` — sample "where next" query (tour_junction + tour_graph_edge + node); returns query_ms.

### Legacy / one-off scripts (local, need DSN; tunnel removed AA-602 -> effectively dead)
- `run.py` — original LLM path: atoms (`tour_atoms` JOIN published_tours, deleted=false) grouped by
  (tour, day) -> **1 tp_extract call per (tour, day) group, retry once** (max 1500 tokens) -> verify.py
  activity grounding -> `geocode_place` (Mapbox forward, cached by lower(name)) -> **1 tp_component_embed
  call per component** -> INSERT (no delete, not idempotent). Superseded by Step C.
- `run_deterministic.py` — no-LLM seeder: atoms -> categorize -> Mapbox geocode (concurrency 10,
  country "" -> blank country) -> bulk INSERT with embedding NULL (produced the 1,081 legacy rows).
- `geocode.py` — Mapbox forward (types place,locality,district,poi; country filter = AA ISOs; prefer tour
  ISO among equal relevance); cache in shared.destinations; ON CONFLICT lower(name) keeps existing row.
  Used by run.py / run_deterministic; helpers (`_mapbox_token`, `AA_ISOS`, `_TYPES`) reused by lambda_entry.
- `backfill_embeddings.py` — UPDATE embedding WHERE NULL, 1 tp_component_embed call per row, resumable.
- `backfill_country.py` — UPDATE destinations.country = mode(raw_tours.country) over its components (only
  blanks unless --all); no external calls.
- `regeocode_outliers.py` — reverse-geocode **every** destination in 6 countries (Mapbox reverse, 1 call/row,
  3 retries) -> forward re-geocode wrong-country rows (country+bbox+proximity, up to 4 calls) -> jittered
  centroid fallback -> UPDATE lat/lng; then re-verify all (another reverse per row). Superseded by relink.

## 4. Model stages & external APIs summary

| Stage / API | Used by | Unit | Per tour |
|---|---|---|---|
| `tp_extract` (Claude via satellite acc3->acc1, gateway route, logged to llm_call_log with op) | tour_days, locate (tour_days/components/relink) | 1 call/tour (only if rules miss an overnight); 1 call/40 new place names | ~1 + ceil(new/40) |
| `tp_component_embed` (Cohere Embed v4, acc2 direct, 1536-d) | components, run.py, backfill_embeddings | 96 texts/call (components) | ceil(n/96), typ. 1 |
| `tp_search_embed` | browse/search (runtime, per query) | 1/query | n/a |
| Mapbox forward geocoding v5 (`mapbox.places`, proximity, AA ISOs, autocomplete=false) | locate confirm (25 km), geocode.py | 1/new name | = new names |
| Mapbox reverse | regeocode_outliers only | 1-2/destination | n/a |

## 5. Readers (runtime) of the place tables

| Reader | Endpoint | Tables read |
|---|---|---|
| browse/tiles.py | GET /browse/tiles/{id} | destinations JOIN itinerary_components (count>0, filters) |
| browse/countries.py | GET /browse/countries, /browse/by-country | destinations JOIN itinerary_components |
| browse/destinations.py | GET /browse/destinations/{id} | destinations (incl. cover_image_url), itinerary_components |
| browse/search.py | GET /browse/search?q= | destinations JOIN itinerary_components (embedding <=> query, tp_search_embed) |
| browse/routes.py | GET /browse/routes?country&days | tour_leg, tour_stop, tour_junction, destinations, itinerary_components (embedding NOT NULL), published_tours.aa_name (RLS) |
| assembly/events.py `_current_components` | GET /trip/{id} and all trip reads | trip_events -> itinerary_components JOIN destinations |
| assembly/suggestions.py | GET /trip/{id}/suggestions | itinerary_components (embeddings taste), tour_graph_node, tour_stop, destinations; fallback destinations+components |
| assembly/coverage.py | GET /trip/{id}/coverage | itinerary_components (dest -> tour,day options), published_tours.aa_name |
| assembly/activities.py | GET /trip/{id}/stops/{dest}/activities | itinerary_components by destination |
| assembly/handler apply-route | POST /trip/{id}/apply-route | component ids from routes proposal (via events) |
| assembly/handoff.py leg_chain | send-to-advisor / inquiry outbox | component source_tour_id/source_day_index (tour_day.day_index semantics) |
| extraction tour_graph / neighbours | ops | tour_day, components, destinations, graph tables |
| CIS (per ADR 0002) | AA-708 photos | shared.destinations (covers), v_destination_photos |
| frontend | DestinationPopup.tsx, lib/types.ts | via APIs only |

Not reading graph tables: tiles/countries/search/destinations use only components+destinations.
`tour_day` is read only by the pipeline itself (tour_graph, relink, prune, orphans, list) — no runtime endpoint.
`tour_graph_edge`/`tour_junction` runtime readers: routes.py (junction), neighbours op; suggestions uses node+stop only.

## 6. Points for AA-712 (move to CIS)
1. Two independent sources: tour_day from `published_tours.aa_itineraries` (text, hash-skipped) vs
   components from atoms (no skip, full replace). CIS port should add a skip key for components
   (e.g. hash of the tour's active atom source_hash set) to avoid re-embedding.
2. Component ids are regenerated on every rebuild and trip_events reference them without FK -> CIS views
   must expose a stable id (e.g. derive from atom_id) or TP drafts break on each wave.
3. Graph rebuild is global (DELETE all) and cheap (no calls) -> one CIS job kind after each wave.
4. Per tour cost envelope: ~1 tp_extract (days) + ~0–1 tp_extract (locate, amortised: ~13 calls/500 anchors)
   + ~1 Cohere embed call + Mapbox per new place; documented $0.89 / 56 tours for tour_days.
5. Writers that must stop/move: geocode.py, locate.upsert, regeocode_outliers, backfill_country,
   backfill_embeddings, components, tour_days persist/relink/prune, tour_graph persist.
6. TP readers to repoint to views: browse/* (5 files), assembly events/suggestions/coverage/activities,
   routes; columns used are listed in §5.
