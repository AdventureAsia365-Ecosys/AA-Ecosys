# Dead Table Registry census — AA-850 (S255, 28/10/2026)

**Scope.** All 335 objects (274 tables, 1 partitioned table, 60 views) of the 16 schemas in
[`db-schema-reference.md`](../../architecture/db-schema-reference.md) (Verified 2026-10-28 04:28 UTC: CIS 292,
tp-020, bk-032). **Static analysis only** — no data was read; row and counter columns are the reference's
`reltuples` estimate and `pg_stat_user_tables` counters. Exact counts and last-write times come from the DRY RUN
script [`scripts/aa850_dead_table_dry_run.py`](scripts/aa850_dead_table_dry_run.py) (orchestrator step, not run yet).

**Plan:** [`wave1-quarantine-plan.md`](wave1-quarantine-plan.md). **Drafts:** [`migrations/`](migrations/) (not in any
repo yet). **Canonical registry:** [`docs/architecture/dead-table-registry.md`](../../architecture/dead-table-registry.md)
(ARCH-09) gets the wave-1 rows as `candidate`.

## Result

| verdict | objects | meaning |
|---|---|---|
| live | 267 | read or written by runtime code of the owner (or a consumer) |
| live (idle) | 34 | a code path exists, no write counted since the stats reset (feature dormant, behind a flag, or rows from migrations) — watch list, no action |
| **dead (wave 1)** | **10** | no runtime reader or writer in any repo, nothing outside the set depends on it — quarantine now |
| **dead (wave 2)** | **4** | no runtime use, but guards / tests / a dead method still name it — unhook first, then quarantine |
| read-only legacy | 2 | read by code, never written (`shared.pipeline_jobs`), or frozen behind an off flag (`shared.pipeline_lessons`, owned by WM-34) |
| reserved | 8 | designed and migrated for a feature not built yet (Booking customer OTP, CRM F2 / AI readers) — keep |
| contract (no consumer) | 2 | catalog contract views no app reads today — keep, review at the next contract version |
| live (to retire) | 2 | DM-2.4 says retire after X4; CIS-internal readers remain (`shared.v_tour_photos`, `shared.v_destination_photos`) |
| live (partition / internal / ops report) | 6 | partitions of `crm.audit_event`, `catalog._live_stop`, `shared.v_country_unmapped` |

**Wave 1 (CIS, 8 tables + 2 views):** `acp_contract.atom_decompose_jobs`, `acp_contract.s1_from_atom_runs`,
`acp_contract.route_pick`, `acp_shared.marketplace_portfolios`, `acp_shared.tenant_atom_state`, `shared.acp_runs`,
`shared.tenant_brand_rule_versions`, `shared.tenant_brand_rules_deleted_aa404`, `shared.v_batch_stats`,
`shared.v_pipeline_summary`. All CIS-owned (`cis_owner`), ~530 kB in total (reference sizes), 0 inserts / updates / deletes counted
on every one of the eight tables.

**Wave 2:** `shared.tenant_export_config` (reader `TenantConfigService.get_export_config()` has no runtime caller),
`gold_aa_internal.content_exports` and `gold_aa_internal.webhook_deliveries` (PRD v4 S5 export / webhook tables,
never written; but listed as RLS parity tables in Infra `db/owners.yaml`, `db/isolation_probe.py`,
`db/rls_catalogue_rules.py` rule b, the X1 245 script and 7 CIS integration tests), `public.checkpoint_migrations`
(LangGraph bookkeeping, master-owned: an Infra `roles/` file; AA-853 drift decision "keep" to revisit).
**Wave 3:** `shared.pipeline_jobs` (retire `GET /admin/jobs/{id}` in `api/routers/jobs_repo.py`, archive 523 rows,
then quarantine); `shared.v_tour_photos` / `shared.v_destination_photos` after CIS reads `catalog.v_*_photo`.

**No Booking, TripPlanner or CRM object is dead.** Their unused tables are reserved for planned slices
(`booking.customer_otps`, `customer_sessions`, `media_files`: ADR 0006 phase 4 / ui-spec; `crm.profile_history`,
`crm.v_ai_*`, `crm.v_insight_fact`: CRM-29b and the AI / insight readers). `crm.audit_event_legacy` looks unused but is
the crm-003 table attached as the MINVALUE partition of `crm.audit_event` (crm-007): live.

## Method

1. Objects, owner, `~rows`, size and `ins / upd / del` from the reference (sections per schema and *Table activity*).
2. Every tracked text file of `origin/main` of AA-CIS-App (`b665382f`), AA-Booking (`611bda4`), AA-TripPlanner-Web
   (`da90c50`), AA-Partner (`3d33850`) and AA-CIS-Infra (`82400b9`), 28/10/2026, read with `git cat-file` (no
   checkout), tokenised; each object counted where its **schema-qualified** name appears, and separately where the
   bare name appears ([`scripts/scan.py`](scripts/scan.py)). Files are split into code (runtime), scripts / infra
   tools, tests, migrations (`api/migrations`, `migrations/`, `db/migrations`, `db/replay_baseline`), docs, CI / agent
   files and the frozen CIS `portal/` copy.
3. Hits in files that list every table on purpose do not count as a use: `services/erasure/inventory.py` /
   `plan.py`, `api/services/data_coverage/registry.py`, `rls_catalogue_rules.py`, `db/isolation_probe.py`,
   `db/owners.yaml`, `db/schema_drift_decisions.json` (`data_coverage/queries.py` counts for the contract views it
   really selects). Each remaining code line was checked for SQL context vs a comment / docstring
   ([`scripts/sqlctx.py`](scripts/sqlctx.py)); every candidate was then read by hand (migration header, the code
   comment, the owning repo's CONTEXT.md). Verdicts the rules cannot make are the `OVR` map in
   [`scripts/gen_registry.py`](scripts/gen_registry.py), each with its evidence in the table.
4. destructive-ops.md STEP0 for wave 1: FKs from the reference's *Foreign keys* (inbound: none from outside the set;
   outbound: `route_pick`, `tenant_atom_state`, `tenant_brand_rule_versions` → `shared.tenants`;
   `s1_from_atom_runs`, `tenant_atom_state` → `silver_aa_internal.raw_tours`; `acp_runs` → `shared.pipeline_runs`),
   view / function dependents and `pg_stat_statements` callers are left to the DRY RUN script (catalog, live).

**Caveats.** (a) The reference's counters say "since the last stats reset (never)", yet several tables hold rows with
`ins = 0` (e.g. `shared.pipeline_jobs` ~523 rows, `silver_aa_internal.raw_sources` ~34): the counters do not reach back
to creation (instance restore / crash recovery resets them), so "0 writes" means "none since the counters started",
and the DRY RUN reads write-time columns too. (b) `rows = n/a` is `reltuples = -1` (never analysed), not zero.
(c) Dynamic table names (`f"{schema}.x"`) are caught by the bare-name pass; every wave-1 bare hit was read by hand
(docstrings only). (d) A table read only through a view counts through that view's own references (none of the wave-1
tables is under a live view; the DRY RUN guard re-checks on the catalog).

## Registry

Legend: *rows (ref)* `~reltuples`; *ins/upd/del* counted since the stats reset; *code references* = number of files
per repo and category on `origin/main` (code counts include the inventory / guard files of step 3; the verdict column
says when those are the only hits).

### `acp_contract` (18)

| object | kind | owner (role) | rows (ref) | ins/upd/del (ref) | code references (origin/main) | verdict | proposed action — evidence |
|---|---|---|---|---|---|---|---|
| `acp_contract.atom_decompose_jobs` | table | AA-CIS-App (`cis_owner`) | ~0 | 0/0/0 | CIS: migrations 2 | **dead** (wave 1) | quarantine (wave 1) — AA-302 Bedrock Batch decompose tracker (081/082); the batch path is gone; migrations + docs only |
| `acp_contract.atom_embedding` | table | AA-CIS-App (`cis_owner`) | ~10,674 | 8456/0/0 | CIS: code 5, migrations 1, tests 3 e.g. `services/acp_contract/atom_matching.py` | live | keep |
| `acp_contract.atom_matches` | table | AA-CIS-App (`cis_owner`) | ~15,152 | 9412/29537/0 | CIS: code 3, migrations 1, tests 4 e.g. `services/acp_contract/atom_ranking.py` | live | keep |
| `acp_contract.atom_ranking` | table | AA-CIS-App (`cis_owner`) | ~97,368 | 13508382/13419564/13443522 | CIS: code 12, migrations 5, tests 5; Infra: scripts 1, tests 2 e.g. `api/routers/admin_atoms.py` | live | keep |
| `acp_contract.atom_segment` | table | AA-CIS-App (`cis_owner`) | ~11,613 | 21485/160547/12892 | CIS: code 19, migrations 14, tests 14; Infra: migrations 8, scripts 1, tests 1 e.g. `api/routers/admin_a4.py` | live | keep |
| `acp_contract.atom_segment_alias` | table | AA-CIS-App (`cis_owner`) | ~1,012 | 2261/231871/1489 | CIS: code 5, migrations 9, tests 10; Infra: migrations 8, scripts 1, tests 1 e.g. `services/acp_contract/segment_gc.py` | live | keep |
| `acp_contract.atom_segment_member` | table | AA-CIS-App (`cis_owner`) | ~17,510 | 55894/471/43204 | CIS: code 24, migrations 9, tests 12; Infra: migrations 8, scripts 1, tests 1 e.g. `api/routers/admin_atoms.py` | live | keep |
| `acp_contract.atomize_day_fingerprint` | table | AA-CIS-App (`cis_owner`) | ~16,159 | 13159/53/0 | CIS: code 2, migrations 2, scripts 1, tests 3 e.g. `services/acp_contract/a3_atomize.py` | live | keep |
| `acp_contract.hub` | table | AA-CIS-App (`cis_owner`) | ~87 | 75/2327/774 | CIS: code 4, migrations 2, tests 3 e.g. `api/routers/admin_dashboard.py` | live | keep |
| `acp_contract.question_embedding` | table | AA-CIS-App (`cis_owner`) | ~1,006 | 99/0/0 | CIS: code 2, migrations 1, tests 3 e.g. `services/acp_contract/atom_matching.py` | live | keep |
| `acp_contract.route` | table | AA-CIS-App (`cis_owner`) | ~11,546 | 11199/10249/0 | CIS: code 19, migrations 16, scripts 1, tests 12; Infra: migrations 8, scripts 1, tests 1 e.g. `api/routers/admin_a4.py` | live | keep |
| `acp_contract.route_pick` | table | AA-CIS-App (`cis_owner`) | n/a | 0/0/0 | CIS: code 3, migrations 2, tests 1; Infra: infra tools 1 e.g. `api/main.py` | **dead** (wave 1) | quarantine (wave 1) — writer create_route_pick() retired with the route hub (AA-859 wave 4); api/main.py itself calls it a Dead Table Registry candidate |
| `acp_contract.s1_from_atom_runs` | table | AA-CIS-App (`cis_owner`) | n/a | 0/0/0 | CIS: code 1, migrations 2 e.g. `api/routers/admin_pipeline.py` | **dead** (wave 1) | quarantine (wave 1) — AA-289 S1-from-atom run log (088); only a docstring mention in admin_pipeline.py; FK to raw_tours |
| `acp_contract.search_demand` | table | AA-CIS-App (`cis_owner`) | ~5,089 | 509/289/0 | CIS: code 10, migrations 2, scripts 1, tests 6 e.g. `api/routers/admin_overview.py` | live | keep |
| `acp_contract.segment_research_log` | table | AA-CIS-App (`cis_owner`) | ~1,337 | 219/0/0 | CIS: code 5, migrations 1 e.g. `api/routers/admin_overview.py` | live | keep |
| `acp_contract.tour_atoms` | table | AA-CIS-App (`cis_owner`) | ~54,494 | 43293/36142/0 | CIS: code 32, migrations 25, scripts 2, tests 28; TripPlanner: migrations 1; Infra: code 1, infra tools 2, migrations 11, scripts 2, tests 3 e.g. `api/core/aa544_tenant_pool.py` | live | keep |
| `acp_contract.v_active_tour_atoms` | view | AA-CIS-App (`cis_owner`) | n/a | - | CIS: code 24, migrations 10, tests 20; TripPlanner: tests 1; Infra: code 1, infra tools 1, migrations 8, scripts 3, tests 2 e.g. `api/routers/admin_overview.py` | live | keep |
| `acp_contract.v_trip_registry` | view | AA-CIS-App (`cis_owner`) | n/a | - | CIS: code 5, migrations 9, tests 2; Infra: migrations 2 e.g. `api/routers/admin_pipeline.py` | live | keep |

