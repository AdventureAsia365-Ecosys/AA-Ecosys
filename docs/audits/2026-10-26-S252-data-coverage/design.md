# Data coverage page: design (S252)

Status: design only, nothing built. Author: Claude Code (subagent), 26/10/2026.
Request (Nghiệp, S252): one admin page or tab, numbers only, for the whole system, to audit where data is missing:
from the inputs (raw Excel uploads for tours, brand uploads) through raw tours imported / deleted / filtered, ready for
S1, written to Master, atoms, segments, ..., the T-series, tenants, TripPlanner, Booking and CRM. Live numbers only.

Ground truth used (every table and column below was checked against them):
- `docs/architecture/db-schema-reference.md` (Verified 2026-10-25 14:58 UTC: CIS 282, tp-019, bk-024; CIS 283–285 and
  crm-019 are applied after the dump and are named only where their own migration file was read).
- `.tmp-session/s252/propagation/coverage.py` (59 queries as `cis_app`, run 2026-10-25 23:57Z: `errors = {}`, every
  query < 120 ms except the Python segment classification, 2.1 s; 3.4 s in all) and its `coverage.json`.
- `.tmp-session/s252/propagation/chain-map.md`, `tripplanner-chain.md`, `aa990-run.txt`
  (`infra/AA-CIS-Infra/db/scripts/aa990_reader_checks.py`, master, read-only).
- `docs/audits/2026-10-26-S252-propagation-audit/README.md`.
- Code read: AA-CIS-App `900f2463` (`services/ingestion/handler.py`, `api/routers/admin_pipeline.py` upload/ingest/
  brand-identity/`/admin/tours`, `api/services/ops_overview/*`, `api/services/crm_console.py`,
  `services/catalog_http/reader.py`, `api/core/staff_authz.py`, `frontend/app/_kit/*`, `frontend/lib/rbac.ts`),
  AA-Booking `migrations/017_ops_overview_views.sql`, AA-CIS-Infra `db/owners.yaml`, `db/isolation_probe.py`,
  `db/rls_catalogue_rules.py`, `modules/ecs/main.tf`, root `docs/database/schema-ownership.md`, `docs/contracts/README.md`,
  `skill/aa-lessons/lessons.md` (X1 rows).

"Live tour" everywhere = the `catalog._live_tour` rule (coverage.py `LIVE` CTE): AA master Master
(`published_tours.tenant_id = MASTER`, `master_status = 'active'`, `deleted_at IS NULL`) joined to `raw_tours` with
`source_status = 'active'` and `deleted_at IS NULL`. Today: **892**. `MASTER` = `00000000-0000-0000-0000-000000000001`
(bound as `$1`, never interpolated).

---

## 0. Decisions in one screen

| # | Decision | Why |
|---|---|---|
| D1 | New page **`/admin/data-coverage`** ("Data coverage"), Platform section, group *Overview* (second item after Overview). Not a tab of `/admin/overview` | Overview is admin-only and a business view; this page is an audit table that reviewers also need, and it is long (≈ 95 rows) |
| D2 | One endpoint **`GET /admin/data-coverage`** returns every row in one call; numbers only (no tour ids, no samples, no names) | Matches "chỉ số liệu"; ids stay on the drill-in pages, which already list them |
| D3 | CIS computes everything it owns itself, as `cis_app`, on the **base tables** (coverage.py SQL, reused) | No grant, same numbers as the S252 audit |
| D4 | TripPlanner rows that depend on view logic (day list regex, located places, served components, stops/legs, retired, purge outbox) read the **`catalog.*` views through the existing tenant pool** (`aa_app_user`, `services/catalog_http/reader.catalog_connection`), which already has SELECT on them | "Measure what the consumer reads"; `cis_app` keeps no USAGE on `catalog` (CIS 244 guard) |
| D5 | TripPlanner-owned and Booking-owned numbers come from **new owner contract views `v_ops_*`** granted to `cis_app` (tp-020, bk-025), aggregates only | Same pattern as tp-015 / bk-017 (AA-858); the CIS 244 guard and the isolation probe already allow-list `v_ops_*` contract views |
| D6 | CRM numbers come over **HTTP `crm.ops.v1` minor 1.4** (`GET /crm/ops/v1/data-coverage`), **not a view** | ADR 0008a decision 1: no AA role has USAGE on `crm`, both directions; the isolation probe asserts 42501. A view is not allowed |
| D7 | Each source query has its own transaction, `statement_timeout`, `asyncio.wait_for` timeout and timing; a failed or slow query turns only its rows into `n/a` | Requested; same rule as `ops_overview.cache.cached_section` |
| D8 | Two cache tiers in Redis: **fast 60 s** (DB counts) and **slow 600 s** (segment classification in Python, S3 listing, CRM HTTP); single-flight lock; last good value kept 24 h | Fast tier ≤ 60 s as asked; the slow sources cost more and change rarely |
| D9 | Row status = green / amber / red / grey from **missing vs expected gap** and a per-row kind (`must` / `backlog` / `info`) | Makes "what is missing" readable at a glance without hiding by-design gaps |
| D10 | **Admin only** in v1: reuse capability **`ops.read`** (`OPS_READ`, as `/admin/overview`); page rule `["admin"]` (critic fix: the request says "từ trang admin" and names no reviewer; most drill pages — atom-curation, places, seo-intelligence, content-quality, photos, tenants, tenant-activity, jobs, platform/agencies — are admin-only in `rbac.ts`, and the CRM rows need an admin token) | Matches the "whole-system views … tenants, jobs" admin-only block of `rbac.ts`; no new capability. Reviewer access = open question 2 |
| D11 | $0: no model call, no DFS, no new AWS service. S3 `ListObjectsV2` on two prefixes at most every 10 min (≈ 0.3 k requests / month, < $0.01) | Paid-run rule |

---

## 1. The table

Columns on the page: **Metric** · **Count** · **Of** (denominator + its label) · **%** · **Missing** · **Expected gap**
(number + one-line reason) · **Status** · **Open** (drill-in link). Hover on the metric shows `source` (table/view) and
`timing_ms`. Counts are integers, % has one decimal, missing = denominator − count (or the count itself for "should be 0"
rows). "Today" below is the value the page would show now, from `coverage.json` (cov), `aa990-run.txt` (tp) or the
audit; "—" = not measured yet (new query).

Kinds: **must** = generated automatically, any gap above the expected one is a defect (red); **backlog** = needs a
manual or paid run, gap is known work (amber, names the issue); **info** = no coverage target (grey, no %).
Status: `ok` (missing ≤ expected), `gap` (missing > expected: red for must, amber for backlog), `info`, `na` (source
failed / timed out / not available, with reason).

Drill-in links use routes that exist today (`frontend/app/_kit/adminNav.tsx`); query parameters only where the page
reads them (`atom-curation?section=` atomize|segment|score|route_hub|slate; `tenants?tenant=`; `content-quality` tab).

### 1.1 Inputs (S0 uploads)

| id | Metric (EN label) | Count SQL key | Of | Expected gap | Kind | Open | Today |
|---|---|---|---|---|---|---|---|
| `in.tour_files` | Tour Excel files ingested | `Q_IN_FILES.files` | — | — | info | /admin/upload | — (raw_sources ~34) |
| ~~`in.tour_files_parse_errors`~~ | (dropped, critic: `raw_sources.parse_errors` is always `'[]'` — `RawSourceRepository.insert` writes the default and `update_status(..., error=)` ignores `error`; a parse failure surfaces as `in.batches_failed`) | — | — | — | — | — | — |
| `in.tour_files_not_ingested` | Tour files uploaded but never ingested | `S3_RAW_INBOX.not_ingested` | files in `raw-inbox/` | previews and exact-duplicate files blocked by hash (not separable): shown, never red | info | /admin/upload | — |
| `in.rows_parsed` | Excel rows parsed | `Q_IN_BATCHES.rows_parsed` | — | — | info | /admin/upload | — |
| `in.rows_landed` | Rows landed as raw tours | `Q_IN_BATCHES.rows_landed` | rows parsed | rows dropped by the A0 gates (next rows) **+ rows staged as near-duplicates** (`Q_IN_BATCHES.rows_staged`; critic fix: `process_file` sends a matched row to `upload_staging`, counted in neither `rows_landed` nor `drops`, so without it every batch with a duplicate goes red) | must | /admin/upload | — |
| `in.drop.<reason>` (one row per reason: `empty_itinerary`, `duplicate_in_file`, `duplicate_of_existing`, `not_a_tour`, `thin_itinerary`, insert failures by their reason) | Rows dropped: <reason> | `Q_IN_DROPS` | rows parsed | all of it (by design: A0 gates, AA-604 / AA-690) except insert-failure reasons | info (insert failures: must) | /admin/upload | — |
| `in.batches_without_details` | Ingest batches with no landed/dropped record | `Q_IN_BATCHES.batches_without_details` | ingest batches | batches older than the `ingest_details` column | info | /admin/upload | — |
| `in.batches_failed` | Ingest batches failed | `Q_IN_BATCHES.batches_failed` | ingest batches | 0 | must | /admin/upload | — |
| `in.staged_pending` | Near-duplicates waiting for a decision | `Q_IN_STAGING.pending` | staged rows | 0 older than 7 days (`pending_over_7d` is the missing count) | backlog (human) | /admin/upload | — |
| `in.staged_decided` | Near-duplicates decided (bypass / replace / update / keep both) | `Q_IN_STAGING.decided` | staged rows | — | info | /admin/upload | — |
| `in.brand_files` | Brand files uploaded (all tenants) | `S3_BRAND.objects` | — | — | info | /admin/tenants | — |
| `in.brand_files_tenants` | Tenants with ≥1 brand file | `S3_BRAND.tenant_prefixes` | active tenants | tenants that typed their brand by hand | info | /admin/tenants | — |
| ~~`in.brand_versions_docx`~~ | (dropped, critic: no code writes `shared.tenant_brand_rule_versions`; only migration 019 creates it, so the row is a constant) | — | — | — | — | — | — |

