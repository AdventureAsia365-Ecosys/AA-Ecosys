# AA-850 wave 1 — quarantine plan (DM-3.8 / DM-3.9)

Source of the candidates: [`registry.md`](registry.md). Procedure: skill `aa-cis-schema`
`references/destructive-ops.md` (STEP0 → DRY RUN → snapshot → SAVEPOINT → COMMIT on approval → independent verify)
and data standards DM-3.9 (candidate → quarantine `ALTER … SET SCHEMA retired` → drop after ≥ 14 days, real rows
archived first). Two steps, each its own migration and its own approval:

| step | what | reversible | file (draft) |
|---|---|---|---|
| 1. quarantine | 10 objects → schema `retired`, all app grants revoked | yes (`SET SCHEMA` back + re-grant) | [`migrations/cis_NNN_aa850_quarantine_wave1.sql`](migrations/cis_NNN_aa850_quarantine_wave1.sql) |
| 2. drop | `DROP … RESTRICT` of the 10, ≥ 14 days after step 1 | no (pre-apply RDS snapshot) | [`migrations/cis_NNN_aa850_drop_wave1.sql`](migrations/cis_NNN_aa850_drop_wave1.sql) |

## Wave-1 set

| object | rows (ref) | FKs out (stay valid in `retired`) | why dead | still named by (must change in the same CIS PR) |
|---|---|---|---|---|
| `acp_contract.atom_decompose_jobs` | ~0 | — | AA-302 batch path gone | — |
| `acp_contract.s1_from_atom_runs` | n/a | `raw_tours.tour_id` | never written by the live S1 | docstring in `api/routers/admin_pipeline.py` (text only) |
| `acp_contract.route_pick` | n/a | `shared.tenants` | writer retired with the route hub (AA-859 w4) | erasure inventory, RLS rule-a allowlist, comments in `api/main.py`, `services/acp_contract/route_detection.py` |
| `acp_shared.marketplace_portfolios` | n/a | — | flow removed (119); 265: "dead" | — |
| `acp_shared.tenant_atom_state` | ~0 | `shared.tenants`, `raw_tours` | not in onboarding since AA-472; 265: "dead" | erasure inventory, RLS allowlist, `api/routers/admin.py` docstring, `tests/integration/test_aa817_migration_239.py` (`REVOKE_239_TABLES`), `tests/integration/test_aa859_migration_241.py` (sample table of the column-grant probe) |
| `shared.acp_runs` | n/a | `shared.pipeline_runs` | 0 rows ever written (AA-492) | erasure inventory, RLS allowlist; `tests/unit/test_aa751_no_acp_runs_reader.py` stays valid |
| `shared.tenant_brand_rule_versions` | n/a | `shared.tenants` | no writer / reader | erasure inventory, RLS allowlist |
| `shared.tenant_brand_rules_deleted_aa404` | n/a (104 archived 6 demo rows here; DRY RUN confirms) | — | AA-404 backup copy | erasure inventory, RLS allowlist; **archive the rows before step 2** |
| `shared.v_batch_stats` | view | — | pre-ACP admin view, no reader | — |
| `shared.v_pipeline_summary` | view | — | pre-ACP admin view, no reader | — |

## STEP0 answers (destructive-ops.md)

1. *Has the new path taken over?* Yes for each: jobs → `shared.job` (ADR 0003a), S1 run evidence →
   `shared.llm_call_log` / `prompt_eval_runs`, route picks → segments / Slate (AA-859 wave 4), tenant selection →
   `GET /v1/marketplace` (AA-444), brand history → `shared.tenant_brand_rules` versions, admin views → `/admin/*`
   pages over `raw_tours`.
2. *FKs (`pg_constraint`)*: no inbound FK from outside the set (reference *Foreign keys*); the migration guard
   re-checks live. Outbound FKs follow the table by OID (verified on a scratch PostgreSQL 16: a parent delete is still
   refused by `retired.route_pick_tenant_id_fkey`).
3. *Rows / counters / callers / bare `*_id`*: counters 0/0/0 in the reference; exact rows + last write + `pg_stat_statements`
   callers come from the DRY RUN; code grep in [`registry.md`](registry.md) (all 5 repos + Infra).