### `acp_deliver` (1)

| object | kind | owner (role) | rows (ref) | ins/upd/del (ref) | code references (origin/main) | verdict | proposed action — evidence |
|---|---|---|---|---|---|---|---|
| `acp_deliver.tenant_tour_pages` | table | AA-CIS-App (`cis_owner`) | ~0 | 0/0/0 | CIS: code 8, migrations 7, tests 8; Infra: infra tools 1, migrations 1, tests 1 e.g. `api/routers/v1_trip_page.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |

### `acp_shared` (21)

| object | kind | owner (role) | rows (ref) | ins/upd/del (ref) | code references (origin/main) | verdict | proposed action — evidence |
|---|---|---|---|---|---|---|---|
| `acp_shared.acp_output_rules` | table | AA-CIS-App (`cis_owner`) | n/a | 0/0/0 | CIS: code 4, migrations 9, tests 6; Infra: infra tools 2, migrations 5 e.g. `api/routers/v1_rules.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `acp_shared.acp_quota_ledger` | table | AA-CIS-App (`cis_owner`) | n/a | 6/0/1 | CIS: code 2, migrations 1, tests 2; Infra: infra tools 1 e.g. `api/routers/admin.py` | live | keep |
| `acp_shared.angle_gate_option` | table | AA-CIS-App (`cis_owner`) | ~57 | 69/72/0 | CIS: code 6, migrations 7, tests 14; Infra: infra tools 1, migrations 3, tests 1 e.g. `api/routers/admin_a4.py` | live | keep |
| `acp_shared.angle_gate_request` | table | AA-CIS-App (`cis_owner`) | ~21 | 25/76/0 | CIS: code 24, migrations 14, scripts 3, tests 27; Infra: infra tools 1, migrations 3, scripts 1, tests 2 e.g. `api/routers/admin_a4.py` | live | keep |
| `acp_shared.atom_place_card` | table | AA-CIS-App (`cis_owner`) | ~26,154 | 26577/31/0 | CIS: code 9, migrations 15, tests 7; Infra: migrations 15, scripts 2, tests 1 e.g. `api/routers/admin_content_quality.py` | live | keep |
| `acp_shared.audit_log` | table | AA-CIS-App (`cis_owner`) | ~3,100 | 3126/0/0 | CIS: code 34, migrations 5, scripts 2, tests 48; Partner: code 1; Infra: code 1, infra tools 1, migrations 3, scripts 1, tests 2 e.g. `api/main.py` | live | keep |
| `acp_shared.content_piece` | table | AA-CIS-App (`cis_owner`) | ~343 | 348/717/0 | CIS: code 25, frozen portal 1, migrations 17, scripts 7, tests 27; Partner: code 1; Infra: migrations 4, tests 1 e.g. `api/routers/admin_a4.py` | live | keep |
| `acp_shared.content_piece_label` | table | AA-CIS-App (`cis_owner`) | n/a | 1/0/0 | CIS: code 4, migrations 1, scripts 2, tests 3; Infra: migrations 1 e.g. `api/routers/admin_content_quality.py` | live | keep |
| `acp_shared.debate_brand_fit_cache` | table | AA-CIS-App (`cis_owner`) | ~312 | 910/0/563 | CIS: code 5, migrations 1, tests 5; Infra: infra tools 1, scripts 1, tests 2 e.g. `services/acp_contract/segment_gc.py` | live | keep |
| `acp_shared.facts` | table | AA-CIS-App (`cis_owner`) | n/a | 0/2/0 | CIS: code 2, migrations 7, tests 4; Infra: migrations 5, tests 2 e.g. `services/acp_content_writing/facts.py` | live | keep |
| `acp_shared.marketplace_portfolios` | table | AA-CIS-App (`cis_owner`) | n/a | 0/0/0 | CIS: migrations 4; Infra: migrations 1 | **dead** (wave 1) | quarantine (wave 1) — pre-tenant portfolio drafts (097); flow removed by ADR-2026-038 / 119; CIS 265: 'stay revoked and dead'; no FK points at it on Dev |
| `acp_shared.place_card` | table | AA-CIS-App (`cis_owner`) | ~4,785 | 4803/4103/18 | CIS: code 8, migrations 17, tests 11; Infra: migrations 17, scripts 1 e.g. `api/routers/admin_content_quality.py` | live | keep |
| `acp_shared.place_card_alias` | table | AA-CIS-App (`cis_owner`) | ~18,503 | 18877/20/0 | CIS: code 3, migrations 9, tests 3; Infra: migrations 9 e.g. `api/routers/admin_content_quality.py` | live | keep |
| `acp_shared.place_card_miss` | table | AA-CIS-App (`cis_owner`) | ~1,331 | 1369/0/1 | CIS: code 1, migrations 1, tests 1; Infra: migrations 1 e.g. `services/acp_shared/place_cards.py` | live | keep |
| `acp_shared.publish_log` | table | AA-CIS-App (`cis_owner`) | n/a | 7/14/0 | CIS: code 11, migrations 6, tests 17; Infra: migrations 3 e.g. `api/routers/admin_a4.py` | live | keep |
| `acp_shared.quarter_plan` | table | AA-CIS-App (`cis_owner`) | ~6 | 0/0/0 | CIS: code 4, migrations 4, tests 7; Infra: infra tools 1, migrations 1, tests 1 e.g. `services/acp_planning/quarter.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `acp_shared.quarter_plan_version` | table | AA-CIS-App (`cis_owner`) | ~0 | 0/0/0 | CIS: code 2, migrations 5, tests 7; Infra: infra tools 1, migrations 1, tests 1 e.g. `services/acp_planning/quarter.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `acp_shared.subject` | table | AA-CIS-App (`cis_owner`) | ~432 | 964/1044/532 | CIS: code 16, migrations 8, scripts 1, tests 13; Infra: migrations 1, scripts 1, tests 2 e.g. `api/routers/admin_a4.py` | live | keep |
| `acp_shared.tenant_atom_state` | table | AA-CIS-App (`cis_owner`) | ~0 | 0/0/0 | CIS: code 2, migrations 2, tests 3; Infra: infra tools 1, migrations 1 e.g. `api/routers/admin.py` | **dead** (wave 1) | quarantine (wave 1) — N1 seeding state (098); not part of onboarding since AA-472 (admin.py docstring); CIS 265: 'dead'; 2 integration tests name it |
| `acp_shared.tenant_config` | table | AA-CIS-App (`cis_owner`) | n/a | 1/0/1 | CIS: code 11, migrations 3, tests 5; Infra: infra tools 1, migrations 2 e.g. `api/routers/admin.py` | live | keep |
| `acp_shared.year_plan` | table | AA-CIS-App (`cis_owner`) | n/a | 0/0/0 | CIS: code 2, migrations 4, tests 7; Infra: migrations 2 e.g. `services/acp_planning/quarter.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |

### `booking` (74)

| object | kind | owner (role) | rows (ref) | ins/upd/del (ref) | code references (origin/main) | verdict | proposed action — evidence |
|---|---|---|---|---|---|---|---|
| `booking.audit_logs` | table | AA-Booking (`bk_owner`) | ~167 | 213/0/0 | Booking: code 10, migrations 8, tests 48; Infra: migrations 8, scripts 7, tests 3 e.g. `backend/app/audit.py` | live | keep |
| `booking.b2b_cancellations` | table | AA-Booking (`bk_owner`) | n/a | 2/0/0 | Booking: code 1, migrations 2, tests 4; Infra: migrations 2 e.g. `backend/app/b2b/cancellation.py` | live | keep |
| `booking.b2b_hold_lines` | table | AA-Booking (`bk_owner`) | ~12 | 20/5/0 | Booking: code 7, migrations 3, tests 7; Infra: migrations 3, scripts 3, tests 1 e.g. `backend/app/b2b/cancellation.py` | live | keep |
| `booking.b2b_holds` | table | AA-Booking (`bk_owner`) | ~2 | 20/22/0 | Booking: code 9, migrations 5, tests 12; Infra: migrations 5, scripts 2, tests 1 e.g. `backend/app/b2b/cancellation.py` | live | keep |
| `booking.b2b_partners` | table | AA-Booking (`bk_owner`) | n/a | 3/0/0 | Booking: code 4, migrations 5, tests 6; Partner: tests 1; Infra: migrations 5, scripts 3 e.g. `backend/app/b2b/access.py` | live | keep |
| `booking.b2b_quote_lines` | table | AA-Booking (`bk_owner`) | n/a | 36/0/0 | Booking: code 4, migrations 2, tests 5; Infra: migrations 2, scripts 2 e.g. `backend/app/b2b/cancellation.py` | live | keep |
| `booking.b2b_quotes` | table | AA-Booking (`bk_owner`) | n/a | 36/0/0 | Booking: code 3, migrations 2, tests 10; Infra: migrations 2, scripts 1 e.g. `backend/app/b2b/cancellation.py` | live | keep |
| `booking.cancellation_policies` | table | AA-Booking (`bk_owner`) | n/a | 1/0/0 | Booking: code 2, migrations 1, tests 4; Infra: migrations 1, scripts 1 e.g. `backend/app/b2b/cancellation.py` | live | keep |
| `booking.countries` | table | AA-Booking (`bk_owner`) | n/a | 21/0/0 | CIS: migrations 2; Booking: code 8, migrations 6, tests 10; Infra: infra tools 1, migrations 8 e.g. `backend/app/catalog/destinations.py` | live | keep |
| `booking.country_profiles` | table | AA-Booking (`bk_owner`) | n/a | 0/0/0 | Booking: code 1, migrations 1, tests 3; Infra: migrations 1 e.g. `backend/app/catalog/geo.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `booking.customer_identities` | table | AA-Booking (`bk_owner`) | n/a | 0/0/0 | Booking: code 4, migrations 1, tests 6; TripPlanner: tests 1; Infra: migrations 1, scripts 1 e.g. `backend/app/auth/customer.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `booking.customer_otps` | table | AA-Booking (`bk_owner`) | n/a | 0/0/0 | Booking: migrations 3, tests 2; Infra: migrations 3 | reserved | keep (ADR 0006 phase 4 customer OTP sign-in) — bk-001 Tier A; not built yet (AA-680 customer half) |
| `booking.customer_sessions` | table | AA-Booking (`bk_owner`) | n/a | 0/0/0 | Booking: migrations 3, tests 1; Infra: migrations 3 | reserved | keep (ADR 0006 phase 4) — bk-001 Tier A; not built yet |
| `booking.customers` | table | AA-Booking (`bk_owner`) | ~1 | 17/0/0 | CIS: code 1, migrations 2, tests 3; Booking: code 14, migrations 10, tests 23; TripPlanner: migrations 1, tests 4; Infra: infra tools 1, migrations 13, scripts 6, tests 3 e.g. `backend/app/auth/admin.py` | live | keep |
| `booking.departure_incidents` | table | AA-Booking (`bk_owner`) | n/a | 0/0/0 | Booking: code 1, migrations 1, tests 4; Infra: migrations 1 e.g. `backend/app/b2b/desk.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `booking.departures` | table | AA-Booking (`bk_owner`) | n/a | 5/0/0 | Booking: code 6, migrations 3, tests 5; Infra: migrations 3, scripts 3 e.g. `backend/app/b2b/cancellation.py` | live | keep |
| `booking.destination_profiles` | table | AA-Booking (`bk_owner`) | n/a | 0/0/0 | Booking: code 1, migrations 1, tests 3; Infra: migrations 1 e.g. `backend/app/catalog/geo.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `booking.entity_media` | table | AA-Booking (`bk_owner`) | n/a | 2/2/0 | CIS: migrations 1; Booking: code 3, migrations 2, tests 5; Infra: code 1, migrations 3 e.g. Infra `accounts/aa365/booking_media.tf` | live | keep |
| `booking.fx_rates` | table | AA-Booking (`bk_owner`) | n/a | 3/0/0 | Booking: code 4, migrations 3, tests 12; Infra: migrations 3, scripts 1, tests 2 e.g. `backend/app/b2b/reads.py` | live | keep |
| `booking.hotel_room_types` | table | AA-Booking (`bk_owner`) | n/a | 5/0/0 | Booking: code 9, migrations 5, tests 7; Infra: infra tools 1, migrations 5, scripts 2 e.g. `backend/app/b2b/components.py` | live | keep |
| `booking.hotels` | table | AA-Booking (`bk_owner`) | n/a | 5/11/0 | CIS: code 1; Booking: code 10, migrations 3, tests 10; Infra: infra tools 1, migrations 3, scripts 2 e.g. `services/places/validity_fix.py` | live | keep |
| `booking.inbox_cursor` | table | AA-Booking (`bk_owner`) | ~2 | 2/13751/0 | Booking: code 2, migrations 2, tests 5; Infra: migrations 2 e.g. `backend/app/catalog/lifecycle.py` | live | keep |
| `booking.inbox_events` | table | AA-Booking (`bk_owner`) | ~5 | 17/22/0 | Booking: code 5, migrations 6, tests 11; TripPlanner: migrations 2; Infra: migrations 8, scripts 1, tests 1 e.g. `backend/app/catalog/lifecycle.py` | live | keep |
| `booking.invoice_items` | table | AA-Booking (`bk_owner`) | n/a | 4/0/0 | Booking: code 1, migrations 1, tests 3; Infra: migrations 1, scripts 1 e.g. `backend/app/ops/invoices.py` | live | keep |
| `booking.invoices` | table | AA-Booking (`bk_owner`) | n/a | 4/14/0 | Booking: code 6, migrations 2, tests 7; Infra: migrations 2, scripts 2 e.g. `backend/app/ops/files.py` | live | keep |
| `booking.job` | table | AA-Booking (`bk_owner`) | ~6,908 | 13807/27673/6899 | CIS: code 1, migrations 12, tests 1; Booking: ci 2, code 14, migrations 6, scripts 1, tests 19; Partner: tests 1; Infra: code 5, infra tools 2, migrations 18, scripts 6, tests 2 e.g. `shared/jobs/job_table_shape.py` | live | keep |
| `booking.media_files` | table | AA-Booking (`bk_owner`) | n/a | 0/0/0 | Booking: migrations 4; Infra: migrations 4 | reserved | keep (ui-spec FileDropzone) — bk-001 Tier A; nothing uploads yet |
| `booking.notification_reads` | table | AA-Booking (`bk_owner`) | n/a | 0/0/0 | Booking: code 2, migrations 2, tests 4; Infra: migrations 2 e.g. `backend/app/notifications/service.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `booking.notifications` | table | AA-Booking (`bk_owner`) | ~22 | 29/0/0 | Booking: code 4, migrations 5, tests 21; Infra: migrations 5, scripts 2 e.g. `backend/app/catalog/lifecycle.py` | live | keep |
| `booking.ops_files` | table | AA-Booking (`bk_owner`) | n/a | 0/0/0 | Booking: code 2, migrations 3, tests 10; Infra: migrations 3 e.g. `backend/app/ops/files.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `booking.ops_transitions` | table | AA-Booking (`bk_owner`) | n/a | 20/0/0 | Booking: code 1, migrations 3, tests 2; Infra: migrations 3 e.g. `backend/app/ops/supplier_bookings.py` | live | keep |
| `booking.outbox` | table | AA-Booking (`bk_owner`) | ~1 | 19/16/0 | CIS: migrations 1; Booking: code 3, migrations 3, tests 6; Infra: migrations 4, scripts 1 e.g. `backend/app/b2b/events.py` | live | keep |
| `booking.payment_schedule` | table | AA-Booking (`bk_owner`) | n/a | 6/0/0 | Booking: code 1, migrations 1, tests 4; Infra: migrations 1, scripts 1 e.g. `backend/app/ops/invoices.py` | live | keep |
| `booking.payments` | table | AA-Booking (`bk_owner`) | n/a | 8/8/0 | Booking: code 4, migrations 2, tests 8; Infra: migrations 2, scripts 2 e.g. `backend/app/ops/files.py` | live | keep |
| `booking.policy_approvals` | table | AA-Booking (`bk_owner`) | ~6 | 8/0/0 | Booking: code 4, migrations 4, tests 10; Infra: migrations 4, scripts 2, tests 1 e.g. `backend/app/b2b/cancellation.py` | live | keep |
| `booking.pricing_rules` | table | AA-Booking (`bk_owner`) | n/a | 4/0/0 | Booking: code 3, migrations 4, tests 8; Infra: migrations 4, scripts 2 e.g. `backend/app/pricing/engine.py` | live | keep |
| `booking.services` | table | AA-Booking (`bk_owner`) | n/a | 5/1/0 | CIS: code 1; Booking: code 10, migrations 5, tests 9; Infra: infra tools 1, migrations 5, scripts 2 e.g. `services/places/validity_fix.py` | live | keep |
| `booking.settings` | table | AA-Booking (`bk_owner`) | n/a | 20/0/0 | Booking: code 9, migrations 10, tests 15; Infra: migrations 10, scripts 5 e.g. `backend/app/b2b/desk.py` | live | keep |
| `booking.staff_assignments` | table | AA-Booking (`bk_owner`) | n/a | 1/0/0 | Booking: code 5, migrations 2, tests 7; Infra: migrations 2 e.g. `backend/app/auth/admin.py` | live | keep |
| `booking.staff_users` | table | AA-Booking (`bk_owner`) | ~8 | 15/49/0 | Booking: code 25, migrations 21, tests 34; Infra: migrations 21, scripts 6, tests 2 e.g. `backend/app/audit.py` | live | keep |
| `booking.supplier_bill_items` | table | AA-Booking (`bk_owner`) | n/a | 2/0/0 | Booking: code 2, migrations 1, tests 3; Infra: migrations 1, scripts 1 e.g. `backend/app/ops/files.py` | live | keep |
| `booking.supplier_bills` | table | AA-Booking (`bk_owner`) | n/a | 1/3/0 | Booking: code 3, migrations 1, tests 4; Infra: migrations 1, scripts 1 e.g. `backend/app/ops/files.py` | live | keep |
| `booking.supplier_bookings` | table | AA-Booking (`bk_owner`) | n/a | 9/12/0 | Booking: code 6, migrations 3, tests 13; Infra: migrations 3, scripts 2 e.g. `backend/app/b2b/desk.py` | live | keep |
| `booking.supplier_contracts` | table | AA-Booking (`bk_owner`) | n/a | 3/7/0 | Booking: code 4, migrations 4, tests 8; Infra: infra tools 1, migrations 4, scripts 2 e.g. `backend/app/suppliers/service.py` | live | keep |
| `booking.supplier_payouts` | table | AA-Booking (`bk_owner`) | n/a | 3/1/0 | Booking: code 2, migrations 1, tests 3; Infra: migrations 1, scripts 1 e.g. `backend/app/ops/files.py` | live | keep |
| `booking.supplier_rates` | table | AA-Booking (`bk_owner`) | n/a | 5/0/0 | Booking: code 4, migrations 4, tests 6; Infra: migrations 4, scripts 1 e.g. `backend/app/suppliers/service.py` | live | keep |
| `booking.suppliers` | table | AA-Booking (`bk_owner`) | n/a | 7/1/0 | CIS: code 1; Booking: code 8, migrations 8, tests 16; Infra: infra tools 1, migrations 8, scripts 4 e.g. `services/places/validity_fix.py` | live | keep |
| `booking.trip_case_checks` | table | AA-Booking (`bk_owner`) | n/a | 40/2/0 | Booking: code 2, migrations 2, tests 4; Infra: migrations 2, scripts 1 e.g. `backend/app/ops/lifecycle.py` | live | keep |
| `booking.trip_case_countries` | table | AA-Booking (`bk_owner`) | n/a | 3/0/0 | Booking: code 2, migrations 2, tests 3; Infra: migrations 2 e.g. `backend/app/trip_cases/service.py` | live | keep |
| `booking.trip_case_legs` | table | AA-Booking (`bk_owner`) | ~8 | 14/8/0 | Booking: code 7, migrations 3, tests 12; Infra: infra tools 1, migrations 3, scripts 1 e.g. `backend/app/catalog/lifecycle.py` | live | keep |
| `booking.trip_case_status_history` | table | AA-Booking (`bk_owner`) | ~1 | 51/0/0 | Booking: code 1, migrations 5, tests 10; Infra: migrations 5 e.g. `backend/app/trip_cases/service.py` | live | keep |
| `booking.trip_case_status_transitions` | table | AA-Booking (`bk_owner`) | n/a | 34/0/0 | Booking: code 1, migrations 5, tests 7; Infra: migrations 5 e.g. `backend/app/trip_cases/service.py` | live | keep |
| `booking.trip_case_version_itinerary` | table | AA-Booking (`bk_owner`) | ~4 | 27/4/0 | Booking: code 5, migrations 8, tests 13; Infra: infra tools 1, migrations 8, scripts 2 e.g. `backend/app/b2b/holds.py` | live | keep |
| `booking.trip_case_versions` | table | AA-Booking (`bk_owner`) | n/a | 14/14/0 | Booking: code 7, migrations 8, tests 20; Infra: migrations 8, scripts 3 e.g. `backend/app/b2b/holds.py` | live | keep |
| `booking.trip_cases` | table | AA-Booking (`bk_owner`) | ~10 | 24/27/0 | CIS: code 2; Booking: code 22, migrations 12, tests 46; Infra: migrations 12, scripts 6, tests 2 e.g. `api/services/ops_overview/activity.py` | live | keep |
| `booking.trip_plan_components` | table | AA-Booking (`bk_owner`) | n/a | 2/0/0 | Booking: code 4, migrations 2, tests 5; Infra: migrations 2, scripts 3, tests 1 e.g. `backend/app/b2b/components.py` | live | keep |
| `booking.trip_plan_prices` | table | AA-Booking (`bk_owner`) | n/a | 0/0/0 | Booking: code 1, migrations 1, tests 3; Infra: migrations 1 e.g. `backend/app/catalog/trip_plan_prices.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `booking.trip_plans` | table | AA-Booking (`bk_owner`) | ~2 | 2/2/0 | Booking: code 15, migrations 7, tests 18; Infra: migrations 7, scripts 3 e.g. `backend/app/b2b/cancellation.py` | live | keep |
| `booking.v_customer_summary` | view | AA-Booking (`bk_owner`) | n/a | - | Booking: code 3, migrations 3, tests 2; Infra: migrations 3 e.g. `backend/app/customers/service.py` | live | keep |
| `booking.v_invoice_balance` | view | AA-Booking (`bk_owner`) | n/a | - | Booking: code 3, migrations 1, tests 2; Infra: migrations 1, scripts 2 e.g. `backend/app/ops/invoices.py` | live | keep |
| `booking.v_ops_case_status` | view | AA-Booking (`bk_owner`) | n/a | - | CIS: code 6, tests 3; Booking: migrations 1, tests 1; Infra: code 1, infra tools 2, migrations 1, tests 1 e.g. `api/services/ops_overview/__init__.py` | live | keep |
| `booking.v_ops_data_totals` | view | AA-Booking (`bk_owner`) | n/a | - | CIS: code 2, tests 2; Booking: migrations 1, tests 1; Infra: code 1, infra tools 2, migrations 1, tests 1 e.g. `api/services/data_coverage/queries.py` | live | keep |
| `booking.v_ops_funnel_daily` | view | AA-Booking (`bk_owner`) | n/a | - | CIS: code 6, tests 3; Booking: migrations 1, tests 1; Infra: code 1, infra tools 2, migrations 1 e.g. `api/services/ops_overview/__init__.py` | live | keep |
| `booking.v_ops_trip_plan_keys` | view | AA-Booking (`bk_owner`) | n/a | - | CIS: code 2, tests 2; Booking: migrations 1, tests 1; Infra: code 1, infra tools 2, migrations 1, tests 1 e.g. `api/services/data_coverage/queries.py` | live | keep |
| `booking.v_payment_schedule_status` | view | AA-Booking (`bk_owner`) | n/a | - | Booking: code 3, migrations 1, tests 3; Infra: migrations 1, scripts 2 e.g. `backend/app/ops/invoices.py` | live | keep |
| `booking.v_schema_versions` | view | AA-Booking (`bk_owner`) | n/a | - | CIS: migrations 1, tests 1; Booking: code 1, migrations 4, tests 20; Infra: code 1, migrations 5 e.g. `backend/app/db.py` | live | keep |
| `booking.v_supplier_bill_balance` | view | AA-Booking (`bk_owner`) | n/a | - | Booking: code 2, migrations 1, tests 2; Infra: migrations 1, scripts 1 e.g. `backend/app/ops/lifecycle.py` | live | keep |
| `booking.v_supply_hotels` | view | AA-Booking (`bk_owner`) | n/a | - | CIS: code 3, migrations 1, tests 3; Booking: migrations 1, tests 1; Infra: code 1, infra tools 3, migrations 2 e.g. `services/supply_content/pull.py` | live | keep |
| `booking.v_supply_media` | view | AA-Booking (`bk_owner`) | n/a | - | CIS: code 1, tests 2; Booking: code 1, migrations 1, tests 1; Infra: code 2, infra tools 2, migrations 1 e.g. `services/supply_content/photos.py` | live | keep |
| `booking.v_supply_outbox` | view | AA-Booking (`bk_owner`) | n/a | - | CIS: code 4, migrations 1, tests 3; Booking: migrations 1, tests 1; Infra: code 1, infra tools 2, migrations 2 e.g. `api/core/ops_metrics_sampler.py` | live | keep |
| `booking.v_supply_services` | view | AA-Booking (`bk_owner`) | n/a | - | CIS: code 2, tests 3; Booking: migrations 1, tests 1; Infra: code 1, infra tools 3, migrations 1 e.g. `services/supply_content/pull.py` | live | keep |
| `booking.v_trip_case_supply_state` | view | AA-Booking (`bk_owner`) | n/a | - | Booking: code 2, migrations 3, tests 1; Infra: migrations 3, scripts 1 e.g. `backend/app/ops/lifecycle.py` | live | keep |
| `booking.v_trip_check_board` | view | AA-Booking (`bk_owner`) | n/a | - | Booking: code 1, migrations 2, tests 2; Infra: migrations 2, scripts 2 e.g. `backend/app/ops/trip_checks.py` | live | keep |
| `booking.version_item_costs` | table | AA-Booking (`bk_owner`) | ~4 | 14/0/1 | Booking: code 3, migrations 5, tests 8; Infra: migrations 5, scripts 1 e.g. `backend/app/b2b/holds.py` | live | keep |