Notes: the brand file upload (`POST /admin/brand-identity/upload`) writes only to S3
(`brand-identity/<tenant>/<uuid>_<name>`); no table records it (`tenants.last_brand_brief_s3_key` and
`tenant_brand_rules.source_docx_s3_key` have no writer left). The S3 listing is the only source; the T0 rows in §1.6
measure what reached the database.

### 1.2 Raw tours (A0)

| id | Metric | Count SQL key | Of | Expected gap | Kind | Open | Today |
|---|---|---|---|---|---|---|---|
| `raw.rows` | Raw tour rows (all versions) | `Q_RAW.rows` | — | — | info | /admin/s1-rewrite | 987 |
| `raw.trashed` | Deleted (trashed) | `Q_RAW.trashed` | raw rows | — | info | /admin/s1-rewrite | 44 |
| `raw.superseded` | Replaced by a newer version (superseded) | `Q_RAW.superseded` | raw rows | — | info | /admin/s1-rewrite | 26 |
| `raw.hitl_rejected` | Rejected in review (hitl_rejected) | `Q_RAW.hitl_rejected` | raw rows | — | info | /admin/review | 1 |
| `raw.live` | Live raw sources | `Q_RAW.live` | raw rows | — | info | /admin/s1-rewrite | 917 |
| `raw.live_no_itinerary` | Live sources with empty itinerary | `Q_RAW.live_no_itinerary` | live sources | 0 (ingest skips them) | must | /admin/s1-rewrite | 0 (cov: atoms_without_action 0; to measure) |
| `raw.live_country_unresolved` | Live sources with no resolved country | `Q_RAW.live_country_unresolved` | live sources | 0 | must | /admin/s1-rewrite | — |
| `raw.live_phasing_out` | Live sources phasing out / retired lifecycle | `Q_RAW.live_lifecycle_not_active` | live sources | — | info | /admin/master-content | 0 |

### 1.3 S1 and Master (A1–A3)

| id | Metric | Count SQL key | Of | Expected gap | Kind | Open | Today |
|---|---|---|---|---|---|---|---|
| `s1.eligible` | Live sources ready for S1 (itinerary present) | `Q_S1.eligible` | live sources | 0 | must | /admin/s1-rewrite | 917 |
| `s1.never_written` | Ready for S1, never written | `Q_S1.never_written` | eligible | 0 (a new upload is expected to sit here until an admin runs S1) | backlog (paid S1) | /admin/s1-rewrite | 0 |
| `s1.in_review` | Written, waiting in Review Queue, no Master yet | `Q_S1.in_review_no_master` | eligible | — | backlog (human) | /admin/review | 25 |
| `s1.written_failed` | Written, no Master, not in review (failed / rejected) | `Q_S1.written_no_master_other` | eligible | 0 | backlog | /admin/s1-rewrite | 0 |
| `master.active` | Live tours (active Master) | `Q_S1.with_master` | live sources | in_review + never_written + written_failed | must | /admin/master-content | 892 / 917 |
| `master.writer_v2` | Live tours whose Master is on the current S1 writer (v2) | `Q_MASTER.writer_v2` (`generated_content.metadata->>'writer_version' = 'v2'` of the published row) | live tours | the kept set: 82 today = 43 golden fixtures + 39 elephant riding (AA-645 policy, kept on v1 on purpose). Expected = `count(live ∩ kept)`, kept read from one closed `shared.rerun_wave` row (`name = 'aa645-kept-on-v1'`, `expected_tour_ids` = the 82; table exists, cis_app has INSERT); a new upload is written on v2 so the gap stays 82 | must (critic addition: "đã viết vào master" had no current-writer row) | /admin/master-content | 810 / 892, expected 82 |
| `master.quality_score` | Masters with a quality score | `Q_MASTER.with_quality_score` | live tours | 0 | must | /admin/master-content | 892 / 892 |
| `master.newer_waiting` | Masters with a newer version waiting (pending / hitl) | `Q_MASTER.newer_waiting_review` | live tours | — | backlog (human) | /admin/review | 2 |
| `master.newer_rejected` | Masters whose newer version was rejected / failed | `Q_MASTER.newer_rejected` | live tours | — | info | /admin/review | 1 |
| `master.content_embedding` | Masters with `content_embedding` | `Q_MASTER.content_embedding` | live tours | all (dead column, AA-989 D2) | info | — | 0 |
| `review.pending` | Review Queue rows pending | `Q_REVIEW.pending` | — | — | info | /admin/review | 43 |
| `seo.with_row` | Live tours with SEO context | `Q_SEO.with_row` | live tours | 0 | must | /admin/seo-intelligence | 892 / 892 |
| `seo.fresh` | SEO context fresh (`ideas_v3` < 180 d) | `Q_SEO.fresh_ideas_v3` | live tours | 0 | must | /admin/seo-intelligence | 892 / 892 |
| `seo.with_paa` | Live tours with PAA questions in SEO | `Q_SEO.with_paa` | live tours | all (DFS has no PAA for every keyword) | info | /admin/seo-intelligence | 634 / 892 |

`s1.*` follows the S1 page's own floor (`GET /admin/tours`, `admin_pipeline.py:2124`: `source_status = 'active'`,
`deleted_at IS NULL`, non-empty `src_itineraries`); "in review" uses `review_queue.review_status = 'pending'` like that
page's `in_review` badge.

### 1.4 A-series derived (atoms → segments → ranking → routes → PAA → embeddings)

| id | Metric | Count SQL key | Of | Expected gap | Kind | Open | Today |
|---|---|---|---|---|---|---|---|
| `atoms.tours` | Live tours with atoms | `Q_ATOMS.with_atoms` | live tours | empty-marker-only tours (`Q_ATOMS.empty_marker_only`) | must | /admin/atom-curation?section=atomize | 892 / 892 |
| `atoms.older_than_master` | Tours whose atoms are older than the Master | `Q_ATOMS.atoms_older_than_master` | live tours | 0 | must | /admin/atom-curation?section=atomize | 0 |
| `atoms.active` | Active atoms (place atoms) | `Q_ATOMS.atoms` (`place_atoms`) | — | — | info | /admin/atom-curation?section=atomize | 25,878 (25,878) |
| `seg.tours` | Live tours with ≥1 segment | `Q_SEG.with_segment` | live tours with place atoms | tours whose every atom is excluded by rule (`SEG_CLASSIFY.all_excluded_tours`, slow tier) | must | /admin/atom-curation?section=segment | 883 / 892, expected 9 |
| `seg.unexplained_atoms` | Place atoms with no segment and no rule reason | `SEG_CLASSIFY.unexplained` | atoms without a segment member | 0 | must | /admin/atom-curation?section=segment | 228 / 9,008 (157 tours) |
| `seg.excluded_atoms` | Atoms excluded by rule (transit / unnamed) | `SEG_CLASSIFY.excluded_by_rule` | atoms without a segment member | all | info | /admin/atom-curation?section=segment | 8,780 |
| `seg.dead_member_rows` | Segment member rows on dead atoms | `Q_SEG.rows_on_dead_atoms` | member rows | 0 | must | /admin/atom-curation?section=segment | 10,547 / 27,712 |
| `seg.orphans_deletable` | Orphan segments the GC would delete | `Q_GC.deletable` (last platform `recompute` result) | orphan segments | 0 | must | /admin/atom-curation?section=segment | 2 |
| `seg.orphans_kept` | Orphan segments kept by a reference | `Q_GC.kept` | orphan segments | all (alias / Subject / brand-fit / angle request) | info | /admin/atom-curation?section=segment | 910 |
| `rank.tours` | Segmented tours with ranking | `Q_RANK.with_ranking` | tours with a segment | 0 | must | /admin/atom-curation?section=score | 883 / 883 |
| `rank.markets` | Markets with current ranking rows | `Q_RANK.markets` | 6 | 0 | must | /admin/atom-curation?section=score | 6 / 6 |
| `route.tours` | Live tours with a route | `Q_ROUTE.with_route` | live tours | live − with_route (no qualifying run, ≥2 consecutive days with ≥2 places; parity checked nightly by AA-991 `routes_missing`) | info | /admin/atom-curation?section=route_hub | 700 / 892 |
| `route.with_hub` | Current routes with a hub | `Q_ROUTE.current_routes_with_hub` | current routes | open question Q3 | backlog (definition) | /admin/atom-curation?section=route_hub | 155 / 1,261 |
| `paa.computed` | Ranked segments with landing computed | `Q_PAA.computed` | ranked segments | 0 | must | /admin/seo-intelligence | 9,040 / 9,040 |
| `paa.with_questions` | Ranked segments with ≥1 question | `Q_PAA.with_questions` | ranked segments | all (no PAA for that place/market) | info | /admin/seo-intelligence | 1,122 / 9,040 |
| `paa.demand_age_days` | Search demand age, oldest market (days) | `Q_PAA.oldest_market_age_days` | — | ≤ 30 | backlog (paid research) | /admin/seo-intelligence | 28 (AU, UK 28/09) |
| `emb.landing_atoms` | Landing-scope atoms with both vectors | `Q_EMB.with_both_views` | landing-scope atoms | 0 (rebuilt on demand by landing) | backlog | /admin/seo-intelligence | 1,982 / 2,047 |
| `emb.inactive_rows` | Atom vectors on inactive atoms (cache) | `Q_EMB.rows_on_inactive_atoms` | vector rows | all (cache, optional GC) | info | — | 6,300 / 10,826 |

### 1.5 Places, place cards, photos