4. *`git ls-files`*: the scan reads tracked blobs of `origin/main` only (no `__pycache__`, no untracked files).
5. *Latest migration comments / dependent views*: 119, 121, 122, 265, 281 read; no `SELECT *` view over the tables
   (the DRY RUN lists `pg_depend` view dependents; the guard refuses one outside the set).
6. *`tests/integration/`*: two files name `tenant_atom_state` (above); the RLS catalogue guard test reads the
   allowlist; nothing else.
7. *Same folder ≠ same fate*: decided per object; `acp_shared.quarter_plan_version` / `year_plan` (same 098/112 era,
   0 writes) stay — live code behind `TRIP_REALLOCATION_FLAG`.

## Code changes that ship with step 1 (one CIS PR + one Infra PR)

The CI database replays every migration, so the guards and tests must agree with the post-quarantine catalog in the
same PR as the migration file (ADR 0017 / D8: the migration commit first).

**AA-CIS-App** (branch `chore/aa-850-dead-table-quarantine-wave1`):
- `api/migrations/NNN_aa850_quarantine_wave1.sql` — the draft, NNN and the DRY RUN row counts filled in (own commit).
- `tests/integration/rls_catalogue_rules.py` (canonical; Infra keeps a byte copy): `SCHEMA_OWNERS["retired"] = "cis"`
  (rule e: the outbound FKs `retired.* → shared.*` stay same-owner); rule-a allowlist keys `shared.acp_runs`,
  `shared.tenant_brand_rule_versions`, `shared.tenant_brand_rules_deleted_aa404`, `acp_contract.route_pick`,
  `acp_shared.tenant_atom_state` → `retired.<name>` with reason "quarantined, AA-850 (no grant to any role)".
- `services/erasure/inventory.py`: remove the five entries (route_pick, tenant_atom_state, tenant_brand_rule_versions,
  tenant_brand_rules_deleted_aa404, acp_runs). The erasure job loads only the 11 runtime schemas and cannot read
  `retired` (cis_app has no USAGE): the DRY RUN verdict therefore refuses any quarantine while a non-platform tenant
  still has rows in a wave-1 table.
- `tests/integration/test_aa817_migration_239.py`: drop `acp_shared.tenant_atom_state` from `REVOKE_239_TABLES` (or
  resolve it through `to_regclass` in either schema); `tests/integration/test_aa859_migration_241.py`: use
  `acp_shared.year_plan` as the column-grant probe table instead of `tenant_atom_state`.
- Comments in `api/main.py`, `services/acp_contract/route_detection.py`, `api/routers/admin.py`,
  `services/export/handler.py`: "quarantined in `retired` (CIS NNN, AA-850)".
- `CONTEXT.md`: one line on the `retired` schema (DM-3.9, no grants, owner migrations only).
- `docs/implementation-notes/AA-850.md` (Decisions / Changed / Tradeoffs / Should know).

**AA-CIS-Infra** (branch `chore/aa-850-retired-schema`):
- `db/owners.yaml` `owners.cis.schemas += retired` — **not** in `runtime_privileges.cis_app.schemas` (the probe must
  not expect cis_app grants there); mirrors `db/run_migration.py` `OWNER_DIRS`, `db/isolation_probe.py` `OWNERS`
  (`db/tests/test_owners_registry.py` checks them). Without it `db/check_migration_ownership.py` refuses the file
  ("schema retired belongs to no owner in db/owners.yaml").
- `db/rls_catalogue_rules.py`: byte copy of the CIS file above.
- `db/migrations/cis/NNN_aa850_quarantine_wave1.sql`: byte copy, after the CIS PR is on `main` (Migration Copy Guard).
- `db/scripts/aa850_dead_table_dry_run.py`: [`scripts/aa850_dead_table_dry_run.py`](scripts/aa850_dead_table_dry_run.py)
  (READ_ONLY, run-script contract of `db/scripts/README.md`) + a README line.

## Orchestrator runbook

1. **DRY RUN T0** — Infra PR with only `db/scripts/aa850_dead_table_dry_run.py` → merge → DB Migrate
   `mode=run-script script=db/scripts/aa850_dead_table_dry_run.py`. Record from the log: `SCRIPT stats_reset`,
   every `SCRIPT wave1 …` line (rows, tenant rows, last write), `wave1_dep` / `wave1_statements`, `SCRIPT verdict`.
   The `SCRIPT census` lines (all 275 tables: exact rows, last write, counters) replace the `~rows` of
   [`registry.md`](registry.md) for the registry update. Quick CIS-only alternative (no PR): S3-mediated ECS exec of
   the same file (`python3 /tmp/s.py`, cis_app; non-CIS tables print `access=none`).
