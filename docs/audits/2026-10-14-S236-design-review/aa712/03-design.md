# AA-712 — Place pipeline in CIS: design (S236, decision-ready draft)

Inputs: `01-tp-pipeline-map.md`, `02-cis-side-map.md`, ADR 0001/0002/0003, `docs/database/schema-ownership.md`,
CIS migrations 169/170/173/220–225, TP `backend/extraction/*` @ 6523816, TP hotfix branch (S236 places fallback).
Note: **ADR 0006 does not exist** in `docs/adr/` (0001–0005 only) — this design proposes the content of one (§9 Q1).

---

## 1. Goal and non-goals

**Goal.** Every live tour (892 today; 56 in the planner graph) gets its itinerary places, day skeleton
(start / end / overnight), stops, legs and junctions **computed and written by CIS job kinds**, automatically on
publish / re-upload / trash, and readable by TripPlanner (and later AA-Booking) **only through `catalog.*` views**.
"Customise this trip" then works for every tour, photo covers follow the places, and TP writes no content.

**Done when** (Linear): one country built by CIS jobs on Dev; TP map + suggestions + routes work from views;
photo covers set; then whole catalog by country (S236 decision).

**Non-goals.**
- Changing TP trip-planning logic (assembly, routes ranking, suggestions scoring) — only its data source.
- Building place cards (facts) for every place. Cards are used when present; a catalog-wide card backfill is a
  separate, optional spend (§8, §9 Q3).
- An outbox/event (`catalog.tour.*`) — still AA-679's next slice; TP keeps polling views.
- Reverse-geocode audits of all destinations (`regeocode_outliers.py`) — replaced by the guard in §4.
- Production. Dev (acc2) only.

## 2. Target data model

### 2.1 Ownership decision
TP-owned `tripplanner.*` tables cannot be written by CIS (ADR 0001 §6, schema-ownership rule 1), and CIS must
not migrate them. So the place tables **move into a new CIS-owned schema `geo`** (internal, never granted to
other apps); readers get `catalog.*` views. `shared.destinations` stays where it is (CIS-owned golden record
since ADR 0002) and gains columns. TP's `tripplanner` place tables are frozen, then dropped by a TP migration
after cutover (§7).

Why a new schema and not `gold_aa_internal` / `acp_shared`: the data is derived from master content but is
neither master content nor tenant content; one schema = one grant to `catalog_owner`, one place for the
Dead-Table registry, and it can be rebuilt from scratch without touching anything else.

### 2.2 Tables (CIS migration 226)

| Table | Key | Content | Write strategy |
|---|---|---|---|
| `geo.tour_build` | `source_id` PK | current `tour_id`, `days_hash`, `components_hash`, `rule_version`, status (ok / partial / failed / retired), counts, `cost_usd`, `built_at`, `job_id` | UPSERT per source |
| `geo.tour_day` | (`source_id`, `day_index`) | `tour_id`, title, start/end/overnight place text, `overnight_destination_id` FK, places text[], `extracted_by` (rule/llm/rule+llm) | per-source DELETE+INSERT in one txn |
| `geo.tour_place` (= itinerary component) | `component_id` uuid PK (stable, see 2.3) | `source_id`, `tour_id`, `day_index`, `destination_id` FK, `place_card_id` NULL, name, activity (8 enum), intensity, season_months, duration_hint, `text_extract`, `text_hash`, `embedding vector(1536)` (HNSW cosine), `atom_ids uuid[]` | per-source DELETE+INSERT in one txn |
| `geo.place_name` | (`name_norm`, `country`) | resolution cache: `destination_id` NULL, status (resolved / pending / unknown / suspect), `tries`, `last_error`, `next_retry_at` | UPSERT |
| `geo.graph_build` | `build_id` | params, stats, `is_current` (partial unique index on true), built_at, job_id | insert + one-row swap |
| `geo.tour_stop`, `geo.graph_node`, `geo.graph_edge`, `geo.tour_leg`, `geo.tour_junction` | TP keys **+ `build_id`**; `source_id` replaces `source_tour_id` | same columns as TP 004 | versioned swap (ADR 0003 §3) |

`shared.destinations` (CIS migration): add `geo_status` (ok / suspect / manual), `confidence`,
`mapbox_id`, `geo_checked_at`, `name_norm`; replace the global `UNIQUE lower(name)` with
**`UNIQUE (name_norm, country)`** — the same name in two countries is two places (02 §2 gap 2).
Existing `id`s are kept (place_photo FK, covers, TP trip events all point at them).

Optional link `acp_shared.place_card.destination_id` FK (CIS migration): a card resolves once to a destination,
so `catalog.v_tour_place` can join by id instead of today's name-match LATERAL.

### 2.3 Identity: `source_id`, not `tour_id`
- Key every row by **`source_id` = `COALESCE(raw_tours.source_group_id, tour_id)`** (the `catalog.v_tour`
  identity); keep `tour_id` as an attribute = the version the rows were built from.
