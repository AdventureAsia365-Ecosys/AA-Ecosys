# AA-990 — countries by ISO 3166, not by a hand-made AA list (design, read-only)

Run 27/10/2026 (S252), Claude Code subagent. No DB, no AWS, no writes outside this file. Code read at AA-CIS-App
`origin/main` c1f896bf and the #1047 branch `fix/aa-990-country-lists` (b9b249f0, worktree `cis-aa990-f3`),
AA-TripPlanner-Web / AA-Booking / AA-Partner `origin/main`, AA-CIS-Infra `origin/main`. Table and column names are
from `docs/architecture/db-schema-reference.md` (Verified 2026-10-26 13:20 UTC, CIS 287).

## 0. Nghiệp's rules (S252, 27/10) this design implements

- (a) **A tour's country is exactly what its raw source says.** The uploaded Excel row's country column (or, only
  when that column is empty, the Excel file it came from). It is never re-labelled from the itinerary.
- (b) **No hand-made "AA country" list restricts anything.** Every ISO 3166-1 country is valid.
- (c) **Each place gets its own real country from geocoding.** A tour sold as India can visit Kilimanjaro (Tanzania),
  and a Thailand tour can visit Cambodia. A place whose country differs from its tour's country is a normal
  cross-border stop, not an error.

Input given by the orchestrator (not re-checked here: no S3 or DB access): the two Kilimanjaro treks (tours
489079d3…, fbe37dd2…) come from raw-inbox `INDIA.xlsx`, sheet "Tour Data", rows 160 and 168, provider Adventure
Nation (an Indian operator), country column `INDIA`. **`raw_tours.country = 'India'` is correct and stays.** The
raw Excel row is also kept verbatim in `raw_tours.raw_data` (the parser stores `row.to_dict()`).

## 1. Where the hand list lives today (every consumer)