2. **Approval** — show Nghiệp the DRY RUN numbers + this plan (destructive-ops step 1). Step 1 is reversible; step 2
   needs its own approval.
3. **Fill the draft** — the `rows` of each table in the migration's `w` list = the DRY RUN counts; NNN = next CIS
   number. Write the numbers into ARCH-09 before the apply.
4. **PRs** — Infra owners/rules PR, then the CIS PR (migration commit first), CI green, merge; Infra migration copy PR.
5. **DB Migrate** `check` then `apply` of `cis/NNN_aa850_quarantine_wave1.sql` while the job tables are idle. The
   transaction is the SAVEPOINT: the guard refuses on any count that differs from the DRY RUN.
6. **Independent verify** — second dispatch of the DRY RUN (new connection): every `wave1 … where=retired`,
   `retired_schema exists=t owner=cis_owner`; as cis_app (ECS exec) the census shows `retired.* access=none`; CIS
   `/health/ready` 200, an admin page smoke, the nightly isolation probe and DB Schema Dump green; merge the
   `bot/db-schema-reference` PR (schema `retired` appears). Update ARCH-09 rows to `quarantined` (apply run, verify run).
7. **≥ 14 days later (not before the date in the object comments)** — DRY RUN T1: counters of the ten unchanged since
   step 6, no `wave1_statements` by an app role. Archive the rows of `retired.tenant_brand_rules_deleted_aa404` (and
   any other table with rows) — the DB Migrate pre-apply snapshot of the drop with `aa:retain-until` = apply + 180 days,
   as for tp-018, until the DM-7.3 S3 archive exists. Nghiệp approves; fill and apply the drop draft; verify
   (`exists=f`); ARCH-09 rows → `dropped`.

## Tested

Both drafts ran on a scratch PostgreSQL 16 (local, roles `cis_owner` / `cis_app` / `aa_app_user` / …, the ten objects
with their FKs, a sequence, an RLS policy, comments and grants as on Dev):
- quarantine refuses unfilled row counts (-1), a count that differs from the DRY RUN, and a view outside the set over
  a wave-1 table; applies; a re-run is a no-op; objects, owned sequence and policy end in `retired` with ACL
  `cis_owner` only, comments prefixed `[AA-850 quarantine <date> from <schema>; drop not before <date + 14>]`;
  cis_app has no USAGE on `retired`; outbound FKs still enforced;
- drop refuses < 14 days after the quarantine registration, then drops all ten (RESTRICT);
- the DRY RUN script (run-script entry `main(conn)`) before and after: counts, tenant rows, FK / sequence / policy
  dependents, grants, `quarantine_ready`; under cis_app after the quarantine every `retired.*` reads `access=none`.
Not tested: DB Migrate's own lint and runner (needs the Infra owners change), PostgreSQL 15 specifics (Dev and the
replay run 15; nothing used is 16-only), `pg_stat_statements` output (extension not preloaded locally).

## Wave 2 / 3 (next)

- **Wave 2** — `shared.tenant_export_config` (delete `TenantConfigService.get_export_config` / `ExportConfig` and its
  two tests), `gold_aa_internal.content_exports` + `webhook_deliveries` (remove from Infra `owners.yaml`
  `rls_parity_tables`, `isolation_probe.RLS_PARITY_TABLES`, rule-b allowlist, `x1_245` script, 244/245 parity
  expectations in CIS integration tests and `_rls_fixture_helpers.py`), `public.checkpoint_migrations` (Infra `roles/`
  file + `db/schema_drift_decisions.json`). Same two steps; quarantine the gold pair together.
- **Wave 3** — `shared.pipeline_jobs` (retire the `/admin/jobs/{id}` history read, archive 523 rows), the two
  `shared.v_*_photos` views after CIS moves to `catalog.v_*_photo` (DM-2.4).
- **Other owners** — none today. When Booking / TripPlanner / CRM retire a table, the quarantine schema is the owner's
  own (`booking_retired`, …, owned by `bk_owner`, …): `retired` is a CIS schema and DM-2.3 forbids mixing owners.
