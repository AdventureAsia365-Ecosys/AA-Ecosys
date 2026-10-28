---
id: ARCH-09
title: Dead Table Registry
description: Tables on the shared RDS that are kept but no longer written or read, or were dropped, with the migration and the evidence.
type: reference
status: draft
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem, aa-cis-dev-db]
last_reviewed: 2026-10-28
review_every_days: 90
related: [ARCH-08, docs/database/schema-ownership.md]
---

# Dead Table Registry

One row per table that is frozen (kept, no writer) or dropped. Procedure for a drop: skill `aa-cis-schema`
`references/destructive-ops.md` (DRY RUN → snapshot → apply → independent verify). Update the row before the apply
(the DRY RUN numbers, the approval) and after it (the apply run, the verify). Table and column names:
[`db-schema-reference.md`](db-schema-reference.md).

| Table | Owner | State | Since | Migration | Why | Evidence |
|---|---|---|---|---|---|---|
| `tripplanner.itinerary_components` | AA-TripPlanner-Web | **dropped** 23/10/2026 | frozen 14/10/2026 (AA-712 slice 6a, TP #75); dropped 23/10/2026 | tp-018 (AA-712 X4) | the pilot's extraction output; CIS builds `geo.tour_place` behind `catalog.v_tour_component` (ADR 0007); unread since the TripPlanner X4 reader removal | DRY RUN: 3,905 rows, last write 2026-09-29 06:43 UTC (`created_at`), insert and update counters 0; dropped by DB Migrate apply run 39905424239; verify run 39905942615 `exists=f` |
| `tripplanner.tour_day` | AA-TripPlanner-Web | **dropped** 23/10/2026 | frozen 14/10/2026; dropped 23/10/2026 | tp-018 (AA-712 X4) | replaced by `geo.tour_day` / `catalog.v_tour_day` | DRY RUN: 599 rows, last write 2026-09-29 05:56 UTC (`extracted_at`), insert and update counters 0; dropped by DB Migrate apply run 39905424239; verify run 39905942615 `exists=f` |
| `tripplanner.tour_stop` | AA-TripPlanner-Web | **dropped** 23/10/2026 | frozen 14/10/2026; dropped 23/10/2026 | tp-018 (AA-712 X4) | replaced by `geo.tour_stop` / `catalog.v_tour_stop` | DRY RUN: 622 rows, last write unknown (no write-time column), insert and update counters 0; dropped by DB Migrate apply run 39905424239; verify run 39905942615 `exists=f` |
| `tripplanner.tour_graph_build` | AA-TripPlanner-Web | **dropped** 23/10/2026 | frozen 14/10/2026; dropped 23/10/2026 | tp-018 (AA-712 X4) | replaced by `geo.graph_build` | DRY RUN: 4 rows, last write 2026-09-29 06:44 UTC (`built_at`), insert and update counters 0; dropped by DB Migrate apply run 39905424239; verify run 39905942615 `exists=f` |
| `tripplanner.tour_graph_edge` | AA-TripPlanner-Web | **dropped** 23/10/2026 | frozen 14/10/2026; dropped 23/10/2026 | tp-018 (AA-712 X4) | replaced by `geo.graph_edge` / `catalog.v_graph_edge` | DRY RUN: 379 rows, last write unknown (no write-time column), insert and update counters 0; dropped by DB Migrate apply run 39905424239; verify run 39905942615 `exists=f` |
| `tripplanner.tour_graph_node` | AA-TripPlanner-Web | **dropped** 23/10/2026 | frozen 14/10/2026; dropped 23/10/2026 | tp-018 (AA-712 X4) | replaced by `geo.graph_node` / `catalog.v_graph_node` | DRY RUN: 299 rows, last write unknown (no write-time column), insert and update counters 0; dropped by DB Migrate apply run 39905424239; verify run 39905942615 `exists=f` |
| `tripplanner.tour_leg` | AA-TripPlanner-Web | **dropped** 23/10/2026 | frozen 14/10/2026; dropped 23/10/2026 | tp-018 (AA-712 X4) | replaced by `geo.tour_leg` / `catalog.v_tour_leg` | DRY RUN: 3,871 rows, last write unknown (no write-time column), insert and update counters 0; dropped by DB Migrate apply run 39905424239; verify run 39905942615 `exists=f` |
| `tripplanner.tour_junction` | AA-TripPlanner-Web | **dropped** 23/10/2026 | frozen 14/10/2026; dropped 23/10/2026 | tp-018 (AA-712 X4) | replaced by `geo.tour_junction` / `catalog.v_tour_junction` | DRY RUN: 3,496 rows, last write unknown (no write-time column), insert and update counters 0; dropped by DB Migrate apply run 39905424239; verify run 39905942615 `exists=f` |
| `gold_aa_internal.published_tours.content_embedding` (column) | AA-CIS-App | **candidate** (dead column, kept) | 27/10/2026 (S253, AA-989 decision) | none yet (a CIS migration drops it with the next `published_tours` change; DRY RUN first) | written by nothing since the ACP v2 move; no reader in any repo (`git grep content_embedding`: only `content_piece.content_embedding`, a different column, is read by `piece_similarity`); the `idx_pt_embedding` ivfflat index rides on it | S252 propagation audit row 9: 0 of 892 active rows non-NULL (`emb.dead_and_tenant_columns`); S253 grep of CIS, Booking, TripPlanner, Partner: no reader |
| `acp_contract.atom_decompose_jobs` | AA-CIS-App | **candidate** (wave 1) | 28/10/2026 (S255, AA-850) | draft `cis_NNN_aa850_quarantine_wave1.sql` (quarantine in `retired`), then `cis_NNN_aa850_drop_wave1.sql` after ≥ 14 days | AA-302 Bedrock Batch decompose tracker (081/082); the batch path is gone | AA-850 S255 census (`docs/audits/2026-10-28-S255-aa850-dead-tables/registry.md`): no runtime reader or writer in CIS, Booking, TripPlanner, Partner, Infra (`origin/main` 28/10/2026); reference counters 0 / 0 / 0. DRY RUN pending |
| `acp_contract.s1_from_atom_runs` | AA-CIS-App | **candidate** (wave 1) | 28/10/2026 (S255, AA-850) | draft `cis_NNN_aa850_quarantine_wave1.sql` (quarantine in `retired`), then `cis_NNN_aa850_drop_wave1.sql` after ≥ 14 days | AA-289 S1-from-atom run log (088); never written by the live S1 | AA-850 S255 census (`docs/audits/2026-10-28-S255-aa850-dead-tables/registry.md`): no runtime reader or writer in CIS, Booking, TripPlanner, Partner, Infra (`origin/main` 28/10/2026); reference counters 0 / 0 / 0. DRY RUN pending |
| `acp_contract.route_pick` | AA-CIS-App | **candidate** (wave 1) | 28/10/2026 (S255, AA-850) | draft `cis_NNN_aa850_quarantine_wave1.sql` (quarantine in `retired`), then `cis_NNN_aa850_drop_wave1.sql` after ≥ 14 days | writer `create_route_pick()` retired with the route hub (AA-859 wave 4) | AA-850 S255 census (`docs/audits/2026-10-28-S255-aa850-dead-tables/registry.md`): no runtime reader or writer in CIS, Booking, TripPlanner, Partner, Infra (`origin/main` 28/10/2026); reference counters 0 / 0 / 0. DRY RUN pending |
| `acp_shared.marketplace_portfolios` | AA-CIS-App | **candidate** (wave 1) | 28/10/2026 (S255, AA-850) | draft `cis_NNN_aa850_quarantine_wave1.sql` (quarantine in `retired`), then `cis_NNN_aa850_drop_wave1.sql` after ≥ 14 days | pre-tenant portfolio drafts (097); flow removed by 119 / ADR-2026-038; CIS 265 "dead" | AA-850 S255 census (`docs/audits/2026-10-28-S255-aa850-dead-tables/registry.md`): no runtime reader or writer in CIS, Booking, TripPlanner, Partner, Infra (`origin/main` 28/10/2026); reference counters 0 / 0 / 0. DRY RUN pending |
| `acp_shared.tenant_atom_state` | AA-CIS-App | **candidate** (wave 1) | 28/10/2026 (S255, AA-850) | draft `cis_NNN_aa850_quarantine_wave1.sql` (quarantine in `retired`), then `cis_NNN_aa850_drop_wave1.sql` after ≥ 14 days | N1 seeding state (098); not part of onboarding since AA-472; CIS 265 "dead" | AA-850 S255 census (`docs/audits/2026-10-28-S255-aa850-dead-tables/registry.md`): no runtime reader or writer in CIS, Booking, TripPlanner, Partner, Infra (`origin/main` 28/10/2026); reference counters 0 / 0 / 0. DRY RUN pending |
| `shared.acp_runs` | AA-CIS-App | **candidate** (wave 1) | 28/10/2026 (S255, AA-850) | draft `cis_NNN_aa850_quarantine_wave1.sql` (quarantine in `retired`), then `cis_NNN_aa850_drop_wave1.sql` after ≥ 14 days | legacy run table (009); 0 rows ever written (AA-492) | AA-850 S255 census (`docs/audits/2026-10-28-S255-aa850-dead-tables/registry.md`): no runtime reader or writer in CIS, Booking, TripPlanner, Partner, Infra (`origin/main` 28/10/2026); reference counters 0 / 0 / 0. DRY RUN pending |
| `shared.tenant_brand_rule_versions` | AA-CIS-App | **candidate** (wave 1) | 28/10/2026 (S255, AA-850) | draft `cis_NNN_aa850_quarantine_wave1.sql` (quarantine in `retired`), then `cis_NNN_aa850_drop_wave1.sql` after ≥ 14 days | AA-82 brand-rule history (019); no writer, no reader | AA-850 S255 census (`docs/audits/2026-10-28-S255-aa850-dead-tables/registry.md`): no runtime reader or writer in CIS, Booking, TripPlanner, Partner, Infra (`origin/main` 28/10/2026); reference counters 0 / 0 / 0. DRY RUN pending |
| `shared.tenant_brand_rules_deleted_aa404` | AA-CIS-App | **candidate** (wave 1) | 28/10/2026 (S255, AA-850) | draft `cis_NNN_aa850_quarantine_wave1.sql` (quarantine in `retired`), then `cis_NNN_aa850_drop_wave1.sql` after ≥ 14 days | AA-404 backup copy of 6 demo brand rows (104); no reader; archive rows before the drop | AA-850 S255 census (`docs/audits/2026-10-28-S255-aa850-dead-tables/registry.md`): no runtime reader or writer in CIS, Booking, TripPlanner, Partner, Infra (`origin/main` 28/10/2026); reference counters 0 / 0 / 0. DRY RUN pending |
| `shared.v_batch_stats` (view) | AA-CIS-App | **candidate** (wave 1) | 28/10/2026 (S255, AA-850) | draft `cis_NNN_aa850_quarantine_wave1.sql` (quarantine in `retired`), then `cis_NNN_aa850_drop_wave1.sql` after ≥ 14 days | pre-ACP admin view (003); no reader | AA-850 S255 census (`docs/audits/2026-10-28-S255-aa850-dead-tables/registry.md`): no runtime reader or writer in CIS, Booking, TripPlanner, Partner, Infra (`origin/main` 28/10/2026); reference counters 0 / 0 / 0. DRY RUN pending |
| `shared.v_pipeline_summary` (view) | AA-CIS-App | **candidate** (wave 1) | 28/10/2026 (S255, AA-850) | draft `cis_NNN_aa850_quarantine_wave1.sql` (quarantine in `retired`), then `cis_NNN_aa850_drop_wave1.sql` after ≥ 14 days | pre-ACP admin view (003, retyped by 281); no reader | AA-850 S255 census (`docs/audits/2026-10-28-S255-aa850-dead-tables/registry.md`): no runtime reader or writer in CIS, Booking, TripPlanner, Partner, Infra (`origin/main` 28/10/2026); reference counters 0 / 0 / 0. DRY RUN pending |

**Exception for the eight `tripplanner` place tables (tp-018), approved by Nghiệp in S248 (decision d14)** (data standards README: an exception to a MUST): root ADR 0007 decision 10 says "14 days after the
flip" (05/11/2026) and DM-3.8 / DM-3.9 ask for 14 days of `pg_stat_user_tables`, a quarantine (`ALTER … SET SCHEMA
retired`) and an S3 archive first. On Dev these are replaced by: two DRY RUN dispatches (before and after a
TripPlanner smoke) whose read and write counters must not move; no quarantine (the rows are derived data CIS rebuilds
in `geo`; a quarantine keeps the foreign keys to `shared.destinations` and needs a second destructive apply);
**archive location** = the DB Migrate pre-apply RDS snapshot of the tp-018 apply, tagged `aa:retain-until` = apply
date + 180 days and `aa:purpose` = `aa712-tp018-pre-drop` (the DM-7.3 S3 archive does not exist yet, N4). ADR 0007
carries the matching conditional amendment (S248). Lock note: the drop takes ACCESS EXCLUSIVE on CIS's
`shared.destinations` for its length (RI triggers of 11 foreign keys); apply while the job tables are idle, retry on a
lock timeout. Record (S248, 23/10/2026):

| Step | Value |
|---|---|
| DRY RUN (before, after a TripPlanner smoke) | DB Migrate run-script `aa712_frozen_tables_dry_run.py`: rows itinerary_components 3,905, tour_day 599, tour_stop 622, tour_graph_build 4, tour_graph_edge 379, tour_graph_node 299, tour_leg 3,871, tour_junction 3,496; last write 2026-09-29 (`itinerary_components`, `tour_day`, `tour_graph_build`; the other five have no write-time column); verdict `drop_ready=true` |
| Approval | Nghiệp, S248 decision d14 (the exception above and the drop) |
| Apply | DB Migrate `apply` of `tripplanner/018_drop_frozen_place_tables.sql`, run 39905424239 |
| Archive (pre-drop snapshot) | `db-migrate-tp-018-39905424239-1`, retained until 2027-04-21 (`aa:retain-until`, apply + 180 days; the default for a DB Migrate snapshot is 30 days) |
| Independent verify | DRY RUN V3, run 39905942615: all eight `exists=f`; `component_id_map` 750 rows kept; no CIS grant left to `tripplanner` |

Kept on purpose: `tripplanner.component_id_map` (tp-017) maps the pre-flip component ids that old drafts' trip events
still carry to catalog ids; it had no foreign key to `itinerary_components` and is kept after the drop.
