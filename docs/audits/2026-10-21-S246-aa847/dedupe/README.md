# AA-847 Problem 2 — automatic duplicate-place merge (design, S246)

Agent: Claude Code (subagent, design only). Owner decision S246 (2): duplicate places are merged **automatically and
correctly**; an admin merging by hand is not the normal path. Decision S246 (1) (linear places are drawn, not hidden)
means rivers, roads and trekking stretches take part in the dedupe too.

| File | What |
|---|---|
| `dedupe_proto.py` | Executable spec of the deterministic part (rules r1.2): `decide(a, b)` → `auto_merge` / `llm` / `keep`, and the evaluation on the pair set. No I/O, no model call. Port target: AA-CIS-App `services/places/dedupe.py`. |
| `pairs.json` | 105 labelled pairs (55 merge / 50 keep): the 22 pairs pinned in CIS `tests/unit/test_aa847_validity.py`, the 4 brief cases, 79 constructed from real places of AA countries. |
| `eval-r1.2.txt` | `python3 -I dedupe_proto.py pairs.json` (every pair, summary). |
| `eval-r1.2-degraded.txt` | The same pairs with less metadata (`--degrade=no_ids_no_stops`, `--degrade=all_model_points`). |

## 1. Why the current rule is not enough

- `validity.same_name` (slice C, review S246) merges only names of the **same kind** and drops every kind word before
  comparing. That stopped the wrong merges (Long Bien Bridge / Long Bien Market, Ben Thanh Market / Night Market) but
  also misses true pairs: "Ben Thanh" / "Ben Thanh Market" (bare name vs a built place is always "keep"), "Royal
  Palace" / "Royal Palace Museum" (both words are kind words, so the name has no distinctive token and never
  matches), "Hoan Kiem Lake" / "Ho Hoan Kiem", cross-language names ("Temple of Literature" / "Van Mieu").
- The catalog-wide merge exists only as the admin fix on `/admin/places` (dry run → apply → undo). The in-tour dedupe
  in `place_extract` is automatic but per tour, with no log row.