- Re-upload: the new `tour_id` publishes → atomize → `place_extract` for the new `tour_id` replaces the rows of
  the same `source_id`. The old rows stay in `geo.*`, **but they are not visible in the gap**: a "replace"
  re-upload sets the old `raw_tours.source_status='superseded'` at once (02 §5), and `catalog.v_tour`
  (225 l.155) requires `source_status='active'`, so the whole source leaves the catalog (and the TP map)
  until the new version publishes. This is AA-679 catalog behaviour, not something AA-712 can fix; it is
  listed as a risk (§9). `keep_both` / `set-active`: the job builds only if its `tour_id` is the live version of
  `source_id`, else it exits as `skipped_not_live`; `set-active` enqueues a build for the newly active version.
- **Race guard (review S236):** the liveness check is repeated inside the persist transaction, after
  `SELECT … FROM geo.tour_build WHERE source_id=$1 FOR UPDATE` (insert the row first if missing). An older
  version's job that started before `set-active` / a re-publish must not overwrite the newer version's rows.
- Views join geo rows to `catalog.v_tour` on `source_id` (not `tour_id`) and expose `built_from_tour_id` plus
  `is_stale = (built_from_tour_id <> v_tour.tour_id)`: after set-active the previous build keeps serving
  (places of two versions of one tour are near-identical) until the rebuild lands, instead of the tour
  dropping off the map.
- **Stable `component_id`** = `uuid5(NS, source_id | day_index | name_norm | country | activity)`.
  **Not** `destination_id`: a name that is `pending` today and resolved tomorrow would otherwise change id
  (and drop every draft pin) the moment geocoding finishes; the destination is an attribute, not identity.
  Survives re-atomize and re-upload as long as the place/day/activity is the same, so TP drafts' pinned
  components (`trip_events.payload.component_id`, no FK) do not break on every wave (01 §6 pt 2).
  Two atoms with the same (day, place, activity) collapse into **one** component (`atom_ids[]` keeps both,
  `text_extract` = the longest atom text) — TP made one component per atom, so per-destination
  `component_count` in TP endpoints drops slightly; a re-upload that inserts a day shifts the ids of the days
  after it (accepted; pins on those days are re-mapped by the next §2.4-style map or lost).
- Liveness is not stored: views join `catalog.v_tour` (active master, not trashed, source active), so trash
  needs no delete. This applies to the **graph views too** (`v_tour_stop`, `v_tour_leg` filter on live
  `source_id`; `v_tour_junction`/`v_graph_edge` keep only edges whose tours are still live) — otherwise a
  trashed tour keeps routing visitors until the next debounced graph build. The graph build itself also only
  includes live sources. `geo.graph_build`: keep the current + 2 previous builds, delete older rows in the
  same swap transaction.

### 2.4 Existing 56-tour data
Do **not** copy rows. Rebuild with CIS jobs (cost ≈ $1–2) and compare against the frozen TP tables as the
parity baseline (§7). Keep all `shared.destinations` rows and ids; new names become new rows only when the
(name_norm, country) key is new. TP's 51 `trip_events` / 21 drafts: one TP-side migration maps old component
ids → new stable ids by (tour, day, destination, activity); unmatched pins are dropped (Dev data, tiny).

### 2.5 Views TripPlanner reads (CIS migration 227, catalog_owner dance as in 225)
Extend the `catalog` schema (one read contract, `security_barrier`, granted to `aa_app_user`, `tripplanner`,
`booking`); `catalog_owner` gets SELECT on `geo.*` and the new destinations columns.
- `catalog.v_tour_place` — swap the name-match LATERAL for `geo.tour_place.destination_id` (additive columns:
  `component_id`, activity, intensity, season_months, duration_hint).
- `catalog.v_tour_component` — TP `itinerary_components` shape incl. `embedding` (TP search/suggestions do
  `embedding <=> $q` in SQL). **Correction (review):** TP never uses the HNSW index — `browse/search.py:49`
  and `assembly/suggestions.py:88,257` compute `MIN(c.embedding <=> $1)` per destination with `GROUP BY`,
  i.e. a full scan of every component's 1536-d vector per request. Today 3,972 rows; whole catalog ≈ 27–45k
  rows ≈ 170–280 MB of vectors scanned per search. See §6 item 5.
- `catalog.v_tour_day_route` — start / end / overnight per day.
- `catalog.v_tour_stop`, `v_tour_leg`, `v_graph_node`, `v_graph_edge`, `v_tour_junction` — current build only.
- `catalog.v_destination` — add `geo_status`, `located_by`; suspect places excluded from graph views.
Contract: additive to `catalog.tour.v1`; graph views documented as `catalog.graph.v1` in `docs/contracts/`.

## 3. Job design (ADR 0003: enqueue-only triggers, stage registry, swap-safe writes)

| Kind | Scope | Cap | Stages | Paid calls |
|---|---|---|---|---|
| `place_extract` | one `tour_id` | **1** (was 2), `background` | `days` → `components` → `link` → `embed` → `persist` | `a3_place_days` (0–1/tour), `a3_place_embed` (≈1/tour) |
| `place_geocode` | pending names (platform, debounced) | 1, `background` | `locate` (40 names/call) → `confirm` (Mapbox) → `guard` → `upsert` → `relink` (SQL) | `a3_place_locate` (1/40 names), Mapbox (1/name) |
| `tour_graph_build` | platform, debounced | 1, `background` | `stops` → `graph` → `swap` → enqueue cover/photo match | none |

