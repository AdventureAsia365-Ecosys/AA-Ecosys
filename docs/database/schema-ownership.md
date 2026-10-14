# Schema ownership — shared RDS on acc2

One PostgreSQL instance (`aa-cis-dev-db`, acc2 `005097885195`, us-west-1) holds the data of every
AA_Ecosys app. This page says **which repo owns each schema** — owns = the only repo that writes
migrations for it and the only app that writes its rows (ADR 0001 decision 6, ADR 0002).

Column-level truth (names, types, enums, FKs) is the live dump in
[`docs/architecture/db-schema-reference.md`](../architecture/db-schema-reference.md). This page only
assigns owners and states the rules. Tracked in AA-684.

## Rules

1. **A schema has one owner repo.** Its migrations live in that repo, next to the code that uses
   the schema, so schema and code change in one PR. An app never migrates another app's schema and
   never writes another app's rows.
2. **Other apps read through grants the owner gives** — a column list or a view, granted in the
   owner's own migration (examples: CIS 173 gateway tables, 180 / 216 atoms, 201 destinations to the
   `tripplanner` role). Prefer a view (read model) over a raw table, so the owner can change the
   table without breaking readers.
3. **AA-CIS-Infra owns the instance, not the schema**: RDS, parameter groups, backups, DB roles and
   the **DB Migrate** workflow that applies a reviewed file. Infra keeps no schema SQL of its own;
   `db/migrations/<owner>/` holds byte-identical copies of the owner's files for the workflow to
   apply (Nghiệp, S225: migrations are applied through Infra so nobody runs them from a laptop).