| # | Where | What it does with the list | Effect for a non-list country (Tanzania, Russia, Kazakhstan…) |
|---|---|---|---|
| 1 | DB `silver_aa_internal.raw_tours` CHECK `chk_raw_tours_country` (150 → 197 → 281's Dev form) | 20 names allowed | INSERT fails; S0 cannot store a tour whose source says Singapore / Maldives / Tibet, although S0's own resolver emits these three |
| 2 | `shared/country_resolver.py` `COUNTRY_MASTER` (S0) | 21 names + spellings. **Falls back to the FILE NAME when the column value is unknown** | A row whose column says "TANZANIA" in `INDIA.xlsx` becomes India, which breaks rule (a). An unknown name in a file with no country name becomes NULL + `country_raw_unresolved` |
| 3 | `services/ingestion/jev_gates.py` + `shared.decision_question` row `a0_country` (mig 183) | Jev "choice" over 21 names + `other`. It fills the country only when the column is empty (enforce mode) | Guesses a country the source never stated (rule a). The list holds `Tibet`, which the CHECK refuses |
| 4 | `services/places/guards.py` `COUNTRY_ISO2` / `ISO2_COUNTRY` / `ISO2_ISO3` / `BBOX` / `AA_ISO2` / `_ALIASES` (20 after #1047) | `canonical_country()` returns None outside the list. `point_ok()` → `not_aa_country` | **This is the root cause for places.** In `locate.parse_answer` the model's correct answer `[-3.07, 37.35, "Tanzania"]` becomes None (`unknown_to_model`). After 3 tries the name is `unknown`. No `shared.destinations` row, no component, no stop, no map |
| 5 | `services/places/geocoder.py` (`countrycode:` filter, `ISO2_COUNTRY.get(...)` on the accepted candidate) | Geoapify is filtered by the model's country. A candidate outside the list is skipped | Same as 4 |
| 6 | `services/places/shape.py` + `geodata/country_polygons.json` (Natural Earth 10m, 20 countries, 528 KB) + `scripts/aa847_country_polygons.py` (literal `ISO3_ISO2`) | Line clipping ("≈ n km in Laos"), `anchored_line` filtering | `in_country()` returns False for an unknown country, so a river or trail in Tanzania is never drawn |
| 7 | `services/places/locate.py` | `NATIVE_NAME_COUNTRIES` (TW, KR). Prompt already says "a Thailand tour may sleep in Siem Reap, Cambodia" | The design already intends cross-border; only the guard blocks it |
| 8 | `services/places/dedupe.py` `COUNTRY_WORDS` | Removes country words from names ("Badshahi Mosque Pakistan") | Heuristic only, not a gate |
| 9 | `services/acp_shared/place_cards.py` | The card's country is the model's free text, never normalised | Source of the compound strings ("India and Pakistan", "Nepal and China", "Pakistan, India, China"). They flow into `geo.tour_place.country` / `geo.place_name.country` and `catalog.v_tour_place.country` |
| 10 | `services/catalog_http/geo.py` (`_EXTRA_ISO2` neighbours, `_ZONE`) | ISO code and IANA zone per place, for catalog.http.v1 (CRM) | Tanzania → no code → the day falls back to the tour's zone (Asia/Kolkata for a Kilimanjaro day) |
| 11 | `services/aa_content/validate.py` `AA_COUNTRY_CODES` + `frontend/lib/aaContent.ts` `AA_COUNTRIES` (mirror test `test_aa977_editor_mirror.py`) | `applies_to.country_codes` must be one of the 20 | The contract (`catalog.http.v1.openapi.yaml` AaContent.applies_to) allows any `^[A-Z]{2}$`. The code is stricter than the contract |
| 12 | `services/seo_intelligence/seed_builder.py` `_country_words()` / `foreign_country()`, `foreign_places()` / `names_foreign_place()`; `services/content_generation/seo_meta_utils.py` `_countries_named()` | Keyword filter (drop keywords that name "another country" or another country's place); meta tail ", in India." | For the Kilimanjaro trek, "kilimanjaro …" keywords would be dropped as foreign once Kilimanjaro is a Tanzania destination. The meta could gain ", over 7 days in India." because Tanzania is not a known country word |
| 13 | `services/content_generation/s1_writer_v2.py` (`COUNTRY:` in the fact sheet, at-a-glance `Destination: <country>`, meta prompt `Country:`) | Shows the source country as the destination | "Destination: India" on a Kilimanjaro page: the content is untrue for the tour |
| 14 | `services/seo_intelligence/seed_builder.py` `DFS_LOCATION_MAP` / `LOCATION_CODE_TO_MARKET` / `MARKET_RANK` (used by s1_prefetch, segment_research(_batch), acp_shared/slate, admin_tenant360) | **Buyer markets** (US, UK, AU, DE, FR, NL: where searchers are), not tour countries | Unrelated to tour/place countries. Stays (§5) |
| 15 | Catalog views: `catalog.v_tour_place.country = COALESCE(place_card.country, tour country)` (256); `catalog.v_tour_component.country = geo.tour_place.country` (256) | Shown to TripPlanner, Booking, CRM | A Kilimanjaro place with no card shows country **India** with Tanzanian lat/lng. A compound card country is shown verbatim, and 256's legacy name+country match never hits it |
| 16 | TripPlanner `frontend/lib/types.ts` `COUNTRY_ISO` (18 names), `COUNTRY_BBOX`, `COUNTRY_GATEWAY`; `backend/browse/countries.py` | Map highlight / zoom / gateways by name. The country list is the countries of **places** | Tanzania gets no highlight or zoom. It does appear in the country list once it has components (by design: F3 note) |
| 17 | Booking `booking.countries` (bk-005, "markets we sell", `active`) used by trip-case countries | Booking's own market list | Out of scope. It is a sales decision, not a geography list (§5) |
| 18 | AA-Partner (CRM) | Reads catalog.http.v1 only. No list | Follows 10 |

`shared.countries` (CIS 279): 249 rows (Debian iso-codes 4.16.0), PK `iso2`, UNIQUE `iso3`, `numeric_code`, `name`
(common English name: 'Vietnam', 'South Korea', 'Laos', 'Taiwan', 'Tanzania', 'North Korea', 'Russian Federation',
'Türkiye'), `iso_name`, `aliases text[]` (lower-case: official names, 'russia', 'turkey', 'tibet' → CN, the
guards `_ALIASES`). Resolver `shared.country_iso2(text)` (STABLE, SQL). `raw_tours.country_iso2` and
`shared.destinations.country_iso2` (FK, trigger `shared.set_country_iso2()`) already exist, and so does
`shared.v_country_unmapped`. All 20 names of `chk_raw_tours_country` are exact `shared.countries.name` values
(checked against 279's VALUES). Of the place-name countries seen on Dev, 'Tanzania', 'Kazakhstan', 'North Korea',
'Bangladesh' and 'Cambodia' are names, 'Russia' is an alias (→ RU, name 'Russian Federation'), and the compounds
resolve to nothing.

## 2. Design

### 2.1 One source: `shared.countries`, with a generated in-code mirror

- **New module `shared/countries/`** (in `shared/` so that S0 `shared/country_resolver.py`, `services/places` and
  `services/catalog_http` all import it), with **`shared/countries/data/countries.json`** generated, never edited
  by hand. One entry per ISO row: `iso2, iso3, numeric, name, iso_name, aliases[]`, plus derived fields
  `bbox` ([min_lat, max_lat, min_lng, max_lng] from the Natural Earth polygon, ±0.3° like today's BBOX, or null
  when NE has no polygon) and `zones` (IANA zones of the country with reference coordinates, from tzdata
  `zone1970.tab`/`zone.tab`, baked in at build time). Size ≈ 60–80 KB.
  API: `resolve(text) -> Country | None` (same matching as `shared.country_iso2`: case- and space-insensitive on
  name, iso_name, alias, iso2, iso3), `by_iso2()`, `name(iso2)`, `all()`.
- **Generator `scripts/aa990_country_data.py`** (offline, `python3 -I`, no network in the script), which replaces
  the literal list in `scripts/aa847_country_polygons.py`:
  1. reads the ISO rows from the migrations that write `shared.countries` (279's VALUES + 288's alias additions,
     §2.2), so the mirror equals what the DB replay produces;
  2. reads Natural Earth 10m admin-0 v5.1.2 (same source as AA-847), keyed by `ISO_A2_EH` → `ISO_A2` → `WB_A2`;
  3. writes `countries.json` and **`services/places/geodata/country_polygons.json` for every ISO country**.
- **Polygon size budget, measured on NE 10m v5.1.2** (238 of the 249 ISO codes have a feature):

  | Douglas-Peucker tolerance | raw | gzip | biggest |
  |---|---|---|---|
  | 0.01° (today's, ≈ 1 km) | 3.55 MB | 1.22 MB | CA 546 KB, RU 303 KB, US 263 KB, AQ 226 KB |
  | 0.02° | 2.20 MB | 0.77 MB | |
  | 0.05° | 1.02 MB | 0.37 MB | |

  Recommendation: **keep 0.01° for every country** (no AA tier, rule b). Budget ≤ 4 MB raw, pinned by a test.
  Memory matters more than disk: parsing 3.5 MB of nested arrays builds ~50 MB of Python lists, and
  `shape._countries()` builds edge bands for every country at once. Store **each country's rings as one JSON
  string** (`{"countries": {"tz": "[[[...]]]", ...}}`). The outer parse is then ~4 MB of strings, and
  `shape._country(iso2)` (lru_cache per code) does `json.loads` and the band index only for the countries a run
  touches.
- **Gaps and disputed areas** in NE: 11 ISO codes have no admin-0 feature (BQ BV CC CX GF GP MQ RE SJ TK YT: they
  are inside FR/NL/NO/AU/NZ). Take them from NE `admin_0_map_units` when available, otherwise list them in the
  drift test as known gaps (test data, not runtime code). Unassigned NE features: fold `Siachen Glacier` into both
  `in` and `pk` (it lies between the AA trekking areas of Ladakh and Baltistan), and skip the rest (XK, Spratly,
  Scarborough, Bir Tawil…). Antimeridian countries (RU, US, FJ, KI, NZ) get a bbox spanning ±180°. That is a
  loose but harmless hard guard, and the polygon stays exact.
- **Drift tests**:
  - Unit, no DB: the JSON equals the rows parsed from the migrations; every lookup key names one country (279's
    guard 2 rule); every name from `chk_raw_tours_country`'s history and every Dev spelling seen
    ('Russia', 'Tanzania', 'Kazakhstan', 'North Korea', 'Bangladesh', 'Cambodia', 'Tibet', 'Okinawa',
    'SRI-LANDKA') resolves; every ISO code with a polygon has a bbox; the file stays under budget; every zone
    exists in tzdata.
  - Integration (conftest replay applies 279 part A and 288): `SELECT iso2, iso3, numeric_code, name, iso_name,
    aliases FROM shared.countries` equals the JSON, and for every lookup key `shared.country_iso2(key)` equals
    `resolve(key).iso2`. This replaces the tie that `test_aa851_migration_279` pins today between the guards
    `_ALIASES` and the DB aliases.
- **`services/places/guards.py`** keeps its public names, which become views of the mirror:
  `canonical_country(name)` → ISO common name or None, `iso2(name)`, `country_spellings(code)`, `in_country` /
  `point_ok` (bbox from `countries.json`). `COUNTRY_ISO2`/`ISO2_COUNTRY`/`ISO2_ISO3`/`BBOX` stay derived from
  the mirror for the few importers, and `AA_ISO2` is removed. The `point_ok` reason `not_aa_country` becomes
  `unknown_country` (only for text that names no ISO country). The hard guards stay as they are: inside the
  country's bbox, and a confirming geocoder result must be in the model's country.

### 2.2 The raw_tours constraint: FK on the canonical name (migration 288)

Options weighed:

| Option | Verdict |
|---|---|
| A. `FOREIGN KEY (country) REFERENCES shared.countries (name)` | **Chosen.** Declarative and reviewable. Enforces both "a real ISO country" and "the one canonical spelling" (no 'INDIA' / 'india' / 'Viet Nam' in the display column). `countries_name_key` is already a UNIQUE constraint, and `idx_aa_internal_raw_tours_country` already indexes the referencing side. 279's `raw_tours_country_iso2_fkey` proves the RI-as-owner path works on this FORCE-RLS table |
| B. `CHECK (country IS NULL OR country_iso2 IS NOT NULL)` (rely on the trigger) | Accepts aliases and any casing in the display column. The truth would hang on a trigger |
| C. CHECK calling a function that reads `shared.countries` "declared IMMUTABLE" | Rejected: a false IMMUTABLE breaks dump/restore and is not re-checked when the table changes |
| D. Composite FK `(country, country_iso2) → (name, iso2)` | Stricter (name and code always agree), but it breaks 279's documented "explicit country_iso2 is a manual override" path and needs a new UNIQUE on `shared.countries`. Not now |

**288 (`api/migrations/288_raw_tours_country_iso.sql`, cis_owner, one BEGIN … COMMIT, lock_timeout 5s,
self-registers `'288'` in `shared.schema_versions`):**
1. Guard before: `shared.countries` has 249 rows; every non-NULL `raw_tours.country` is a `shared.countries.name`
   (RAISE listing the offending values otherwise; expected none, because the old CHECK only allowed 20 names that
   are all names); no row has `country IS NOT NULL AND country_iso2 IS NULL`.
2. Aliases: `UPDATE shared.countries SET aliases = <sorted distinct union>` for the S0 spellings that
   `shared/country_resolver.py` knows and the table lacks (for example 'japanese', 'thai', 'khmer', 'bali',
   'phil', 'prc', 'srilanka', 'sri landka'; the generator lists the exact delta). Re-run 279's guard 2 (each key
   names one country).
3. `ALTER TABLE silver_aa_internal.raw_tours ADD CONSTRAINT raw_tours_country_fkey FOREIGN KEY (country)
   REFERENCES shared.countries (name) NOT VALID;` then `VALIDATE CONSTRAINT` (~1k rows).
4. `ADD CONSTRAINT raw_tours_country_iso2_set CHECK ((country IS NULL) = (country_iso2 IS NULL)) NOT VALID;`
   then `VALIDATE` (the trigger fills `country_iso2` before the check runs).
5. `ALTER TABLE … DROP CONSTRAINT IF EXISTS chk_raw_tours_country;`
6. Guard after: both new constraints exist and are validated, `chk_raw_tours_country` is gone, the trigger
   `raw_tours_country_iso2` is still present. NOTICE the count of rows per country.

Locks: SHARE ROW EXCLUSIVE on `shared.countries` and `raw_tours` for the FK, ACCESS EXCLUSIVE on `raw_tours` for the
DROP. Seconds. Apply with the job tables idle (DM-11.4). Byte copy to AA-CIS-Infra `db/migrations/cis/288_…`.
Rollback = a new forward migration that re-adds the 20-name CHECK `NOT VALID` and drops the FK and the CHECK (only
valid while no row holds a 21st country). There is no ERD design page for `silver_aa_internal` or `shared` (only
crm and tripplanner are enforced), so the root design ERD needs no edit. `schema-ownership.md` (row `countries`)
gets one line: "raw_tours.country is FK to countries.name (CIS 288)".

**S0 changes** (merge only **after** 288 is applied: new values may not reach a constrained column before the
constraint allows them):
- `shared/country_resolver.resolve_country(raw, filename)` resolves through `shared/countries` (all ISO, plus the
  S0 spellings, which now live in the DB aliases). Rule (a) order:
  1. the column value resolves to one country → that country's canonical `name`;
  2. **the column is empty** → the file name (`INDIA.xlsx` → India, longest match first, as today);
  3. the column is present but unresolvable: if it is a compound ("India & Nepal") and one of its parts is the
     file's country, take that; else NULL + `country_raw_unresolved` (existing AA-571 path, visible on the
     data-coverage page). **Never** the file name over an explicit, different column value.
  - 'Tibet' → China, as 279 already maps it (ISO has no Tibet). The verbatim value stays in `raw_data`.
  - `COUNTRY_MASTER` is kept only as a generated view for `seo_meta_utils` / `seed_builder` callers, or those
    switch to `shared.countries` (§2.6). The unused `excel_parser._COUNTRY_KEYWORDS` /
    `detect_country_from_filename` are removed.
- `jev_gates` `a0_country`: the source gave no country (empty column and no file-name country), so a Jev guess is
  not "what the source says". Keep the question **shadow-only** (a note in the preview). In `handler.py`, a Jev
  pick is never written to `country`. No migration is needed (mode lives on `/admin/decisions`). The 21-name
  criteria text in `shared.decision_question` stays as it is (a preview hint, not a gate).
- `near_duplicate` compares `country` strings, which are now always canonical: no change.

### 2.3 Compound strings at place level

Rule: **a compound is never stored as a country. A place's country is decided where the place is located.**
- Where they come from: the place-card model (`place_cards.build_card_for_group`: `country = card["country"]` or the
  tour country, free text).
- New cards: a `normalise_card_country(raw, tour_country)` in `place_cards.py`:
  - resolve the whole text;
  - else split on `,` `/` `&` `;` ` and ` ` or ` (never on `-`: Timor-Leste, Guinea-Bissau) and resolve each part;
    when several parts resolve, take the tour's country if it is one of them, else the first;
  - nothing resolves → the tour's country (today's fallback).
  Store the canonical ISO name. This is code only. **Do not change `_CARD_SYSTEM` / `_CHECK_SYSTEM`**: a prompt
  change rotates `PROMPT_SHA`, which invalidates every stored miss and pays for re-drafts.
- Existing cards / components / place names that carry a compound keep it **as part of their identity key**
  (`place_card.place_key`, `place_card_alias.country_norm`, `geo.place_name` PK, `geo.tour_place.country_norm`,
  and the `component_id` uuid5 input). Rewriting those keys would orphan TripPlanner pins and redirects (AA-989).
  The compound is harmless there. In `geocode_pending` it only reaches the model as the hint "tour country: India
  and Pakistan". The model returns the place's real country, and `upsert_destination` writes
  `shared.destinations.country = located.country` (already so in `store.py`). With §2.1 that answer is accepted
  for any ISO country.
- What consumers see: migration **289** makes the place-level catalog views show the **destination's** country
  when the place is linked (§2.4). A compound or a wrong tour country then never reaches TripPlanner, Booking or
  CRM for a located place.

### 2.4 Kilimanjaro: no country change; its places become Tanzanian places of an India tour

Nothing touches `raw_tours` for tours 489079d3… / fbe37dd2…. What changes is that their places get located:

1. After the code change (§2.1), `locate.parse_answer` keeps `[lat, lng, "Tanzania"]`. `point_ok` checks
   Tanzania's bbox. Geoapify searches with `countrycode:tz` and confirms Kilimanjaro / Moshi / Arusha / Machame
   Gate. `geocoder.confirm` maps `tz` → 'Tanzania'. `upsert_destination` writes a `shared.destinations` row with
   country 'Tanzania' (the trigger sets `country_iso2 = 'TZ'`). `relink` links `geo.tour_place` and the overnight
   anchors of `geo.tour_day` (keyed by the tour country 'india', which is fine: the key is identity, the
   destination is truth). `place_geocode` re-enqueues `tour_graph_build`.
2. These names are now `unknown` (3 tries) or `pending` with `last_error` `unknown_to_model`. They need **one
   reset** (no code path re-opens an `unknown` name): an ECS-exec script as `cis_app` (UPDATE on `geo.place_name`
   is granted) that sets `status='pending', tries=0, next_retry_at=now(), last_error=NULL`. First the keys of these
   two sources (via `geo.tour_place` and `geo.tour_day` anchors, see Q3), then one `place_geocode`. Then, as a
   second tranche, every name with `last_error IN ('unknown_to_model', 'not_aa_country', 'outside_country_bbox')`
   (Q2 sizes it; ≈ $0.015 per 40 names for the model plus Geoapify credits, 2,500/day). Paid-runs rule: the two
   tours first, then ≤ 50 tours' worth, then the rest. A follow-up worth having is an admin "retry unknown names"
   action on `/admin/places` (observability-UI rule), so this is not an ECS-exec habit.
3. The graph (`graph.py`) already handles cross-border: `countries` per leg and `cross = country_a != country_b`.
   TripPlanner's tour-route then shows the Tanzanian stops for an India-sold tour. The planner country list gains
   'Tanzania' (it lists the countries of **places**, by design, see the F3 note), while the catalogue still lists the
   tour under India (`v_tour.country`, rule a).
4. Content truth (Nghiệp: "tour nào thì ghi đúng nội dung của tour"). The source country must not be written as
   the place where the tour happens:
   - `s1_writer_v2.at_a_glance`: the `Destination:` line shows the source country only when the source text does
     not name a different ISO country without naming the source country; otherwise it lists the countries the source
     names (Kilimanjaro trek → "Destination: Tanzania"). The fact-sheet label becomes `COUNTRY (as the source file
     lists it; the route may be in other countries)`.
   - `seo_meta_utils._countries_named` recognises every ISO name/alias, so a meta that names Tanzania never gets
     ", in India.".
   - `seed_builder.names_foreign_place`: the tour's own title place terms and the tour's own destinations are never
     "foreign" (otherwise "kilimanjaro trek" is dropped for this tour).
   - Q5 checks whether the two published Masters already say India somewhere. If they do, it is a content fix
     (re-run S1 for these 2 tours), not a data relabel.

**289 (`api/migrations/289_catalog_place_country_from_destination.sql`, catalog-view recipe, as catalog_owner):**
`CREATE OR REPLACE VIEW catalog.v_tour_place` (256's statement) with
`COALESCE(d_country, pc.country, g.tour_country) AS country`. The `d` lateral gains `dd.country`, and the column
keeps its name, position and type `text`. `catalog.v_tour_component` (256/258's statement) gets `d.country AS country`
instead of `gp.country` (the view inner-joins `shared.destinations` already). Same rows, grants unchanged. Closing
check as catalog_owner (`LIMIT 1`). Contracts: a description note in `catalog.tour.v1.3` / `catalog.graph.v1.2`
("places[].country / component country = the located destination's country when linked"; additive semantics, no
shape change). `catalog_http.mapping._place` then gets 'Tanzania' → `TZ` → `Africa/Dar_es_Salaam` (§2.5).

### 2.5 Other code switched to the mirror

- `services/catalog_http/geo.py`: `_EXTRA_ISO2` is dropped (every ISO name resolves). `time_zone(code, lng, lat)`
  keeps the hand-tuned ID / MY / MN splits and the explicit `_ZONE` for the AA-heavy countries. For any other
  country it returns its single zone, or, for a multi-zone country, the zone in `countries.json` whose reference
  point is nearest to (lat, lng). `all_zones()` covers them, and the test checks that each exists in tzdata.
- `services/aa_content/validate.py`: `COUNTRY_CODES` = every ISO2 in the mirror (the contract already allows any
  `^[A-Z]{2}$`). The error stays `invalid_country_code`.
- `frontend/lib/aaContent.ts`: `AA_COUNTRIES` → generated `frontend/lib/countries.generated.ts` (iso2 → name, ~6 KB,
  emitted by the generator). The picker lists all countries sorted by name, as a searchable select (249 options).
  `test_aa977_editor_mirror.py` compares the generated TS with the mirror.
- `services/places/shape.py`: lazy per-country parse (§2.1). `country_isos()` returns every code with a polygon.
- `services/places/dedupe.py` `COUNTRY_WORDS`: **unchanged** in this slice. Widening it to all ISO names would
  strip real words ("Jordan", "Georgia", "Chad", "Turkey") from place names and shift dedupe cores. Revisit
  with data.

### 2.6 What legitimately stays AA-specific (do not break)

| Item | Why it stays |
|---|---|
| `DFS_LOCATION_MAP`, `LOCATION_CODE_TO_MARKET`, `MARKET_RANK`, `_DEFAULT_MARKET`, `resolve_buyer_market(s)` (SEO, segment research, slate, tenant 360) | **Buyer markets** (where searchers are: US/UK/AU/DE/FR/NL), a commercial choice. Not a geography list |
| `seed_builder.COUNTRY_NORMALIZE` / `detect_region_landmark` (SEO seed display text) | Seed wording; an unmapped country falls back to its own name |
| `booking.countries` (bk-005, `active`) and the trip-case country picker | Booking's own sales-market list, same iso2 keys (279 note). A Tanzania trip case is a Booking product question (flag, not in this change) |
| `geo.place_dedupe_country` (mode `apply` per country) | An approval gate per country for automatic merges. A new country (TZ) runs dry until approved. That is the intended behaviour |
| Brand content rules (forbidden words, tone, CTA, elephant-riding policy), `NATIVE_NAME_COUNTRIES` (TW, KR native-script retry), the ID / MY / MN time-zone splits, TripPlanner `COUNTRY_GATEWAY` | Rules or data tuned for specific countries, not allow-lists. They add behaviour for those countries and block nothing for others |
| `a0_country` Jev criteria (21 names) | Shadow hint only after §2.2 |

## 3. Risks

1. **Wrong-country acceptance.** Widening the guard lets a model mistake through ("Pokhara" placed in another
   country). Mitigations stay: bbox of the claimed country, the geocoder must agree on the country, the 600 km
   outlier rule → `suspect`, and model-only points are `area` precision. Watch: count of destinations whose
   country ≠ tour country after the reset tranche (Q6), reviewed by hand for the first tranche.
2. **Memory.** All-country polygons are parsed lazily (§2.1). Measure RSS of a `place_shape` run before/after.
3. **Order of deploy.** 288 must be applied before the S0 change ships. The places/guards change does not depend
   on 288 (`shared.destinations.country` has no CHECK; its trigger resolves any ISO name).
4. **Card normalisation** only affects new cards. Old compound keys stay (by design). 289 hides them from
   consumers once linked. An unlinked place still shows the card's compound text in `v_tour_place`.
5. **Display names.** ISO common names differ from colloquial ones for a few countries ('Russian Federation',
   'Türkiye', 'Iran', 'Syria'). The aliases resolve the colloquial spellings, and the stored name is ISO's.
   Accept, or change `name` by a later migration (FK `NO ACTION` would then need an UPDATE path; none of these are
   tour countries today).
6. **SEO filters widen.** ISO-wide country words can flag a keyword like "turkey dinner" as foreign. Add a small
   ambiguity denylist (turkey, chad, jordan, georgia, jersey, guinea, niger, mali, oman) in `_country_words` /
   `_countries_named`. Low impact: it only drops a keyword or a meta tail.
7. **Tests that pin the 20-name list** must be rewritten, not deleted: `test_aa990_country_lists.py` (parses the
   latest `chk_raw_tours_country`), `test_aa712_place_pipeline::test_guard_countries_cover_every_raw_tours_country`
   (reads 150), `test_aa977_editor_mirror.py`, `test_aa976_catalog_http.py`, `test_aa313_…`, `test_aa571_…`,
   `test_aa851_migration_279.py` (alias tie). `test_aa853_migration_281.py` already tolerates a missing
   `chk_raw_tours_country` (`if row:`).
8. **#1047** (PK/PH, 20-country lists + drift test) merges first as planned. This design replaces its lists with
   the mirror on top of that branch. The PK/PH bboxes and polygons are reproduced by the generator.

## 4. Exact file list

AA-CIS-App, PR 1 "places & lists from shared.countries" (no DB dependency):
- new `shared/countries/__init__.py`, `shared/countries/data/countries.json` (generated)
- new `scripts/aa990_country_data.py`; `scripts/aa847_country_polygons.py` (no literal list; all ISO; string-per-country; Siachen fold)
- `services/places/geodata/country_polygons.json` (regenerated, ≤ 4 MB)
- `services/places/guards.py`, `services/places/shape.py`, `services/places/locate.py` (docstring, reason name), `services/places/geocoder.py` (no logic change beyond the mirror)
- `services/acp_shared/place_cards.py` (`normalise_card_country`)
- `services/catalog_http/geo.py`
- `services/aa_content/validate.py`; `frontend/lib/aaContent.ts`, new `frontend/lib/countries.generated.ts`, `frontend/app/admin/aa-content/AaContentEditor.tsx`, `AaContentConsole.tsx` (name lookup)
- `services/content_generation/s1_writer_v2.py` (at-a-glance / label), `services/content_generation/seo_meta_utils.py`, `services/seo_intelligence/seed_builder.py` (country words, own-places rule)
- tests: rewrite `tests/unit/test_aa990_country_lists.py`; new `tests/unit/test_aa990_country_mirror.py`; update `test_aa712_place_pipeline.py`, `test_aa977_editor_mirror.py`, `test_aa976_catalog_http.py`, `test_aa712_geoapify.py`, `test_aa847_shape.py` (country set)
- `CONTEXT.md` (Countries section: the mirror, the place-country rule (c); places guard wording "ISO country", not "AA country"); `docs/implementation-notes/AA-990.md`

AA-CIS-App, PR 2 "raw_tours country = any ISO country" (merge after 288 is applied on Dev):
- `api/migrations/288_raw_tours_country_iso.sql`
- `shared/country_resolver.py`, `services/ingestion/excel_parser.py`, `services/ingestion/handler.py`
- tests: new `tests/integration/test_aa990_migration_288.py` (+ the DB drift test), update `test_aa313_country_resolver_pakistan_srilanka.py`, `test_aa571_country_validation.py`, `test_aa851_migration_279.py`

AA-CIS-App, PR 3 "place country from the destination" (migration only):
- `api/migrations/289_catalog_place_country_from_destination.sql`, `tests/integration/test_aa990_migration_289.py`

AA-CIS-Infra: `db/migrations/cis/288_raw_tours_country_iso.sql`, `db/migrations/cis/289_catalog_place_country_from_destination.sql` (byte copies).

Root AA-Ecosys: `docs/database/schema-ownership.md` (countries / raw_tours line), `docs/contracts/catalog.tour.v1.3.json` + `catalog.graph.v1.2.json` (description note), `docs/architecture/db-schema-reference.md` (bot PR after apply), this audit folder.

AA-TripPlanner-Web, follow-up PR: `frontend/lib/types.ts` (`COUNTRY_ISO` / `COUNTRY_BBOX` → `catalog.v_country` + the
country's destinations bbox via `v_destination.country_iso2`, already granted), `frontend/components/MapView.tsx`.

Ops after PR 1 deploy: the place-name reset (§2.4 step 2), two tours first.

## 5. Migration numbers

Highest on AA-CIS-App `origin/main` and every remote branch: **287** (`287_writing_memory_release.sql`). AA-CIS-Infra
`db/migrations/cis/` main and open PRs (#411, #412 are dependabot): **287**. Open CIS PRs #1047 and #1048 carry no
migration. → **288** (raw_tours FK + aliases), **289** (catalog place-country views). Re-check both repos right
before opening the PRs: parallel lanes (AA-682 is Booking `bk-026`, not CIS) can take a number.

## 6. Read-only queries for the orchestrator (as `cis_app`, S3-mediated ECS exec)

```sql
-- Q1 place-name countries that resolve to no ISO country (compounds etc.)
SELECT country, status, last_error, count(*) FROM geo.place_name
 WHERE shared.country_iso2(country) IS NULL GROUP BY 1, 2, 3 ORDER BY 4 DESC;
-- Q2 size of the reset tranche
SELECT status, last_error, count(*) FROM geo.place_name
 WHERE status IN ('pending', 'unknown') GROUP BY 1, 2 ORDER BY 3 DESC;
-- Q3 the Kilimanjaro tours' names (components + overnight anchors)
SELECT pn.name_norm, pn.country, pn.status, pn.tries, pn.last_error
  FROM geo.place_name pn
 WHERE (pn.name_norm, pn.country_norm, pn.locality_norm) IN (
       SELECT tp.name_norm, tp.country_norm, tp.locality_norm FROM geo.tour_place tp
        WHERE tp.tour_id IN (<489079d3… full uuid>, <fbe37dd2… full uuid>)
       UNION SELECT td.anchor_norm, td.anchor_country_norm, td.anchor_locality_norm FROM geo.tour_day td
        WHERE td.tour_id IN (<…>, <…>) AND td.anchor_norm IS NOT NULL);
-- Q4 compound / unresolvable place-card countries
SELECT country, count(*) FROM acp_shared.place_card
 WHERE shared.country_iso2(country) IS NULL GROUP BY 1 ORDER BY 2 DESC;
-- Q5 does the published Master of the two tours call the trek Indian?
SELECT tour_id, aa_name, seo_meta, position('India' IN coalesce(aa_summary, '') || coalesce(aa_itineraries, '')) > 0 AS says_india
  FROM gold_aa_internal.published_tours WHERE tour_id IN (<…>, <…>);
-- Q6 (after the reset) cross-border destinations per tour country
SELECT rt.country AS tour_country, d.country AS place_country, count(DISTINCT d.id)
  FROM geo.tour_place tp JOIN shared.destinations d ON d.id = tp.destination_id
  JOIN silver_aa_internal.raw_tours rt ON rt.tour_id = tp.tour_id
 WHERE d.country_iso2 IS DISTINCT FROM rt.country_iso2 GROUP BY 1, 2 ORDER BY 3 DESC;
```

`raw_tours` is FORCE RLS but has `raw_tours_cis_app_all` (USING true) for `cis_app`. If Q5 returns no rows, set
`app.tenant_id` to the AA tenant first (as the catalog reads do) and run it again.