**Single writer of coordinates (review):** only `place_geocode` (cap 1, platform) INSERTs/UPDATEs
`shared.destinations` and `geo.place_name.status`. `place_extract` only reads them and inserts *new* names
as `pending` (`ON CONFLICT DO NOTHING`). No two jobs ever race on a destination row.

- **days**: port `tour_days.py` rules + grounded prompt as-is (`services/places/days.py`); model only when a
  non-last day lacks an overnight. **components**: port `deterministic.categorize_atom`, unified with
  `card_skip_reason()` (one lodging/transit rule set, 02 §2). **link**: name → destination via
  `geo.place_name` cache → place card (`atom_place_card` → card display_name/country → its destination) →
  else mark `pending`; components with unresolved places are written with `destination_id NULL` and hidden by
  views until resolved. **embed**: reuse embedding when `text_hash` unchanged. **persist**: per-source txn.
- **Triggers (layer A, all best-effort enqueue):**
  - end of `_run_a3_atomize_background` (next to `enqueue_recompute`): `place_extract`, key
    `place_extract:<version_id>`; covers publish, re-upload and admin re-atomize;
  - `set-active`, master status change, trash / restore (admin.py, AA-716/713 paths): `tour_graph_build`
    (debounced) and, for set-active/restore, `place_extract` of the live version;
  - `place_extract` finishing with pending names → `place_geocode` (debounced `run_after` like recompute,
    `WAVE_DEBOUNCE_S`, coalesced into the one queued platform job); geocode's last stage **`relink` is plain
    SQL inside the geocode job** (`UPDATE geo.tour_place SET destination_id … WHERE (name_norm, country)
    newly resolved AND destination_id IS NULL`, same for `geo.tour_day.overnight_destination_id`) →
    `tour_graph_build` (debounced). **No per-tour re-link jobs** (review: the draft enqueued one
    `place_extract` per affected source after every geocode run — during a 50-tour batch that is up to 50
    extra jobs per geocode pass, each one a deploy-gate blocker; a catalog backfill would fan out to ~900).
  - **Backfill**: `POST /admin/places/backfill {country?, limit≤50, only_stale, dry_run}` (+ CLI wrapper) —
    dry run returns tour count, expected calls and cost; real run enqueues per-tour jobs. **Refuses (409)
    while any `s1_rewrite`, `a3_atomize` or `recompute` job is queued or running** (a wave is in progress)
    and while a previous backfill batch still has queued `place_extract` jobs.
- **Idempotency — two hashes (review):** `days_hash = sha256(RULE_VERSION ‖ aa_itineraries)` gates the paid
  `days` stage; `components_hash = sha256(RULE_VERSION ‖ sorted(day, place, activity_type, text[:280]) of active
  atoms)` gates `components/link/embed`. The draft's single hash re-paid the Sonnet day call whenever only
  atoms changed — i.e. on every A3 re-atomize wave, the common case. Both stored in `geo.tour_build`, keyed by
  `source_id`, so a re-upload whose itinerary text is unchanged also skips the model. Equal hash →
  `skipped_unchanged` unless `force`. Job idempotency key includes the version id, so duplicate enqueues collapse.
- **Concurrency — no starvation of A3 (review, S217/S218 lesson "cap per kind < worker slots",
  `test_aa737_worker_throughput`):** `claim()` is FIFO over all kinds (`ORDER BY run_after, created_at`), and
  today `s1_rewrite 6 + a3_atomize 1 = 7` of 8 slots — exactly one spare. The draft's `2 + 1 + 1` place
  caps would let `6 s1 + 2 place_extract` fill all 8 slots during a wave and starve `a3_atomize` (the S217
  59-minute tail). Fix:
  1. caps 1 / 1 / 1;
  2. new `JobKind.background: bool` (registry); `Worker._fill_slots()` drops background kinds from the caps
     it passes to `claim()` when `max_parallel - len(running) <= BACKGROUND_RESERVE` (= 2). ~10 lines, no SQL
     change; background work can never take the last two slots;
  3. extend `test_aa737`: with every non-background kind at cap except one slot, a3_atomize still has a slot;
     and a background kind is never claimed with ≤ 2 free slots;
  4. backfill refuses during a wave (above).
  Mapbox throttled in-process to 5 req/s. The LLM/Cohere calls run in a worker thread like a3_atomize (S201
  /health starvation).
- **Failure / retry**: `max_attempts=3`, standard backoff; LLM day-extraction failure → rules-only result,
  status `partial` (never fails the tour); Mapbox / locate failure → names stay `pending` with `next_retry_at`
  (1 d), `unknown` after 3 tries (negative cache like `place_card_miss`); `NonRetryable` for "not live".
  Graph build refuses if 0 live sources (TP guard kept). `spend_budget` rows `job:place_extract`,
  `job:place_geocode`, `mapbox` (per run / per day, hard stop) → `stopped_budget`.
