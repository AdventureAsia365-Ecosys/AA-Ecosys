# ADR 0007 — Place pipeline in CIS: `geo` schema, `catalog.*` views, background jobs

- **Status:** Accepted (14/10/2026, S236 — Nghiệp approved the AA-712 design with every recommendation
  Q1–Q7, and chose Geoapify as the geocoder the same session, see decision 9).
- **Scope:** AA-Ecosys: AA-CIS-App (schema `geo`, job kinds, admin page, `catalog` views),
  AA-TripPlanner-Web (readers move to views, writers removed, legacy tables dropped), AA-CIS-Infra
  (migration copies, the `aa-cis/dev/geoapify` secret readable by the worker task role). AA-Booking reads the same views later.
- **Implements:** ADR 0002 consequence 1 ("The place pipeline moves to CIS"). Uses ADR 0003 (one durable
  job model) as is. **Amends nothing else.**
- **Linear:** AA-712. **Design:** `docs/audits/2026-10-14-S236-design-review/aa712/03-design.md`
  (inputs `01-tp-pipeline-map.md`, `02-cis-side-map.md`). The design calls this record "ADR 0006"; that
  number went to ecosystem identity, so it is 0007.

## Context

ADR 0002 made CIS the only writer of content, including a tour's itinerary places and the tour graph.
On 14/10/2026 that pipeline still lives in TripPlanner and is frozen:

- `backend/extraction/*` (Lambda) derives the day skeleton, itinerary components, stops, legs and
  junctions from CIS tours and writes them to `tripplanner.itinerary_components`, `tour_day`, `tour_stop`,
  `tour_graph_*`, `tour_leg`, `tour_junction`; it geocodes names (model + Mapbox) into `shared.destinations`.
- Only 56 of 892 live tours are in the planner graph, so "Customise this trip" works for few tours, and
  destination photo covers (AA-708) wait for the places.
- `shared.destinations` is unique on global `lower(name)`: the same name in two countries is one row.
- CIS cannot write `tripplanner.*` (ADR 0001 decision 6, schema-ownership rule 1), and TripPlanner may
  not write content (ADR 0002). The tables have to move, not just the code.

## Decisions

### 1. Data lives in a new CIS-owned schema `geo`