- The ambiguous cases need context the name does not carry ("Ben Thanh" in a Saigon day text is the market; "Long
  Bien" can be the district). A rule cannot settle them; a person should not have to.

## 2. Decision for one pair (`dedupe.decide(a, b, ctx)`)

Same country, usable destinations (not `suspect`, `duplicate_of IS NULL`). Steps in order; the first that applies
decides.

| # | Step | Outcome |
|---|---|---|
| 1 | Other country | keep |
| 2 | A number differs ("Plain of Jars" / "Site 1"), or a direction / age qualifier differs (old, new, upper, lower, north …: "Bagan" / "Old Bagan") | keep |
| 3 | Kind matrix says incompatible (§2.2) — incl. **town vs landmark** | keep (same Geoapify object + incompatible kinds is logged as a geocode defect) |
| 4 | Farther apart than the kind radius (§2.3) | keep |
| 5 | Same `geocoder_place_id` (Geoapify id of one OSM object) | **auto_merge** |
| 6 | Same place card (`place_card_id`, or both names are aliases of one card in `acp_shared.place_card_alias`) | **auto_merge** |
| 7 | Score = name × kind × (0.6 + 0.4 × distance) + evidence (+ embedding) | ≥ 0.80 **auto_merge**; ≥ 0.30 **llm**; else keep |
| 7a | Cap: an ambiguous name relation (extra distinctive word, loose spelling) or kind relation (bare name vs a built place, local-word-only kind difference, "X" vs "X Museum"), or a bare name > 2 km from a natural feature without a geocoder POI result | at most **llm** |

### 2.1 Name normalisation

Lower case, accents stripped (`đ` → `d`), parentheses dropped (an alias such as "(Monkey Temple)"), possessive `'s`
dropped, a comma tail kept as part of the name ("Old Quarter, Hanoi" = "Hanoi Old Quarter"), whole-word spelling
variants (`vat`→`wat`, `phou`→`phu`, `tad`→`tat`, `paya`→`pagoda`, `bazaar`→`market`, plurals), and in name words
only `ou`→`u` ("Phousi" = "Phu Si", "Vat Phou" = "Wat Phu"). Each word is then one of: **kind word** (English =
hard kind, local = soft kind: wat, tat, tham, hang, doi, nam, cho, cau, ho (lake, except "Ho Chi Minh"), mahal …),
two-word kinds first (night market, floating market, old town / old quarter / ancient town, national park, imperial
city, city palace), **qualifier**, **number**, **generic** (the, of, scenic, landscape, complex, site, weekend …,
country names) or **core** word.

Name relation: `exact` (same core set, or the same letters run together with ≥ 4 letters, also with local words
kept) 1.0; `fuzzy` (ratio ≥ 0.85, ≥ 4 letters: "Amber" / "Amer") 0.85; `contain_locality` (the extra words are a
settlement name of that country) 0.9; `contain_extra` (an extra distinctive word: "Ban Gioc - Detian Falls") 0.55;
`fuzzy_low` (ratio ≥ 0.7 or a prefix: "Boudhanath" / "Boudha", "Khuvsgul" / "Khovsgol") 0.6; `kind_only` (no core
word, same kinds) 0.6; else half the token Jaccard. A core made only of weak words (royal, national, imperial,
golden …) scores × 0.85 beyond 300 m.

### 2.2 Kind matrix

Settlement status of a destination: **hard** = overnight stop of a live tour (`geo.tour_day.overnight_destination_id`),
Geoapify `result_type='city'`, or a town word in the name; **soft** = `suburb` / `district`; else none.

| Kinds of a / b | Relation | Kind score |
|---|---|---|
| both none | `both_bare` | 1.0 |
| equal | `same_kind` | 1.0 |
| differ only by local (soft) words, same English kinds | `soft_kind_diff` | 0.6, capped at llm |
| one bare, the bare one a **hard settlement** | `town_vs_place` | **keep** (unless the other is a town) |
| one bare, other only natural kinds (waterfall, cave, mountain, lake, river, island, village, valley, pass, beach, bay, park) | `bare_natural` | 0.9 (capped at llm beyond 2 km unless the bare name has a Geoapify POI result) |
| one bare, other built, bare one resolved by Geoapify to a POI (`amenity` / `building`) | `bare_resolved_poi` | 0.85 |
| one bare, other built, anything else (incl. a soft settlement) | `bare_vs_built` | 0.5, capped at llm |
| "X" vs "X Museum" for palace / fort / temple / monument | `heritage_museum` | 0.8, capped at llm |
| anything else (market vs night market, bridge vs market, temple vs stupa, lake vs night market, cave vs national park …) | `different_kinds` | **keep** |

A kind only keeps names apart or sends them to the LLM; a missing synonym costs a missed auto-merge, never a wrong one.

### 2.3 Distance radius

The pair takes the largest radius of its kinds, × 2 when either point is the model's (`located_by='llm'`) or an
area: POI (temple, market, bridge, museum, palace, square, fort, monument, viewpoint …) 0.5 km; old town 1.5;
waterfall / cave / beach 2; pass / mountain / island / village 3; town 5; valley / park / gorge 10; lake / bay 15;
national park / reserve / plateau 25; river / road / trail / delta 50 (linear features: until Problem 1 stores a line,
the distance is between representative points; with a line, use line-to-line distance ≤ 1 km instead). Both bare: 2 km,
5 km when one is a hard settlement; `bare_vs_built`: at least 1 km (2 km for a soft settlement, whose point is a ward
centroid).

### 2.4 Evidence and embeddings

- Both confirmed by Geoapify as POIs with **different** place ids: −0.15 (the geocoder found two objects).
- Embedding of `"<name>, <kinds>, <locality>, <country>"` (`cohere-embed-v4`, 1536-d, stored in a new
  `geo.destination_vector`, keyed by destination id + text hash): ± 0.1 around cosine 0.8, and a **candidate
  generator** for pairs with unrelated names: cosine ≥ 0.8 within 1 km and compatible kinds → llm band (catches
  "Temple of Literature" / "Van Mieu - Quoc Tu Giam" when Geoapify did not give both the same id). Not in the offline
  evaluation below (no paid call); the evaluation treats it as absent.

## 3. LLM adjudication of the middle band (one call per pair, cached)

- **Stage `a3_place_dedupe`, role `validate`, not `judge`.** ADR 0006 §5 / ADR 0008 keep judges non-Anthropic
  (`test_judge_stages_offer_non_anthropic_models`); Haiku as a judge would break the vendor rule. This call is a check
  whose output no judge scores — the ADR 0008 definition of `validate`, which may use any vendor. Primary **haiku**
  (per the brief), fallback `gpt-6-luna`; the measurement run (§8) A/Bs both before the route is chosen (lesson S234:
  Haiku lost to GPT-5.6 Luna on place-card identity, 24/28 vs 27/27).
- Called through `LLMClient.generate(LLMRequest(stage="a3_place_dedupe", json_schema=…, temperature=0))`, so every
  call is one `shared.llm_call_log` row with the job id (AA-927). Seed row in `shared.llm_role_config` and
  `SAFE_DEFAULTS`.
- Input: both places (name, kinds, settlement status, locality, coordinates, distance, `located_by`, Geoapify name
  and `result_type`, place-card display name), and up to two day-text excerpts per name (the sentence that names it,
  ≤ 300 characters, from `geo.tour_place.text_extract` of live tours). Output:
  `{"verdict": "same" | "different" | "unsure", "confidence": 0..1, "reason": "…"}`.
- **Merge only on `same` with confidence ≥ 0.8.** `unsure` and `different` keep the two places — no queue. A
  verdict is final until its inputs change.
- Cache `geo.place_pair_verdict` (PK: lower id, higher id, `input_hash` = sha256 of both names, coordinates rounded
  to 4 decimals, kinds, rule version, prompt sha, model): the same pair is never asked twice; a re-geocode or rename
  changes the hash and asks again. Pins (verdict written by an undo or an admin, `source='undo'|'admin'`) hold for any
  hash.
- Spend: `shared.spend_budget` row `job:place_dedupe` (hard stop), ≤ 100 calls per job run.

## 4. Where it runs

- New CIS job kind **`place_dedupe`** (ADR 0003: platform, debounced, `background`, cap 1). Enqueued by
  `place_geocode` when it wrote or moved a destination, and by a merge undo. Chain: `place_geocode` →
  `place_dedupe` → `tour_graph_build`. `place_geocode` stays the single writer of coordinates; `place_dedupe` writes
  only `duplicate_of` and the repoints. Both take one advisory lock (`pg_advisory_xact_lock(hashtext('geo:destinations'))`)
  so a merge never races a relink.
- Candidates per country: usable destinations within the largest radius (bounding box first), then a cheap name
  prefilter (a shared core word, run-together or fuzzy ≥ 0.7, same place id, same card, or the embedding rule).
  Incremental: pairs that touch a destination changed since the last run, plus pairs whose verdict hash changed. A
  rule-version change runs a full **dry run** first and stores the diff (merges it would add / undo) in the job result.
- Clusters: keeper first (`manual` > Geoapify point > card-linked > most live components > oldest > id); a member
  merges only on its **own** decision against the keeper (no chaining, lessons S239 / AA-857). If two members are
  `keep` with each other on a hard rule, the cluster is not merged and is reported as a conflict.
- Re-check of existing merges every run (rules only, no call): a merge that now fails a hard keep (country, kind,
  distance after a re-geocode) is undone automatically and logged.
- **Circuit breaker:** more than max(10, 3 % of usable destinations of a country) auto-merges in one run → nothing
  applied, job result `held_volume`, alert. A rule bug cannot rewrite a country silently.
- `place_extract` in-tour dedupe calls the same `decide` with rules only (`auto_merge` band); everything else waits for
  `place_dedupe`. The validity report V2 `near_duplicate` = an `auto_merge` pair not merged yet (gate); an `llm` pair
  with no verdict yet = new informational reason `possible_duplicate`.

## 5. Merge log and undo (reversible)

- **`geo.place_merge`** (CIS migration, next free number ≥ 255): `id`, `merged_id`, `keeper_id`, `country`,
  `decided_by` (`provider_id` / `place_card` / `rule` / `llm` / `admin`), `rule_version`, `score`, `features` jsonb
  (every factor of §2), `verdict` ref, `repointed` jsonb (table → key rows, the `validity_fix.REPOINT` set:
  `geo.tour_place`, `geo.tour_day`, `geo.place_name`, `acp_shared.place_card`, `shared.place_photo`), `prior` jsonb
  (chain flattening), `created_at`, `created_by` (job id or staff), `undone_at`, `undone_by`, `undo_reason`.
- Apply = the existing repoint + `duplicate_of = keeper`; a merged row that was itself a keeper has its own members
  re-pointed to the new keeper (`duplicate_of` always names a root), recorded in `prior`.
- **Undo** by merge id (`/admin/places` Merges tab, API): restores rows that still hold the merged values (409 on
  drift, as `validity_fix.undo`), refuses while a later merge depends on it (lists it; undo that first), writes a
  `different` pin so the job does not merge the pair again, and enqueues the graph build. Every undo is also a new
  labelled `keep` pair for `pairs.json` / the CI pair test (the set grows from real corrections).
- The admin duplicate fix keeps working (override path) and writes the same log with `decided_by='admin'`.

## 6. Consumers

- Catalog views already hide merged rows (CIS 253: `duplicate_of IS NULL`). TripPlanner drafts keep old destination
  ids in `trip_events` payloads; add **`catalog.v_destination_redirect`** (`destination_id`, `keeper_id`, merged rows
  only; owner `catalog_owner`, granted to `tripplanner`, `booking`) so a reader resolves an old id; after an undo the
  row disappears and the old id is live again. Appended contract `catalog.graph.v1.2`. Booking rows are reported, not
  written (unchanged).

## 7. Evaluation (rules r1.2, offline, $0)

`python3 -I dedupe_proto.py pairs.json` — 105 pairs, 55 merge / 50 keep.

| Run | Auto-merge precision | Auto-merge recall | False merges | LLM band (merge / keep) | Recall if the LLM is right |
|---|---|---|---|---|---|
| Full metadata | **1.000** | 0.764 (42/55) | **0** | 12 / 1 | **0.982** (54/55) |
| No place ids, no overnight stops | 1.000 | 0.709 | 0 | 12 / 1 | 0.927 |
| All points from the model (no ids, no result types, no stops) | 1.000 | 0.636 | 0 | 16 / 9 | 0.927 |

- **0 false merges by rules in all three runs** (target met). Recall ≥ 0.9 is met **only with the LLM band**: rules
  alone reach 0.76. The middle band holds exactly the pairs a name cannot settle: Ben Thanh (both variants), Royal
  Palace Museum, Bayon, Potala, My Son, Japanese (Covered) Bridge, Ban Gioc - Detian, Boudha, Khovsgol, Inle and Mekong
  (bare name > 2 km), and one keep pair (Long Bien / Long Bien Bridge) that the LLM must answer "different".
- Missed by everything offline: "Temple of Literature" / "Van Mieu - Quoc Tu Giam" (no shared id; needs the embedding
  candidate rule). With metadata stripped, the cross-language pairs with a shared Geoapify id (Van Mieu, Wat Arun,
  Tiger's Nest) are missed too: the place id is the strongest signal and must be kept on every row.
- The 22 S246 pairs: 8/8 merges auto, 0 false merges (the current rule also scores 8/8, 0; the new rule adds the
  brief's cases without breaking these).
- **Caveats (read before trusting the numbers).** The 79 constructed pairs are author-labelled with approximate
  coordinates, not read from Dev and not blind-labelled. The thresholds were set before the first run; three rule
  fixes came after it and are part of r1.2 (transliteration was wrongly applied to kind words; `fuzzy` now accepts 4-letter names, was 5;
  "X Museum" and a far bare name now cap at llm). The set must be extended with a blind sample before apply is
  enabled (§8).

## 8. Rollout

1. **Code (one CIS PR, after slice C):** `services/places/dedupe.py` (port of `decide`, candidates, clusters),
   `tests/unit/test_aa847_dedupe.py` (this pair set: 0 false merges required, rules recall ≥ 0.75), migration
   (`geo.place_merge`, `geo.place_pair_verdict`, `geo.destination_vector`, stage row `a3_place_dedupe`, spend budget row,
   `catalog.v_destination_redirect`), job kind `place_dedupe`, `/admin/places` Merges tab (log, filters, undo).
   Mode setting `off | dry_run | apply`, default `dry_run`, stored as a CIS runtime setting (not a new environment
   variable). `validity.is_same_place` and `pipeline._in_tour_keepers` call `dedupe.decide`.
2. **Measurement run (paid, quoted below):** the LLM band of this set on Haiku and GPT-6 Luna, three repeats each;
   enable `apply` only if the chosen model gives 0 wrong `same` verdicts on labelled `keep` pairs and is stable across
   repeats.
3. **Blind set:** after the paid place run, `place_dedupe` in `dry_run` on Laos + Vietnam; sample ≥ 60 decided pairs
   (all bands), label them with an agent panel (lesson S245 / memory "Claude audits quality") without showing the
   decision, add them to the CI set, re-measure. Then `apply`, country by country, with the dry-run report saved here.
4. **ADR 0007 amendment** (proposed text): "Duplicate destinations are merged automatically by `place_dedupe`
   (rules, provider id, place card, and a cached `validate` model call for the middle band); every merge is logged in
   `geo.place_merge` and reversible; the admin fix is an override path. `place_geocode` stays the only writer of
   coordinates; `place_dedupe` is the writer of `duplicate_of`."

## 9. Cost (USD)

| Item | Provider | Calls / volume | Cost |
|---|---|---|---|
| Measurement run (§8.2) | Bedrock Claude Haiku 4.5 ($1 / $5 per Mtok) | ~25 band prompts × 3 repeats = 75 calls × (~900 in + 80 out tokens) | ≈ $0.10 |
| same | Bedrock GPT-6 Luna ($0.10 / $0.50) | 75 calls | ≈ $0.01 |
| Name embeddings, one-off | Bedrock Cohere Embed v4 (~$0.12 / Mtok; catalog price not verified) | ~1,700 texts × ~12 tokens, 96 per request ≈ 18 requests (fits the 20 RPM quota) | < $0.01 |
| First catalog sweep, LLM band | Haiku | est. 75–150 pairs (13 % of candidate pairs here; far fewer per destination in the catalog); hard cap 300 calls | ≈ $0.10–0.20, cap $0.40 |
| Steady state | Haiku + Cohere | ~0.1 call per new destination | < $0.01 / month |
| Geocoder | Geoapify | none (uses stored place ids) | $0 |

Upfront ≤ $0.60 with the caps; no new AWS service.

## 10. Open points for Nghiệp

1. Stage role `validate` instead of `judge` (vendor rule) — proposed.
2. Labels that are a policy, not a fact: "town vs its old town" = keep; "Long Bien" (district) vs the bridge = keep;
   "Royal Palace" vs "Royal Palace Museum" in Luang Prabang = merge. The LLM decides the bare-name cases from the day
   text; the CI set pins the policy.
3. Model after the A/B (Haiku per the brief, or GPT-6 Luna if it is as accurate at ~1/10 the price).
4. Circuit-breaker threshold (proposed max(10, 3 %) per country per run).

## 11. Implementation (S246, after the skeptic pass)

Built on the revised plan (12 changes) in AA-CIS-App `feat/aa-847-dedupe` (decision, rules **r1.4**) and
`feat/aa-847-dedupe-job` (job, storage), AA-CIS-Infra `feat/aa-847-cis-257-copy`, AA-TripPlanner-Web
`feat/aa-847-destination-redirect` (301). Details: AA-CIS-App `docs/implementation-notes/AA-847-dedupe.md`.

- **Migration 257, not 256:** the lines lane took 256 (`256_catalog_line_places.sql`) while this lane ran.
- **One line rule:** two drawn lines are auto-merged by the lines lane's `shape.same_line_place` (≥ 70 % overlap by
  length or the same OSM id, two-way name match, same class); dedupe adds only the model band (shared OSM object or
  ≥ 30 % overlap) — §2's "≥ 0.6 overlap" auto rule was dropped so the codebase has one line rule.
- **Offline evaluation r1.4** (CIS `tests/unit/test_aa847_dedupe.py`, 134 pairs: the 105 here + the review's
  adversarial / linear pairs + the revised plan's keeps + the homonym list; `eval-r1.4.txt`, misses in
  `eval-r1.4-misses.txt`):

  | Run | Auto precision | Rules recall | False merges | Band merge / keep | Recall if the check is right |
  |---|---|---|---|---|---|
  | Full metadata | 1.000 | 0.689 (42/61) | 0 | 17 / 6 | 0.967 |
  | No ids / stops / cards | 1.000 | 0.689 | 0 | 14 / 5 | 0.918 |
  | All points the model's | 1.000 | 0.623 | 0 | 18 / 15 | 0.918 |
  | One shared city id | 1.000 | 0.066 | 0 | 52 / 15 | 0.918 |
  | No shapes | 1.000 | 0.623 | 0 | 19 / 5 | 0.934 |

- The plan's §6.1 target "rules recall ≥ 0.75" is **not met** (0.689): its own §0.1 sends Van Mieu, Wat Arun and
  Tiger's Nest (shared Geoapify id, unrelated names) to the model. No rule was loosened to reach the number.
- The six keep pairs left to the model (Long Bien ×2, Hoan Kiem on the suburb id, Lao Cai / Lao Chai, a Dhammayazika
  model point, a Cu Chi Tunnels model point) are what the paid measurement run (§6.2) must see answered
  `different` / `unsure`.
- Nothing paid ran: the model check is tested with stubs; the job spends only for countries an admin lists.