- **Deploy gate**: jobs are short and per tour; a 50-tour batch at cap 1 ≈ 20–35 min of gate. The gate
  (`queue.py:415`) counts **every** `queued` job including future `run_after`, so the debounced geocode and
  graph jobs extend it by up to `MAX_WAIT_S` (20 min) after the last tour. Budget ≈ 40–55 min per batch.
- **Observability** (admin, required): `queue.domain_links()` for the three kinds (tour, country);
  new `/admin/places` page — coverage per country (live tours / built / with ≥1 stop per day / in graph),
  pending + unknown + suspect names with a fix-coordinates action, last graph build stats, per-tour rebuild,
  backfill button with dry-run cost. Cost per job from `job.cost_usd` + `llm_call_log.job_id`.
- **Place-card reuse**: when a card exists for the atom, its display name + country is the geocode input and
  its destination is reused (zero calls). Cards are not created by these jobs (keeps AA-712 cost small and
  avoids the card verify queue becoming a blocker).
- **What cards can and cannot replace (review):**
  - *Can*: name normalisation and alias resolution (`atom_group_key`, `place_card_alias`, admin merge of
    duplicates) — when a card exists, `(card_id)` is a better identity than `(name_norm, country)` and the
    `link` stage should prefer it; and the lodging/logistics filter (`card_skip_reason()` — use it as the one
    rule set, as already planned). Card `locality` disambiguates generic names ("Ban Na", "Base Camp") that
    `(name_norm, country)` would wrongly merge (§4).
  - *Cannot*: the day skeleton (overnight town comes from `aa_itineraries`, and cards deliberately skip
    hotels/camps — 02 §2 gap 3); coordinates (cards have none); activity/intensity/season (atoms + rules).
  - *Lever, if the card backfill (Q3) is ever approved*: add `[lat, lng]` to the `a3_place_card` draft output
    and drop the separate `a3_place_locate` call for carded places. Saves ≤ $3 on the catalog — not a reason
    to couple AA-712 to the card backfill.
  - *Lever to measure in the trial*: before calling `a3_place_days`, try a rule from atoms — the town of the
    day's `stay` atom (its place card locality, or the place itself when `card_skip_reason` is not lodging).
    If the trial shows it fills ≥ 50% of the nights the rules miss, the largest cost line halves.

## 4. Geocoding (Mapbox in CIS)
- Secret `aa-cis/dev/mapbox` (acc2), read grant on the **worker** task role (AA-CIS-Infra);
  `shared/secrets.get_mapbox_token()` same shape as DataForSEO. ⚠️ The env-var names contain underscores —
  Nghiệp edits task-def/env names manually in VSCode.
- Method = TP `locate.py` (S202 lesson: Mapbox by name alone is wrong for Asian names): model proposes
  [lat, lng, country] per name (40/call, must return null when unsure) → Mapbox forward with proximity,
  AA ISO filter, types place/locality/district/poi → accept within 25 km (`mapbox`), else keep the model
  point (`llm`, lower confidence).
- **Mapbox terms (review, verified docs.mapbox.com/api/search/geocoding, 14/10/2026):** "Temporary results
  are not allowed to be cached, while Permanent results are allowed to be cached and stored indefinitely."
  Default is Temporary. We store coordinates forever in `shared.destinations`, so **every confirm call must
  use `permanent=true`** (v6) / `mapbox.places-permanent` (v5), which needs a card on file or an enterprise
  contract. Price (mapbox.com/pricing, 14/10): Permanent **$5.00 / 1,000 requests** (the page's free-tier line
  is ambiguous — budget as if there is none). Consequences: (a) the Mapbox line in §8 is no longer $0;
  (b) TP's existing `located_by='mapbox'` rows were stored from Temporary calls → re-confirm them with
  Permanent during the backfill (≈ 1.2k requests, counted in §8); (c) when Mapbox does not confirm, the model
  point (`llm`) is ours and may be stored. If the account cannot enable Permanent, the fallback is "store the
  model point only, use Mapbox Temporary purely as a yes/no check and never persist its coordinates" — ask
  Mapbox/legal before relying on it.
- **Legacy rows (review):** the 1,178 `shared.destinations` rows include `run_deterministic.py` output
  (Mapbox by name only — the source of "Chiang Mai → Roi Et"), rows with `located_by IS NULL` and rows with
  blank `country` (01 §3 legacy). The `link` stage reuses a destination only when `located_by IS NOT NULL`
  **and** `geo_status <> 'suspect'`; everything else goes to `pending` (TP's rule, kept). Migration 226 runs a
  pre-check: blank/NULL `country` rows get `country` from `backfill_country`'s rule (mode of tour countries) or
  are marked `suspect`; the `UNIQUE (name_norm, country)` index is created only after duplicates are resolved
  (NULL country would otherwise bypass uniqueness).
- **Quality guard:** reject non-AA country or coordinates outside the country bbox (hard); country must
  match the model's country (hard). **Outlier check (reworked in review)** — the draft's "> 600 km from the
  day ±1 stops → suspect, excluded from graph views" fires on legitimate flight/sleeper days (Delhi→Leh,
  Hanoi→Hoi An, Bangkok→Chiang Mai ≈ 600–700 km) and is per tour although a destination is shared by many
  tours. New rule: an outlier observation is recorded per (destination, tour, day) and ignored when the day
  text has a transit keyword (`is_transit` rule set: flight/fly/train/sleeper/overnight bus/ferry). A
  destination becomes `suspect` when it is an outlier in ≥ 1 tour **and** `located_by='llm'`, or in ≥ 2 tours
  whatever its source. Suspect = excluded from graph views + listed on `/admin/places` with the tours that
  flagged it. Destinations with `geo_status='manual'` are never overwritten by a job. Relink overwrite of
  coordinates only when the new result is `mapbox` and the old is `llm`, or when an admin forces it.