| id | Metric | Count SQL key | Of | Expected gap | Kind | Open | Today |
|---|---|---|---|---|---|---|---|
| `geo.built` | Live sources with a place build | `Q_GEO.built` | live tours | — (AA-905 backlog, `PLACE_PIPELINE_AUTO` off) | backlog (paid, AA-905) | /admin/places | 123 / 892 |
| `geo.served` | Live tours with ≥1 served component | `Q_GEO.with_served_component` | live tours | follows `geo.built` | backlog | /admin/places | 121 / 892 |
| `geo.built_not_served` | Built sources with no served component | `Q_GEO.built − with_served_component` | built sources | 0 | must | /admin/places | 2 |
| `geo.no_destination` | Components with no destination | `Q_GEO.components_no_destination` | components | — | backlog (geocode) | /admin/places | 309 / 2,152 |
| `geo.inactive_atoms` | Components on inactive atoms | `Q_GEO.components_on_inactive_atoms` | components | 0 | must | /admin/places | 0 |
| `geo.graph` | Built sources in the current tour graph | `Q_GEO.in_current_graph` | built sources | 0 | must | /admin/places | 122 / 123 |
| `geo.names_waiting` | Place names unknown / pending | `Q_GEO.names_unknown + names_pending` | place names | — | backlog | /admin/places | 217 + 189 / 2,303 |
| `geo.shapes` | Line places with a usable shape (ok / approximate) | `Q_GEO.shapes_usable` | line shapes | not_found (no geometry exists) | backlog | /admin/places | 40 / 50 |
| `card.linked` | Place atoms linked to a place card | `Q_CARD.linked` | place atoms | all (place cards are optional enrichment; built on request, paid, AA-784) | info (critic fix: was backlog/amber) | /admin/content-quality (tab Place cards) | 878 / 25,878 |
| `card.no_row` | Place atoms with no card link and no miss | `Q_CARD.no_row` | place atoms | all (optional, AA-784) | info | /admin/content-quality (tab Place cards) | 18,755 |
| `card.tours` | Live tours with ≥1 place card | `Q_CARD.tours_with_a_card` | live tours | all (optional) | info | /admin/content-quality (tab Place cards) | 160 / 892 |
| `photo.tours` | Live tours with ≥1 photo | `Q_PHOTO.with_photo` | live tours | tours with no Drive folder (not knowable) | backlog (Drive) | /admin/photos | 162 / 892 |
| `photo.destinations` | Served destinations with ≥1 photo | `Q_PHOTO.dest_with_photo` | served destinations | — | backlog | /admin/photos | 0 / 1,182 |
| `photo.unmatched` | Photos not matched to a tour | `Q_PHOTO.unmatched` | photos | — | backlog (assign) | /admin/photos | 603 / 3,232 |

### 1.6 T-series and tenants

| id | Metric | Count SQL key | Of | Expected gap | Kind | Open | Today |
|---|---|---|---|---|---|---|---|
| `ten.active` | Active tenants (Content studio) | `Q_TEN.active` | — | — | info | /admin/tenants | — (shared.tenants ~4) |
| `ten.members` | Active tenant members | `Q_TEN.members_active` | — | — | info | /admin/tenants | — |
| `t0.brand` | T0 tenants with a filled active brand (system prompt set) | `Q_TEN.with_filled_brand` | active tenants | 0 (an empty placeholder brand falls back to the AA generic prompt) | must | /admin/tenants | — |
| `t0.markets` | Tenants with markets and channels configured | `Q_TEN.with_config` | active tenants | 0 | must | /admin/tenants | — |
| `t2.tours` | T2 tenant tours (latest version per tour) | `Q_T2.tenant_tours` | — | — | info | /admin/content-quality (tab Tour versions) | 15 |
| `t2.older` | Tenant tours older than their Master | `Q_T2.older_than_master` | tenant tours | — (tenant decides) | info | /admin/content-quality (tab Tour versions) | 2 / 15 |
| `t2.inactive_master` | Tenant tours on an inactive Master | `Q_T2.on_inactive_master` | tenant tours | 0 | must | /admin/content-quality (tab Tour versions) | 0 |
| `t3.qa_open` | Tenant versions with QA failed / escalated | `Q_T2.qa_failed_or_escalated` | tenant tours | — | backlog (tenant) | /admin/content-quality (tab Tour versions) | — |
| `t4.pool` | T4 pool: tenant tours whose latest version is approved (critic addition: T1–T4 live in `tenant_tour_versions`; T1 = a row exists, T4 = latest `status = 'approved'`) | `Q_T2.pool` (`count(*) FILTER (WHERE l.status = 'approved')`, add `v.status` to the `latest` CTE) | tenant tours | — (tenant decides) | info | /admin/content-quality (tab Tour versions) | — |
| `plan.quarters` | Quarter plans | `Q_PLAN.quarter_plans` | — | — | info | /admin/tenant-activity | 6 |
| `t7.subjects` | T7 Subjects (proposed / picked / used / cut) | `Q_T7.*` (4 rows) | — | — | info | /admin/atom-curation?section=slate | 383 / 4 / 18 / 2 |
| `t7.stale` | Open Subjects (proposed / picked) on a segment with no active member | `Q_T7.on_dead_segment` (critic fix: restrict to `state IN ('proposed','picked')`; used / cut Subjects are history the segment GC keeps on purpose) | open subjects | 0 | must | /admin/atom-curation?section=slate | — |
| `t8.requests` | T8 angle requests | `Q_T8.requests` | — | — | info | /admin/tenant-activity | 25 |
| `t8.inactive_atoms` | Angle requests on replaced atoms | `Q_T8.on_inactive_atom` | angle requests | 0 | must (AA-988 follow-up) | /admin/tenant-activity | 14 / 25 |
| `t9.pieces` | T9 content pieces (approved / held) | `Q_T9.approved`, `Q_T9.held` | pieces | — | info | /admin/content-quality (tab Pieces) | 214 / 132 of 346 |
| `t9.embedded` | Pieces with a content vector | `Q_T9.embedded` | pieces | 0 | must | /admin/content-quality (tab Pieces) | 305 / 346 |
| `pub.published` | Pieces published (publish log, latest status) | `Q_PUB.by_status` (one row per status) | approved pieces | — | info | /admin/tenant-activity | — |
| `pub.failed` | Publish attempts failed (latest status) | `Q_PUB.failed` | publish rows | 0 | must | /admin/tenant-activity | — |
| `deliver.pages` | Tenant trip pages tracked | `Q_DELIVER.pages` | — | — | info | /admin/tenant-activity | 0 |

### 1.7 TripPlanner

| id | Metric | Count SQL key | Of | Expected gap | Kind | Open | Today |
|---|---|---|---|---|---|---|---|
| `tp.tours` | Tours served to TripPlanner (`catalog.v_tour`) | `C_TP.v_tour` | live tours (CIS count) | 0 (must equal) | must | /admin/master-content | 892 / 892 |
| `tp.day_list` | Tours with a day list | `C_TP.with_day_list` | served tours | 0 | must | /admin/master-content | 892 / 892 |
| `tp.located` | Tours with ≥1 located place on the tour page | `C_TP.with_located_places` | served tours | follows geo / cards | backlog | /admin/places | 627 / 892 |
| `tp.components` | Tours with planner stops (components) | `C_TP.with_components` | served tours | follows `geo.built` | backlog (AA-905) | /admin/places | 121 / 892 |
| `tp.stale_components` | Tours with stale components | `C_TP.with_stale_components` | tours with components | 0 | must | /admin/places | 0 |
| `tp.unembedded` | Served components without a vector | `C_TP.unembedded_components` | served components | 0 | must | /admin/places | 0 / 1,843 |
| `tp.route_stops` | Tours with route stops / legs | `C_TP.with_route_stops`, `with_route_legs` | served tours | 1-day tours have no leg | backlog | /admin/places | 122 / 110 |
| `tp.retired_served` | Retired / paused keys still served (tours + components + stops + days) | `C_TP.retired_served` | retired / paused keys | 0 | must | /admin/master-content | 0 |
| `tp.purge_no_job` | Lifecycle events with no purge job | `C_TP.events_without_job` (+ `Q_JOBS` join) | lifecycle events | 0 | must | /admin/jobs | 4 / 10 |
| `tp.trips` | Saved trips (drafts) / sent | `V_TP.trip_drafts`, `trip_drafts_sent` | — | — | info | — | 103 / 10 |
| `tp.pins_served` | Pinned stops still served | `V_TP_PINS.served` | pins | 0 dangling | must | /admin/places | 49 / 371 |
| `tp.pins_dangling` | Pinned stops with no component row | `V_TP_PINS.no_component_row` | pins | 0 | must | /admin/places | 322 / 371 |
| `tp.id_map` | Component id map rows | `V_TP.component_id_map_rows` | — | — | info | — | 750 |
| `tp.sessions` | Planner sessions / traveller accounts / customers | `V_TP.sessions`, `traveller_accounts`, `customers` | — | — | info | — | 106 / 3 / 8 |
| `tp.narration` | Narration cache rows | `V_TP.narration_cache_rows` | — | — | info | — | 1 |

### 1.8 Booking

| id | Metric | Count SQL key | Of | Expected gap | Kind | Open | Today |
|---|---|---|---|---|---|---|---|
| `bk.plans` | Trip plans (sellable) | `V_BK.trip_plans`, `trip_plans_sellable` | live tours | all (a plan exists only for tours staff sell) | info | (Booking admin link, lib/apps.ts) | — |
| `bk.plans_orphaned` | Trip plans whose tour is no longer live | `V_BK_KEYS` × CIS live set | trip plans | 0 | must | (Booking admin) | — |
| `bk.departures` | Departures scheduled / guaranteed | `V_BK.departures_open` | — | — | info | (Booking admin) | — |
| `bk.suppliers` | Active suppliers / contracts published / rates current | `V_BK.suppliers_active`, `contracts_published`, `rates_current` | — | — | info | (Booking admin) | — |
| `bk.supply_active` | Active hotels + services (Booking) | `Q_SUPPLY.bk_active` (existing `booking.v_supply_hotels` / `v_supply_services`) | — | — | info | /admin/supply-content | — |
| `bk.supply_mirrored` | Active Booking supply known to CIS | `Q_SUPPLY.mirrored_active` | active Booking supply | 0 | must | /admin/supply-content | — |
| `bk.supply_published` | Active supply with AA content published | `Q_SUPPLY.published_active` | active Booking supply | drafts in review | backlog (review) | /admin/supply-content | 0 / 0 (both entities inactive) |
| `bk.hotels_no_destination` | Active hotels with no destination | `Q_SUPPLY.hotels_no_destination` | active hotels | 0 | must | /admin/supply-content | — |
| `bk.media_rights` | Supplier photos with usage rights | `V_BK.media_active_with_rights` | active supplier photos | — | info | /admin/supply-content | — |
| `bk.cases_open` | Open trip cases | existing `booking.v_ops_case_status` (not completed / cancelled) | — | — | info | /admin/overview | — |
| `bk.inquiries_stuck` | Inquiries parked / failed (last 400 days) | existing `booking.v_ops_funnel_daily` (`inquiry_parked`, `inquiry_failed`; the view keeps only the last 400 UTC days, bk-017 — not "all days") | inquiries received (same window) | 0 | must | /admin/overview | — |
| `bk.b2b` | B2B partners active / holds active | `V_BK.b2b_partners_active`, `b2b_holds_active` | — | — | info | (Booking admin) | 2 holds |

