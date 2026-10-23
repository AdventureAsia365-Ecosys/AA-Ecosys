---
id: ARCH-08-schema-ownership
title: Schema ownership — shared RDS on acc2
description: Which repo owns, migrates and writes each schema on the shared RDS, and the migration-key rules.
type: reference
status: active
owner: nghiep
audience: [engineer, agent]
applies_to: [ecosystem, aa-cis-dev-db]
last_reviewed: 2026-10-23
review_every_days: 90
related: [ARCH-08, APP-04, infra/AA-CIS-Infra/db/owners.yaml]
---

# Schema ownership — shared RDS on acc2

One PostgreSQL instance (`aa-cis-dev-db`, acc2 `005097885195`, us-west-1) holds the data of every
AA_Ecosys app. This page says **which repo owns each schema** — owns = the only repo that writes
migrations for it and the only app that writes its rows (ADR 0001 decision 6, ADR 0002).

Column-level truth (names, types, enums, FKs) is the live dump in
[`docs/architecture/db-schema-reference.md`](../architecture/db-schema-reference.md). This page only
assigns owners and states the rules. Tracked in AA-684.

**Registry = `infra/AA-CIS-Infra/db/owners.yaml`** (data standards DM-1.2, since X1 S1, AA-CIS-Infra #163):
owner dirs, repos, version-key prefixes, owner and runtime roles and job-kind prefixes are read from it by
DB Migrate, the Migration Copy Guard and the schema dump. This page explains that registry for people; when
the two disagree, `owners.yaml` wins and this page is fixed in the same PR train.

## Rules

1. **A schema has one owner repo.** Its migrations live in that repo, next to the code that uses
   the schema, so schema and code change in one PR. An app never migrates another app's schema and
   never writes another app's rows.
2. **Other apps read only through contract views the owner grants** in its own migration
   (ADR 0008 decision 5, S237): tenant/catalog contract views live in `catalog`, others are
   `<schema>.v_<entity>` or `v_<event>_outbox`. No new table or column grant to another app's role.
   The TripPlanner pilot's table/column grants are revoked by the TripPlanner decoupling (data standards roadmap
   X4): CIS 254 (179 `raw_tours`, 180 `tour_atoms`) and CIS 270 (AA-712: `published_tours`, 201 `destinations` and
   photo views, 216 `v_active_tour_atoms`); the `tripplanner` role keeps only the catalog views and the Model
   Gateway (CIS 173: SELECT on the two config tables). The one standing write exception is INSERT on
   `shared.llm_call_log`. Rules in full:
   `docs/architecture/data-standards/` (Part A, CON-1..5 and SEC-3..5).
3. **AA-CIS-Infra owns the instance, not the schema**: RDS, parameter groups, backups, DB roles and
   the **DB Migrate** workflow that applies a reviewed file. Infra keeps no schema SQL of its own;
   `db/migrations/<owner>/` holds byte-identical copies of the owner's files for the workflow to
   apply (Nghiệp, S225: migrations are applied through Infra so nobody runs them from a laptop).
   The one Infra-native dir is `db/migrations/roles/` (key `rl-NNN`, X1): role bootstrap (LOGIN/NOLOGIN
   roles, memberships, `CONNECTION LIMIT`), `CREATE/ALTER/DROP EXTENSION`, the `public.*` leftovers and the
   prepared undo files of the X1 ownership transfers. No owner file creates or alters a role or an
   extension; those statements go into a `roles/` file.