- **Homonyms (review):** `(name_norm, country)` merges two different villages with the same name in one
  country ("Ban Na" in Laos, "Base Camp" anywhere). For names `is_generic_name()` flags, the key becomes
  `(name_norm, country, locality)` with locality from the place card when present, else the tour's
  overnight town of that day; without either, the name stays `unknown` (no coordinates) rather than borrowing
  another tour's point.
- Cache: `geo.place_name` (name_norm, country) + `shared.destinations` (name_norm, country) — the TP
  `lower(name)` cache is kept, but country-scoped. Geocode once per place, never per tour.
- Rate: Mapbox default limit is ~600 req/min; we send ≤ 5 req/s.
- **Trial acceptance for data quality:** on the trial country, an admin spot-checks 30 random destinations
  on the map (pass = ≤ 1 wrong by > 25 km) before the rest of the country runs.

## 5. Embeddings
New stage `a3_place_embed` → `cohere-embed-v4` (Bedrock acc2, catalog `api_style='embed'`),
`input_type=search_document`, **1536-d** (must equal TP's `tp_search_embed` query vectors), 96 texts per
call, via `shared.llm_client.embed.embed()` (cost-logged; `test_aa685_no_raw_model_calls` stays green).
Embeddings reused by `text_hash`, so reruns of unchanged tours cost nothing. TP keeps `tp_search_embed`
for queries. If either side changes model/dimension, both change in one coordinated pair of PRs.

## 6. TripPlanner changes
1. **Readers → views** behind `PLACES_SOURCE=cis|legacy` (default legacy until the trial country passes):
   browse/tiles, countries, destinations, search, routes; assembly events `_current_components`,
   suggestions, coverage, activities, apply-route, handoff `leg_chain`. Mostly table-name swaps;
   `source_tour_id` → view exposes `tour_id` and `source_id`; RLS `SET LOCAL` no longer needed for views.
2. **Disable writers**: remove extraction ops `tour_days`, `components`, `relink`, `tour_graph`, `prune`
   from `lambda_entry`; delete `invoke_tour_days.py`, `geocode.py` upsert path, `locate.py`,
   `regeocode_outliers.py`, `backfill_*`, `run*.py`; drop Mapbox secret + `tp_extract` grant from the Lambda.
3. **Keep the S236 places fallback** (hotfix branch: "Customise this trip" from `catalog.v_tour_place`,
   offered when it pins ≥ half the days) for tours not yet in the graph, **until `/admin/places` shows
   coverage = 100% of live tours**; then remove it in its own PR.
4. TP migration `tp-0NN` (DRY RUN): map trip_events component ids (§2.4) — **must run in the same step as the
   flag flip, not later** (review): old ids do not exist in the views, so every saved draft loses its pins
   the moment `PLACES_SOURCE=cis`. Shape: `tripplanner.component_id_map(old_id, new_id)` built from
   (tour_id → source_id via `catalog.v_tour`, day, name_norm, activity); `_current_components` resolves
   `COALESCE(map.new_id, event.component_id)`. Rollback to `legacy` keeps working for old pins (tables frozen,
   not dropped); pins made after the flip are lost on rollback (Dev only, accepted).
   After 14 days on views, drop `tripplanner.itinerary_components`, `tour_day`, `tour_stop`, `tour_graph_*`,
   `tour_leg`, `tour_junction`.
5. **Vector search at catalog scale (review):** TP's search/suggestion SQL is a brute-force
   `MIN(embedding <=> q) GROUP BY destination` (§2.5). At ≈ 30–45k components this scans 170–280 MB per
   request on the shared RDS. Before the catalog-wide run (not before the trial), either rewrite to a top-k
   subquery that the HNSW index can serve (`ORDER BY embedding <=> q LIMIT 200` on `geo.tour_place`, then
   group — with `hnsw.ef_search` raised because the liveness join filters rows after the index scan), or add
   a per-destination centroid embedding to `catalog.v_destination`. Measure p95 of `/browse/search` after
   the first country.

## 7. Rollout (PR slices, each verified)

| # | Repo | Slice | Verify |
|---|---|---|---|
| 1 | CIS (+ Infra copy) | Migration 226: `geo` schema + tables, destinations columns + (name_norm,country) key, card→destination FK, stage keys `a3_place_days` (sonnet, luna shadow), `a3_place_locate` (sonnet), `a3_place_embed` (cohere) + `SAFE_DEFAULTS`, spend_budget rows | DB Migrate green; schema ref regenerated; no duplicate (name_norm,country) before the index |
| 2 | Infra | Secret `aa-cis/dev/mapbox`, worker task-role read | `get_mapbox_token()` from ECS exec |
| 3 | CIS | `services/places/` (ported pure modules + TP unit tests), three job kinds, hooks, backfill endpoint, budget | unit + 5 CI jobs; worker claims kinds; deploy api+worker same SHA |
| 4 | CIS (+ Infra copy) | Migration 227 catalog views; contract docs; photo `itinerary_places()` → `geo` | `SELECT` as `tripplanner` role; 225 view tests |
| 5 | CIS | `/admin/places` page + job domain links | aa-ui-verify screenshots |
| 6 | TP | Readers behind flag; writers removed; fallback kept | preview + UI smoke |
| 7 | TP | id-map migration + flag → cis in one window (after the §7 b2 coverage check); drop migration 14 days later | coverage SQL check; live map/suggestions/routes; drafts keep pins |
| 8 | CIS (+ Infra copy) | Migration that drops `destinations_lower_name_uidx` — **only after slice 6 has removed TP's writers** | TP extraction no longer writes `shared.destinations`; DB Migrate green |

**Global `lower(name)` index (build review, finding 1).** TP's live extraction writers upsert
`ON CONFLICT (lower(name))` (`backend/extraction/locate.py` `UPSERT_SQL`, `geocode.py`), so migration 226
**keeps** `destinations_lower_name_uidx` next to the new `(name_norm, country, locality_norm)` key; dropping it
would break every TP extraction run. Until slice 8, CIS's `upsert_destination` stores a second place whose
plain name is taken as `"<name> (<locality|country>)"` (its `name_norm` / key stay the plain name), and adopts
a same-country row TP wrote after 226 without `name_norm`. TP rows written meanwhile stay invisible to the
CIS key lookups until CIS geocodes the same name (then adopted). While TP's writers run, TP's upsert can
still overwrite a CIS row's point by name (`DO UPDATE SET lat/lng…`, admin-fixed rows included) — so the
backfill's real runs (§7 runs b/c) should wait for slice 6's writer removal, or accept that TP may
overwrite until then.

**Runs:** (a) **trial 3 tours** of one country already in the 56-tour set (parity: overnight ids, stop count,
geocode distance vs TP ≤ 25 km, embeddings present, cost/tour; 30-destination spot check §4);
(b) **rest of that country** (≤ 50) → graph build → photo covers → verify the views on Dev (curl as the
`tripplanner` role, `/admin/places` coverage) → **Linear done-when met for the CIS side**;
(b2) **flag flip gate (review — the draft flipped TP after one country, which would have dropped every other
tour of the 56-tour set off the TP map):** flip `PLACES_SOURCE=cis` only when the views cover every
`source_id` the frozen TP tables cover (one SQL check: legacy `source_tour_id` → `source_id`, all present in
`catalog.v_tour_component` and in the current graph build). So build the remaining 56-set tours first
(≤ 50 per batch, ≈ $1–2), then run the id-map migration (§6.4) and flip in the same window; then curl
`/browse/routes`, `/trip/{id}/suggestions`, UI "Customise this trip" on 5 tours. Rollback = flag back to
`legacy` (TP tables frozen, not dropped). No TP downtime: views exist before the TP deploy (slice 4 before
6), the flag is runtime config, and migrations 226/227 are additive (227 must only *append* columns to the
225 views — `CREATE OR REPLACE VIEW` cannot reorder/retype them).
(c) **whole catalog by country, batches ≤ 50**, each batch gated automatically (failed < 5%, suspect names
< 5%, **LLM cost/tour < $0.05; Mapbox tracked on its own budget row**) before the next is enqueued, and only
when no wave is running (§3); report per country (tours / built / in graph / cost). Expect 18–20 batches,
≈ 40–55 min of deploy gate each — run them outside deploy windows.

## 8. Cost estimate — whole catalog (892 live tours)

Prices (`shared.llm_model_catalog`, migrations 169/170): Sonnet 4.6 $3 / $15 per Mtok; Haiku 4.5 $1 / $5;
GPT-5.6 Luna $0.20 / $1.20; Cohere Embed v4 $0.12 per Mtok in.
Shape (schema ref + 01 map): ≈ 12.3 days/tour, ≈ 36 atoms/tour, 30–50 components/tour; TP measured
$0.89 tp_extract for 56 tours (= $0.016/tour incl. locate); ~13 locate calls per 500 names.

| Item | Assumption (per unit) | Units | Cost |
|---|---|---|---|
| Day skeleton `a3_place_days` (Sonnet) | prompt ≈ 3.2k tok in (12.3 days × ≤ 900 chars + instructions) → $0.0096; 0.7–1.2k out (≈ 60 tok/day JSON, longer tours) → $0.011–0.018 → **$0.020–0.028/call** | 892 × 50–100% need the model (TP sample: $0.89/56 tours minus ≈ $0.16 locate ⇒ ≈ $0.013/tour ⇒ ~55% needed it) | **$9–25** |
| Luna shadow 20% on days | (3.2k × $0.20 + 1k × $1.20)/Mtok ≈ $0.0018/call | ≈ 90–180 calls | **≈ $0.3** |
| Locate `a3_place_locate` (Sonnet) | 40 names: ≈ 1k in, 0.6–0.8k out → $0.012–0.015/call | 3k–7k distinct (name, country) + ≈ 1.2k legacy re-locates = 4.2k–8.2k → 105–205 calls | **$1.3–3** |
| Retries, fallbacks, trial + parity reruns | +20% of the LLM lines | — | **$2–6** |
| Cohere embed | 30–50 comps × ≈ 80 tok = 2.4–4k tok/tour at $0.12/Mtok | 2.1–3.6 Mtok | **$0.3–0.5** |
| Mapbox **Permanent** geocoding (§4, required to store) | $5.00 / 1,000 requests, budgeted with no free tier | 4.2k–8.2k requests (new names + re-confirm of TP's Temporary-sourced rows) | **$21–41** |
| Worker time | 20–40 s/tour at **cap 1** → 5–10 h spread over 18–20 batches; geocode ≈ 1 h; graph builds seconds | existing Fargate worker (always on) | **≈ $0–2** marginal |
| **Total AA-712 (core)** | | | **≈ $34–78 → $0.04–0.09 per tour** |
| of which LLM + embed | | | $13–35 ($0.015–0.04/tour) |
| of which Mapbox Permanent | | | $21–41 |
| Optional: place cards for all places (`a3_place_card` Luna + `_check` Haiku ≈ $0.0045/place) | 3k–7k places minus 110 existing | | +$13–31 |

Draft said $14–32: it priced Mapbox at $0 (Temporary geocoding may not be stored — §4) and assumed one
global name per place (the country-scoped key and the legacy re-locate add ≈ 1.2k–2k names).
Biggest uncertainty: the share of tours whose day skeleton needs the model (50–100%) — the trial measures it,
and the atom `stay` rule (§3) or the Luna switch (Q4) can cut that line by half to ~10×.

Steady state (review: split hashes): re-atomize with unchanged itinerary text → $0 for days and embeddings
(text_hash reuse); a new or re-written tour ≈ $0.025 LLM + ≈ $0.005 per genuinely new place (Mapbox).
Budget rows: `job:place_extract` $5/run, $40/day; `job:place_geocode` $3/run; **`mapbox` $25/day, $50 per
backfill**; hard stop on (`stopped_budget`).

## 9. Risks and open questions for Nghiệp

**Decisions (each with a recommendation):**
- **Q1 Table home.** New CIS schema `geo` + `catalog.*` views (rec.) vs CIS writing `tripplanner.*`
  (violates ADR 0001 §6). Record it as **ADR 0006** "Place pipeline data model" (cross-repo).
- **Q2 Destination key.** Change `shared.destinations` uniqueness from global `lower(name)` to
  (name_norm, country). Rec: **yes**, in migration 226 (needs a duplicate check first; ids preserved).
- **Q3 Place cards.** Rec: **use when present (card identity preferred over name), do not build cards in
  AA-712**; card backfill (+$13–31) is a separate T9-quality decision (§3 "What cards can and cannot replace").
- **Q4 Day-skeleton model.** Rec: **Sonnet** (parity with the grounded TP prompt) with GPT-5.6 Luna as 20%
  shadow; switch by migration if shadow parity ≥ 95% (would cut that line ~10×).
- **Q5 Batch gating.** Paid-run rule says ≤ 50 per batch. Rec: **automatic gate between 50-tour batches**
  (thresholds in §7) with a report per country, instead of a manual approval per batch (~18 stops).
- **Q6 Mapbox terms (resolved in review, needs Nghiệp's account action).** Storing results requires
  Permanent geocoding (`permanent=true`; card on file or enterprise contract), $5/1k → $21–41 for the
  backfill, then cents per month. TP's stored rows came from Temporary calls and get re-confirmed. Rec:
  **enable Permanent on the Mapbox account before slice 3**; if that is not possible, decide between the
  "model point only, Mapbox as yes/no check" fallback (legal check) and another geocoder with storage rights.
- **Q7 TP draft pins.** Rec: **map the 51 events to stable ids**, drop unmatched (Dev only).

**Risks:**
- `catalog_owner` dance on view changes (227) — follow the 225 header exactly; test as `tripplanner` role.
- Wrong geocodes poisoning junctions — mitigated by hard country/bbox guard, transit-aware outlier rule,
  generic-name locality key, `suspect` exclusion + admin fix list, and the 30-destination spot check.
- Deploy gate during the catalog run — 40–55 min per batch incl. debounced follow-ups; schedule outside
  deploy windows.
- Slot pressure during S1/A3 waves — fixed by caps 1/1/1 + `background` kinds never taking the last 2 slots
  + backfill refused during a wave (§3); guarded by the extended `test_aa737`.
- Re-upload gap: a "replace" re-upload removes the source from `catalog.v_tour` (and the TP map) until the new
  version publishes — catalog (AA-679) behaviour; raise it there if the gap is too long in practice.
- TP vector search scans all components (§6.5) — must be rewritten or centroid-backed before the catalog run.
- Embedding dimension/model drift between CIS documents and TP queries — pinned to cohere-embed-v4 1536-d.
- Photo matching keyed by `tour_id` (shared.place_photo) — re-uploads still need re-match; out of scope, noted.

---

## Review notes (S236)

Adversarial review against 01/02 maps, ADR 0001–0005, CIS `origin/main` @ 1a10c1c7 (`shared/jobs/queue.py`,
`worker.py`, `registry.py`, `services/jobs/*`, migrations 169/170/173/225), TP @ 6523816
(`extraction/tour_days.py`, `locate.py`, `browse/search.py`, `assembly/suggestions.py`), lessons log
(S217/S218 slot starvation), Mapbox docs + pricing page (14/10/2026). Edited in place:

**Changes**
1. **§2.3 component_id** — removed `destination_id` from the uuid5 input (a pending→resolved name changed the
   id and broke pins); now `(source_id, day, name_norm, country, activity)`; duplicate atoms merge into one
   component (`atom_ids[]`).
2. **§2.3 re-upload** — corrected the claim that the old version stays live: a replace re-upload supersedes
   the old raw row at once and `catalog.v_tour` drops the source until republish (225 l.155). Added persist-time
   liveness re-check under `FOR UPDATE` on `geo.tour_build` (older job cannot overwrite a newer build), views
   join on `source_id` with `built_from_tour_id` / `is_stale` so set-active does not blank a tour.
3. **§2.3 liveness** — graph views also filter on live sources (trashed tour no longer routes until the next
   graph build); `geo.graph_build` keeps current + 2.
4. **§2.5** — HNSW claim corrected: TP search/suggestions are full scans (`MIN(<=>) GROUP BY`); new §6.5.
5. **§3 hashes** — single `input_hash` split into `days_hash` (paid Sonnet stage) and `components_hash`; the
   draft re-paid the day call on every re-atomize wave.
6. **§3 job storm** — geocode's relink is SQL inside the geocode job; no per-tour re-link jobs.
7. **§3 starvation** — caps 2/1/1 → 1/1/1; new `background` flag: worker never gives the last 2 slots to
   place kinds; backfill refuses during a wave; extend `test_aa737`. (Draft: 6 s1 + 2 place = 8 slots → A3
   starved, exact S217 shape; `claim()` is FIFO across kinds.)
8. **§3** — single writer for `shared.destinations` (place_geocode only).
9. **§3 deploy gate** — counts queued jobs with future `run_after`; budget 40–55 min per batch, not 15–25.
10. **§3 place cards** — explicit can/cannot-replace list; two measured levers (card coordinates, `stay`-atom
    rule for overnights).
11. **§4 Mapbox ToS** — Temporary results may not be stored; Permanent (`permanent=true`, $5/1k, card on
    file) is required; TP's stored Mapbox rows re-confirmed. Q6 rewritten.
12. **§4 data quality** — legacy destination rows (unlocated, blank country, Mapbox-by-name) go back to
    `pending`; pre-index cleanup of NULL/blank country; outlier rule made transit-aware and per destination
    across tours (the 600 km rule hit legit flight/sleeper days); generic-name homonyms keyed by locality;
    30-destination spot check in the trial.
13. **§6.4 / §7 cut-over** — flag flip gated on views ⊇ legacy coverage (draft flipped after one country and
    would have dropped the other 56-set tours from TP); id-map migration runs *with* the flip, not later;
    227 appends columns only; rollback path stated.
14. **§6.5** — vector search must be rewritten (top-k HNSW subquery or destination centroid) before the
    catalog run.
15. **§8 cost** — recomputed from code + catalog prices: **$34–78 total ($0.04–0.09/tour)**, of which LLM
    + embed $13–35 and Mapbox Permanent $21–41 (draft $14–32 priced Mapbox at $0). Batch gate threshold now
    LLM cost/tour < $0.05 with a separate `mapbox` budget row ($25/day, $50/backfill).

**Remaining risks**
- Share of tours needing the day model (50–100%) dominates the LLM line; known only after the trial.
- Mapbox Permanent availability on the account (Nghiệp action); fallback has a legal question.
- Re-upload gap in `catalog.v_tour` (AA-679 behaviour) hides a tour from TP for the whole S1 review of
  its new version.
- `(name_norm, country[, locality])` still merges true homonyms without a card or overnight context; they
  stay `unknown` (no point) rather than wrong — coverage < 100% for such places.
- `background` worker reserve is per worker task; with 2 worker tasks during an ECS rollout (AA-711 yields
  the old one) the reserve holds, but a future horizontal scale-out needs it re-checked.
- TP search latency at catalog scale until §6.5 lands; draft pins on days shifted by a re-upload are lost.
- ADR 0006 still to be written (Q1); `PLACES_SOURCE` and Mapbox env names contain underscores — Nghiệp edits
  them by hand in VSCode.