4. **Every migration registers itself** in `shared.schema_versions` (`INSERT … ON CONFLICT DO
   NOTHING`, inside the file's own `BEGIN; … COMMIT;`). Version key per owner:

   | Owner | Version key | Files |
   |---|---|---|
   | AA-CIS-App | plain number, `217` (kept for history) | `api/migrations/NNN_*.sql` |
   | AA-TripPlanner-Web | `tp-NNN` | `migrations/NNN_*.sql` |
   | AA-Booking (AAA) | `bk-NNN` | `migrations/NNN_*.sql` (first: `bk-001`, applied 14/10/2026) |

   Without the prefix two repos' `007` would collide and the second one would silently not register.
5. **Cross-owner grant migrations do not wrap the grant in `IF EXISTS (role)`.** Apply them only after
   the grantee role exists. A guarded no-op still registers its version permanently, so the grant would
   never be retried (what tp-008 did for role `tripplanner`); an unguarded grant fails loudly and DB
   Migrate does not register a failed file, so it can be re-run (ADR 0004 decision 6).
6. **Destructive changes** (DROP, DELETE of data) follow the DRY RUN procedure in
   `skill/aa-cis-schema/references/destructive-ops.md`, whoever the owner is.

## Owners by schema

| Schema | Owner | What it is | Read by others |
|---|---|---|---|
| `silver_aa_internal` | AA-CIS-App | A0 raw tours, A1 rewrites (`generated_content`), `review_queue`, `seo_context`, upload staging | — |
| `gold_aa_internal` | AA-CIS-App | Master Content (`published_tours`), tenant tour versions, exports | TripPlanner: `published_tours` read (tenant RLS) |
| `acp_contract` | AA-CIS-App | A3 platform atoms, Segments, Routes, Hubs, search demand; view `v_active_tour_atoms` | TripPlanner: `v_active_tour_atoms` (216), `tour_atoms` columns (180, legacy) |
| `acp_shared` | AA-CIS-App | Tenant T-series: plans, angle gate, `content_piece`, `publish_log`, quota, audit | — |
| `acp_deliver` | AA-CIS-App | `tenant_tour_pages` (only table left after AA-603) | — |
| `tripplanner` | AA-TripPlanner-Web | Trip user state (`sessions`, `customers`, `trip_events`, `trip_drafts`). Legacy place read models (`itinerary_components`, `tour_day`, `tour_stop`, `tour_graph_*`, `tour_leg`, `tour_junction`) are **frozen** (ADR 0002) and replaced by CIS `geo` + `catalog` views (ADR 0007); a TripPlanner migration drops them 14 days after the reader cut-over | — |
| `geo` | AA-CIS-App | Place pipeline (ADR 0007, AA-712, CIS 226+): per-tour builds (`tour_build`), day skeleton (`tour_day`), itinerary components (`tour_place`, stable `component_id`), name resolution cache (`place_name`), versioned tour graph (`graph_build`, `tour_stop`, `graph_node`, `graph_edge`, `tour_leg`, `tour_junction`). Keyed by `source_id`; written only by CIS jobs `place_extract` / `place_geocode` / `tour_graph_build` | **None directly** — internal; other apps read the `catalog.*` place and graph views (owner `catalog_owner` has `SELECT`) |
| `booking` | AA-Booking | Customers, OTPs/sessions, media, audit, `inbox_events` (`bk-001`, 14/10/2026, ADR 0004); later trip cases, suppliers and prices (ADR 0005). DB role `booking` created by `bk-001` (NOLOGIN, then LOGIN with a password set out-of-band, DSN in `booking/dev/database-url`), `USAGE` only on the schema | — |
| `catalog` | AA-CIS-App | Catalog read model for other apps (AA-679, CIS 225): views only — `v_tour`, `v_tour_day`, `v_tour_place`, `v_tour_photo`, `v_destination`, `v_destination_photo` over the CIS pipeline tables. Contract `docs/contracts/catalog.tour.v1.json`. ADR 0007 (CIS 227) adds the place/graph views over `geo`: `v_tour_component`, `v_tour_day_route`, `v_tour_stop`, `v_tour_leg`, `v_graph_node`, `v_graph_edge`, `v_tour_junction` (contract `catalog.graph.v1`), appending columns only to the 225 views. Owned by NOLOGIN `catalog_owner` (RDS `aa_cis_admin` is not BYPASSRLS) | AA-Booking, TripPlanner (and `aa_app_user`): `USAGE` + `SELECT` on every view (225, unguarded) |
| `public` | — | `checkpoint_migrations` (LangGraph checkpointer, CIS) and enums created before schemas existed | — |
| `shared` | per table, below | Platform tables every app may need | see below |

Empty schemas `acp_gold_output`, `acp_silver_s3`, `acp_silver_s4` are leftovers of ACPv1 (CIS); drop
them in a CIS migration when convenient.

## `shared.*` by table

Every `shared` table is **owned by AA-CIS-App** unless the row says otherwise.

| Table(s) | Owner | Notes |
|---|---|---|
| `tenants`, `membership_plans`, `admin_users`, `tenant_*` (brand rules, configs, integrations, usage) | CIS | Tenant and admin identity of the CIS platform. AA-Booking owns *customer* identity (ADR 0001). |
| `job`, `job_worker` | CIS | Durable job runner (ADR 0003). A second repo enqueuing is deferred (AA-751). |
| `llm_role_config`, `llm_model_catalog` | CIS | Model Gateway config; TripPlanner has SELECT (CIS 173). |
| `llm_call_log`, `llm_shadow_log` | CIS | Cost log; TripPlanner has INSERT on `llm_call_log` only, rows tagged `quality_signal.app = "tripplanner"` (CIS 173). |
| `decision_log`, `decision_question`, `decision_cache_hits_daily`, `jev_*` | CIS | Jev decision layer. |
| `dfs_call_log`, `dfs_balance_snapshot`, `cost_explorer_snapshot`, `spend_budget` | CIS | Cost tracking and guard. |
| `notifications` | CIS | Admin bell. |
| `place_photo` (+ photo views) | CIS | Photo sync and matching (AA-708); TripPlanner reads the views (CIS 201). |
| `destinations` | **CIS** (since ADR 0002) | Golden record of places. Created by TripPlanner migrations 002 / 005 (history); since CIS 201 the `tripplanner` role is read-only on it and only CIS writes it. Future column changes are CIS migrations. The place pipeline moves to CIS in AA-712 (ADR 0007): uniqueness changes from global `lower(name)` to `(name_norm, country)` (ids kept), new geo-quality columns, and only the CIS job `place_geocode` writes coordinates. |
| `schema_versions` | CIS (table), every owner (its rows) | Each owner registers its own versions with its prefix (rule 4). |
| `pipeline_jobs`, `pipeline_runs`, `acp_runs`, `pipeline_lessons`, `prompt_eval_runs`, `unmapped_market_requests` | CIS | `pipeline_jobs` is history only (no new writes, ADR 0003). |

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
