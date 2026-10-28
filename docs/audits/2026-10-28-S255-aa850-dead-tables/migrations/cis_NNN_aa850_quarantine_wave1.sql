-- DRAFT (AA-850, S255) — not applied. Lives in the audit folder until the wave-1 CIS PR copies it to AA-CIS-App
-- api/migrations/NNN_aa850_quarantine_wave1.sql (NNN = the next free CIS number at merge; 292 was the latest on
-- 28/10/2026) and AA-CIS-Infra db/migrations/cis/ (byte copy). Replace every NNN and every -1 row count below.
--
-- Migration NNN: AA-850 (data standards DM-3.8 / DM-3.9) — Dead Table Registry wave 1: quarantine 8 dead CIS tables
-- and 2 dead CIS views in the new schema `retired`. Reversible: nothing is dropped, no row changes.
--
-- Why. DM-3.9: retirement goes candidate → quarantine (ALTER … SET SCHEMA retired) → drop after >= 14 days. The
-- AA-850 audit (AA-Ecosys docs/audits/2026-10-28-S255-aa850-dead-tables/registry.md) grepped every repo that reads the
-- shared RDS (CIS, Booking, TripPlanner, Partner, Infra; origin/main 28/10/2026) for every table name and found no
-- runtime reader or writer for these ten objects:
--   acp_contract.atom_decompose_jobs      AA-302 Bedrock Batch tracker (081/082); the batch path is gone
--   acp_contract.s1_from_atom_runs        AA-289 S1-from-atom run log (088); never written by the live S1
--   acp_contract.route_pick               writer create_route_pick() retired with the route hub (AA-859 wave 4)
--   acp_shared.marketplace_portfolios     pre-tenant portfolio drafts (097); flow removed (119, ADR-2026-038)
--   acp_shared.tenant_atom_state          N1 seeding state (098); not part of onboarding since AA-472
--   shared.acp_runs                       legacy run table (009); 0 rows ever written (AA-492)
--   shared.tenant_brand_rule_versions     AA-82 brand-rule history (019); no writer, no reader
--   shared.tenant_brand_rules_deleted_aa404  AA-404 backup of 6 mis-attached demo rows (104); no reader
--   shared.v_batch_stats                  pre-ACP admin view (003); no reader
--   shared.v_pipeline_summary             pre-ACP admin view (003, retyped by 281); no reader
-- The DRY RUN (AA-CIS-Infra db/scripts/aa850_dead_table_dry_run.py, DB Migrate run-script, twice >= 14 days apart)
-- gave the row counts written into `w` below and found no dependent view, inbound foreign key, function body or app
-- statement (pg_stat_statements) on any of them.
--
-- What (one transaction, as cis_owner, the live owner of `shared`):
--   1. Guard: each object is in its source schema (or already in `retired`: a re-run is a no-op), its exact row count
--      equals the DRY RUN value (-1 = not filled in: refused), and nothing outside the ten depends on it (view, inbound
--      FK). Outbound FKs (to shared.tenants, silver_aa_internal.raw_tours, shared.pipeline_runs) stay: a FK follows
--      the table by OID, so the quarantined rows keep their integrity and the parents' deletes are still checked.
--   2. CREATE SCHEMA retired (owner cis_owner, CREATE ON DATABASE from rl-002), no USAGE for anyone but the owner.
--   3. ALTER TABLE / VIEW … SET SCHEMA retired. Indexes, constraints, owned sequences, policies and triggers move with
--      the table. The object's comment gets the prefix `[AA-850 quarantine <date> from <schema>; drop not before
--      <date + 14>]` so the restore path is in the catalog.
--   4. REVOKE ALL on every table and sequence in `retired` from PUBLIC and every app role: any forgotten reader now
--      fails loudly (42501 / 42P01) instead of reading stale rows.
--   5. Post-check: all ten in `retired`, no app role holds USAGE on the schema or any privilege on the objects.
--
-- Order with the code (one CIS PR, ADR 0017 / D8): this file + tests/integration/rls_catalogue_rules.py
-- (SCHEMA_OWNERS gains "retired": "cis"; rule-a allowlist keys renamed shared.acp_runs -> retired.acp_runs, …) +
-- services/erasure/inventory.py (the five tenant-keyed entries removed) + the two integration tests that name
-- tenant_atom_state (test_aa817_migration_239.py, test_aa859_migration_241.py). AA-CIS-Infra PR first or together:
-- db/owners.yaml cis.schemas += retired (NOT runtime_privileges), its mirrors run_migration.OWNER_DIRS and
-- isolation_probe.OWNERS, db/rls_catalogue_rules.py byte copy — without it the migration ownership lint refuses
-- `retired` ("no owner in db/owners.yaml"). Apply through DB Migrate (check, then apply) while the job tables are idle.
--
-- Restore (a NEW forward migration, per object):
--   ALTER TABLE retired.<name> SET SCHEMA <from>;  then re-grant what the DRY RUN listed (wave1_grant lines; on Dev
--   cis_app DELETE, INSERT, SELECT, UPDATE on each table) and strip the comment prefix.
-- Drop: cis_NNN_aa850_drop_wave1.sql (step 2 of DM-3.9), not before the date in the comments, after a second DRY RUN.

BEGIN;

SET LOCAL lock_timeout = '5s';

-- 1. Guard ---------------------------------------------------------------------------------------------------------
DO $$
DECLARE
    -- rows: exact count from the approved DRY RUN (T1). -1 = not filled in.
    w jsonb := '[
      {"from": "acp_contract", "name": "atom_decompose_jobs",              "kind": "r", "rows": -1},
      {"from": "acp_contract", "name": "s1_from_atom_runs",                "kind": "r", "rows": -1},
      {"from": "acp_contract", "name": "route_pick",                       "kind": "r", "rows": -1},
      {"from": "acp_shared",   "name": "marketplace_portfolios",           "kind": "r", "rows": -1},
      {"from": "acp_shared",   "name": "tenant_atom_state",                "kind": "r", "rows": -1},
      {"from": "shared",       "name": "acp_runs",                         "kind": "r", "rows": -1},
      {"from": "shared",       "name": "tenant_brand_rule_versions",       "kind": "r", "rows": -1},
      {"from": "shared",       "name": "tenant_brand_rules_deleted_aa404", "kind": "r", "rows": -1},
      {"from": "shared",       "name": "v_batch_stats",                    "kind": "v", "rows": null},
      {"from": "shared",       "name": "v_pipeline_summary",               "kind": "v", "rows": null}
    ]';
    e       jsonb;
    src     regclass;
    wave    oid[] := '{}';
    n       bigint;
    dep     text;
BEGIN
    -- the OIDs of the set, so dependencies inside the set are allowed
    FOR e IN SELECT * FROM jsonb_array_elements(w) LOOP
        src := coalesce(to_regclass(format('%I.%I', e->>'from', e->>'name')),
                        to_regclass(format('retired.%I', e->>'name')));
        IF src IS NULL THEN
            RAISE EXCEPTION 'migration NNN: %.% is missing (neither in its schema nor in retired)', e->>'from', e->>'name';
        END IF;
        wave := wave || src::oid;
    END LOOP;

    FOR e IN SELECT * FROM jsonb_array_elements(w) LOOP
        src := to_regclass(format('%I.%I', e->>'from', e->>'name'));
        CONTINUE WHEN src IS NULL;                                   -- already in retired (re-run)
        IF (SELECT relkind FROM pg_class WHERE oid = src) <> (e->>'kind') THEN
            RAISE EXCEPTION 'migration NNN: % is not of kind %', src, e->>'kind';
        END IF;
        IF e->>'kind' = 'r' THEN
            IF (e->>'rows')::bigint < 0 THEN
                RAISE EXCEPTION 'migration NNN: % has no DRY RUN row count (fill in "rows" from the approved DRY RUN)', src;
            END IF;
            EXECUTE format('SELECT count(*) FROM %s', src) INTO n;
            IF n <> (e->>'rows')::bigint THEN
                RAISE EXCEPTION 'migration NNN: % has % rows, the approved DRY RUN counted % (someone wrote to it: '
                                'stop and re-check)', src, n, e->>'rows';
            END IF;
        END IF;
        SELECT string_agg(DISTINCT v.oid::regclass::text, ', ') INTO dep
          FROM pg_depend d
          JOIN pg_rewrite r ON r.oid = d.objid AND d.classid = 'pg_rewrite'::regclass
          JOIN pg_class v ON v.oid = r.ev_class
         WHERE d.refobjid = src AND v.oid <> src AND NOT v.oid = ANY(wave);
        IF dep IS NOT NULL THEN
            RAISE EXCEPTION 'migration NNN: view(s) % depend on % (not in wave 1)', dep, src;
        END IF;
        SELECT string_agg(c.conrelid::regclass::text || '.' || c.conname, ', ') INTO dep
          FROM pg_constraint c
         WHERE c.contype = 'f' AND c.confrelid = src AND c.conrelid <> src AND NOT c.conrelid = ANY(wave);
        IF dep IS NOT NULL THEN
            RAISE EXCEPTION 'migration NNN: foreign key(s) % reference % from outside wave 1', dep, src;
        END IF;
    END LOOP;
END $$;

-- 2. The quarantine schema -----------------------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS retired;
COMMENT ON SCHEMA retired IS
    'Quarantine of retired objects (data standards DM-3.9): ALTER … SET SCHEMA retired, no grant to any app role, '
    'drop after >= 14 days by a migration of the owner. One row per object in AA-Ecosys '
    'docs/architecture/dead-table-registry.md. Owner cis_owner (AA-850).';
REVOKE ALL ON SCHEMA retired FROM PUBLIC;

-- 3. Move ----------------------------------------------------------------------------------------------------------
ALTER TABLE IF EXISTS acp_contract.atom_decompose_jobs              SET SCHEMA retired;
ALTER TABLE IF EXISTS acp_contract.s1_from_atom_runs                SET SCHEMA retired;
ALTER TABLE IF EXISTS acp_contract.route_pick                       SET SCHEMA retired;
ALTER TABLE IF EXISTS acp_shared.marketplace_portfolios             SET SCHEMA retired;
ALTER TABLE IF EXISTS acp_shared.tenant_atom_state                  SET SCHEMA retired;
ALTER TABLE IF EXISTS shared.acp_runs                               SET SCHEMA retired;
ALTER TABLE IF EXISTS shared.tenant_brand_rule_versions             SET SCHEMA retired;
ALTER TABLE IF EXISTS shared.tenant_brand_rules_deleted_aa404       SET SCHEMA retired;
ALTER VIEW  IF EXISTS shared.v_batch_stats                          SET SCHEMA retired;
ALTER VIEW  IF EXISTS shared.v_pipeline_summary                     SET SCHEMA retired;

-- Comment prefix with the way back (dynamic SQL: reported as a warning by the ownership lint, the object is in
-- retired, a CIS schema once owners.yaml lists it).
DO $$
DECLARE
    m  jsonb := '{"atom_decompose_jobs": "acp_contract", "s1_from_atom_runs": "acp_contract",
                  "route_pick": "acp_contract", "marketplace_portfolios": "acp_shared",
                  "tenant_atom_state": "acp_shared", "acp_runs": "shared", "tenant_brand_rule_versions": "shared",
                  "tenant_brand_rules_deleted_aa404": "shared", "v_batch_stats": "shared",
                  "v_pipeline_summary": "shared"}';
    k  text;
    o  regclass;
    old text;
    tag text;
BEGIN
    FOR k IN SELECT jsonb_object_keys(m) LOOP
        o := to_regclass(format('retired.%I', k));
        old := obj_description(o, 'pg_class');
        CONTINUE WHEN old LIKE '[AA-850 quarantine%';                -- re-run
        tag := format('[AA-850 quarantine %s from %s; drop not before %s] ', current_date, m->>k, current_date + 14);
        EXECUTE format('COMMENT ON %s %s IS %L',
                       CASE (SELECT relkind FROM pg_class WHERE oid = o) WHEN 'v' THEN 'VIEW' ELSE 'TABLE' END,
                       o, tag || coalesce(old, ''));
    END LOOP;
END $$;

-- 4. No app role keeps a way in ------------------------------------------------------------------------------------
REVOKE ALL ON ALL TABLES    IN SCHEMA retired FROM PUBLIC, cis_app, aa_app_user, catalog_owner, booking, tripplanner;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA retired FROM PUBLIC, cis_app, aa_app_user, catalog_owner, booking, tripplanner;

-- 5. Post-check ----------------------------------------------------------------------------------------------------
DO $$
DECLARE
    names text[] := ARRAY['atom_decompose_jobs', 's1_from_atom_runs', 'route_pick', 'marketplace_portfolios',
                          'tenant_atom_state', 'acp_runs', 'tenant_brand_rule_versions',
                          'tenant_brand_rules_deleted_aa404', 'v_batch_stats', 'v_pipeline_summary'];
    k  text;
    r  text;
    o  regclass;
BEGIN
    FOREACH k IN ARRAY names LOOP
        o := to_regclass(format('retired.%I', k));
        IF o IS NULL THEN
            RAISE EXCEPTION 'migration NNN: post-check: retired.% missing', k;
        END IF;
        FOREACH r IN ARRAY ARRAY['cis_app', 'aa_app_user', 'catalog_owner', 'booking', 'tripplanner'] LOOP
            CONTINUE WHEN NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r);
            IF has_table_privilege(r, o, 'SELECT, INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER') THEN
                RAISE EXCEPTION 'migration NNN: post-check: % still has a privilege on %', r, o;
            END IF;
        END LOOP;
    END LOOP;
    FOREACH r IN ARRAY ARRAY['cis_app', 'aa_app_user', 'catalog_owner', 'booking', 'tripplanner', 'crm_app'] LOOP
        CONTINUE WHEN NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r);
        IF has_schema_privilege(r, 'retired', 'USAGE') THEN
            RAISE EXCEPTION 'migration NNN: post-check: % has USAGE on schema retired', r;
        END IF;
    END LOOP;
END $$;

INSERT INTO shared.schema_versions (version, applied_at, description)
VALUES ('NNN', now(),
        'AA-850 wave 1 (DM-3.9): quarantine 8 dead CIS tables and 2 dead views in schema retired (no grants); '
        'drop after >= 14 days')
ON CONFLICT (version) DO NOTHING;

COMMIT;
