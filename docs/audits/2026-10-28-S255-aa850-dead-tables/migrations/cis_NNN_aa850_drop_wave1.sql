-- migrate: destructive
-- DRAFT (AA-850, S255) — not applied; step 2 of DM-3.9. Copy to AA-CIS-App api/migrations/MMM_aa850_drop_wave1.sql
-- (MMM = next free CIS number then) only after: (a) the quarantine NNN has been registered for >= 14 days, (b) a
-- second DRY RUN (db/scripts/aa850_dead_table_dry_run.py) shows the counters of the ten objects did not move since the
-- quarantine and the row counts below, (c) the rows of tenant_brand_rules_deleted_aa404 (and any other table with
-- rows > 0) are archived (DM-3.9 / §7: DB Migrate takes the pre-apply snapshot because of the header above; move its
-- `aa:retain-until` to apply + 180 days and record id + date in docs/architecture/dead-table-registry.md, as for
-- tp-018 — the DM-7.3 S3 archive does not exist yet), and (d) Nghiệp approved the drop (destructive-ops.md step 4).
-- Replace NNN, MMM and every -1.
--
-- Migration MMM: AA-850 (DM-3.9 step 2) — drop the wave-1 objects quarantined in `retired` by CIS NNN.
--
-- Lock note: dropping retired.route_pick / tenant_atom_state / tenant_brand_rule_versions / s1_from_atom_runs /
-- acp_runs removes their FKs and the RI triggers on the parents (shared.tenants, silver_aa_internal.raw_tours,
-- shared.pipeline_runs), which takes ACCESS EXCLUSIVE on those parents for the length of the DROP. Apply while the
-- job tables are idle (DB Migrate waits for that anyway); lock_timeout 5s, retry on a timeout.
-- The schema `retired` stays (empty) for the next waves.
-- Rollback: none in SQL. Restore from the pre-apply snapshot (db-migrate-MMM-<run>-<attempt>).

BEGIN;

SET LOCAL lock_timeout = '5s';

DO $$
DECLARE
    -- rows: exact counts of the second DRY RUN (must equal the quarantine's), -1 = not filled in.
    w jsonb := '[
      {"name": "atom_decompose_jobs",              "kind": "r", "rows": -1},
      {"name": "s1_from_atom_runs",                "kind": "r", "rows": -1},
      {"name": "route_pick",                       "kind": "r", "rows": -1},
      {"name": "marketplace_portfolios",           "kind": "r", "rows": -1},
      {"name": "tenant_atom_state",                "kind": "r", "rows": -1},
      {"name": "acp_runs",                         "kind": "r", "rows": -1},
      {"name": "tenant_brand_rule_versions",       "kind": "r", "rows": -1},
      {"name": "tenant_brand_rules_deleted_aa404", "kind": "r", "rows": -1},
      {"name": "v_batch_stats",                    "kind": "v", "rows": null},
      {"name": "v_pipeline_summary",               "kind": "v", "rows": null}
    ]';
    e   jsonb;
    o   regclass;
    n   bigint;
    q   timestamptz;
BEGIN
    SELECT applied_at INTO q FROM shared.schema_versions WHERE version = 'NNN';
    IF q IS NULL THEN
        RAISE EXCEPTION 'migration MMM: the quarantine NNN is not registered';
    END IF;
    IF now() - q < interval '14 days' THEN
        RAISE EXCEPTION 'migration MMM: quarantine NNN applied % (< 14 days ago, DM-3.9)', q;
    END IF;
    FOR e IN SELECT * FROM jsonb_array_elements(w) LOOP
        o := to_regclass(format('retired.%I', e->>'name'));
        CONTINUE WHEN o IS NULL;                                     -- already dropped (re-run)
        IF e->>'kind' = 'r' THEN
            IF (e->>'rows')::bigint < 0 THEN
                RAISE EXCEPTION 'migration MMM: % has no DRY RUN row count', o;
            END IF;
            EXECUTE format('SELECT count(*) FROM %s', o) INTO n;
            IF n <> (e->>'rows')::bigint THEN
                RAISE EXCEPTION 'migration MMM: % has % rows, the DRY RUN counted %', o, n, e->>'rows';
            END IF;
        END IF;
    END LOOP;
END $$;

-- RESTRICT (the default): anything that grew a dependency since the quarantine stops the drop.
DROP VIEW  IF EXISTS retired.v_batch_stats;
DROP VIEW  IF EXISTS retired.v_pipeline_summary;
DROP TABLE IF EXISTS retired.atom_decompose_jobs;
DROP TABLE IF EXISTS retired.s1_from_atom_runs;
DROP TABLE IF EXISTS retired.route_pick;
DROP TABLE IF EXISTS retired.marketplace_portfolios;
DROP TABLE IF EXISTS retired.tenant_atom_state;
DROP TABLE IF EXISTS retired.acp_runs;
DROP TABLE IF EXISTS retired.tenant_brand_rule_versions;
DROP TABLE IF EXISTS retired.tenant_brand_rules_deleted_aa404;

INSERT INTO shared.schema_versions (version, applied_at, description)
VALUES ('MMM', now(), 'AA-850 wave 1 (DM-3.9 step 2): drop the 8 tables and 2 views quarantined in retired by NNN')
ON CONFLICT (version) DO NOTHING;

COMMIT;