### `catalog` (24)

| object | kind | owner (role) | rows (ref) | ins/upd/del (ref) | code references (origin/main) | verdict | proposed action — evidence |
|---|---|---|---|---|---|---|---|
| `catalog._live_stop` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: code 1, migrations 2, tests 1; TripPlanner: tests 1; Infra: migrations 2 e.g. `services/places/dedupe_run.py` | live (internal) | keep — liveness base of the catalog place / graph views (253) |
| `catalog._live_tour` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: code 5, migrations 8, tests 5; TripPlanner: tests 1; Infra: migrations 8 e.g. `api/services/data_coverage/defs.py` | live | keep |
| `catalog._tour_day_text` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: code 5, migrations 6, tests 5; Booking: code 1; Infra: infra tools 1, migrations 6 e.g. `services/catalog_http/reader.py` | live | keep |
| `catalog.v_component_embedding` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: migrations 1, tests 2; TripPlanner: code 3, tests 5; Infra: migrations 1, scripts 2, tests 1 e.g. `backend/assembly/suggestions.py` | live | keep |
| `catalog.v_component_redirect` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: code 1, migrations 1, tests 2; TripPlanner: code 1, tests 2; Infra: migrations 1, scripts 1 e.g. `services/places/components.py` | live | keep |
| `catalog.v_country` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: migrations 1, tests 2; Booking: code 2, migrations 1, tests 3; Infra: migrations 2 e.g. `backend/app/catalog/geo.py` | live | keep |
| `catalog.v_destination` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: code 2, migrations 7, tests 6; Booking: code 13, migrations 3, tests 5; TripPlanner: code 9, tests 11; Infra: migrations 10, scripts 1, tests 1 e.g. `services/catalog_http/mapping.py` | live | keep |
| `catalog.v_destination_photo` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: migrations 3, tests 1; Booking: code 1, tests 3; TripPlanner: code 1; Infra: migrations 3 e.g. `backend/app/catalog/geo.py` | live | keep |
| `catalog.v_destination_redirect` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: migrations 2, tests 2; TripPlanner: code 1, tests 1; Infra: migrations 2 e.g. `backend/browse/destinations.py` | live | keep |
| `catalog.v_destination_shape` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: code 1, migrations 1, tests 1; TripPlanner: code 1, tests 2; Infra: migrations 1 e.g. `services/places/dedupe.py` | live | keep |
| `catalog.v_graph_edge` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: migrations 2, tests 1; Infra: migrations 2 | contract (no consumer) | keep; review at the next catalog.graph contract version — ADR 0007 contract view (228); TripPlanner reads none of the graph views today |
| `catalog.v_graph_node` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: migrations 2, tests 2; TripPlanner: code 1, tests 2; Infra: migrations 2, scripts 2, tests 1 e.g. `backend/assembly/suggestions.py` | live | keep |
| `catalog.v_supply_content` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: code 6, migrations 1, tests 3; Booking: code 4, tests 2; Infra: migrations 1 e.g. `frontend/app/admin/supply-content/SupplyContentDetail.tsx` | live | keep |
| `catalog.v_tour` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: code 7, migrations 12, tests 10; Booking: code 25, migrations 2, tests 24; TripPlanner: code 8, tests 10; Infra: infra tools 2, migrations 14, scripts 7, tests 6 e.g. `api/routers/catalog_http.py` | live | keep |
| `catalog.v_tour_component` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: code 6, migrations 6, tests 6; TripPlanner: code 12, migrations 1, tests 11; Infra: migrations 7, scripts 3, tests 1 e.g. `api/services/data_coverage/defs.py` | live | keep |
| `catalog.v_tour_day` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: code 3, migrations 3, tests 3; Booking: code 1, tests 8; TripPlanner: code 2, tests 4; Infra: migrations 3, scripts 2 e.g. `services/catalog_http/mapping.py` | live | keep |
| `catalog.v_tour_day_route` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: migrations 2, tests 1; Infra: migrations 2 | contract (no consumer) | keep; review at the next catalog.graph contract version — ADR 0007 contract view (228) |
| `catalog.v_tour_junction` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: migrations 2, tests 1; TripPlanner: code 1, tests 1; Infra: migrations 2, scripts 1 e.g. `backend/browse/routes.py` | live | keep |
| `catalog.v_tour_leg` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: code 1, migrations 2, tests 2; TripPlanner: code 1, tests 1; Infra: migrations 2, scripts 2 e.g. `backend/browse/routes.py` | live | keep |
| `catalog.v_tour_lifecycle_outbox` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: code 3, migrations 1, tests 2; Booking: code 2, tests 2; TripPlanner: code 1; Infra: migrations 1, scripts 1 e.g. `services/jobs/tripplanner_purge_job.py` | live | keep |
| `catalog.v_tour_photo` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: code 2, migrations 2, tests 1; Booking: code 2, tests 10; TripPlanner: code 1, tests 3; Infra: migrations 2 e.g. `services/catalog_http/mapping.py` | live | keep |
| `catalog.v_tour_place` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: code 4, migrations 7, tests 5; Booking: code 1, tests 3; TripPlanner: code 2, tests 5; Infra: migrations 7, scripts 2 e.g. `api/services/data_coverage/sources.py` | live | keep |
| `catalog.v_tour_retired` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: code 4, migrations 1, tests 2; Booking: code 8, tests 2; TripPlanner: code 2, tests 4; Infra: migrations 1, scripts 2, tests 2 e.g. `api/routers/catalog_http.py` | live | keep |
| `catalog.v_tour_stop` | view | AA-CIS-App (`catalog_owner`) | n/a | - | CIS: code 1, migrations 2, tests 4; TripPlanner: code 2, tests 4; Infra: migrations 2, scripts 2 e.g. `backend/assembly/suggestions.py` | live | keep |