- New schema **`geo`**, owned by AA-CIS-App (migrations `226+`), internal: no grant to any other app's
  role. Tables: `tour_build`, `tour_day`, `tour_place` (= itinerary component), `place_name`
  (resolution cache), `graph_build`, and `tour_stop` / `graph_node` / `graph_edge` / `tour_leg` /
  `tour_junction` (TripPlanner's columns + `build_id`).
- Not `gold_aa_internal` or `acp_shared`: the data is derived from master content, neither master nor
  tenant content; one schema means one grant to the view owner, one place in the Dead Table Registry, and
  a rebuild from scratch touches nothing else.
- `shared.destinations` stays the golden record of places (ADR 0002), keeps every existing `id`
  (photos, covers and TripPlanner trip events point at them) and gains geo-quality columns
  (`geo_status` ok / suspect / manual, `located_by`, `precision` point / area, `confidence`, provider,
  provider id, `result_type`, `geocoded_at`, `name_norm`), which decision 9 fills.

### 2. `catalog.*` views are the TripPlanner contract

- TripPlanner (and later AA-Booking) reads places and the graph **only** through views in the `catalog`
  schema (AA-679, CIS 225): `v_tour_place` (now by `destination_id`, not name match),
  `v_tour_component` (TripPlanner's component shape incl. `embedding`), `v_tour_day_route`,
  `v_tour_stop`, `v_tour_leg`, `v_graph_node`, `v_graph_edge`, `v_tour_junction`, and `v_destination`
  with `geo_status` / `located_by`.
- `v_destination` and `v_tour_place` carry `located_by` and `precision` (appended columns, see below),
  so TripPlanner can draw an unconfirmed point as an area and show the provider attribution.
- Views are `security_barrier`, owned by the dedicated NOLOGIN role `catalog_owner` exactly as in
  migration 225 (on RDS `aa_cis_admin` is not BYPASSRLS; a view over a FORCE-RLS table needs its own owner
  role + policy), and granted to `aa_app_user`, `tripplanner`, `booking`.
- Liveness is not stored: every view, the graph views included, joins `catalog.v_tour` (active master,
  not trashed, source active), so trash or supersede needs no delete and a trashed tour stops routing at
  once. Suspect destinations are excluded from the graph views.
- Changes to the 225 views only **append** columns (`CREATE OR REPLACE VIEW` cannot reorder or retype).
  Additive to contract `catalog.tour.v1` (`catalog.tour.v1.1.json`); the graph views are documented as
  `catalog.graph.v1` in `docs/contracts/catalog.graph.v1.json`.
- Implemented by **CIS migration 228** (S237; 227 went to `sonnet5_no_temperature`): views only, no top-k
  function (S237 decision D7 — TripPlanner keeps its exact `MIN(embedding <=> q)` on the cis read path until
  the catalog-wide run, see Consequences).

### 3. Identity: `source_id`, stable `component_id`

- Every `geo` row is keyed by **`source_id` = `COALESCE(raw_tours.source_group_id, tour_id)`** (the
  `catalog.v_tour` identity). `tour_id` is an attribute: the version the rows were built from. Views
  expose `built_from_tour_id` and `is_stale`, so after `set-active` the previous build keeps serving
  until the rebuild lands.
- A build writes only if its `tour_id` is still the live version of `source_id`, re-checked inside the
  persist transaction under `SELECT … FOR UPDATE` on `geo.tour_build` (an older job cannot overwrite a
  newer build); otherwise it exits `skipped_not_live`.
- **`component_id` = `uuid5(NS, source_id | day_index | name_norm | country | activity)`** — no
  `destination_id`, so a name resolved later keeps its id. Survives re-atomize and re-upload while the
  place/day/activity is the same; atoms with the same (day, place, activity) collapse into one component
  (`atom_ids[]`). TripPlanner draft pins (`trip_events.payload.component_id`) therefore stay valid across
  waves.

### 4. Jobs on `shared.job`, background priority

- Three CIS job kinds (ADR 0003: enqueue-only triggers, stage registry, swap-safe writes), all cap 1:
  `place_extract` (one tour: days → components → link → embed → persist), `place_geocode` (platform,
  debounced: locate → confirm → guard → upsert → relink in SQL), `tour_graph_build` (platform, debounced:
  stops → graph → versioned swap → cover/photo match).
- New registry flag **`JobKind.background`**: the worker never gives its last **2** free slots to
  background kinds, so place work cannot starve `s1_rewrite` / `a3_atomize` during a wave (S217 lesson,
  guarded by an extended `test_aa737`).
- Triggers are best-effort enqueues: end of A3 atomize (`place_extract:<version_id>`), set-active /
  master status / trash / restore (graph build, and extract of the live version), extract with pending
  names → one debounced geocode. No per-tour re-link jobs.
- **Single writer of coordinates:** only `place_geocode` writes `shared.destinations` and the name cache
  status; `place_extract` only inserts new names as `pending`.
- Idempotency by two hashes on `geo.tour_build`: `days_hash` gates the paid day-skeleton call,
  `components_hash` gates components/link/embed; embeddings are reused by `text_hash`. Unchanged input →
  `skipped_unchanged`, no spend.
- Spend guarded by `shared.spend_budget` rows (`job:place_extract`, `job:place_geocode`, and one row for
  the geocoder) with a hard stop. Observability: job domain links + a new admin page `/admin/places`
  (coverage per country, pending / unknown / suspect names with a fix action, graph build stats,
  per-tour rebuild, backfill with dry-run cost).

### 5. Destinations unique on `(name_norm, country, locality_norm)`

- Replace the global `UNIQUE lower(name)` with **`UNIQUE (name_norm, country, locality_norm)`**; ids are
  kept. `locality_norm` is `text NOT NULL DEFAULT ''`: empty for every non-generic name, so for them the
  key is effectively `(name_norm, country)`. `geo.place_name` uses the **same three-column key**.
- `country` becomes **`NOT NULL`** on both tables. Blank or NULL `country` rows are fixed (or the row is
  set aside) before migration 226 adds the constraint and the index; marking a row `suspect` is not
  enough, because NULLs are distinct in a unique index.
- Generic names (`is_generic_name()`: "Ban Na", "Base Camp") get a non-empty `locality_norm` (place card
  locality, else the day's overnight town), so two "Ban Na" in Laos with different localities are two
  rows; without a locality they stay `unknown` (no point) rather than borrow another tour's coordinates.
- Legacy rows are reused only when `located_by` is `geoapify`, `llm` or `manual` and not `suspect`;
  `located_by='mapbox'` rows are re-confirmed with Geoapify (decision 9); everything else is
  re-resolved. `geo_status='manual'` is never overwritten by a job.

### 6. Place cards are used when present, not built

- When an atom has a place card (`acp_shared.place_card`), the card's identity and display name/country
  are preferred over the name key and its destination is reused (zero calls); an optional
  `place_card.destination_id` FK makes the join by id. `card_skip_reason()` is the one lodging/transit
  rule set for components.
- AA-712 does **not** create cards. A catalog-wide card backfill is a separate decision (T9 quality).

### 7. Models: Sonnet for the day skeleton, Luna in shadow

- Stage keys `a3_place_days` (Sonnet, **GPT-5.6 Luna as 20% shadow**), `a3_place_locate` (Sonnet),
  `a3_place_embed` (`cohere-embed-v4`, 1536-d, `search_document` — must match TripPlanner's query
  vectors; a model or dimension change is one coordinated pair of PRs). All calls go through the
  Model Gateway and `shared.llm_call_log`.
- Switch the day skeleton to Luna by migration if shadow parity reaches ≥ 95%.

### 8. Automatic batch gate, ≤ 50 tours per batch

- Backfill (`POST /admin/places/backfill`, dry run first) enqueues at most 50 tours per batch, refuses
  while a wave (`s1_rewrite`, `a3_atomize`, `recompute`) or the previous batch is queued or running.
- Order: trial 3 tours (parity vs the frozen TripPlanner tables, 30-destination map spot check) → rest
  of that country → whole catalog by country. Between batches the gate is **automatic**: failed < 5%,
  suspect names < 5%, LLM cost/tour < $0.05, geocoder on its own budget row; a report per country
  replaces a manual approval per batch.

### 9. Geocoder: Geoapify behind an adapter; storage rights required

- CIS calls the geocoder through one adapter (forward geocode with country filter, returns point,
  provider id, `result_type`, raw confidence). The method is TripPlanner's (S202): the model proposes a
  point, the provider confirms it, else the model point is kept with lower precision.
- **Only a provider/mode whose terms allow storing results indefinitely may be used**, because
  coordinates live forever in `shared.destinations`.
- **Provider: Geoapify** (Nghiệp, S236) is the confirming geocoder for **all countries**. OpenStreetMap
  data; Free plan 3,000 credits/day, commercial use allowed; results may be stored. Mapbox is the
  **basemap only** (no Mapbox geocoding is called or stored); Amazon Location is not used. Evidence:
  [`04-geocoder-research.md`](../audits/2026-10-14-S236-design-review/aa712/04-geocoder-research.md)
  (terms, prices, coverage) and
  [`05-geocoder-bakeoff.md`](../audits/2026-10-14-S236-design-review/aa712/05-geocoder-bakeoff.md)
  (64 real names, 13 countries: Geoapify named-or-related 38/64, Amazon Location Geocode 14/64; hard
  names 18/29 vs 1/29).
- Rejected:
  - **Amazon Location Places v2 (Stored)** — the bake-off found almost only cities (0 correct in
    BT/CN/MN/LA, homonyms in NP/TW), several AA countries are *Unsupported*, Japan results may not be
    stored (HERE §82.5.a), and there is no endpoint in us-west-1.
  - **Mapbox Permanent geocoding** — Product Terms §2.7.3 allow Permanent geocodes in an app only as an
    ancillary feature, with one request per end-user account and no lat/lng exposed to end users;
    TripPlanner's public map breaks all three (and there is no free tier).
- **Acceptance rule** (from the bake-off; the adapter implements it, the design doc holds the detail):
  - Query `/v1/geocode/search?text=<normalised name>&filter=countrycode:<iso2>&format=json&limit=3`.
    Normalise first: drop "(5,164m)"-style altitudes, split "X to Y" into its endpoints, split
    "X, City". Generic phrases with no proper noun ("ger camp", "local market", "village center",
    "fishing village") are not geocoded; they take the day's town point. Taiwan / Korea: when the model
    supplied a native-script name (中文 / 한글), query it as a second attempt.
  - Scan the top 3 and accept the **first** candidate that passes all of: (a) name similarity
    (diacritics, parentheses and altitudes stripped; generic words such as temple/lake/pass/village
    dropped) = 1.0, or ≥ 0.5 when the query has ≥ 2 distinctive tokens; (b) `result_type` not
    country/state/county/postcode, and `city` only when the query itself is a settlement; (c) distance to
    the model point ≤ 25 km, or ≤ 50 km for lake/river/valley/park/trail/road.
  - `rank.confidence` is **not** a gate (correct POIs often score 0); it is recorded for audit only.
  - Accepted → `located_by='geoapify'`, with provider, `geocoded_at`, raw confidence and `result_type`
    stored for audit (a later re-run on another provider is a job, not a migration). None accepted → keep
    the model point, `located_by='llm'`, precision **area** (shown as an area, not a pin); hard types
    (monastery, pass, lake, village, …) go on the `/admin/places` review list.
- Operation: ≤ 5 requests/s, retry with backoff on 429/5xx, a daily credit guard (stop at 2,500/day,
  configurable) on top of the geocoder's `shared.spend_budget` row. The API key is the Secrets Manager
  secret `aa-cis/dev/geoapify` (plain string), read through CIS's existing secrets helper; the key and
  full request URLs are never logged. The provider setting defaults to `geoapify`; `model_only` remains
  for tests and emergencies.
- **Attribution is required wherever these coordinates are shown**: a "Powered by Geoapify" link near
  the map or place information (Free-plan condition) plus "© OpenStreetMap contributors". The source
  is kept with every stored row (`located_by`, provider).
- TripPlanner's stored `located_by='mapbox'` rows came from Mapbox **Temporary** geocoding, which may
  not be stored; the backfill re-confirms every one of them with Geoapify (or replaces it with the
  model point as `llm`).

### 10. TripPlanner cut-over and legacy drop

- TripPlanner readers switch behind a runtime flag (`legacy` → `cis`). The flip happens **only when the
  views cover every `source_id` the frozen TripPlanner tables cover** (one SQL check), and in the same
  window as a TripPlanner migration that maps old component ids to the new stable ids (unmatched pins are
  dropped; Dev only).
- TripPlanner extraction writers (Lambda ops, geocode/locate/backfill scripts, the server-side
  Mapbox geocoding secret, `tp_extract` grant) are removed. The S236 "places fallback" stays until `/admin/places` shows 100%
  coverage of live tours.
- Rollback = flag back to `legacy` (tables frozen, not dropped). **The legacy tables**
  (`tripplanner.itinerary_components`, `tour_day`, `tour_stop`, `tour_graph_*`, `tour_leg`,
  `tour_junction`) **are dropped by a TripPlanner migration 14 days after the flip** (DRY RUN procedure).

## Consequences

- TripPlanner keeps only trip-planning logic and its user state; it writes no content (ADR 0002 met for
  places). AA-Booking reads the same views from its first catalog slice.
- The `tripplanner` read-model tables disappear from the schema-ownership table after the drop; `geo` is
  added as a CIS schema.
- Destination covers (AA-708) can be switched on once a country is built.
- Cost for the whole catalog ≈ $13–35 LLM + embeddings; the geocoder is $0 on the Geoapify Free plan
  (≈ 6,000–8,200 requests = 3–4 days of the 3,000/day quota under the 2,500/day guard). Steady state
  ≈ $0.025 per new or rewritten tour. If the free tier changes, Geoapify API 10 ($59/month) is the paid
  fallback.
- Every surface that shows place coordinates (TripPlanner map and place cards, later AA-Booking) must
  carry "Powered by Geoapify" + "© OpenStreetMap contributors". Points that no provider confirmed
  (`located_by='llm'`) are drawn as an area, not a pin.
- Geoapify Free has no SLA and its terms can change; storing provider + `geocoded_at` per row keeps a
  switch to another storable provider a re-run job. Mapbox Temporary coordinates stop being a source of
  stored points.
- Deploy gate: each 50-tour batch holds the gate ≈ 40–55 min (debounced follow-ups included); batches run
  outside deploy windows.
- Before the catalog-wide run (not before the trial), TripPlanner's vector search (`MIN(embedding <=> q)
  GROUP BY destination`, a full scan) must be rewritten to an HNSW top-k subquery or a per-destination
  centroid. The planner may not push `ORDER BY embedding <=> q LIMIT k` into the HNSW index through a
  `security_barrier` view joined to `catalog.v_tour`, so the top-k may need its own view or SQL function
  over `geo.tour_place` (owner `catalog_owner`); the plan is checked with `EXPLAIN` as the `tripplanner`
  role.
- Accepted risks: a "replace" re-upload hides the tour from `catalog.v_tour` until the new version
  publishes (AA-679 behaviour); true homonyms without card or overnight context stay unlocated; the
  background slot reserve is per worker task and must be re-checked on horizontal scale-out.
- **Amended S246 (AA-847), no decision changed:**
  - *Top-k view.* The HNSW top-k is `catalog.v_component_embedding` (CIS 253): components of live tours on a usable
    destination (the rows of `v_tour_component`: never a suspect or merged place) with their embedding, **not** a
    `security_barrier` view, so `ORDER BY embedding <=> q LIMIT k` is served by the index on `geo.tour_place`
    (`hnsw.iterative_scan` on pgvector ≥ 0.8; liveness and the usable-destination rule are EXISTS filters, which an
    iterative scan keeps); granted to `tripplanner` only (it exposes ids and vectors, which Booking and
    `aa_app_user` do not need). The reader checks nothing after the scan. Contract `catalog.graph.v1.1`.
    TripPlanner `vector_topk` reads it with `source=CIS` (slice 6c).
  - *Liveness without the barrier cost.* Every place / graph view joins the internal, ungranted, non-barrier
    `catalog._live_tour` (CIS 253) instead of `catalog.v_tour`, so the planner flattens it and prunes `v_tour`'s
    per-tour photo count, cover, duration regex and md5. `security_barrier` stays on the contract views; turning it
    off on the graph views (they hide only non-live rows from trusted app roles) is a measured follow-up (CIS 255+)
    only if the AA-847 probe shows consumer quals blocked above a barrier subquery.
  - *Not a pin.* Linear features (trail, river, road, range, loop …) are not drawn at all: stored `suspect` +
    `review_reason='linear_feature'`, hidden by every view, name kept in the day text (proposed display rule,
    Nghiệp's decision); area features (national park, delta, plateau, coast, gorge) are `precision='area'` even when
    a geocoder confirms a point. A deterministic content-validity report (CIS `services/places/validity.py`) runs
    after every graph build and on `/admin/places`, with audited, undoable fixes (duplicate merge, area / linear).
  - *Flip.* `PLACES_SOURCE=cis` is set on both TripPlanner Lambdas together, after the coverage gate
    (`missing_in_cis_live = 0`), with `tripplanner.component_id_map` (tp-017) bridging old component ids; then CIS
    254 revokes TripPlanner's grandfathered `raw_tours` (179) and `tour_atoms` (180) reads.
- **Revisit** if Geoapify's terms stop allowing storage or the free tier, if the confirm rate per
  country after the trial is too low to be useful, or if a second app needs to author places.