4. **Every migration registers itself** in `shared.schema_versions` (`INSERT … ON CONFLICT DO
   NOTHING`, inside the file's own `BEGIN; … COMMIT;`). Version key per owner:

   | Owner | Version key | Files |
   |---|---|---|
   | AA-CIS-App | plain number, `217` (kept for history) | `api/migrations/NNN_*.sql` |
   | AA-TripPlanner-Web | `tp-NNN` | `migrations/NNN_*.sql` |
   | AA-Booking (AAA) | `bk-NNN` | `migrations/NNN_*.sql` (first: `bk-001`, applied 14/10/2026) |
   | AA-Partner (partner CRM, AA-932) | `crm-NNN` | `api/migrations/NNN_*.sql` (first: `crm-001`; Infra copy in `db/migrations/crm/`) |
   | AA-CIS-Infra (`roles`, Infra-native) | `rl-NNN` | `db/migrations/roles/NNN_*.sql` (first: `rl-001`, X1 S3/S8) |

   Without the prefix two repos' `007` would collide and the second one would silently not register.
5. **Cross-owner grant migrations do not wrap the grant in `IF EXISTS (role)`.** Apply them only after
   the grantee role exists. A guarded no-op still registers its version permanently, so the grant would
   never be retried (what tp-008 did for role `tripplanner`); an unguarded grant fails loudly and DB
   Migrate does not register a failed file, so it can be re-run (ADR 0004 decision 6).
6. **Destructive changes** (DROP, DELETE of data) follow the DRY RUN procedure in
   `skill/aa-cis-schema/references/destructive-ops.md`, whoever the owner is.
7. **Who runs a file (X1, AA-852 / AA-860, done 19/10/2026).** DB Migrate, DB Schema Dump and the DB
   Isolation Probe log in as **`db_migrator`** (LOGIN, NOCREATEROLE, `CONNECTION LIMIT` 5, created by
   `rl-002`) from the migrator task definition. Before each owner file the runner reads the live owner of
   the dir's anchor schema (`shared`, `booking`, `tripplanner`, `crm`) and runs the file as that role (`SET ROLE`),
   so a file creates objects owned by the owner role in the table below, with no `OWNER TO`. A `roles/`
   file always runs as the RDS master `aa_cis_admin`, read in the task; so do DB Migrate `set-password`
   and `run-script`. Otherwise the master is break-glass only (data standards Part B DM-8.9).

## Owners by schema

| Schema | Owner | DB owner role / runtime role(s) | What it is | Read by others |
|---|---|---|---|---|
| `silver_aa_internal` | AA-CIS-App | `cis_owner` / `cis_app`, `aa_app_user` | A0 raw tours, A1 rewrites (`generated_content`), `review_queue`, `seo_context`, upload staging | — |
| `gold_aa_internal` | AA-CIS-App | `cis_owner` / `cis_app`, `aa_app_user` | Master Content (`published_tours`), tenant tour versions, exports | None since CIS 270 (AA-712 X4; TripPlanner reads `catalog.v_tour`) |
| `acp_contract` | AA-CIS-App | `cis_owner` / `cis_app` | A3 platform atoms, Segments, Routes, Hubs, search demand; view `v_active_tour_atoms` | None since CIS 270 (216 revoked; 180 revoked by CIS 254) |
| `acp_shared` | AA-CIS-App | `cis_owner` / `cis_app`, `aa_app_user` | Tenant T-series: plans, angle gate, `content_piece`, `publish_log`, quota, audit | — |
| `acp_deliver` | AA-CIS-App | `cis_owner` / `cis_app`, `aa_app_user` | `tenant_tour_pages` (only table left after AA-603) | — |
| `tripplanner` | AA-TripPlanner-Web | `tp_owner` (since tp-013) / `tripplanner` | Trip user state (`sessions`, `customers`, `trip_events`, `trip_drafts`). The legacy place read models of the pilot (`itinerary_components`, `tour_day`, `tour_stop`, `tour_graph_*`, `tour_leg`, `tour_junction`), frozen since AA-712 slice 6a and unread since the X4 reader removal, are dropped by **tp-018** (AA-712 X4; replaced by CIS `geo` + `catalog` views, ADR 0007). ADR 0007 decision 10 sets that drop 14 days after the reader cut-over (05/11/2026); tp-018 comes earlier only on Nghiệp's written approval after the DRY RUN (ADR 0007 amendment S248, the exception to DM-3.8 / DM-3.9 recorded in the Dead Table Registry), otherwise the 14-day date stands. `component_id_map` (tp-017, AA-847, kept after tp-018): pre-flip component id → catalog component id for drafts and cached answers across the `PLACES_SOURCE=cis` flip; `tripplanner` SELECT + INSERT only (filled once by AA-CIS-Infra `aa847_component_id_map_fill.py`) | AA-Booking (`booking`): `v_inquiry_outbox` (tp-009); CIS runtime `cis_app`: `v_ops_traffic_daily` (tp-015, AA-858) |
| `geo` | AA-CIS-App | `cis_owner` / `cis_app` | Place pipeline (ADR 0007, AA-712, CIS 226+): per-tour builds (`tour_build`), day skeleton (`tour_day`), itinerary components (`tour_place`, stable `component_id`), name resolution cache (`place_name`), versioned tour graph (`graph_build`, `tour_stop`, `graph_node`, `graph_edge`, `tour_leg`, `tour_junction`). Keyed by `source_id`; written only by CIS jobs `place_extract` / `place_geocode` / `tour_graph_build` | **None directly** — internal; other apps read the `catalog.*` place and graph views (owner `catalog_owner` has `SELECT`). Only `EXECUTE` on the pure `geo.name_norm(text)` to `aa_app_user`, `tripplanner`, `booking` (CIS 228: a view calls functions with the reader's rights; no `USAGE` on `geo`) |
| `booking` | AA-Booking | `bk_owner` (since bk-014) / `booking` | Customers, OTPs/sessions, media, audit, `inbox_events` (`bk-001`, 14/10/2026, ADR 0004); later trip cases, suppliers and prices (ADR 0005). DB role `booking` created by `bk-001` (NOLOGIN, then LOGIN with a password set out-of-band, DSN in `booking/dev/database-url`), `USAGE` only on the schema. The schema and every object belong to NOLOGIN `bk_owner` since `bk-014` (X1 S6/S8); default privileges `FOR ROLE bk_owner` give `booking` what a new file creates | CIS runtime `cis_app`: `v_ops_funnel_daily`, `v_ops_case_status` (bk-017, AA-858) |
| `crm` | AA-Partner | `crm_owner` (since rl-003, born owned) / `crm_app` | Partner CRM (ADR 0010, ADR 0008a, data standards DM-6.8): the agency is the controller, AA the processor. `crm-001` (AA-932): privilege model (no PUBLIC `EXECUTE` on functions; default privileges `FOR ROLE crm_owner` give `crm_app` DML on tables and `USAGE, SELECT` on sequences) and the job queue `crm.job` (ADR 0003a template, kinds `crm_*`); the tenant tables follow from `crm-002` (AA-933). Roles: `crm_owner` NOLOGIN, `crm_app` LOGIN `CONNECTION LIMIT` 6, **NOINHERIT**, DSN `crm/dev/database-url`; four NOLOGIN roles reached only by `SET LOCAL ROLE` from `crm_app` (`crm_ai_reader`, `crm_insights`, `crm_support_reader`, `crm_eraser`; rl-004), whose grants come table by table and never on the F1 vault tables | **Nobody, in either direction** (ADR 0008a decision 1): no AA app role (`cis_app`, `aa_app_user`, `booking`, `tripplanner`) has `USAGE` on `crm`, and `crm_app` has nothing outside `crm`; everything goes over the HTTP contracts `crm.ops.v1`, `booking.b2b.v1`, `catalog.http.v1`, `tenant.membership.v1`. The isolation probe asserts 42501 both ways |
| `catalog` | AA-CIS-App | schema `cis_owner`, views `catalog_owner` / none (consumers read) | Catalog read model for other apps (AA-679, CIS 225): views only — `v_tour`, `v_tour_day`, `v_tour_place`, `v_tour_photo`, `v_destination`, `v_destination_photo` over the CIS pipeline tables. Contract `docs/contracts/catalog.tour.v1.json`. ADR 0007 (CIS 228, views only) adds the place/graph views over `geo`: `v_tour_component`, `v_tour_day_route`, `v_tour_stop`, `v_tour_leg`, `v_graph_node`, `v_graph_edge`, `v_tour_junction` (contract `docs/contracts/catalog.graph.v1.json`); CIS 253 (AA-847) adds `v_component_embedding` (HNSW top-k over live resolved components, not security_barrier, **`tripplanner` only**, pgvector only; contract `catalog.graph.v1.1.json`) and the internal, ungranted `_live_tour` / `_live_stop` every place / graph view reads liveness from, appending columns only to the 225 views (`v_destination` + `geo_status`, `located_by`, `precision`; `v_tour_place` + `located_by`, `precision`: contract `catalog.tour.v1.1.json`). Views owned by NOLOGIN `catalog_owner` (RDS `aa_cis_admin` is not BYPASSRLS), the schema by `cis_owner` since CIS 245; a view change follows the catalog-view recipe (AA-CIS-App `CONTEXT.md`, skill `aa-cis-schema`) | AA-Booking, TripPlanner (and `aa_app_user`): `USAGE` + `SELECT` on every view (225 + 228, unguarded) |
| `public` | — | `pg_database_owner`; objects and extensions `aa_cis_admin` (Infra `roles/`) | `checkpoint_migrations` (LangGraph checkpointer, CIS) and enums created before schemas existed | — |
| `shared` | per table, below | `cis_owner` / `cis_app`, `aa_app_user` | Platform tables every app may need | see below |

Empty schemas `acp_gold_output`, `acp_silver_s2`, `acp_silver_s3`, `acp_silver_s4` are leftovers of ACPv1 (CIS);
drop them in a CIS migration when convenient (owner `cis_owner`, runtime grants from CIS 244).

Owner and runtime roles come from `owners.yaml` (`owner_role`, `runtime_roles`) and the live dump: `cis_owner`
owns the 12 CIS schemas since CIS 245 (X1 S21), `bk_owner` and `tp_owner` own theirs since bk-014 / tp-013
(X1 S8), `crm_owner` owns `crm` from its creation (rl-003, AA-932; no transfer). `cis_app` is the CIS api + worker login since X1 S18; `aa_app_user` is the CIS tenant pool.

## `shared.*` by table

Every `shared` table is **owned by AA-CIS-App** unless the row says otherwise.

| Table(s) | Owner | Notes |
|---|---|---|
| `tenants`, `membership_plans`, `admin_users`, `staff_app_grant`, `tenant_*` (brand rules, configs, integrations, usage) | CIS | Tenant and admin identity of the CIS platform. `admin_users` is the ecosystem staff directory (CIS 247: `email`, `display_name`, `cognito_iss`/`cognito_sub`, `last_login_at`, `is_owner`; ADR 0006a) and `staff_app_grant` holds each staff member's role in another app (`app` = `booking` today, roles `admin`/`sales`/`contracting`/`content_creator`). Only the CIS staff directory writes them; no other app reads them (Booking gets `cis_role` from the bridge token today and will read `cognito:groups` from Phase 2). AA-Booking owns *customer* identity (ADR 0001; target Cognito EXTERNAL, ADR 0006). |
| `job`, `job_worker` | CIS | Durable job runner of CIS (ADR 0003). Other owners do not enqueue here: each owner has its own job table from the shared DDL template (ADR 0003a; `booking.job` bk-002, `tripplanner.job` when needed). Job kind prefixes per owner (ADR 0003a decision 3; registry: `owners.yaml` `job_kind_prefix`): CIS `shared.job` keeps its unprefixed names; Booking `bk_` (`booking.job` `job_kind_chk`); TripPlanner `tp_`; partner CRM `crm_` (`crm.job` `job_kind_chk`, crm-001); a new app `<prefix>_`. Every job table is created from the DDL template `apps/AA-CIS-App/shared/jobs/job_table_template.sql` (AA-751). Idle-exempt kinds (not counted by the deploy guards or the DB Migrate idle check): Booking `bk_inquiry_pull`; CRM `crm_heartbeat` (AA-932, the AA-Partner worker's liveness kind); CIS none since AA-751 (registry: `owners.yaml` `idle_exempt_kinds`, which DB Migrate reads; Booking `DEPLOY_GATE_EXEMPT` mirrors it). |
| `llm_role_config`, `llm_model_catalog` | CIS | Model Gateway config; TripPlanner has SELECT (CIS 173). |
| `llm_call_log`, `llm_shadow_log` | CIS | Cost log; TripPlanner has INSERT on `llm_call_log` only, rows tagged `quality_signal.app = "tripplanner"` (CIS 173). |
| `decision_log`, `decision_question`, `decision_cache_hits_daily`, `jev_*` | CIS | Jev decision layer. |
| `dfs_call_log`, `dfs_balance_snapshot`, `cost_explorer_snapshot`, `spend_budget` | CIS | Cost tracking and guard. |
| `notifications` | CIS | Admin bell. |
| `place_photo` (+ photo views) | CIS | Photo sync and matching (AA-708); other apps read photos through `catalog.v_tour_photo` / `v_destination_photo` (TripPlanner's CIS 201 grant on the `shared` photo views is revoked by CIS 270). |
| `destinations` | **CIS** (since ADR 0002) | Golden record of places. Created by TripPlanner migrations 002 / 005 (history); since CIS 201 only CIS writes it, and since CIS 270 (AA-712 X4) the `tripplanner` role cannot read it either (TripPlanner reads `catalog.v_destination`). Future column changes are CIS migrations. The place pipeline moves to CIS in AA-712 (ADR 0007): uniqueness changes from global `lower(name)` to `(name_norm, country, locality_norm)` (`locality_norm` NOT NULL DEFAULT '', non-empty only for generic names; `country` NOT NULL; same key on `geo.place_name`; ids kept), new geo-quality columns, and only the CIS job `place_geocode` writes coordinates. |
| `schema_versions` | CIS (table), every owner (its rows) | Each owner registers its own versions with its prefix (rule 4). From CIS 243 (X1): `bk_owner`/`tp_owner` insert only their own prefix (BEFORE INSERT key guard); from CIS 269 (AA-932) `crm_owner` likewise, `crm-` keys only; members of the registry owner insert any key; every other role none. `crm_owner` holds only `USAGE` on `shared` + `SELECT, INSERT` on this table. |
| `pipeline_jobs`, `pipeline_runs`, `acp_runs`, `pipeline_lessons`, `prompt_eval_runs`, `unmapped_market_requests` | CIS | `pipeline_jobs` is history only (no new writes, ADR 0003). `acp_runs` has no runtime reader since CIS #785 (AA-751; `/admin/acp/stuck-runs` removed) — Dead Table Registry candidate. |

## Current gaps (AA-684)

- [ ] **TripPlanner migrations 001–006 are not registered** in `shared.schema_versions`, so nobody
      can tell from the DB which ones ran. Fix: TripPlanner migration `007_register_versions.sql`
      registers `tp-001` … `tp-006` only for objects that exist (checked in the file), and every new
      TripPlanner migration registers `tp-NNN`. Needs DB Migrate to accept the `tripplanner/` owner
      and its `tp-` key.
- [ ] **`AA-CIS-Infra/modules/rds/migrations/001–008`** are byte-identical copies of CIS 001–008 that
      nothing references — delete them (not to be confused with `db/migrations/`, which the DB
      Migrate workflow applies).
- [ ] Every repo's `CONTEXT.md` links this page.
- [ ] ADR 0001 decision 6 / steering mention rule 1 (an app never migrates another app's schema).
- [ ] **Dead Table Registry** — `docs/architecture/dead-table-registry.md` is referenced (skill
      `aa-cis-schema`, `skill/README.md`) but does not exist yet; create it (S235 data lens: empty
      `acp_gold_output` / `acp_silver_s3` / `acp_silver_s4`, likely-legacy `pipeline_jobs`, `acp_runs`,
      `pipeline_runs`, …).