### 1.9 CRM (partner CRM, over HTTP)

| id | Metric | Count source | Of | Expected gap | Kind | Open | Today |
|---|---|---|---|---|---|---|---|
| `crm.agencies` | Agencies active / locked / offboarding | `CRM.agencies.*` | — | — | info | /admin/platform/agencies | — |
| `crm.members` | Agency members active / invited | `CRM.members.*` | — | — | info | /admin/platform/agencies | — |
| `crm.cache_served` | AA tours cached in the CRM (served) | `CRM.catalog_cache.served` | live tours (CIS) | 0 (must equal) | must | /admin/platform/agencies | 892 / 892 |
| `crm.cache_paused_retired` | Cached tours paused / retired | `CRM.catalog_cache.paused`, `.retired` | — | — | info | /admin/platform/agencies | 0 / 0 |
| `crm.cache_age_min` | Minutes since the last full catalog pass | `CRM.catalog_cache.last_full_pass_at` | — | ≤ 120 | must | /admin/platform/agencies | ~60 |
| `crm.cache_failures` | Catalog sync failures in a row | `CRM.catalog_cache.failures` | — | 0 | must | /admin/platform/agencies | 0 |
| `crm.aa_content` | AA content items published (CIS, served to the CRM) | `Q_AA_CONTENT.published_items` | content items | retired items | info | /admin/aa-content | — (~28 items) |

Agency business data (trips, proposals, travellers, revenue) has **no row**: AA is the processor, the agency the
controller (ADR 0008a, DM-6.8); `crm.ops.v1` forbids `trip_count` / `revenue` and personal data by contract CI. The page
shows this as a footnote under the CRM group, not as a number.

---

## 2. SQL (precise)

Conventions: `$1` = MASTER. CTE fragments are coverage.py's, verbatim: `LIVE` (with `$1` instead of the f-string),
`ACTIVE_ATOMS`, `PLACE_ATOM`, `SERVED_DEST`. Every statement runs in `BEGIN READ ONLY` with
`SET LOCAL statement_timeout = '4s'`, `SET LOCAL lock_timeout = '1s'`. (Critic: drop `SET LOCAL app.tenant_id` —
coverage.py set it, but CIS runtime code sets no tenant GUC (owners.yaml `rls_parity_tables` note) and every table read
here has a `<t>_cis_app_all` policy, checked against the dump; setting it only invites the reader to think it filters.) Pool: `app.state.pool` (cis_app) unless marked `[tenant pool]`
(aa_app_user, `catalog_connection`), `[S3]` or `[HTTP]`.

### 2.1 Inputs

```sql
-- Q_IN_FILES
SELECT count(*)::int AS files,
       count(*) FILTER (WHERE parse_errors IS NOT NULL AND jsonb_typeof(parse_errors) = 'array'
                          AND jsonb_array_length(parse_errors) > 0)::int AS files_with_parse_errors,
       coalesce(sum(row_count), 0)::int AS rows_recorded
  FROM silver_aa_internal.raw_sources WHERE tenant_id = $1;

-- Q_IN_BATCHES (ingest batches = pipeline_runs rows created by process_file: s3_source_path under raw-inbox/)
SELECT count(*)::int AS batches,
       count(*) FILTER (WHERE ingest_details IS NULL)::int AS batches_without_details,
       count(*) FILTER (WHERE status = 'ingest_failed')::int AS batches_failed,
       coalesce(sum((ingest_details->>'rows_parsed')::int), 0)::int AS rows_parsed,
       coalesce(sum((ingest_details->>'rows_landed')::int), 0)::int AS rows_landed,
       coalesce(sum((ingest_details->>'rows_dropped')::int), 0)::int AS rows_dropped,
       -- critic fix: matched rows go to upload_staging (not landed, not dropped); count them per ingest batch
       (SELECT count(*) FROM silver_aa_internal.upload_staging s
         WHERE s.tenant_id = $1 AND s.batch_id IN (SELECT r2.batch_id FROM shared.pipeline_runs r2
                                                    WHERE r2.tenant_id = $1 AND r2.s3_source_path LIKE 'raw-inbox/%'
                                                      AND r2.ingest_details IS NOT NULL))::int AS rows_staged
  FROM shared.pipeline_runs WHERE tenant_id = $1 AND s3_source_path LIKE 'raw-inbox/%';

-- Q_IN_DROPS (one result row per reason)
SELECT d->>'reason' AS reason, sum((d->>'count')::int)::int AS n
  FROM shared.pipeline_runs r
 CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN jsonb_typeof(r.ingest_details->'drops') = 'array'
                                              THEN r.ingest_details->'drops' ELSE '[]'::jsonb END) d
 WHERE r.tenant_id = $1 GROUP BY 1 ORDER BY 2 DESC;

-- Q_IN_STAGING
SELECT count(*) FILTER (WHERE decision = 'pending')::int AS pending,
       count(*) FILTER (WHERE decision = 'pending' AND created_at < now() - interval '7 days')::int AS pending_over_7d,
       count(*) FILTER (WHERE decision <> 'pending')::int AS decided, count(*)::int AS staged
  FROM silver_aa_internal.upload_staging WHERE tenant_id = $1;

-- Q_IN_S3_PATHS (for S3_RAW_INBOX): SELECT s3_path FROM silver_aa_internal.raw_sources WHERE tenant_id = $1;
```

`[S3]` `S3_RAW_INBOX`: `ListObjectsV2(Bucket=bronze_bucket(), Prefix=f"raw-inbox/{MASTER}/")`, paginated, keys ending
`.xlsx`/`.xls`; `not_ingested = |keys − {s3_path}|`, `objects = |keys|`. `S3_BRAND`: same on `Prefix="brand-identity/"`;
`objects`, `tenant_prefixes` = distinct second path segment. Stop after 10 pages (10,000 keys) and mark the row
"≥ N". The ECS task role already has `s3:ListBucket` (`modules/ecs/main.tf:242`, Resource `*`); no Infra change.

### 2.2 Raw, S1, Master, review, SEO

```sql
-- Q_RAW
SELECT count(*)::int AS rows,
       count(*) FILTER (WHERE source_status = 'trashed' OR deleted_at IS NOT NULL)::int AS trashed,
       count(*) FILTER (WHERE source_status = 'superseded' AND deleted_at IS NULL)::int AS superseded,
       count(*) FILTER (WHERE pipeline_status = 'hitl_rejected')::int AS hitl_rejected,
       count(*) FILTER (WHERE source_status = 'active' AND deleted_at IS NULL)::int AS live,
       count(*) FILTER (WHERE source_status = 'active' AND deleted_at IS NULL
                          AND (src_itineraries IS NULL OR btrim(src_itineraries) = ''))::int AS live_no_itinerary,
       count(*) FILTER (WHERE source_status = 'active' AND deleted_at IS NULL
                          AND (country_iso2 IS NULL OR country_raw_unresolved IS NOT NULL))::int AS live_country_unresolved,
       count(*) FILTER (WHERE source_status = 'active' AND deleted_at IS NULL
                          AND lifecycle_stage <> 'active')::int AS live_lifecycle_not_active
  FROM silver_aa_internal.raw_tours WHERE tenant_id = $1;

-- Q_S1 (S1 page floor, admin_pipeline.py get_all_tours)
WITH e AS (
  SELECT rt.tour_id,
         EXISTS (SELECT 1 FROM gold_aa_internal.published_tours pt WHERE pt.tour_id = rt.tour_id
                    AND pt.master_status = 'active' AND pt.deleted_at IS NULL) AS has_master,
         EXISTS (SELECT 1 FROM silver_aa_internal.generated_content g WHERE g.tour_id = rt.tour_id) AS written,
         EXISTS (SELECT 1 FROM silver_aa_internal.review_queue q WHERE q.tour_id = rt.tour_id
                    AND q.review_status = 'pending') AS in_review
    FROM silver_aa_internal.raw_tours rt
   WHERE rt.tenant_id = $1 AND rt.source_status = 'active' AND rt.deleted_at IS NULL
     AND rt.src_itineraries IS NOT NULL AND btrim(rt.src_itineraries) <> '')
SELECT count(*)::int AS eligible,
       count(*) FILTER (WHERE has_master)::int AS with_master,
       count(*) FILTER (WHERE NOT has_master AND NOT written)::int AS never_written,
       count(*) FILTER (WHERE NOT has_master AND in_review)::int AS in_review_no_master,
       count(*) FILTER (WHERE NOT has_master AND written AND NOT in_review)::int AS written_no_master_other
  FROM e;

-- Q_MASTER: coverage.py master.quality + master.newer_version_waiting (newest_status IN ('pending','hitl') →
--   newer_waiting_review; ('rejected','failed') → newer_rejected) + emb.dead_and_tenant_columns
--   (published_tours_content_embedding_nonnull), folded into one statement with the LIVE CTE.
-- Q_REVIEW:  SELECT count(*) FILTER (WHERE review_status = 'pending')::int AS pending FROM silver_aa_internal.review_queue;
-- Q_SEO:     coverage.py seo.coverage (with_row, fresh_ideas_v3, with_paa).
```

