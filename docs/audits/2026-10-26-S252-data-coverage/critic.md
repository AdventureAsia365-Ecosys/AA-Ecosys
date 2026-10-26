# Data coverage design: critic review (S252)

Read-only review of `design.md` against `docs/architecture/db-schema-reference.md` (Verified 2026-10-25, CIS 282 /
tp-019 / bk-024), `.tmp-session/s252/propagation/coverage.py` + `coverage.json`, `aa990-run.txt`, the AA-991 probe,
and code at AA-CIS-App `900f2463`, AA-Booking `8124230`, AA-CIS-Infra `07ed3cc`. No live query was run.
Each fix marked "fixed" was edited into `design.md` in place, with "critic" in the text.

## Blocking (all fixed in design.md)

| # | Where | Problem | Evidence | Fix |
|---|---|---|---|---|
| B1 | §1.1 `in.rows_landed` | Gives a false red on every batch that has a near-duplicate. Staged rows go to `upload_staging`; they are counted in neither `rows_landed` nor `drops`. So parsed = landed + staged + dropped. | `services/ingestion/handler.py` 199–287 | Expected gap now includes `rows_staged`, and `Q_IN_BATCHES` gains a `rows_staged` subquery |
| B2 | §1.1 `in.tour_files_parse_errors` | Always 0, so a `must` row can never fire. `parse_errors` is always `'[]'`, and `update_status(error=)` ignores its argument. | `shared/repository/raw_source_repository.py` | Row dropped; parse failures already show in `in.batches_failed` |
| B3 | §1.1 `in.brand_versions_docx` | No code writes `shared.tenant_brand_rule_versions`; only migration 019 creates it. | grep of api/services/shared | Row dropped |
| B4 | §1.3 | The stage "đã viết vào master" has no current-writer row, so the 82 kept masters are invisible. | `coverage.json` master.version_meta: sonnet-5-5 810, haiku 81, sonnet-4-6 1 | New row `master.writer_v2` from `generated_content.metadata->>'writer_version' = 'v2'`. Expected gap = the kept set (43 golden + 39 elephant = 82), read from one closed `shared.rerun_wave` row `aa645-kept-on-v1`. Nothing is hard-coded and no migration is needed |
| B5 | §2.8 `Q_SUPPLY` | `published_active` counted unpublished rows: `published_version_id` stays set after unpublish (today: 2 inactive `unpublished` rows that still have an id). The join also ignored `entity_type`. | supply_entity checks; `coverage.json` supply.entities | `content_status = 'published'`, plus a join on `entity_type`. The "confirm source_system" note is resolved: the CHECK pins it to `'booking'` |
| B6 | D10, §4.4, Q2 | Says "Requested scope: admin + reviewer", but the request says "từ trang admin" and names no reviewer. In `rbac.ts`, 9 of the drill targets are admin-only, so a reviewer would get broken links, and CRM rows need an admin token. | `frontend/lib/rbac.ts` PAGE_RULES | Admin only in v1. Reuse `OPS_READ`, as `/admin/overview` does, so no new capability. Reviewer moves to Q2 with `canSeePage` gating |
| B7 | §3.3, §6.2 | The PR order breaks the copy guard. The canonical `rls_catalogue_rules.py` is in AA-CIS-App `tests/integration/`, and Infra keeps a byte-identical copy (Migration Copy Guard). The design edits only the Infra copy, and the CIS PR comes after Infra. | header of `db/rls_catalogue_rules.py` | Added PR 3b: CIS canonical allow-list (4 rule-g keys named) first, then the Infra copy, both before DB Migrate apply |
| B8 | §3.1, §3.2 | tp-020 and bk-025 lack the pattern their predecessors use: `REVOKE INSERT,UPDATE,DELETE,TRUNCATE … FROM tripplanner/booking` (default privileges give those roles DML on every new view), `COMMENT ON VIEW`, and the `shared.schema_versions` row. | tp-015 l.71–77, bk-017 l.99–110 | Added to both |
| B9 | §4.3 tenant-pool group | Contention. The catalog gate is `MAX_CONCURRENT_READS = 1` per task and the tenant pool has 2 connections per task, shared with Content studio routes and the CRM catalog sync. A fast-tier 8 s hold every minute can starve them. The statements have never been timed. | `services/catalog_http/reader.py:43`, `aa544_tenant_pool.py:182` | Moved to the slow tier. Measure with EXPLAIN ANALYZE as `aa_app_user` first; split per statement if over ~2 s |
| B10 | Q10 / AA-991 overlap | The claim "does not duplicate those metrics" is false. At least 9 rows repeat probe metrics with different definitions: the probe's "active" counts Masters only, its `PLACE_ATOM` has no empty-marker filter, and its "changed" includes `v_tour_liveness`. The two will drift. | `aa991_freshness_probe.py` 93–104 | Proposed shared module `api/services/data_coverage/defs.py` (canonical, stdlib only) with an Infra copy `db/coverage_defs.py` under the same copy guard. Both the probe and the page import it; `coverage.py` is retired |
| B11 | §4.2 status maths | Rows mix three meanings under one "Of" column: coverage, defect count (`atoms.older_than_master`, `seg.dead_member_rows`, `t8.inactive_atoms`) and threshold (`paa.demand_age_days`, `crm.cache_age_min`). The registry has no field that tells `build.py` which is which. | §1 tables | Added `polarity: coverage|defect|threshold` to `Row` and `CoverageRow`. `seg.tours` shows `na` when its slow-tier expected gap fails |
| B12 | §3.4 CRM | The contract audits every read in each agency's log, so an aggregate route every 10 min means per-agency noise. A token-less or reviewer build could also fill the shared slow cache with `na`. And `cache_served` "must equal" turns red after every publish until the next hourly pass. | `crm.ops.v1.openapi.yaml` description; `crm_console.py` | 1.3 text must name where it is audited (one platform event or none). CRM gets its own cache key, refreshed only by an admin with a Cognito token. `cache_served` is compared as of `last_full_pass_at` |