### `crm` (84)

| object | kind | owner (role) | rows (ref) | ins/upd/del (ref) | code references (origin/main) | verdict | proposed action — evidence |
|---|---|---|---|---|---|---|---|
| `crm.aa_catalog_state` | table | AA-Partner (`crm_owner`) | ~1 | 1/481/0 | Partner: code 3, migrations 1, tests 2; Infra: migrations 1, scripts 1 e.g. `api/app/catalog/__init__.py` | live | keep |
| `crm.aa_catalog_tour` | table | AA-Partner (`crm_owner`) | ~892 | 892/20007/0 | Partner: code 6, migrations 2, tests 6; Infra: migrations 2, scripts 1 e.g. `api/app/catalog/__init__.py` | live | keep |
| `crm.aa_content` | table | AA-Partner (`crm_owner`) | ~23 | 23/437/0 | CIS: code 1, tests 1; Partner: code 4, migrations 1, tests 3; Infra: migrations 1 e.g. `api/app/catalog/content.py` | live | keep |
| `crm.aa_request` | table | AA-Partner (`crm_owner`) | ~19 | 24/42/0 | Partner: code 5, migrations 1, tests 2; Infra: migrations 1 e.g. `api/app/booking/__init__.py` | live | keep |
| `crm.agency_supplier` | table | AA-Partner (`crm_owner`) | n/a | 16/12/0 | Partner: code 5, migrations 7, tests 5; Infra: migrations 7 e.g. `api/app/ledger/__init__.py` | live | keep |
| `crm.agreement_doc` | table | AA-Partner (`crm_owner`) | ~18 | 22/42/0 | Partner: code 8, migrations 1, tests 4; Infra: migrations 1 e.g. `api/app/portal/access.py` | live | keep |
| `crm.audit_event` | part. table | AA-Partner (`crm_owner`) | n/a | 0/0/0 | Partner: code 10, migrations 5, tests 21; Infra: code 2, infra tools 1, migrations 5, tests 2 e.g. Infra `accounts/aa365/crm_storage.tf` | live | keep |
| `crm.audit_event_legacy` | table | AA-Partner (`crm_owner`) | ~2,612 | 2720/0/0 | Partner: migrations 1, tests 1; Infra: migrations 1 | live (partition) | keep — crm-007: the crm-003 table attached as the MINVALUE partition of crm.audit_event |
| `crm.audit_event_p202611` | table | AA-Partner (`crm_owner`) | n/a | 0/0/0 | none | live (partition) | keep — monthly partition of crm.audit_event (crm-007) |
| `crm.audit_event_p202612` | table | AA-Partner (`crm_owner`) | n/a | 0/0/0 | none | live (partition) | keep — monthly partition of crm.audit_event (crm-007) |
| `crm.audit_event_p202701` | table | AA-Partner (`crm_owner`) | n/a | 0/0/0 | none | live (partition) | keep — monthly partition of crm.audit_event (crm-007) |
| `crm.audit_export_manifest` | table | AA-Partner (`crm_owner`) | ~290 | 306/0/0 | Partner: code 2, migrations 1, tests 3; Infra: migrations 1 e.g. `api/app/audit_export/export.py` | live | keep |
| `crm.audit_export_tenant` | table | AA-Partner (`crm_owner`) | ~4 | 4/319/0 | Partner: code 2, migrations 3, tests 3; Infra: migrations 3 e.g. `api/app/audit_export/export.py` | live | keep |
| `crm.booking_feed_state` | table | AA-Partner (`crm_owner`) | ~1 | 1/3720/0 | Partner: code 1, migrations 1, tests 1; Infra: migrations 1 e.g. `api/app/booking/sync.py` | live | keep |
| `crm.booking_line` | table | AA-Partner (`crm_owner`) | n/a | 6/18/0 | Partner: code 7, migrations 7, tests 4; Infra: migrations 7 e.g. `api/app/booking/aa_lines.py` | live | keep |
| `crm.booking_line_money` | table | AA-Partner (`crm_owner`) | n/a | 12/0/0 | Partner: code 1, migrations 3, tests 4; Infra: migrations 3 e.g. `api/app/ledger/__init__.py` | live | keep |
| `crm.channel_account` | table | AA-Partner (`crm_owner`) | n/a | 1/8/0 | Partner: code 7, migrations 1, tests 7; Infra: migrations 1 e.g. `api/app/mail/conversations.py` | live | keep |
| `crm.client_link` | table | AA-Partner (`crm_owner`) | ~39 | 50/153/0 | Partner: code 10, migrations 9, tests 5; Infra: migrations 9 e.g. `api/app/intake/stage2.py` | live | keep |
| `crm.consent` | table | AA-Partner (`crm_owner`) | ~106 | 110/0/0 | Partner: code 5, migrations 3, tests 8; Infra: infra tools 1, migrations 3 e.g. `api/app/dispatch/worker.py` | live | keep |
| `crm.conversation` | table | AA-Partner (`crm_owner`) | n/a | 8/16/0 | Partner: code 5, migrations 6, tests 6; Infra: migrations 6 e.g. `api/app/mail/conversations.py` | live | keep |
| `crm.dispatch_queue` | table | AA-Partner (`crm_owner`) | ~52 | 55/59/0 | Partner: code 7, migrations 5, tests 10; Infra: migrations 5 e.g. `api/app/dispatch/__init__.py` | live | keep |
| `crm.document` | table | AA-Partner (`crm_owner`) | n/a | 1/0/0 | Partner: code 7, migrations 11, tests 7; Infra: infra tools 1, migrations 11 e.g. `api/app/documents/__init__.py` | live | keep |
| `crm.erasure_request` | table | AA-Partner (`crm_owner`) | n/a | 0/0/0 | Partner: code 2, migrations 2, tests 6; Infra: migrations 2 e.g. `api/app/lifecycle/offboarding.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `crm.form_definition` | table | AA-Partner (`crm_owner`) | n/a | 3/0/0 | Partner: code 3, migrations 1, tests 4; Infra: migrations 1 e.g. `api/app/intake/forms.py` | live | keep |
| `crm.form_submission` | table | AA-Partner (`crm_owner`) | ~62 | 88/55/0 | Partner: code 7, migrations 12, tests 9; Infra: infra tools 1, migrations 12 e.g. `api/app/intake/process.py` | live | keep |
| `crm.fx_rate_override` | table | AA-Partner (`crm_owner`) | n/a | 0/0/0 | Partner: code 1, migrations 2, tests 4; Infra: migrations 2 e.g. `api/app/ledger/fx.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `crm.fx_rate_platform` | table | AA-Partner (`crm_owner`) | ~63 | 105/0/0 | Partner: code 1, migrations 1, tests 3; Infra: migrations 1 e.g. `api/app/fx/fetch.py` | live | keep |
| `crm.inbox_events` | table | AA-Partner (`crm_owner`) | n/a | 0/0/0 | Partner: code 2, migrations 1, tests 2; Infra: migrations 1 e.g. `api/app/booking/__init__.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `crm.ingest_address` | table | AA-Partner (`crm_owner`) | n/a | 1/0/0 | Partner: code 3, migrations 1, tests 3; Infra: migrations 1 e.g. `api/app/mail/ingest.py` | live | keep |
| `crm.intake_form` | table | AA-Partner (`crm_owner`) | n/a | 3/0/0 | Partner: code 3, migrations 1, tests 5; Infra: migrations 1 e.g. `api/app/intake/forms.py` | live | keep |
| `crm.integration_credential` | table | AA-Partner (`crm_owner`) | n/a | 2/9/1 | Partner: code 5, migrations 3, tests 5; Infra: infra tools 1, migrations 3 e.g. `api/app/mail/health.py` | live | keep |
| `crm.job` | table | AA-Partner (`crm_owner`) | ~7,917 | 22507/45009/14523 | CIS: code 4; Partner: ci 3, code 14, migrations 2, scripts 1, tests 23; Infra: code 7, infra tools 1, migrations 2, scripts 2, tests 2 e.g. `api/routers/admin_platform_ops.py` | live | keep |
| `crm.legal_hold` | table | AA-Partner (`crm_owner`) | n/a | 0/0/0 | Partner: code 1, migrations 11, tests 6; Infra: migrations 11 e.g. `api/app/lifecycle/policy.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `crm.lifecycle_run` | table | AA-Partner (`crm_owner`) | n/a | 13/0/0 | Partner: code 2, migrations 2, tests 3; Infra: migrations 2 e.g. `api/app/lifecycle/job.py` | live | keep |
| `crm.llm_call` | table | AA-Partner (`crm_owner`) | n/a | 0/0/0 | CIS: code 2; Partner: code 1, migrations 4, tests 7; Infra: migrations 4 e.g. `api/core/app_registry.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `crm.llm_usage_daily` | table | AA-Partner (`crm_owner`) | n/a | 0/0/0 | CIS: code 2; Partner: code 2, migrations 3, tests 3; Infra: migrations 3 e.g. `api/services/platform_apps.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `crm.mail_import` | table | AA-Partner (`crm_owner`) | n/a | 4/18/0 | Partner: code 1, migrations 1, tests 3; Infra: migrations 1 e.g. `api/app/mail/history_import.py` | live | keep |
| `crm.meeting_slot` | table | AA-Partner (`crm_owner`) | n/a | 11/8/0 | Partner: code 2, migrations 5, tests 2; Infra: migrations 5 e.g. `api/app/intake/slots.py` | live | keep |
| `crm.member` | table | AA-Partner (`crm_owner`) | ~6 | 13/1/0 | Partner: code 17, migrations 9, tests 26; Infra: code 1, infra tools 1, migrations 9, tests 1 e.g. Infra `accounts/aa365/identity_partner.tf` | live | keep |
| `crm.member_invitation` | table | AA-Partner (`crm_owner`) | n/a | 3/4/0 | Partner: code 4, migrations 2, tests 5; Infra: migrations 2 e.g. `api/app/members/invitations.py` | live | keep |
| `crm.membership_feed_state` | table | AA-Partner (`crm_owner`) | ~1 | 1/10821/0 | Partner: code 3, migrations 2, tests 7; Infra: migrations 2 e.g. `api/app/cis/feed_state.py` | live | keep |
| `crm.membership_inbox` | table | AA-Partner (`crm_owner`) | n/a | 3/0/0 | Partner: code 3, migrations 3, tests 3; Infra: code 1, migrations 3 e.g. Infra `accounts/aa365/crm_membership_alarms.tf` | live | keep |
| `crm.message` | table | AA-Partner (`crm_owner`) | n/a | 18/12/2 | Partner: code 8, migrations 2, tests 9; Infra: migrations 2 e.g. `api/app/dispatch/worker.py` | live | keep |
| `crm.message_template` | table | AA-Partner (`crm_owner`) | n/a | 4/0/0 | Partner: code 2, migrations 1, tests 2; Infra: migrations 1 e.g. `api/app/catalog/content.py` | live | keep |
| `crm.metric_event` | table | AA-Partner (`crm_owner`) | n/a | 8/0/0 | Partner: code 1, migrations 2, tests 2; Infra: migrations 2 e.g. `api/app/proposals/events.py` | live | keep |
| `crm.note` | table | AA-Partner (`crm_owner`) | n/a | 19/0/0 | Partner: code 4, migrations 12, tests 5; Infra: infra tools 1, migrations 12 e.g. `api/app/intake/process.py` | live | keep |
| `crm.option` | table | AA-Partner (`crm_owner`) | n/a | 39/3/0 | Partner: code 3, migrations 1, tests 5; Infra: migrations 1 e.g. `api/app/proposals/builder.py` | live | keep |
| `crm.option_block` | table | AA-Partner (`crm_owner`) | ~42 | 60/22/0 | Partner: code 1, migrations 1, tests 4; Infra: migrations 1 e.g. `api/app/proposals/builder.py` | live | keep |
| `crm.option_rule` | table | AA-Partner (`crm_owner`) | n/a | 5/0/0 | Partner: code 1, migrations 1, tests 3; Infra: migrations 1 e.g. `api/app/proposals/builder.py` | live | keep |
| `crm.otp_challenge` | table | AA-Partner (`crm_owner`) | n/a | 7/7/7 | Partner: code 3, migrations 1, tests 4; Infra: migrations 1, tests 1 e.g. `api/app/mail/sender.py` | live | keep |
| `crm.owner_recovery_request` | table | AA-Partner (`crm_owner`) | n/a | 0/0/0 | Partner: code 1, migrations 1, tests 5; Infra: migrations 1 e.g. `api/app/members/recovery.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `crm.payment` | table | AA-Partner (`crm_owner`) | n/a | 7/0/0 | Partner: code 1, migrations 2, tests 2; Infra: migrations 2 e.g. `api/app/proposals/service.py` | live | keep |
| `crm.payment_schedule` | table | AA-Partner (`crm_owner`) | n/a | 16/7/0 | Partner: code 4, migrations 1, tests 3; Infra: migrations 1 e.g. `api/app/portal/public.py` | live | keep |
| `crm.placeholder_map` | table | AA-Partner (`crm_owner`) | n/a | 0/0/0 | Partner: code 3, migrations 3, tests 5; Infra: migrations 3 e.g. `api/app/llm/gateway.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `crm.prep_pack_selection` | table | AA-Partner (`crm_owner`) | n/a | 0/0/0 | Partner: code 2, migrations 1, tests 2; Infra: migrations 1 e.g. `api/app/catalog/content.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `crm.profile_history` | table | AA-Partner (`crm_owner`) | n/a | 0/0/0 | Partner: migrations 1, tests 1; Infra: migrations 1 | reserved | keep (CRM-29b writes it) — crm-006 F2 table; writer not built; offboarding lists it |
| `crm.proposal` | table | AA-Partner (`crm_owner`) | ~16 | 17/109/0 | Partner: code 9, migrations 5, tests 8; Infra: migrations 5 e.g. `api/app/portal/public.py` | live | keep |
| `crm.proposal_day` | table | AA-Partner (`crm_owner`) | ~54 | 76/0/0 | Partner: code 1, migrations 2, tests 3; Infra: migrations 2 e.g. `api/app/proposals/builder.py` | live | keep |
| `crm.saved_reply` | table | AA-Partner (`crm_owner`) | n/a | 0/0/0 | Partner: code 1, migrations 2, tests 2; Infra: migrations 2 e.g. `api/app/mail/conversations.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `crm.selection` | table | AA-Partner (`crm_owner`) | n/a | 2/0/0 | Partner: code 4, migrations 2, tests 2; Infra: migrations 2 e.g. `api/app/proposals/builder.py` | live | keep |
| `crm.signature_request` | table | AA-Partner (`crm_owner`) | n/a | 7/0/0 | Partner: code 3, migrations 1, tests 3; Infra: migrations 1 e.g. `api/app/portal/access.py` | live | keep |
| `crm.status_transition` | table | AA-Partner (`crm_owner`) | ~121 | 136/0/0 | Partner: code 1, migrations 12, tests 5; Infra: migrations 12 e.g. `api/db/templates/tenant_table.sql` | live | keep |
| `crm.studio_invitation` | table | AA-Partner (`crm_owner`) | n/a | 2/4/0 | CIS: code 2; Partner: code 3, migrations 2, tests 5; Infra: migrations 2 e.g. `api/services/crm_console.py` | live | keep |
| `crm.task` | table | AA-Partner (`crm_owner`) | ~91 | 106/86/0 | Partner: code 13, migrations 11, tests 13; Infra: migrations 11 e.g. `api/app/booking/sync.py` | live | keep |
| `crm.tenant` | table | AA-Partner (`crm_owner`) | n/a | 4/0/0 | Partner: code 22, migrations 20, tests 36; Infra: migrations 20 e.g. `api/app/agencies.py` | live | keep |
| `crm.tenant_entitlement` | table | AA-Partner (`crm_owner`) | n/a | 0/0/0 | Partner: code 2, migrations 2, tests 6; Infra: migrations 2 e.g. `api/app/members/team.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `crm.tenant_key` | table | AA-Partner (`crm_owner`) | n/a | 4/0/0 | Partner: code 3, migrations 2, tests 5; Infra: infra tools 1, migrations 2 e.g. `api/app/vault/__init__.py` | live | keep |
| `crm.tenant_settings` | table | AA-Partner (`crm_owner`) | n/a | 1/18/0 | Partner: code 13, migrations 6, tests 13; Infra: migrations 6 e.g. `api/app/intake/settings.py` | live | keep |
| `crm.traveler` | table | AA-Partner (`crm_owner`) | ~51 | 55/0/0 | Partner: code 30, migrations 13, tests 20; Infra: infra tools 1, migrations 13, tests 3 e.g. `api/app/dispatch/queue.py` | live | keep |
| `crm.traveler_access` | table | AA-Partner (`crm_owner`) | n/a | 7/14/0 | Partner: code 3, migrations 1, tests 2; Infra: migrations 1 e.g. `api/app/portal/access.py` | live | keep |
| `crm.traveler_health` | table | AA-Partner (`crm_owner`) | n/a | 0/0/0 | Partner: code 4, migrations 1, tests 4; Infra: infra tools 1, migrations 1, tests 2 e.g. `api/app/intake/stage2.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `crm.traveler_profile` | table | AA-Partner (`crm_owner`) | ~44 | 55/170/0 | Partner: code 4, migrations 2, tests 6; Infra: migrations 2, tests 1 e.g. `api/app/intake/completeness.py` | live | keep |
| `crm.traveler_relation` | table | AA-Partner (`crm_owner`) | n/a | 0/0/0 | Partner: code 2, migrations 11, tests 4; Infra: infra tools 1, migrations 11 e.g. `api/app/privacy/known.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `crm.trip` | table | AA-Partner (`crm_owner`) | ~54 | 55/432/0 | Partner: code 33, migrations 12, tests 31; Infra: migrations 12, tests 3 e.g. `api/app/booking/aa_lines.py` | live | keep |
| `crm.trip_commitment` | table | AA-Partner (`crm_owner`) | n/a | 13/6/0 | Partner: code 7, migrations 3, tests 5; Infra: migrations 3 e.g. `api/app/booking/checker.py` | live | keep |
| `crm.trip_party` | table | AA-Partner (`crm_owner`) | ~51 | 55/0/0 | Partner: code 3, migrations 12, tests 6; Infra: migrations 12 e.g. `api/app/intake/process.py` | live | keep |
| `crm.trip_stage_history` | table | AA-Partner (`crm_owner`) | ~161 | 181/0/0 | Partner: code 4, migrations 4, tests 9; Infra: migrations 4 e.g. `api/app/intake/process.py` | live | keep |
| `crm.trip_traveler` | table | AA-Partner (`crm_owner`) | ~45 | 55/7/0 | Partner: code 15, migrations 12, tests 17; Infra: infra tools 1, migrations 12, tests 1 e.g. `api/app/intake/completeness.py` | live | keep |
| `crm.v_ai_traveler_profile` | view | AA-Partner (`crm_owner`) | n/a | - | Partner: migrations 1, tests 2; Infra: migrations 1 | reserved | keep — crm-006 view for crm_ai_reader; AI reader not built |
| `crm.v_ai_trip_context` | view | AA-Partner (`crm_owner`) | n/a | - | Partner: migrations 1, tests 1; Infra: migrations 1 | reserved | keep — crm-006 view for crm_ai_reader |
| `crm.v_ai_trip_party` | view | AA-Partner (`crm_owner`) | n/a | - | Partner: migrations 1, tests 2; Infra: migrations 1 | reserved | keep — crm-006 view for crm_ai_reader |
| `crm.v_booking_line_money_current` | view | AA-Partner (`crm_owner`) | n/a | - | Partner: code 2, migrations 1, tests 1; Infra: migrations 1 e.g. `api/app/booking/sync.py` | live | keep |
| `crm.v_insight_fact` | view | AA-Partner (`crm_owner`) | n/a | - | Partner: migrations 2, tests 1; Infra: migrations 2 | reserved | keep — crm-006 / crm-011 view for crm_insights |
| `crm.v_schema_versions` | view | AA-Partner (`crm_owner`) | n/a | - | Partner: code 1, migrations 1, tests 2; Infra: migrations 1 e.g. `api/app/db.py` | live | keep |

### `geo` (18)

| object | kind | owner (role) | rows (ref) | ins/upd/del (ref) | code references (origin/main) | verdict | proposed action — evidence |
|---|---|---|---|---|---|---|---|
| `geo.component_redirect` | table | AA-CIS-App (`cis_owner`) | n/a | 27/0/1 | CIS: code 5, migrations 1, tests 4; TripPlanner: code 1, migrations 1; Infra: migrations 2, scripts 2, tests 1 e.g. `services/places/components.py` | live | keep |
| `geo.geocode_call` | table | AA-CIS-App (`cis_owner`) | ~49 | 82/3/0 | CIS: code 7, migrations 2, tests 3; Infra: migrations 2 e.g. `services/jobs/place_geocode_job.py` | live | keep |
| `geo.graph_build` | table | AA-CIS-App (`cis_owner`) | ~3 | 70/139/67 | CIS: code 7, migrations 6, tests 7; TripPlanner: tests 1; Infra: migrations 6, scripts 2 e.g. `api/routers/admin_places.py` | live | keep |
| `geo.graph_edge` | table | AA-CIS-App (`cis_owner`) | ~8,412 | 101891/0/93479 | CIS: code 1, migrations 3, tests 2; Infra: migrations 3 e.g. `services/places/store.py` | live | keep |
| `geo.graph_node` | table | AA-CIS-App (`cis_owner`) | ~5,359 | 64402/0/59043 | CIS: code 1, migrations 3, tests 1; TripPlanner: tests 1; Infra: migrations 3 e.g. `services/places/store.py` | live | keep |
| `geo.place_dedupe_country` | table | AA-CIS-App (`cis_owner`) | n/a | 0/0/0 | CIS: code 4, migrations 1, tests 1; Infra: migrations 1 e.g. `api/routers/admin_places.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `geo.place_merge` | table | AA-CIS-App (`cis_owner`) | n/a | 0/0/0 | CIS: code 6, migrations 1, tests 1; Infra: migrations 1 e.g. `api/routers/admin_places.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `geo.place_name` | table | AA-CIS-App (`cis_owner`) | ~9,545 | 9545/14077/0 | CIS: code 10, migrations 3, tests 6; Infra: migrations 3 e.g. `services/jobs/place_geocode_job.py` | live | keep |
| `geo.place_outlier` | table | AA-CIS-App (`cis_owner`) | n/a | 0/0/0 | CIS: code 2, migrations 2, tests 2; Infra: migrations 2 e.g. `services/places/merges.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `geo.place_pair_verdict` | table | AA-CIS-App (`cis_owner`) | n/a | 0/0/0 | CIS: code 3, migrations 1, tests 1; Infra: migrations 1 e.g. `services/places/dedupe.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `geo.place_shape` | table | AA-CIS-App (`cis_owner`) | ~284 | 284/377/0 | CIS: code 12, migrations 4, tests 8; TripPlanner: tests 1; Infra: migrations 4 e.g. `frontend/app/admin/places/LinesTab.tsx` | live | keep |
| `geo.tour_build` | table | AA-CIS-App (`cis_owner`) | ~892 | 892/1911/0 | CIS: code 9, migrations 1, scripts 1, tests 4; Infra: migrations 1, scripts 4, tests 2 e.g. `api/routers/admin_places.py` | live | keep |
| `geo.tour_day` | table | AA-CIS-App (`cis_owner`) | ~6,996 | 15313/2274/8317 | CIS: code 7, migrations 4, tests 7; Infra: migrations 4, scripts 1 e.g. `api/routers/admin_places.py` | live | keep |
| `geo.tour_junction` | table | AA-CIS-App (`cis_owner`) | ~222,234 | 1845810/0/1623576 | CIS: code 1, migrations 3, tests 2; Infra: migrations 3 e.g. `services/places/store.py` | live | keep |
| `geo.tour_leg` | table | AA-CIS-App (`cis_owner`) | ~96,123 | 1144081/0/1047958 | CIS: code 1, migrations 3, tests 2; Infra: migrations 3 e.g. `services/places/store.py` | live | keep |
| `geo.tour_place` | table | AA-CIS-App (`cis_owner`) | ~13,356 | 29944/7996/16588 | CIS: code 12, migrations 9, tests 14; TripPlanner: code 2, migrations 1, tests 1; Infra: ci 1, migrations 10, scripts 4, tests 2 e.g. `services/photos/sync.py` | live | keep |
| `geo.tour_segment` | table | AA-CIS-App (`cis_owner`) | ~1,195 | 11570/0/10375 | CIS: code 7, migrations 4, tests 5; TripPlanner: code 1, tests 2; Infra: migrations 4 e.g. `services/jobs/place_shape_job.py` | live | keep |
| `geo.tour_stop` | table | AA-CIS-App (`cis_owner`) | ~19,422 | 232992/0/213570 | CIS: code 4, migrations 5, tests 4; TripPlanner: tests 1; Infra: migrations 5, scripts 1 e.g. `api/routers/admin_places.py` | live | keep |

### `gold_aa_internal` (9)

| object | kind | owner (role) | rows (ref) | ins/upd/del (ref) | code references (origin/main) | verdict | proposed action — evidence |
|---|---|---|---|---|---|---|---|
| `gold_aa_internal.aa_content_item` | table | AA-CIS-App (`cis_owner`) | ~28 | 29/29/0 | CIS: code 4, migrations 1, tests 3; Infra: migrations 1 e.g. `services/aa_content/__init__.py` | live | keep |
| `gold_aa_internal.aa_content_version` | table | AA-CIS-App (`cis_owner`) | ~28 | 32/29/0 | CIS: code 2, migrations 1, tests 1; Infra: migrations 1 e.g. `services/aa_content/store.py` | live | keep |
| `gold_aa_internal.content_exports` | table | AA-CIS-App (`cis_owner`) | n/a | 0/0/0 | CIS: code 1, migrations 6, tests 7; Infra: code 1, infra tools 2, migrations 3, scripts 1 e.g. Infra `db/scripts/x1_245_cis_owner_objects.py` | **dead** (wave 2) | unhook the guards, then quarantine — PRD v4 S5 export jobs (006); no writer or reader; but listed as an RLS parity table in Infra owners.yaml / isolation probe / X1 checks |
| `gold_aa_internal.published_tours` | table | AA-CIS-App (`cis_owner`) | ~892 | 497/2259/0 | CIS: code 28, migrations 30, scripts 8, tests 47; Booking: code 2, tests 1; TripPlanner: code 1, migrations 1, tests 3; Infra: code 1, infra tools 2, migrations 15, scripts 7, tests 5 e.g. `api/routers/admin.py` | live | keep |
| `gold_aa_internal.tenant_tour_versions` | table | AA-CIS-App (`cis_owner`) | ~53 | 61/129/0 | CIS: code 20, frozen portal 1, migrations 10, scripts 1, tests 27; Partner: code 1; Infra: code 2, infra tools 2, migrations 6, scripts 1, tests 2 e.g. `api/routers/admin.py` | live | keep |
| `gold_aa_internal.tour_lifecycle_event` | table | AA-CIS-App (`cis_owner`) | n/a | 12/0/0 | CIS: code 2, migrations 2, tests 7; TripPlanner: code 1; Infra: migrations 2, scripts 1 e.g. `services/jobs/tripplanner_purge_job.py` | live | keep |
| `gold_aa_internal.v_aa_content_published` | view | AA-CIS-App (`cis_owner`) | n/a | - | CIS: code 3, migrations 1, tests 3; Infra: migrations 1 e.g. `api/routers/catalog_http.py` | live | keep |
| `gold_aa_internal.v_tour_liveness` | view | AA-CIS-App (`cis_owner`) | n/a | - | CIS: code 6, migrations 6, tests 4; Infra: migrations 6, scripts 2, tests 1 e.g. `api/routers/_served.py` | live | keep |
| `gold_aa_internal.webhook_deliveries` | table | AA-CIS-App (`cis_owner`) | n/a | 0/0/0 | CIS: code 1, migrations 6, tests 4; Infra: code 1, infra tools 2, migrations 3, scripts 1 e.g. Infra `db/scripts/x1_245_cis_owner_objects.py` | **dead** (wave 2) | unhook the guards, then quarantine — PRD v4 S5 webhook log (006); same as content_exports |

### `public` (1)

| object | kind | owner (role) | rows (ref) | ins/upd/del (ref) | code references (origin/main) | verdict | proposed action — evidence |
|---|---|---|---|---|---|---|---|
| `public.checkpoint_migrations` | table | platform (Infra roles/) (`aa_cis_admin`) | n/a | 0/0/0 | CIS: migrations 2; Infra: code 1, migrations 1 | **dead** (wave 2) | drop via an Infra roles/ file (master-owned) — LangGraph checkpointer bookkeeping; its data tables were dropped by 122; no PostgresSaver in code; drift decision 'keep (AA-853)' to revisit |

### `shared` (64)

| object | kind | owner (role) | rows (ref) | ins/upd/del (ref) | code references (origin/main) | verdict | proposed action — evidence |
|---|---|---|---|---|---|---|---|
| `shared.acp_runs` | table | AA-CIS-App (`cis_owner`) | n/a | 0/0/0 | CIS: code 2, migrations 3, tests 3; Infra: infra tools 1 e.g. `services/export/handler.py` | **dead** (wave 1) | quarantine (wave 1) — legacy run table (009); 0 rows ever written (services/export/handler.py comment, AA-492); test_aa751 guards against readers |
| `shared.admin_users` | table | AA-CIS-App (`cis_owner`) | ~11 | 9/761/4 | CIS: code 23, migrations 14, scripts 1, tests 21; Booking: migrations 3, tests 1; Infra: code 2, migrations 14, scripts 3, tests 1 e.g. `api/core/staff_authz.py` | live | keep |
| `shared.alert_recipient` | table | AA-CIS-App (`cis_owner`) | ~2 | 2/2426/0 | CIS: code 7, migrations 1, tests 4; Infra: code 1, migrations 1 e.g. `api/services/alert_recipients.py` | live | keep |
| `shared.cost_explorer_app_snapshot` | table | AA-CIS-App (`cis_owner`) | ~9,108 | 9108/0/0 | CIS: code 2, migrations 1, tests 2; Infra: migrations 1 e.g. `api/services/platform_cost.py` | live | keep |
| `shared.cost_explorer_snapshot` | table | AA-CIS-App (`cis_owner`) | ~2,766 | 9536/0/8951 | CIS: code 3, migrations 3, tests 1; Infra: migrations 2 e.g. `api/services/platform_cost.py` | live | keep |
| `shared.countries` | table | AA-CIS-App (`cis_owner`) | ~249 | 249/7/0 | CIS: code 12, migrations 2, scripts 2, tests 9; Booking: migrations 1; Infra: migrations 3, tests 1 e.g. `api/routers/admin_pipeline.py` | live | keep |
| `shared.decision_cache_hits_daily` | table | AA-CIS-App (`cis_owner`) | ~290 | 293/24641/0 | CIS: code 2, migrations 1, scripts 1 e.g. `api/routers/admin_decisions.py` | live | keep |
| `shared.decision_log` | table | AA-CIS-App (`cis_owner`) | ~427,684 | 425285/6/695728 | CIS: code 9, migrations 5, scripts 5, tests 11; Infra: infra tools 1, migrations 1, tests 1 e.g. `api/routers/admin_decisions.py` | live | keep |
| `shared.decision_question` | table | AA-CIS-App (`cis_owner`) | ~5 | 1/20/0 | CIS: code 7, migrations 16, tests 3 e.g. `api/routers/admin_decisions.py` | live | keep |
| `shared.destinations` | table | AA-CIS-App (`cis_owner`) | ~7,898 | 6954/3462/0 | CIS: code 22, migrations 15, tests 19; Booking: code 5, migrations 2, tests 1; TripPlanner: code 3, migrations 7, tests 14; Infra: code 2, infra tools 1, migrations 17, scripts 4, tests 5 e.g. `api/routers/admin_photos.py` | live | keep |
| `shared.dfs_balance_snapshot` | table | AA-CIS-App (`cis_owner`) | n/a | 24/0/0 | CIS: code 1, migrations 2 e.g. `shared/dfs_client/balance.py` | live | keep |
| `shared.dfs_call_log` | table | AA-CIS-App (`cis_owner`) | ~2,545 | 705/0/0 | CIS: code 9, migrations 3, scripts 1, tests 5; Infra: infra tools 1 e.g. `api/routers/admin_llm_ops.py` | live | keep |
| `shared.eval_golden_item` | table | AA-CIS-App (`cis_owner`) | ~100 | 103/0/0 | CIS: code 4, migrations 1, tests 4; Infra: migrations 1 e.g. `services/golden_set/store.py` | live | keep |
| `shared.eval_golden_set` | table | AA-CIS-App (`cis_owner`) | n/a | 4/0/0 | CIS: code 7, migrations 2, tests 5; Infra: migrations 2 e.g. `services/golden_set/derive.py` | live | keep |
| `shared.eval_item_result` | table | AA-CIS-App (`cis_owner`) | ~140 | 193/0/0 | CIS: code 4, migrations 1, tests 5; Infra: migrations 1 e.g. `services/golden_set/derive.py` | live | keep |
| `shared.jev_credit_topup` | table | AA-CIS-App (`cis_owner`) | n/a | 2/0/0 | CIS: code 4, migrations 1, tests 3 e.g. `api/routers/admin_decisions.py` | live | keep |
| `shared.jev_tenant_allowlist` | table | AA-CIS-App (`cis_owner`) | n/a | 4/0/7 | CIS: code 4, migrations 2, tests 4; Infra: infra tools 1 e.g. `api/routers/admin.py` | live | keep |
| `shared.job` | table | AA-CIS-App (`cis_owner`) | ~7,682 | 7068/65882/0 | CIS: code 51, frozen portal 1, migrations 28, scripts 7, tests 62; Booking: code 1, migrations 4, tests 3; Partner: code 1, tests 1; Infra: code 8, infra tools 1, migrations 27, scripts 3, tests 8 e.g. `api/core/ops_metrics_sampler.py` | live | keep |
| `shared.job_worker` | table | AA-CIS-App (`cis_owner`) | ~175 | 452/122250/338 | CIS: code 8, migrations 3, tests 6; Infra: migrations 1 e.g. `api/core/app_registry.py` | live | keep |
| `shared.llm_call_daily` | table | AA-CIS-App (`cis_owner`) | n/a | 5/0/0 | CIS: code 5, migrations 1, tests 6; Infra: infra tools 1, migrations 1 e.g. `api/services/platform_cost.py` | live | keep |
| `shared.llm_call_log` | table | AA-CIS-App (`cis_owner`) | ~383,796 | 269812/0/200 | CIS: code 45, migrations 18, scripts 7, tests 31; TripPlanner: code 2, migrations 2, tests 2; Infra: code 1, infra tools 2, migrations 7, scripts 1, tests 2 e.g. `api/core/app_registry.py` | live | keep |
| `shared.llm_model_catalog` | table | AA-CIS-App (`cis_owner`) | n/a | 3/5/0 | CIS: code 8, migrations 13, scripts 1, tests 10; TripPlanner: code 1; Infra: code 2, infra tools 1, migrations 8 e.g. `api/routers/admin_llm_ops.py` | live | keep |
| `shared.llm_role_config` | table | AA-CIS-App (`cis_owner`) | ~36 | 20/26/6 | CIS: code 11, migrations 31, scripts 1, tests 14; TripPlanner: code 1; Infra: code 1, infra tools 1, migrations 19, tests 1 e.g. `api/routers/admin_llm_ops.py` | live | keep |
| `shared.llm_shadow_log` | table | AA-CIS-App (`cis_owner`) | ~5,554 | 3024/0/0 | CIS: code 2, migrations 2; TripPlanner: code 1 e.g. `api/routers/admin_llm_ops.py` | live | keep |
| `shared.membership_plans` | table | AA-CIS-App (`cis_owner`) | n/a | 0/0/0 | CIS: code 3, frozen portal 1, migrations 3, tests 4; Partner: code 1; Infra: migrations 3 e.g. `api/routers/_billing.py` | live (idle) | keep — no write counted since the stats reset; read by code; rows come from migrations or a dormant path |
| `shared.notifications` | table | AA-CIS-App (`cis_owner`) | ~39 | 29/29/0 | CIS: code 17, migrations 2, tests 16; Infra: code 1, migrations 1 e.g. `api/core/aa544_tenant_pool.py` | live | keep |
| `shared.pipeline_jobs` | table | AA-CIS-App (`cis_owner`) | ~523 | 0/0/0 | CIS: code 8, migrations 2, tests 3 e.g. `api/routers/admin_job_runner.py` | read-only legacy | keep; wave 3: retire GET /admin/jobs/{id}, archive to S3, then quarantine — AA-735: read-only history (api/routers/jobs_repo.py); jobs moved to shared.job |
| `shared.pipeline_lessons` | table | AA-CIS-App (`cis_owner`) | n/a | 0/0/0 | CIS: code 2, migrations 3, scripts 1, tests 1; Infra: migrations 1 e.g. `services/content_generation/flag_fix_node.py` | read-only legacy (frozen) | keep; dropped by WM-34 (AA-919 writing memory), not by AA-850 — AA-915: AA-132 lessons loop frozen behind PIPELINE_LESSONS_ENABLED (default off, no SQL sent); superseded by app ADR 0010 |
| `shared.pipeline_runs` | table | AA-CIS-App (`cis_owner`) | ~46 | 0/1679/0 | CIS: code 9, migrations 13, tests 19; Infra: code 2, infra tools 3, migrations 6, scripts 1, tests 1 e.g. `api/routers/admin.py` | live | keep |
| `shared.place_photo` | table | AA-CIS-App (`cis_owner`) | ~3,232 | 0/22624/0 | CIS: code 6, migrations 7, tests 7; TripPlanner: tests 1; Infra: migrations 4 e.g. `api/routers/admin_photos.py` | live | keep |
| `shared.prompt_eval_runs` | table | AA-CIS-App (`cis_owner`) | n/a | 30/7/0 | CIS: code 8, migrations 4, tests 6; Infra: migrations 3 e.g. `services/eval/regression.py` | live | keep |
| `shared.rerun_wave` | table | AA-CIS-App (`cis_owner`) | ~25 | 25/130/0 | CIS: ci 1, code 8, migrations 1, tests 4; Infra: ci 1, infra tools 1, migrations 1, tests 1 e.g. `api/routers/admin_waves.py` | live | keep |
| `shared.schema_versions` | table | AA-CIS-App (`cis_owner`) | ~301 | 164/0/0 | CIS: code 3, migrations 247, tests 64; Booking: migrations 32, tests 16; TripPlanner: migrations 14, tests 11; Partner: migrations 22, tests 20; Infra: ci 4, code 2, infra tools 9, migrations 147, scripts 8, tests 5 e.g. `api/core/readiness.py` | live | keep |
| `shared.spend_budget` | table | AA-CIS-App (`cis_owner`) | n/a | 8/0/0 | CIS: code 8, migrations 7, tests 6; Infra: code 1, migrations 6 e.g. `api/routers/admin_budgets.py` | live | keep |
| `shared.staff_app_grant` | table | AA-CIS-App (`cis_owner`) | n/a | 2/0/1 | CIS: code 6, migrations 3, tests 3; Infra: migrations 3 e.g. `api/routers/admin_platform.py` | live | keep |
| `shared.supply_content_version` | table | AA-CIS-App (`cis_owner`) | n/a | 8/7/0 | CIS: code 1, migrations 1, tests 2; Infra: migrations 1 e.g. `services/supply_content/review.py` | live | keep |
| `shared.supply_entity` | table | AA-CIS-App (`cis_owner`) | n/a | 4/16/0 | CIS: code 6, migrations 1, tests 2; Infra: migrations 1 e.g. `api/core/ops_metrics_sampler.py` | live | keep |
| `shared.supply_event_inbox` | table | AA-CIS-App (`cis_owner`) | n/a | 15/0/0 | CIS: code 1, migrations 1, tests 2; Infra: migrations 1 e.g. `services/supply_content/pull.py` | live | keep |
| `shared.supply_feed_cursor` | table | AA-CIS-App (`cis_owner`) | ~1 | 1/1022/0 | CIS: code 3, migrations 1, tests 2; Infra: migrations 1 e.g. `api/core/ops_metrics_sampler.py` | live | keep |
| `shared.supply_media` | table | AA-CIS-App (`cis_owner`) | n/a | 2/8/0 | CIS: code 5, migrations 1, tests 2; Infra: migrations 1 e.g. `services/jobs/supply_content_draft_job.py` | live | keep |
| `shared.tenant_api_usage` | table | AA-CIS-App (`cis_owner`) | ~154,162 | 114309/0/200 | CIS: code 11, migrations 4, tests 10; Infra: infra tools 1, migrations 2 e.g. `api/middleware/rate_limit.py` | live | keep |
| `shared.tenant_api_usage_monthly` | table | AA-CIS-App (`cis_owner`) | n/a | 3/0/0 | CIS: code 6, migrations 1, tests 4; Infra: infra tools 1, migrations 1 e.g. `api/routers/admin.py` | live | keep |
| `shared.tenant_brand_rule_versions` | table | AA-CIS-App (`cis_owner`) | n/a | 0/0/0 | CIS: code 1, migrations 1, tests 1; Infra: infra tools 1 | **dead** (wave 1) | quarantine (wave 1) — AA-82 brand-rule history (019); no writer or reader in any repo |
| `shared.tenant_brand_rules` | table | AA-CIS-App (`cis_owner`) | ~27 | 25/56/1 | CIS: code 17, frozen portal 1, migrations 16, scripts 1, tests 15; Partner: code 1; Infra: code 1, migrations 3 e.g. `api/routers/admin.py` | live | keep |
| `shared.tenant_brand_rules_deleted_aa404` | table | AA-CIS-App (`cis_owner`) | n/a | 0/0/0 | CIS: code 1, migrations 1, tests 1; Infra: infra tools 1 | **dead** (wave 1) | quarantine (wave 1); archive rows to S3 before the drop — AA-404 backup copy of 6 mis-attached demo brand rows (104); no reader |
| `shared.tenant_export_config` | table | AA-CIS-App (`cis_owner`) | n/a | 0/0/0 | CIS: code 2, migrations 4, tests 2; Infra: infra tools 1 e.g. `shared/services/tenant_config_service.py` | **dead** (wave 2) | remove the unused reader, then quarantine — only reader TenantConfigService.get_export_config() has no runtime caller (tests only); export webhooks never built |
| `shared.tenant_integrations` | table | AA-CIS-App (`cis_owner`) | n/a | 14/11/14 | CIS: code 4, migrations 4, tests 13; Infra: migrations 3 e.g. `api/core/aa544_tenant_pool.py` | live | keep |
| `shared.tenant_members` | table | AA-CIS-App (`cis_owner`) | n/a | 6/4/0 | CIS: code 14, migrations 1, tests 4; Infra: infra tools 1, migrations 1, tests 1 e.g. `api/core/partner_identity.py` | live | keep |
| `shared.tenant_membership_event` | table | AA-CIS-App (`cis_owner`) | n/a | 14/0/0 | CIS: code 4, migrations 1, tests 4; Infra: infra tools 1, migrations 1 e.g. `api/routers/tenant_membership.py` | live | keep |
| `shared.tenant_rewrite_usage` | table | AA-CIS-App (`cis_owner`) | ~6 | 4/56/0 | CIS: code 2, migrations 1, tests 2; Infra: infra tools 1 e.g. `api/routers/v1_tours.py` | live | keep |
| `shared.tenant_seo_config` | table | AA-CIS-App (`cis_owner`) | n/a | 4/11/0 | CIS: code 8, migrations 6, tests 7; Infra: migrations 1 e.g. `api/routers/admin.py` | live | keep |
| `shared.tenants` | table | AA-CIS-App (`cis_owner`) | ~4 | 7/34/1 | CIS: code 41, migrations 46, scripts 3, tests 68; Booking: tests 1; Partner: code 2; Infra: code 1, infra tools 2, migrations 10, tests 3 e.g. `api/core/e2e_staff.py` | live | keep |
| `shared.unmapped_market_requests` | table | AA-CIS-App (`cis_owner`) | n/a | 0/0/0 | CIS: code 3, migrations 1, tests 3; Infra: infra tools 1 e.g. `api/routers/admin_tenant360.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `shared.v_batch_stats` | view | AA-CIS-App (`cis_owner`) | n/a | - | CIS: migrations 1 | **dead** (wave 1) | quarantine (wave 1) — pre-ACP admin view (003) over raw_tours; no reader |
| `shared.v_country_unmapped` | view | AA-CIS-App (`cis_owner`) | n/a | - | CIS: migrations 3, tests 1; Infra: migrations 3 | live (ops report) | keep — AA-851 orphan report (279), read by hand / tests; expected empty |
| `shared.v_destination_photos` | view | AA-CIS-App (`cis_owner`) | n/a | - | CIS: code 2, migrations 9, tests 6; TripPlanner: tests 1; Infra: code 1, infra tools 1, migrations 7, scripts 1 e.g. `api/services/data_coverage/queries.py` | live (to retire) | keep; move services/photos/sync.py to catalog.v_destination_photo, then retire (DM-2.4) — DM-2.4 says retired after X4; photo sync and data coverage still read it |
| `shared.v_pipeline_summary` | view | AA-CIS-App (`cis_owner`) | n/a | - | CIS: migrations 2; Infra: migrations 1 | **dead** (wave 1) | quarantine (wave 1) — pre-ACP admin view (003, retyped by 281) over raw_tours / generated_content / quality_scores; no reader |
| `shared.v_tenant_monthly_usage` | view | AA-CIS-App (`cis_owner`) | n/a | - | CIS: code 7, migrations 4, tests 6; Infra: migrations 3 e.g. `api/routers/_billing.py` | live | keep |
| `shared.v_tour_photos` | view | AA-CIS-App (`cis_owner`) | n/a | - | CIS: code 2, migrations 8, tests 6; TripPlanner: tests 1; Infra: code 1, infra tools 1, migrations 6, scripts 1, tests 1 e.g. `api/services/data_coverage/queries.py` | live (to retire) | keep; move CIS readers to catalog.v_tour_photo, then retire (DM-2.4) — DM-2.4 says retired after X4 (X4 done 23/10); CIS data coverage still reads it |
| `shared.writing_memory_release` | table | AA-CIS-App (`cis_owner`) | ~4 | 20/80/1 | CIS: code 9, migrations 3, scripts 1, tests 4; Infra: migrations 3 e.g. `api/core/readiness.py` | live | keep |
| `shared.writing_memory_shadow` | table | AA-CIS-App (`cis_owner`) | n/a | 0/0/0 | CIS: code 2, migrations 1, tests 2; Infra: migrations 1 e.g. `services/writing_memory/shadow.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |
| `shared.writing_memory_writer` | table | AA-CIS-App (`cis_owner`) | n/a | 4/8/0 | CIS: code 2, migrations 2, tests 1; Infra: migrations 2 e.g. `services/writing_memory/insertion.py` | live | keep |
| `shared.writing_rule` | table | AA-CIS-App (`cis_owner`) | n/a | 25/16/0 | CIS: code 9, migrations 3, tests 7; Infra: migrations 3 e.g. `api/core/readiness.py` | live | keep |
| `shared.writing_signal` | table | AA-CIS-App (`cis_owner`) | ~580 | 600/586/0 | CIS: code 14, migrations 2, tests 14; Infra: migrations 2 e.g. `api/core/ops_metrics_sampler.py` | live | keep |

### `silver_aa_internal` (7)

| object | kind | owner (role) | rows (ref) | ins/upd/del (ref) | code references (origin/main) | verdict | proposed action — evidence |
|---|---|---|---|---|---|---|---|
| `silver_aa_internal.generated_content` | table | AA-CIS-App (`cis_owner`) | ~2,296 | 1804/851/0 | CIS: code 15, migrations 18, scripts 7, tests 26; Infra: code 1, infra tools 2, migrations 4, scripts 1 e.g. `api/routers/admin.py` | live | keep |
| `silver_aa_internal.quality_scores` | table | AA-CIS-App (`cis_owner`) | ~2,272 | 1811/1773/7 | CIS: code 4, migrations 9, scripts 3, tests 13; Infra: code 1, infra tools 2, migrations 4, scripts 1 e.g. `api/routers/admin_pipeline.py` | live | keep |
| `silver_aa_internal.raw_sources` | table | AA-CIS-App (`cis_owner`) | ~34 | 0/0/0 | CIS: code 6, migrations 3, tests 4; Infra: code 1, infra tools 2, migrations 2 e.g. `api/routers/admin_pipeline.py` | live (idle) | keep — no write counted since the stats reset; read by code; rows come from migrations or a dormant path |
| `silver_aa_internal.raw_tours` | table | AA-CIS-App (`cis_owner`) | ~987 | 0/2645/0 | CIS: code 52, migrations 43, scripts 7, tests 56; TripPlanner: tests 5; Infra: code 1, infra tools 2, migrations 15, scripts 7, tests 4 e.g. `api/routers/admin.py` | live | keep |
| `silver_aa_internal.review_queue` | table | AA-CIS-App (`cis_owner`) | ~229 | 178/109/0 | CIS: code 13, migrations 2, scripts 2, tests 9; Infra: infra tools 1 e.g. `api/routers/admin.py` | live | keep |
| `silver_aa_internal.seo_context` | table | AA-CIS-App (`cis_owner`) | ~918 | 506/75/0 | CIS: code 12, migrations 9, scripts 4, tests 10; Infra: code 1, infra tools 2, migrations 3, scripts 2, tests 1 e.g. `api/routers/admin_pipeline.py` | live | keep |
| `silver_aa_internal.upload_staging` | table | AA-CIS-App (`cis_owner`) | n/a | 0/0/0 | CIS: code 5, migrations 1, tests 2; Infra: infra tools 1 e.g. `api/routers/admin_pipeline.py` | live (idle) | keep — no write counted since the stats reset; a code writer exists |

### `tripplanner` (14)

| object | kind | owner (role) | rows (ref) | ins/upd/del (ref) | code references (origin/main) | verdict | proposed action — evidence |
|---|---|---|---|---|---|---|---|
| `tripplanner.component_id_map` | table | AA-TripPlanner-Web (`tp_owner`) | ~750 | 756/0/0 | CIS: migrations 1; TripPlanner: code 2, migrations 3, tests 8; Infra: migrations 4, scripts 5, tests 3 e.g. `backend/assembly/events.py` | live | keep |
| `tripplanner.customers` | table | AA-TripPlanner-Web (`tp_owner`) | n/a | 7/7/1 | CIS: code 1; Booking: code 6, migrations 1; TripPlanner: code 3, migrations 5, tests 9; Infra: migrations 5, scripts 2, tests 1 e.g. `backend/app/contracts/inquiry.submitted.v1.1.json` | live | keep |
| `tripplanner.llm_spend_daily` | table | AA-TripPlanner-Web (`tp_owner`) | ~8 | 8/1502/0 | TripPlanner: code 2, migrations 2, tests 3; Infra: migrations 2, scripts 2, tests 1 e.g. `backend/config.py` | live | keep |
| `tripplanner.narration_cache` | table | AA-TripPlanner-Web (`tp_owner`) | n/a | 1/1/0 | TripPlanner: code 2, migrations 3, tests 2; Infra: infra tools 1, migrations 3, scripts 2, tests 1 e.g. `backend/assembly/narration_cache.py` | live | keep |
| `tripplanner.outbox` | table | AA-TripPlanner-Web (`tp_owner`) | n/a | 8/0/3 | Booking: code 5, migrations 1, tests 6; TripPlanner: code 1, migrations 6, tests 8; Infra: migrations 7, scripts 1 e.g. `backend/app/contracts/inquiry.submitted.v1.1.json` | live | keep |
| `tripplanner.sessions` | table | AA-TripPlanner-Web (`tp_owner`) | ~102 | 81/43/3 | CIS: migrations 2, tests 3; TripPlanner: code 5, migrations 8, tests 9; Infra: infra tools 1, migrations 9, scripts 1, tests 1 e.g. `backend/assembly/account.py` | live | keep |
| `tripplanner.traveller_accounts` | table | AA-TripPlanner-Web (`tp_owner`) | n/a | 3/1/0 | TripPlanner: code 1, migrations 2, tests 4; Infra: migrations 2, scripts 1 e.g. `backend/assembly/account.py` | live | keep |
| `tripplanner.trip_drafts` | table | AA-TripPlanner-Web (`tp_owner`) | ~98 | 79/284/1 | TripPlanner: code 4, migrations 6, tests 5; Infra: migrations 5, scripts 3 e.g. `backend/assembly/account.py` | live | keep |
| `tripplanner.trip_events` | table | AA-TripPlanner-Web (`tp_owner`) | ~416 | 363/0/6 | CIS: migrations 1; Booking: code 5; TripPlanner: code 2, migrations 6, tests 13; Infra: migrations 5, scripts 3 e.g. `backend/app/contracts/inquiry.submitted.v1.1.json` | live | keep |
| `tripplanner.v_inquiry_outbox` | view | AA-TripPlanner-Web (`tp_owner`) | n/a | - | CIS: tests 1; Booking: code 7, migrations 1, tests 4; TripPlanner: code 1, migrations 4, tests 5; Infra: code 1, infra tools 2, migrations 5 e.g. `backend/app/contracts/inquiry.submitted.v1.1.json` | live | keep |
| `tripplanner.v_ops_component_id_map` | view | AA-TripPlanner-Web (`tp_owner`) | n/a | - | CIS: code 1, tests 2; TripPlanner: migrations 1, tests 1; Infra: code 1, infra tools 2, migrations 1, tests 1 e.g. `api/services/data_coverage/queries.py` | live | keep |
| `tripplanner.v_ops_data_totals` | view | AA-TripPlanner-Web (`tp_owner`) | n/a | - | CIS: code 2, tests 2; TripPlanner: migrations 1, tests 1; Infra: code 1, infra tools 2, migrations 1, tests 1 e.g. `api/services/data_coverage/queries.py` | live | keep |
| `tripplanner.v_ops_pin_components` | view | AA-TripPlanner-Web (`tp_owner`) | n/a | - | CIS: code 2, tests 2; TripPlanner: migrations 1, tests 1; Infra: code 1, infra tools 2, migrations 1, tests 1 e.g. `api/services/data_coverage/queries.py` | live | keep |
| `tripplanner.v_ops_traffic_daily` | view | AA-TripPlanner-Web (`tp_owner`) | n/a | - | CIS: code 4, tests 3; TripPlanner: migrations 1, tests 1; Infra: code 1, infra tools 2, migrations 1, tests 1 e.g. `api/services/ops_overview/__init__.py` | live | keep |