### 2.3 A-series (coverage.py, unchanged except dropping sample arrays and per-country ROLLUP)

- `Q_ATOMS` = `atoms.coverage` (live, with_atoms, empty_marker_only, atoms, place_atoms, atoms_older_than_master).
- `Q_SEG` = `segments.tour_coverage` (total row only: `with_place_atoms`, `with_segment`) +
  `segments.dead_member_rows` (`member_rows`, `rows_on_dead_atoms`) + `segments.inventory`.
- `SEG_CLASSIFY` (slow tier) = coverage.py `segment_classification()` over `NO_MEMBER_ATOMS`, imported in-process from
  `services.acp_contract.segment_matching` (`SegmentAtom`, `forms_segment`), plus one new output:
  `all_excluded_tours` = tours in `Q_SEG` "place tours without a segment" whose every non-member atom is
  `excluded_by_rule` (the expected gap of `seg.tours`; 9 today). 2.1 s on Dev; runs at most every 10 min.
- `Q_GC` = the newest succeeded platform `recompute` job:
  ```sql
  SELECT (result->'segment_gc'->>'orphans')::int AS orphans, (result->'segment_gc'->>'deletable')::int AS deletable,
         (result->'segment_gc'->>'kept')::int AS kept, result->'segment_gc'->>'mode' AS mode, finished_at
    FROM shared.job WHERE kind = 'recompute' AND status = 'succeeded' AND result->>'scope' = 'platform'
     AND jsonb_typeof(result->'segment_gc') = 'object'
   ORDER BY finished_at DESC NULLS LAST LIMIT 1;
  ```
  (The CIS stage itself counts orphans; no second definition. The row shows the job's `finished_at` as its own "as of".)
- `Q_RANK` = `ranking.tour_coverage` + `SELECT count(DISTINCT market) AS markets FROM acp_contract.atom_ranking WHERE
  superseded_at IS NULL`.
- `Q_ROUTE` = `routes.by_country` total row (`with_route`) + `routes.hubs` (`current_routes`, `current_routes_no_hub`).
- `Q_PAA` = `paa.ranked_segment_landing` + `SELECT max(current_date - max_day) ... ` written as:
  ```sql
  SELECT max(age_days)::int AS oldest_market_age_days
    FROM (SELECT market, (current_date - max(retrieved_on)::date) AS age_days
            FROM acp_contract.search_demand
           WHERE market IN ('AU', 'DE', 'FR', 'NL', 'UK', 'US') GROUP BY market) m;
  ```
  The market list = the ranking markets (`Q_RANK`), passed as a parameter, not hard-coded, in the build.
- `Q_EMB` = `emb.atom_embedding_landing_scope` + `emb.atom_embedding_totals`.

### 2.4 Places, cards, photos (coverage.py)

- `Q_GEO` = `geo.by_country` total row (`built`, `with_served_component`, `in_current_graph`, `components`,
  `components_no_destination`, `components_on_inactive_atoms`) + `geo.place_name_status` summed (`names_unknown`,
  `names_pending`, `names_total`) + `SELECT count(*) FILTER (WHERE status IN ('ok','approximate')) AS shapes_usable,
  count(*) AS line_shapes FROM geo.place_shape WHERE kind = 'line'`.
- `Q_CARD` = `cards.by_country` total row (`place_atoms`, `linked`, `miss_rows`, `no_row`, `tours_with_a_card`).
- `Q_PHOTO` = `photos.by_country` total row (`with_photo_on_current_tour`) + `photos.served_destinations` +
  `SELECT count(*) FILTER (WHERE status = 'unmatched') AS unmatched, count(*) AS photos FROM shared.place_photo`.

### 2.5 Tenants and T-series

```sql
-- Q_TEN
WITH t AS (SELECT tenant_id FROM shared.tenants
            WHERE is_active AND cancelled_at IS NULL AND tenant_id <> $1)
SELECT (SELECT count(*) FROM t)::int AS active,
       (SELECT count(*) FROM shared.tenant_members m JOIN t USING (tenant_id) WHERE m.status = 'active')::int
           AS members_active,
       (SELECT count(DISTINCT b.tenant_id) FROM shared.tenant_brand_rules b JOIN t USING (tenant_id)
         WHERE b.is_active AND btrim(coalesce(b.system_prompt, '')) <> '')::int AS with_filled_brand,
       (SELECT count(*) FROM acp_shared.tenant_config c JOIN t USING (tenant_id)
         WHERE cardinality(c.markets) > 0 AND cardinality(c.channels) > 0)::int AS with_config;

-- Q_BRAND
SELECT count(*)::int AS versions, count(*) FILTER (WHERE source_type = 'docx_parse')::int AS versions_docx
  FROM shared.tenant_brand_rule_versions;

-- Q_T2 (coverage.py tenant.versions_vs_master + QA)
WITH latest AS (
  SELECT DISTINCT ON (v.tenant_id, v.published_tour_id) v.tenant_id, v.published_tour_id, v.created_at, v.qa_status
    FROM gold_aa_internal.tenant_tour_versions v ORDER BY v.tenant_id, v.published_tour_id, v.version_number DESC)
SELECT count(*)::int AS tenant_tours,
       count(*) FILTER (WHERE l.created_at < p.updated_at)::int AS older_than_master,
       count(*) FILTER (WHERE p.master_status <> 'active' OR p.deleted_at IS NOT NULL)::int AS on_inactive_master,
       count(*) FILTER (WHERE l.qa_status IN ('failed', 'escalated'))::int AS qa_failed_or_escalated
  FROM latest l JOIN gold_aa_internal.published_tours p ON p.id = l.published_tour_id;

-- Q_PLAN:  SELECT count(*)::int AS quarter_plans FROM acp_shared.quarter_plan;
-- Q_T7
WITH live_seg AS (SELECT DISTINCT m.segment_id FROM acp_contract.atom_segment_member m
                    JOIN acp_contract.v_active_tour_atoms a ON a.atom_id = m.atom_id AND NOT a.deleted)
SELECT s.state, count(*)::int AS n,
       count(*) FILTER (WHERE s.segment_id IS NOT NULL
                          AND NOT EXISTS (SELECT 1 FROM live_seg l WHERE l.segment_id = s.segment_id))::int AS on_dead_segment
  FROM acp_shared.subject s GROUP BY 1;
-- Q_T8 = coverage.py tenant.angle_requests, summed (requests, on_inactive_atom).
-- Q_T9
SELECT count(*)::int AS pieces, count(*) FILTER (WHERE status = 'approved')::int AS approved,
       count(*) FILTER (WHERE status = 'held')::int AS held,
       count(*) FILTER (WHERE content_embedding IS NOT NULL)::int AS embedded
  FROM acp_shared.content_piece;
-- Q_PUB (latest row per piece + channel)
WITH latest AS (SELECT DISTINCT ON (piece_id, channel) status FROM acp_shared.publish_log
                 ORDER BY piece_id, channel, created_at DESC)
SELECT status, count(*)::int AS n FROM latest GROUP BY 1;
-- Q_DELIVER: SELECT count(*)::int AS pages FROM acp_deliver.tenant_tour_pages;
-- Q_AA_CONTENT
SELECT count(*)::int AS items, count(*) FILTER (WHERE i.retired_at IS NULL AND EXISTS (
         SELECT 1 FROM gold_aa_internal.aa_content_version v
          WHERE v.content_id = i.content_id AND v.status = 'published'))::int AS published_items
  FROM gold_aa_internal.aa_content_item i;
```

(Critic correction: `publish_log.status` IS enumerated by `publish_log_status_check`: `requested`, `published`,
`unpublished`, `failed`. `pub.failed` reads `failed`; nothing left to confirm. Note `Q_PUB` counts (piece, channel)
pairs while `pub.published` is "of approved pieces" (per piece): use `count(DISTINCT piece_id) FILTER (status =
'published')` for that row so numerator and denominator have the same unit.)

`Q_T7` critic fix: add `AND s.state IN ('proposed', 'picked')` to the `on_dead_segment` FILTER.

### 2.6 TripPlanner over the catalog views `[tenant pool]`

One `catalog_connection(tenant_pool)` transaction (READ ONLY, REPEATABLE READ, the pool's 15 s statement_timeout,
`app.tenant_id = ''`), statements in sequence:
- `C_TP.layers` = `aa990_reader_checks.TP_TOUR_LAYERS_SQL` without the three sample arrays.
- `C_TP.components` = `TP_COMPONENTS_SQL` minus the `v_component_embedding` and `geo.tour_place` sub-selects
  (aa_app_user has no grant on either): `served_components`, `stale_components`, `embedded_components` → 
  `unembedded_components = served − embedded`.
- `C_TP.retired` = `TP_RETIRED_SQL` minus `builds_not_marked` (geo); `retired_served = tours + components + stops + days`.
- `C_TP.outbox` = `SELECT idempotency_key FROM catalog.v_tour_lifecycle_outbox` (keys only; ~10 rows today). Then on the
  cis_app pool: `SELECT count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM shared.job j WHERE j.idempotency_key =
  'tripplanner_purge:' || k)) AS events_without_job, count(*) AS events FROM unnest($1::text[]) k` (TP_PURGE_SQL, split
  across the two pools).

### 2.7 Pins (TripPlanner view + CIS resolution)

`V_TP_PINS`: read `tripplanner.v_ops_pin_components` (§3.1) as cis_app, then resolve on the cis_app pool exactly like
`aa990_reader_checks.chain_sql` (map first, then `geo.component_redirect`, ≤ 5 hops, cycle-safe), with
`unnest($1::text[], $2::text[], $3::bigint[])` as the `pins` input instead of `trip_events`:
`served` = resolved id is a served component (the `catalog.v_tour_component` rule on base tables: `geo.tour_place` of a
live `source_key`, destination `SERVED_DEST`; or check against the tenant-pool component id set from §2.6),
`no_component_row` = no `geo.tour_place` row, `on_retired_or_paused` = row exists but the source is not live.
Pins are counted per (component, trip) pair: `pins = sum(trips)`.

### 2.8 Booking supply (existing contract views, no new grant)

```sql
-- Q_SUPPLY
WITH bk AS (
  SELECT 'hotel'::text AS t, id::text AS id, (status = 'active') AS active, (destination_id IS NULL) AS no_dest
    FROM booking.v_supply_hotels
  UNION ALL
  SELECT 'service', id::text, (status = 'active'), (destination_id IS NULL) FROM booking.v_supply_services)
SELECT count(*) FILTER (WHERE bk.active)::int AS bk_active,
       count(*) FILTER (WHERE bk.active AND e.id IS NOT NULL)::int AS mirrored_active,
       count(*) FILTER (WHERE bk.active AND e.content_status = 'published')::int AS published_active,
       count(*) FILTER (WHERE bk.active AND bk.t = 'hotel' AND bk.no_dest)::int AS hotels_no_destination
  FROM bk LEFT JOIN shared.supply_entity e
         ON e.source_system = 'booking' AND e.entity_type = bk.t AND e.source_id = bk.id;
```

(Critic corrections: `supply_entity_source_system_check` pins `source_system = 'booking'`, nothing to confirm.
`published_version_id` stays set after unpublish (today both entities are inactive + `unpublished` with a published
version id), so "published" reads `content_status = 'published'`. Join on `entity_type` too.)

---

## 3. Data access: owner views and the CRM endpoint

Rules followed: `docs/database/schema-ownership.md` rule 2 (other apps read only through contract views the owner
grants in its own migration; no table/column grant) and rule 5 (cross-owner grants unguarded, after the role exists);
contracts README rule 5 (producer grants SELECT to the consumer role); lessons: guards by named allow-list (`v_ops_*`,
S243 AA-858/860), a re-applied migration must not trip an older guard, integration test runs the real SQL on a temp
cluster (S246/S231). `cis_app` exists since rl-001, so grants are plain `GRANT ... TO cis_app`.

### 3.1 TripPlanner — tp-020 `migrations/020_ops_data_coverage_views.sql` (run as `tp_owner`)

```sql
CREATE OR REPLACE VIEW tripplanner.v_ops_data_totals AS
SELECT 'sessions'::text AS metric, count(*)::bigint AS n FROM tripplanner.sessions
UNION ALL SELECT 'trip_drafts', count(*) FROM tripplanner.trip_drafts
UNION ALL SELECT 'trip_drafts_sent', count(*) FROM tripplanner.trip_drafts WHERE status = 'sent'
UNION ALL SELECT 'trips_with_events', count(DISTINCT trip_id) FROM tripplanner.trip_events
UNION ALL SELECT 'pin_events', count(*) FROM tripplanner.trip_events WHERE event_type = 'add_component'
UNION ALL SELECT 'component_id_map_rows', count(*) FROM tripplanner.component_id_map
UNION ALL SELECT 'customers', count(*) FROM tripplanner.customers
UNION ALL SELECT 'traveller_accounts', count(*) FROM tripplanner.traveller_accounts
UNION ALL SELECT 'outbox_rows', count(*) FROM tripplanner.outbox
UNION ALL SELECT 'narration_cache_rows', count(*) FROM tripplanner.narration_cache;

-- One row per pinned component id (no trip id, no session, no payload text): the CIS page resolves it.
CREATE OR REPLACE VIEW tripplanner.v_ops_pin_components AS
WITH pins AS (
  SELECT DISTINCT e.trip_id, e.payload->>'component_id' AS cid
    FROM tripplanner.trip_events e
   WHERE e.event_type = 'add_component' AND e.payload ? 'component_id')
SELECT p.cid AS component_id, m.new_id::text AS mapped_id, count(*)::bigint AS trips
  FROM pins p LEFT JOIN tripplanner.component_id_map m ON m.old_id::text = p.cid
 GROUP BY p.cid, m.new_id;

GRANT USAGE ON SCHEMA tripplanner TO cis_app;     -- already held since tp-015; repeated, idempotent
GRANT SELECT ON tripplanner.v_ops_data_totals, tripplanner.v_ops_pin_components TO cis_app;
```
Critic additions (copy tp-015 exactly): `REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON <both views> FROM tripplanner;`
(default privileges FOR ROLE tp_owner hand role `tripplanner` DML on every new view, tp-015 line 71),
`COMMENT ON VIEW … 'tp-020 (AA-xxx): … aggregates only, contract ops.data_coverage.v1, read by AA-CIS-App
/admin/data-coverage (role cis_app)'`, and the `INSERT INTO shared.schema_versions ('tp-020', …)` registration row.
`v_ops_pin_components` reads `trip_events.payload` (tagged `pii:free_text`); it exposes only `payload->>'component_id'`
(a CIS catalog key) — say so in the view comment so the DM-6.1 reviewer does not have to re-derive it.
Guard `current_user = 'tp_owner'`, role `cis_app` exists; re-runnable (CREATE OR REPLACE, grants repeat). Cost: four
table scans of < 500 rows. Undo: DROP VIEW + no REVOKE of USAGE (tp-015 still needs it).

### 3.2 Booking — bk-025 `migrations/025_ops_data_coverage_views.sql` (run as `bk_owner`)

```sql
CREATE OR REPLACE VIEW booking.v_ops_data_totals AS
SELECT 'trip_plans'::text AS metric, count(*)::bigint AS n FROM booking.trip_plans
UNION ALL SELECT 'trip_plans_sellable', count(*) FROM booking.trip_plans WHERE sellable
UNION ALL SELECT 'trip_plan_components', count(*) FROM booking.trip_plan_components
UNION ALL SELECT 'departures_open', count(*) FROM booking.departures
           WHERE status IN ('scheduled', 'guaranteed') AND start_date >= current_date
UNION ALL SELECT 'suppliers_active', count(*) FROM booking.suppliers WHERE status = 'active'
UNION ALL SELECT 'contracts_published', count(*) FROM booking.supplier_contracts
           WHERE status = 'published' AND valid_from <= current_date AND (valid_to IS NULL OR valid_to >= current_date)
UNION ALL SELECT 'rates_current', count(*) FROM booking.supplier_rates
           WHERE valid_from <= current_date AND (valid_to IS NULL OR valid_to >= current_date)
UNION ALL SELECT 'media_active', count(*) FROM booking.entity_media WHERE status = 'active'
UNION ALL SELECT 'media_active_with_rights', count(*) FROM booking.entity_media WHERE status = 'active' AND usage_rights
UNION ALL SELECT 'customers', count(*) FROM booking.customers WHERE deleted_at IS NULL
UNION ALL SELECT 'b2b_partners_active', count(*) FROM booking.b2b_partners WHERE status = 'active'
UNION ALL SELECT 'b2b_holds_active', count(*) FROM booking.b2b_holds WHERE status = 'active';

-- Catalog keys of trip plans only (no price, channel, notes: the conf:commercial columns stay out), so CIS can count
-- plans whose tour left the live catalogue against its own tables.
CREATE OR REPLACE VIEW booking.v_ops_trip_plan_keys AS
SELECT source_system, source_id, sellable FROM booking.trip_plans;

GRANT SELECT ON booking.v_ops_data_totals, booking.v_ops_trip_plan_keys TO cis_app;
```
Critic additions (copy bk-017 exactly): `REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON <both views> FROM booking;`
(default privileges FOR ROLE bk_owner, bk-017), `COMMENT ON VIEW` naming the contract and the reader, the guard block
(`current_user = 'bk_owner'`, `cis_app` exists) and `INSERT INTO shared.schema_versions ('bk-025', …)`.
`v_ops_trip_plan_keys` is row-level, unlike every other `v_ops_*` view ("aggregates only" is the bk-017 comment
wording); the CIS 244 guard accepts it by name, but its comment must say "catalog keys only, no conf:commercial
column" and the integration test asserts its exact column list `(source_system, source_id, sellable)`.
`V_BK_KEYS` on the CIS side: `count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM silver_aa_internal.raw_tours rt JOIN
gold_aa_internal.published_tours pt ON ... LIVE ... WHERE rt.source_key = k.source_id))` for `source_system = 'cis'`.
Alternative if the keys view is refused (it is row-level, though not personal or commercial): Booking computes
`trip_plans_orphaned` inside `v_ops_data_totals` by reading `catalog.v_tour`; that needs `bk_owner` SELECT on
`catalog.v_tour` (a CIS catalog-recipe grant, today only role `booking` holds it). The keys view is simpler.

### 3.3 Infra and root bookkeeping (same PRs as the owners' Infra copies)

- AA-CIS-Infra: byte-identical copies `db/migrations/tripplanner/020_*.sql`, `db/migrations/booking/025_*.sql`;
  `db/owners.yaml` `consumer_grants` (4 rows, `status: contract`, `expected_from: tp-020 / bk-025`);
  `db/isolation_probe.py` `CONSUMER_GRANTS` (4 rows) + its test; `db/rls_catalogue_rules.py` rule `g` allow-list
  entries (4: `tripplanner.v_ops_data_totals:cis_app`, `tripplanner.v_ops_pin_components:cis_app`,
  `booking.v_ops_data_totals:cis_app`, `booking.v_ops_trip_plan_keys:cis_app`; schema USAGE keys
  `booking:cis_app` / `tripplanner:cis_app` already exist). Then DB Migrate `check` → `apply` (tp, bk; idle guard:
  every job table idle), then the `bot/db-schema-reference` PR.
  **Critic fix (ordering):** the canonical `rls_catalogue_rules.py` is AA-CIS-App `tests/integration/
  rls_catalogue_rules.py`; Infra holds a byte-identical copy checked by its Migration Copy Guard. The 4 rule-`g`
  entries therefore land first in a CIS App PR, then the Infra copy — before DB Migrate apply, or the nightly dump
  lists 4 unallowlisted violations in `db-schema-reference.md`.
- Root: `docs/contracts/README.md` registry rows for `ops.data_coverage.v1` (4 views, metric names are the contract:
  add, never rename; the `ops.overview.v1.md` file the bk-017 comment cites does not exist: write
  `docs/contracts/ops.overview.v1.md` covering both families in the same PR); `schema-ownership.md` consumer-grant
  column for `tripplanner` and `booking`.

### 3.4 CRM — `crm.ops.v1` minor 1.4, `GET /crm/ops/v1/data-coverage` (AA-Partner)

> Renumbered 1.3 → 1.4 in the S252 fix round 2: minor 1.3 went to AA-979 P2b (root #267, `POST /tenants/{tenant_id}/studio-invitations`, AA-Partner #74) while this build was open.

A view is not acceptable: ADR 0008a decision 1 and `schema-ownership.md` (`crm` row: "Nobody, in either direction ...
The isolation probe asserts 42501 both ways"). The CIS admin already talks to the CRM over `crm.ops.v1` with the
signed-in staff member's own WORKFORCE token (`api/services/crm_console.py`), so the new read is one more allowed
route there.

Response (additive, every object `additionalProperties: false`, no `x-pii`, no trip/proposal/traveller/revenue field):
```json
{"as_of": "...",
 "agencies": {"active": 0, "locked": 0, "offboarding": 0, "offboarded": 0, "synthetic": 0},
 "members": {"active": 0, "invited": 0, "disabled": 0},
 "catalog_cache": {"served": 892, "paused": 0, "retired": 0, "last_full_pass_at": "...", "last_ok_at": "...",
                   "failures": 0, "last_error_class": null}}
```
Auth: route class OPS read (`cis-admin` or `crm-platform-admin`). CIS: add `("GET", r"/data-coverage")` to
`crm_console.ALLOWED`, read timeout 2 s. Contract CI: bump `info.version` to 1.4 in `crm.ops.v1.openapi.yaml` (the
1.1 → 1.2 precedent edits the same file), samples under `samples/crm.ops.v1/`, checker policy unchanged (it already
forbids `trip_count`, `revenue`, `pii:`). Because the token is the caller's, the CRM group is computed only for
`admin` callers (admin-only page in v1, D10).
Critic additions: (1) the contract says every crm.ops.v1 read lands in "that agency's own audit log" as `ops_read`;
this route is platform-wide aggregates, so the 1.4 text must say where it is audited (one platform-level `ops_read`
event, or none) — not one event per agency every 10 min. (2) The CRM source is cached under its own Redis key and
refreshed only on an admin request with a Cognito token (a legacy password session gets `na:
cognito_session_required`, crm_console rule); it is never part of the shared slow-tier key a token-less build fills.
(3) `crm.cache_served` "must equal" compares against the CIS live count as of `last_full_pass_at`: a tour published
after the last pass is `ok (next pass)`, red only when the pass is older than 120 min (same rule as
`crm.cache_age_min`), or every publish turns the row red for up to an hour.

---

## 4. CIS API

### 4.1 Endpoint

`GET /admin/data-coverage` (router `api/routers/admin_data_coverage.py`, prefix `/admin/data-coverage`,
`dependencies=[Depends(staff_policy)]`), query `refresh: bool = false`.

Response model (`api/schemas/data_coverage.py`, pydantic, so OpenAPI documents it):
```
DataCoverageResponse { as_of: datetime, generated_ms: int, cached: bool, stale: bool, live_tours: int | null,
  groups: [ CoverageGroup { id, label, rows: [ CoverageRow ] } ], sources: { <query key>: SourceStatus } }
CoverageRow { id: str, label: str, value: int | null, unit: "tours"|"atoms"|"rows"|"files"|"days"|"minutes"|...,
  denominator: int | null, denominator_label: str | null, pct: float | null, missing: int | null,
  expected_gap: int | null, expected_note: str | null, kind: "must"|"backlog"|"info",
  status: "ok"|"gap"|"info"|"na", issue: str | null, drill: str | null, source: str, as_of: datetime | null }
SourceStatus { status: "ok"|"error"|"timeout"|"unavailable", reason: str | null, timing_ms: int, tier: "fast"|"slow" }
```
No ids, names or samples anywhere in the response.

### 4.2 Module layout

`api/services/data_coverage/`:
- `queries.py` — the SQL of §2 as constants (CTE fragments imported from one place; coverage.py copied in, with
  `$1` binding).
- `registry.py` — one `Source` per query (key, pool: `cis` | `tenant` | `s3` | `crm`, tier, timeout) and one `Row`
  per §1 line (id, group, label, value/denominator/expected extractors, kind, issue, drill). The page order is the
  registry order.
- Critic fix: each `Row` carries an explicit **`polarity`**: `coverage` (missing = denominator − value, e.g.
  `atoms.tours`), `defect` (missing = value, the denominator is context only, e.g. `atoms.older_than_master`,
  `seg.dead_member_rows`, `t8.inactive_atoms`), or `threshold` (missing = max(0, value − limit), e.g.
  `paa.demand_age_days` ≤ 30, `crm.cache_age_min` ≤ 120). §1 mixes all three under the same "Of" column; without the
  field `build.py` cannot tell them apart. `CoverageRow` exposes `polarity` so the CSV and the UI need not guess.
  A row whose value is from the fast tier and expected gap from the slow tier (`seg.tours`) shows status `na: expected
  gap unavailable` when the slow source failed, not `gap`.
- `build.py` — `build(pool, tenant_pool, redis, *, caller_role, authorization, refresh)`; runs sources, derives rows,
  computes status: `missing = denominator − value` (or `value` for "should be 0" rows); `ok` if `missing <=
  (expected_gap or 0)`; else `gap`; `info` rows never get a status colour; a row whose source failed is `na` with the
  source's reason.
- `cache.py` — reuse `api/services/ops_overview/cache.cached_section` with a `key_prefix` parameter
  (`admin:data-coverage`, version `v1`) instead of copying it; tiers: `fast` 60 s, `slow` 600 s, error results 60 s,
  last good 24 h, single-flight `SET NX` lock 30 s. `refresh=1` recomputes the fast tier only if its cached copy is
  older than 15 s (stops refresh hammering); the slow tier keeps its TTL.

### 4.3 Time and failure budget

- Each CIS / TripPlanner-view / Booking-view source: its own pool connection and `BEGIN READ ONLY` transaction,
  `SET LOCAL statement_timeout = '4s'`, `lock_timeout = '1s'`, wrapped in `asyncio.wait_for(…, 5 s)`; at most **3**
  concurrent connections from `app.state.pool` (max_size 10) through an `asyncio.Semaphore(3)`.
- Tenant-pool catalog group: one `catalog_connection` (its own semaphore and 15 s timeout), `wait_for` 8 s for the group.
  **Critic fix:** that semaphore is `MAX_CONCURRENT_READS = 1` per api task and the tenant pool has 2 connections per
  task (`TENANT_POOL_MAX_SIZE`), shared with every Content studio tenant route and the CRM catalog sync. The group
  therefore goes in the **slow tier (600 s)**, never fast; its statements (`TP_TOUR_LAYERS_SQL` aggregates
  `v_tour_place` / `v_tour_day` over all 892 tours, never timed: `aa990-run.txt` has no timings) are first measured
  with `EXPLAIN (ANALYZE, BUFFERS)` through DB Migrate run-script as `aa_app_user`; if the group exceeds ~2 s it is
  split into one `catalog_connection` per statement (releasing the gate between them) so a CRM sync page waits at
  most one statement.
- S3: `asyncio.to_thread` boto3 calls, 5 s per listing, max 10 pages. CRM: 2 s (crm_console read timeout).
- Whole build: deadline 12 s; a source not started by then → `na: time budget`. Expected wall time on Dev: ≈ 1 s
  fast tier (coverage.py measured 1.2 s for these queries serially; 3-way parallel), ≈ 3 s slow tier.
- Errors: `UndefinedTable` / `InsufficientPrivilege` / `InvalidSchemaName` on an owner view → `unavailable:
  contract_view_missing` (same tuple as `ops_overview/activity._CONTRACT_ERRORS`), so the API can ship before tp-020 /
  bk-025 are applied. Every failure logs one `data_coverage_source_failed` line (key, error class, ms), never SQL text.
- Timing per source in `sources[key].timing_ms`; one structlog line per build with total ms and cache hits.

### 4.4 Authorization

- (Critic fix, D10) `api/core/staff_authz.py`: `POLICY[("GET", "/admin/data-coverage")] = OPS_READ` (admin only,
  like `/admin/overview`); no new capability. Not a machine route.
- `frontend/lib/rbac.ts`: `{ prefix: "/admin/data-coverage", roles: ["admin"] }` in the admin-only block (prefixes
  stay disjoint). `tests/unit/test_aa882_staff_authz.py` keeps both in sync; `test_aa882_route_policy.py` snapshot
  gains the route.
- If reviewers are added later (open question 2): the UI renders `Open` only when `canSeePage(role, drill)`, since
  most drill pages are admin-only; CRM rows are `na` for them.

### 4.5 OpenAPI

`docs/api/openapi.json` regenerated (the Unit Tests check `test_aa899_openapi_export.py` fails when stale). A new
`/admin/*` GET is additive: the API contract job (oasdiff 1.33.0) reports no breaking change; `/admin/*` breaking
changes are warnings anyway.

---

## 5. Admin UI

- Route `frontend/app/admin/data-coverage/page.tsx` (client page, kit only: `AdminShell` chrome, `primitives`,
  `DataTable`, `csv.ts`). Nav: `adminNav.tsx` Platform › Overview group, second item
  `{ href: "/admin/data-coverage", icon: <ListChecks/> or <Table2/>, label: "Data coverage" }`; reviewers see the
  Platform section with just this item (`visibleSections` already handles it).
- Header: title "Data coverage", subtitle "Live counts from raw upload to TripPlanner, Booking and CRM. Numbers only.",
  `As of 10:42:13 UTC (cached 23 s)` + a `stale` badge when served from the last good copy, **Refresh** button
  (calls `?refresh=1`, disabled 15 s after use), **Export CSV** (all rows of all groups:
  stage, metric, count, of, %, missing, expected gap, expected note, status, source, as of).
- Summary strip (4 numbers): live tours · rows `gap` (red) · rows `backlog` amber · rows `na`.
- Body: one section per group (§1.1–1.9) with a stage header (label + "n rows · k gaps"), each a `DataTable`
  (`compact`, `paginate={false}`, `searchable={false}`, `enableCsv={false}`, `stickyHeader`), columns:
  Metric (label + issue chip) · Count (right, tabular-nums) · Of · % (bar-free, number only) · Missing · Expected gap
  (number + note in muted text) · Status (kit `Badge`: green "OK", red "Gap", amber "Backlog", grey "Info",
  grey "n/a" with reason tooltip) · Open (link icon to `drill`).
  Colour rule exactly the API `status` + `kind` (UI computes nothing).
- 1440: two-column header, tables at full width (≤ 8 columns fit without sideways scroll, as S251 compact tables).
  390: DataTable phone card mode (label rows per cell; `Open` column `meta.hideLabelOnCard`), stage headers stay,
  summary strip wraps 2 × 2, 16 px gutters. English only (pages default to English).
- Empty / error: API 5xx → page-level error with Retry; a group whose every row is `na` shows the reason once.
- Loading: skeleton rows per group; numbers render as they arrive (single call, so all at once).

---

## 6. Tests, PR split and order, cost, live verification

### 6.1 Tests

- TripPlanner (tp-020): integration test on the temp cluster (lesson S246): views exist with exactly the documented
  columns, return aggregates, `has_table_privilege('cis_app', view, 'SELECT')` true and false on every base table,
  guard refuses a non-`tp_owner` runner, file re-runs cleanly.
- Booking (bk-025): same, modelled on `backend/tests/integration/test_bk017_ops_views.py`; `test_migration_guard.py`
  updated; assert no `conf:commercial` column is exposed by `v_ops_trip_plan_keys`.
- AA-CIS-Infra: `test_isolation_probe.py` with the 4 new consumer cells; owners.yaml/rls rules lint.
- AA-Partner: endpoint unit + route-class test (OPS read only), response allow-list test, contract sample validated by
  root `contracts.yml`.
- CIS API (`tests/unit/test_data_coverage_*.py`): registry completeness (every row has group, label, kind, source,
  a drill that is a nav href or null); status maths (ok / gap / info / na, expected gap, "should be 0" rows); one source
  raising → only its rows `na`; a `wait_for` timeout → `na: timeout`; `contract_view_missing` mapping; cache tiers,
  lock, last-good, refresh throttle; reviewer 200 / content 403 / viewer 403 / machine 403; CRM skipped for reviewer;
  response has no key named `*_id`, `sample*`, `name` (no-ids guard). Integration (`tests/integration/`, temp
  cluster with all CIS migrations): every SQL in `queries.py` executes as `cis_app` on an empty DB (UndefinedColumn
  surfaces, lesson S231) and `EXPLAIN` shows no sequential scan on `shared.llm_call_log` / `decision_log` (the two
  big tables are never read). OpenAPI export test regenerated.
- UI: Playwright smoke (preview, public smoke only) that the route redirects to login; live evidence spec (below).

### 6.2 PR split and order

1. **AA-TripPlanner-Web** — tp-020 views + test (risky: grants → independent review subagent before merge).
2. **AA-Booking** — bk-025 views + test (same review).
3. **AA-Partner** — `crm.ops.v1` 1.4 `/data-coverage` (+ root contract file/samples PR, same day).
3b. (Critic fix) **AA-CIS-App** — rule-`g` allow-list entries in the canonical `tests/integration/
   rls_catalogue_rules.py` + `api/services/data_coverage/defs.py` (shared definitions, open question 10); merged before 4
   so the Infra byte-identical copies match.
4. **AA-CIS-Infra** — copies of tp-020 / bk-025, owners.yaml, isolation probe, RLS rules; then **DB Migrate** check →
   apply (tripplanner, booking), then merge the `bot/db-schema-reference` PR.
5. **AA-CIS-App API** — `api/services/data_coverage/`, router, schemas, staff_authz, openapi.json, tests. Can merge
   before 1–4 (owner-view rows show `n/a: contract_view_missing`); deploy guard: `shared.job` idle.
6. **AA-CIS-App UI** — page, nav, rbac, smoke; after 5 is live.
7. **Root** — contracts registry + `ops.overview.v1.md`, schema-ownership consumer grants, this design moved to
   `docs/audits/2026-10-26-S252-propagation-audit/` (or `docs/architecture/`), backlog row.
Per the S241 D-13 rule the orchestrator merges each PR itself when CI is green; 1, 2 and 4 get an agent review first
(grants / migration).

### 6.3 Cost

$0 in model and DFS spend; no new AWS service or resource. Recurring: DB reads (≈ 40 statements per fast build, at most
one build per minute while someone has the page open), S3 `ListObjectsV2` ≤ 2 prefixes × ≤ 10 pages per 10 min
(< $0.01 / month), one CRM HTTP call per 10 min per admin. No new Redis keyspace cost beyond ~10 KB.

### 6.4 Live verification (orchestrator)

1. After DB Migrate: `aa990`-style run-script or ECS exec as cis_app: `SELECT * FROM tripplanner.v_ops_data_totals`,
   `booking.v_ops_data_totals` return rows; isolation probe workflow green (new cells pass, old 42501 cells unchanged).
2. After CIS deploy (rollout COMPLETED, api + worker same SHA): with the A10b E2E admin
   (`tests/e2e/admin-evidence/`, `E2E_CIS_ADMIN_EMAIL`, Cognito email code), `page.request.get('/api/admin/data-coverage')`:
   200, every group present, `sources[*].status == ok` except documented `na`, `generated_ms < 5000`, no id-like keys.
3. Cross-check 10 rows against a coverage.py run taken the same hour (live tours, atoms, segments, routes, geo.built,
   cards linked, photos, tp components, pins dangling, CRM served): equal or explained by changes in between.
4. Screenshots `/admin/data-coverage` at 1440 × 900 and 390 × 844, light and dark, full page, plus the CSV file
   opened; console has 0 errors; network has no 4xx/5xx; Refresh changes "as of".
5. Reviewer role check: a reviewer session (or the policy unit test, since the E2E identity is admin) sees the page
   and gets `na` on CRM rows.

---

## 7. Open questions (with proposed answers)

1. **Page or tab?** Proposed: own page `/admin/data-coverage` in Platform › Overview (reviewers can open it; Overview is
   admin-only and already dense).
2. **Who sees it?** (Critic correction: the request does not name reviewers.) Proposed: admin only in v1 (D10);
   reviewer later = one rbac line + a capability, with drill links hidden by `canSeePage`.
3. **Hub rule:** 1,106 / 1,261 current routes have no hub, while chain-map says "every current route has a hub".
   Proposed: show the row as backlog "definition to confirm" until the hub rule is settled in the route-detection code
   (hub only for routes that start at a known hub city); then it becomes `must` or `info`.
4. **Per-country split?** Proposed: not in v1 (numbers-only single table); add a country filter in v2 by running the
   same registry with a `country` parameter (coverage.py already has ROLLUP per country).
5. **CRM business numbers (trips, proposals, travellers):** Proposed: never shown (ADR 0008a, controller/processor);
   footnote only.
6. **Booking keys view (`v_ops_trip_plan_keys`) vs a catalog grant to `bk_owner`:** Proposed: keys view (no commercial
   or personal column, no new cross-owner catalog grant).
7. **S3 listing for uploads:** Proposed: yes, slow tier (it is the only record of brand files and of uploads never
   ingested); cost < $0.01 / month.
8. **History / trend?** Proposed: v1 is live-only as asked; a nightly snapshot of the response into a CIS table
   (`shared.data_coverage_snapshot`, one JSON row per day) is a cheap v2 for "what got worse since yesterday".
9. **Expected-gap numbers that need Python (`seg.tours` 9, routes 192):** Proposed: segments use the in-process
   classifier (slow tier); routes stay `info` with the AA-991 nightly parity as the defect signal, because
   re-running `derive_routes` per page view is not worth it.
10. **Where the "Data coverage" numbers meet the AA-991 probe:** (Critic correction: the page DOES repeat ≥ 9 probe
    metrics — `atoms.older_than_master` ↔ `atoms_older_than_master`, `atoms.tours` ↔ `active_tours_without_atoms`,
    `seg.tours` ↔ `tours_with_place_atoms_but_no_segment`, `rank.tours` ↔ `ranking_missing` /
    `active_tours_without_ranking`, `route.tours` ↔ `active_tours_without_route`, `card.no_row` ↔
    `active_place_atoms_without_card_link`, `geo.inactive_atoms` ↔ `geo_tour_place_stale_rows`, `t2.older` ↔
    `tenant_versions_older_than_master`, `t8.inactive_atoms` ↔ `angle_gate_requests_on_inactive_atoms`, `seo.fresh` ↔
    `seo_context_expired_active_tours` — with different definitions: the probe's "active" is Master-only
    (`ACTIVE_PT`, no `raw_tours.source_status` filter, no tenant filter), its `PLACE_ATOM` lacks `NOT
    is_empty_marker`, its "changed" includes `v_tour_liveness`.) Proposed: **one shared definitions module**. Canonical
    `AA-CIS-App api/services/data_coverage/defs.py` (stdlib only: the `LIVE` / `ACTIVE_ATOMS` / `PLACE_ATOM` /
    `SERVED_DEST` fragments with `$1`, plus the SQL of each overlapping metric under the probe's metric name),
    byte-identical copy `AA-CIS-Infra db/coverage_defs.py` under the same Migration Copy Guard as
    `rls_catalogue_rules.py`; `aa991_freshness_probe.py` imports it for those metrics (the probe keeps its own
    staleness/age logic on top), the page imports it, and the S252 `coverage.py` is retired in favour of it. The row
    hover names the probe metric; the footer links the latest probe run. One PR in each repo, CIS first.