## Corrected facts (fixed)

- `publish_log.status` **has** a CHECK (`requested|published|unpublished|failed`). The design said it did not. `pub.published` now counts distinct pieces, so it is in the same unit as its denominator "approved pieces".
- `bk.inquiries_stuck` covers the last 400 days (the bk-017 view window), not "all days".
- Place cards are optional enrichment, so `card.*` rows are now `info`, not amber backlog.
- `t7.stale` is restricted to open Subjects (`proposed`/`picked`). Used and cut Subjects are history.
- Added `t4.pool` (latest tenant version `approved`). T1–T4 all live in `tenant_tour_versions`.
- Dropped `SET LOCAL app.tenant_id`: CIS runtime sets no GUC, and every table read has a `<t>_cis_app_all` policy (checked against the dump).

## Checked and correct

- Every other table and column in §2 exists with the stated name and type: raw_sources, pipeline_runs.ingest_details, upload_staging (enum values), raw_tours (`country_iso2`, `country_raw_unresolved`, `lifecycle_stage`), review_queue, tenants, tenant_members, tenant_brand_rules, tenant_config, tenant_tour_versions (`qa_status` CHECK), subject, content_piece, aa_content_item/version, search_demand.retrieved_on, place_shape, all bk-025 Booking columns and CHECK values, and tp-020 TripPlanner columns (`trip_drafts.status` draft|sent, `trip_events.event_type`, `component_id_map`).
- Every CIS table read cross-tenant has a `<t>_cis_app_all` policy, so RLS does not hide other tenants' rows.
- `aa_app_user` has SELECT on every `catalog.*` view used. It has none on `v_component_embedding`, which the design already drops.
- The CIS 244 guard accepts the new views by their `v_ops_` prefix if `cis_app` has SELECT only.
- The ECS task role has `s3:ListBucket` on `*`, and the raw-inbox key format `raw-inbox/{MASTER}/…` matches the upload URL code.
- The purge key `'tripplanner_purge:' || key` matches `tripplanner_purge_job.py`.
- No PII or row data is exposed: tp-020 exposes only catalog component ids and counts; bk-025 keys carry no `conf:commercial` column; CRM sends aggregates only. `llm_call_log` and `decision_log` are never read, and the EXPLAIN guard test covers that.
- Expected-gap notes match the S252 data: 9 all-excluded (transit/unnamed) tours on `seg.tours`; place builds 123/892 (AA-905, in progress); dead members 10,547 and 228 unexplained atoms are real defects, so red is correct; pins dangling 322/371 is a real AA-989 defect.

## Non-blocking (not edited)

- `master.active` cannot go red: its expected gap is in_review + never_written + written_failed, which is exactly its missing count. Make the expected gap `in_review` only, or mark the row info.
- `tp.pins_served` and `tp.pins_dangling` duplicate each other. Keep `pins_dangling` (must) and make `pins_served` info.
- `tp.purge_no_job`: the 4 events without a job date from 23/10. Check whether they predate the AA-987 job. If so, the expected gap is those 4, or they should be backfilled; otherwise it shows red from launch.
- `rank.markets` "Of 6" is hard-coded. Take the market set from config (ranking markets) as `Q_PAA` already does.
- `t0.brand` and `t0.markets` may go red on synthetic or E2E tenants. Exclude `is_canary` tenants or name them in the expected note.
- `Q_IN_DROPS` should filter `s3_source_path LIKE 'raw-inbox/%'` like `Q_IN_BATCHES`, so the two use the same scope.
- `v_ops_pin_components` counts `add_component` pins and ignores `remove_component`, the same as aa990. Say so in the label ("pins ever added").

## Open questions (with proposed answers)

1. Kept-set source for `master.writer_v2`: a closed `shared.rerun_wave` row `aa645-kept-on-v1` with the 82 tour ids (proposed). The alternative is a derived rule: golden set ∪ brand-audit elephant flag. That needs two more joins and the golden set is in S3, so it is not proposed.
2. Shared definitions module (B10): canonical in CIS App and copied to Infra (proposed). The alternative is that the probe writes its metrics to a CIS table and the page reads them. That gives one number, but it needs a new table and is only refreshed nightly.
3. Audit of the CRM aggregate read: one platform-level `ops_read` event per call (proposed), or none, because no agency data is read.
4. `v_ops_trip_plan_keys` is row-level inside an "aggregates only" `v_ops_*` family. Proposed: keep it, with an exact column-list test. The alternative, Booking counting orphans itself, needs a catalog grant for `bk_owner`.
5. Reviewer access: v1 is admin only (proposed). Add reviewers when asked, with drill links gated by `canSeePage`.
6. Pins removed later (`remove_component`): keep the aa990 "ever added" semantics in v1 (proposed) and add net pins in v2.
