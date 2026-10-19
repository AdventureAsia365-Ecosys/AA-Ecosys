-- Migration rl-0NN: AA-860 (X1 plan S21 rollback) — UNDO of CIS 245: the 12 CIS schemas and every object cis_owner owns
-- in them back to the RDS master aa_cis_admin, the 8 <table>_cis_owner_all policies dropped, the default privileges of
-- cis_app back FOR ROLE aa_cis_admin (CIS 244's rows).
--
-- PREPARED, NOT MERGED. Infra-native roles/ file (key rl-NNN): rename to db/migrations/roles/<next free NNN>_x1_cis_owner_undo.sql
-- and replace 0NN in the version key below with that number only if 245 has to be rolled back. It must be a roles/ file:
-- once schema shared is owned by cis_owner, DB Migrate runs cis/ files as cis_owner (X1 XD8), and cis_owner cannot give
-- objects to aa_cis_admin (not a member of it). roles/ files always run as the master, which is a member of cis_owner
-- (rl-002). After it commits the runner runs cis/ files as aa_cis_admin again, automatically, and the isolation probe's
-- CIS ownership / runtime-grant cells go back to pending (they key on 245 AND the live owner of shared). Never key 246
-- (the S22 probe key). 245 stays registered (history); a later re-transfer is a new CIS file.
-- Before S22 only: after S22 the DB Migrate login is db_migrator, and roles/ files need the runner's master connection
-- (plan S22); the content is the same.
--
-- Catalog-driven like 245 step 4 (the same object kinds), so objects that cis/ files created as cis_owner after 245
-- (246 and later) go back too. catalog.* views stay catalog_owner's: this file moves only what cis_owner owns.
-- The cis_app grants of 244 are untouched (ALTER … OWNER keeps every ACL; the last guard compares them with a snapshot).
-- Locks: as in 245, one LOCK TABLE statement takes ACCESS EXCLUSIVE on every table of the 11 runtime schemas first
-- (shared.job first), all or none within lock_timeout 5s; apply only with shared.job / booking.job idle.
-- Dry-run (S244, local PostgreSQL 16, the AA-CIS-App test_aa860_migration_245 fixture: RDS-like master, 244, 245):
-- the undo commits, every CIS object is the master's again, no policy or default privilege names cis_owner, cis_app's
-- privileges are unchanged, and 245 applies again on top of it (round trip).

BEGIN;

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '15min';

DO $$
BEGIN
    IF current_user <> 'aa_cis_admin' OR session_user <> current_user THEN
        RAISE EXCEPTION 'rl undo: runs only as the RDS master aa_cis_admin (current_user %, session_user %)',
            current_user, session_user;
    END IF;
    IF NOT pg_catalog.pg_has_role('aa_cis_admin', 'cis_owner', 'MEMBER') THEN
        RAISE EXCEPTION 'rl undo: aa_cis_admin is not a member of cis_owner (rl-002)';
    END IF;
END $$;

-- Every table lock this file needs, in one statement: all or none within lock_timeout, held until COMMIT.
DO $$
DECLARE
    stmt text;
BEGIN
    SELECT 'LOCK TABLE ' || string_agg(pg_catalog.format('%I.%I', n.nspname, c.relname), ', '
                                       ORDER BY (n.nspname = 'shared' AND c.relname = 'job') DESC,
                                                n.nspname, c.relname)
           || ' IN ACCESS EXCLUSIVE MODE'
      INTO stmt
      FROM pg_catalog.pg_class c
      JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = ANY (ARRAY['acp_contract', 'acp_deliver', 'acp_gold_output', 'acp_shared', 'acp_silver_s2',
                                  'acp_silver_s3', 'acp_silver_s4', 'geo', 'gold_aa_internal', 'shared',
                                  'silver_aa_internal'])
       AND c.relkind IN ('r', 'p');
    EXECUTE stmt;
END $$;

-- Privileges of every role other than the owner, owner-independent (CIS 245 step 2's query). Compared at the end.
SELECT pg_catalog.set_config('rl_undo_245.privileges', coalesce(string_agg(p, E'\n' ORDER BY p), ''), true)
FROM (
    SELECT pg_catalog.format('schema %I: %s %s %s', n.nspname, a.grantee::regrole, a.privilege_type, a.is_grantable) AS p
      FROM pg_catalog.pg_namespace n,
           pg_catalog.aclexplode(coalesce(n.nspacl, pg_catalog.acldefault('n', n.nspowner))) a
     WHERE n.nspname = ANY (ARRAY['acp_contract', 'acp_deliver', 'acp_gold_output', 'acp_shared', 'acp_silver_s2',
                                  'acp_silver_s3', 'acp_silver_s4', 'catalog', 'geo', 'gold_aa_internal', 'shared',
                                  'silver_aa_internal'])
       AND a.grantee <> n.nspowner
    UNION ALL
    SELECT pg_catalog.format('rel %I.%I: %s %s %s', n.nspname, c.relname, a.grantee::regrole, a.privilege_type, a.is_grantable)
      FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace,
           pg_catalog.aclexplode(coalesce(c.relacl, pg_catalog.acldefault(
               CASE WHEN c.relkind = 'S' THEN 's'::"char" ELSE 'r'::"char" END, c.relowner))) a
     WHERE n.nspname = ANY (ARRAY['acp_contract', 'acp_deliver', 'acp_gold_output', 'acp_shared', 'acp_silver_s2',
                                  'acp_silver_s3', 'acp_silver_s4', 'catalog', 'geo', 'gold_aa_internal', 'shared',
                                  'silver_aa_internal'])
       AND c.relkind IN ('r', 'p', 'v', 'm', 'f', 'S') AND a.grantee <> c.relowner
    UNION ALL
    SELECT pg_catalog.format('col %I.%I.%I: %s %s %s', n.nspname, c.relname, t.attname, a.grantee::regrole,
                             a.privilege_type, a.is_grantable)
      FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
      JOIN pg_catalog.pg_attribute t ON t.attrelid = c.oid,
           pg_catalog.aclexplode(t.attacl) a
     WHERE n.nspname = ANY (ARRAY['acp_contract', 'acp_deliver', 'acp_gold_output', 'acp_shared', 'acp_silver_s2',
                                  'acp_silver_s3', 'acp_silver_s4', 'catalog', 'geo', 'gold_aa_internal', 'shared',
                                  'silver_aa_internal'])
       AND t.attacl IS NOT NULL AND a.grantee <> c.relowner
    UNION ALL
    SELECT pg_catalog.format('routine %I.%I(%s): %s %s %s', n.nspname, f.proname,
                             pg_catalog.pg_get_function_identity_arguments(f.oid), a.grantee::regrole,
                             a.privilege_type, a.is_grantable)
      FROM pg_catalog.pg_proc f JOIN pg_catalog.pg_namespace n ON n.oid = f.pronamespace,
           pg_catalog.aclexplode(coalesce(f.proacl, pg_catalog.acldefault('f', f.proowner))) a
     WHERE n.nspname = ANY (ARRAY['acp_contract', 'acp_deliver', 'acp_gold_output', 'acp_shared', 'acp_silver_s2',
                                  'acp_silver_s3', 'acp_silver_s4', 'catalog', 'geo', 'gold_aa_internal', 'shared',
                                  'silver_aa_internal'])
       AND a.grantee <> f.proowner
    UNION ALL
    SELECT pg_catalog.format('type %I.%I: %s %s %s', n.nspname, y.typname, a.grantee::regrole, a.privilege_type,
                             a.is_grantable)
      FROM pg_catalog.pg_type y JOIN pg_catalog.pg_namespace n ON n.oid = y.typnamespace,
           pg_catalog.aclexplode(coalesce(y.typacl, pg_catalog.acldefault('T', y.typowner))) a
     WHERE n.nspname = ANY (ARRAY['acp_contract', 'acp_deliver', 'acp_gold_output', 'acp_shared', 'acp_silver_s2',
                                  'acp_silver_s3', 'acp_silver_s4', 'catalog', 'geo', 'gold_aa_internal', 'shared',
                                  'silver_aa_internal'])
       AND a.grantee <> y.typowner
) s;

ALTER SCHEMA acp_contract OWNER TO aa_cis_admin;
ALTER SCHEMA acp_deliver OWNER TO aa_cis_admin;
ALTER SCHEMA acp_gold_output OWNER TO aa_cis_admin;
ALTER SCHEMA acp_shared OWNER TO aa_cis_admin;
ALTER SCHEMA acp_silver_s2 OWNER TO aa_cis_admin;
ALTER SCHEMA acp_silver_s3 OWNER TO aa_cis_admin;
ALTER SCHEMA acp_silver_s4 OWNER TO aa_cis_admin;
ALTER SCHEMA catalog OWNER TO aa_cis_admin;
ALTER SCHEMA geo OWNER TO aa_cis_admin;
ALTER SCHEMA gold_aa_internal OWNER TO aa_cis_admin;
ALTER SCHEMA shared OWNER TO aa_cis_admin;
ALTER SCHEMA silver_aa_internal OWNER TO aa_cis_admin;

-- Everything cis_owner owns in the 12 schemas (catalog included: a cis/ file after 245 may have created something
-- there as cis_owner; the catalog_owner views are not cis_owner's and stay).
DO $$
DECLARE
    o      record;
    moved  int := 0;
BEGIN
    FOR o IN
        WITH s AS (
            SELECT ns.oid, ns.nspname FROM pg_catalog.pg_namespace ns
             WHERE ns.nspname = ANY (ARRAY['acp_contract', 'acp_deliver', 'acp_gold_output', 'acp_shared',
                                           'acp_silver_s2', 'acp_silver_s3', 'acp_silver_s4', 'catalog', 'geo',
                                           'gold_aa_internal', 'shared', 'silver_aa_internal'])),
        ext AS (SELECT d.classid, d.objid FROM pg_catalog.pg_depend d WHERE d.deptype = 'e'),
        own AS (SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = 'cis_owner'),
        objects AS (
            SELECT 1 AS ord,
                   CASE c.relkind WHEN 'v' THEN 'VIEW' WHEN 'm' THEN 'MATERIALIZED VIEW' WHEN 'f' THEN 'FOREIGN TABLE'
                                  WHEN 'S' THEN 'SEQUENCE' WHEN 'c' THEN 'TYPE' ELSE 'TABLE' END AS kind,
                   pg_catalog.format('%I.%I', s.nspname, c.relname) AS name
              FROM pg_catalog.pg_class c JOIN s ON s.oid = c.relnamespace
             WHERE c.relkind IN ('r', 'p', 'v', 'm', 'f', 'S', 'c')
               AND c.relowner = (SELECT oid FROM own)
               AND NOT EXISTS (SELECT 1 FROM ext WHERE ext.classid = 'pg_catalog.pg_class'::regclass AND ext.objid = c.oid)
               AND NOT (c.relkind = 'S' AND EXISTS (
                        SELECT 1 FROM pg_catalog.pg_depend d
                         WHERE d.classid = 'pg_catalog.pg_class'::regclass AND d.objid = c.oid
                           AND d.refclassid = 'pg_catalog.pg_class'::regclass AND d.deptype IN ('a', 'i')))
            UNION ALL
            SELECT 2, CASE y.typtype WHEN 'd' THEN 'DOMAIN' ELSE 'TYPE' END, pg_catalog.format('%I.%I', s.nspname, y.typname)
              FROM pg_catalog.pg_type y JOIN s ON s.oid = y.typnamespace
             WHERE y.typtype IN ('e', 'd', 'r') AND y.typowner = (SELECT oid FROM own)
               AND NOT EXISTS (SELECT 1 FROM ext WHERE ext.classid = 'pg_catalog.pg_type'::regclass AND ext.objid = y.oid)
            UNION ALL
            SELECT 3, CASE f.prokind WHEN 'p' THEN 'PROCEDURE' WHEN 'a' THEN 'AGGREGATE' ELSE 'FUNCTION' END,
                   pg_catalog.format('%I.%I(%s)', s.nspname, f.proname, pg_catalog.pg_get_function_identity_arguments(f.oid))
              FROM pg_catalog.pg_proc f JOIN s ON s.oid = f.pronamespace
             WHERE f.proowner = (SELECT oid FROM own)
               AND NOT EXISTS (SELECT 1 FROM ext WHERE ext.classid = 'pg_catalog.pg_proc'::regclass AND ext.objid = f.oid)
            UNION ALL
            SELECT 4, 'STATISTICS', pg_catalog.format('%I.%I', s.nspname, x.stxname)
              FROM pg_catalog.pg_statistic_ext x JOIN s ON s.oid = x.stxnamespace
             WHERE x.stxowner = (SELECT oid FROM own)
            UNION ALL
            SELECT 5, 'COLLATION', pg_catalog.format('%I.%I', s.nspname, x.collname)
              FROM pg_catalog.pg_collation x JOIN s ON s.oid = x.collnamespace
             WHERE x.collowner = (SELECT oid FROM own)
            UNION ALL
            SELECT 6, 'CONVERSION', pg_catalog.format('%I.%I', s.nspname, x.conname)
              FROM pg_catalog.pg_conversion x JOIN s ON s.oid = x.connamespace
             WHERE x.conowner = (SELECT oid FROM own)
            UNION ALL
            SELECT 7, 'TEXT SEARCH DICTIONARY', pg_catalog.format('%I.%I', s.nspname, x.dictname)
              FROM pg_catalog.pg_ts_dict x JOIN s ON s.oid = x.dictnamespace
             WHERE x.dictowner = (SELECT oid FROM own)
            UNION ALL
            SELECT 8, 'TEXT SEARCH CONFIGURATION', pg_catalog.format('%I.%I', s.nspname, x.cfgname)
              FROM pg_catalog.pg_ts_config x JOIN s ON s.oid = x.cfgnamespace
             WHERE x.cfgowner = (SELECT oid FROM own))
        SELECT kind, name FROM objects ORDER BY ord, name
    LOOP
        EXECUTE pg_catalog.format('ALTER %s %s OWNER TO aa_cis_admin', o.kind, o.name);
        moved := moved + 1;
        RAISE NOTICE 'rl undo: % % -> aa_cis_admin', lower(o.kind), o.name;
    END LOOP;
    RAISE NOTICE 'rl undo: % object(s) back to aa_cis_admin (plus the 12 schemas)', moved;
END $$;

DROP POLICY IF EXISTS content_exports_cis_owner_all ON gold_aa_internal.content_exports;
DROP POLICY IF EXISTS published_tours_cis_owner_all ON gold_aa_internal.published_tours;
DROP POLICY IF EXISTS webhook_deliveries_cis_owner_all ON gold_aa_internal.webhook_deliveries;
DROP POLICY IF EXISTS pipeline_runs_cis_owner_all ON shared.pipeline_runs;
DROP POLICY IF EXISTS generated_content_cis_owner_all ON silver_aa_internal.generated_content;
DROP POLICY IF EXISTS quality_scores_cis_owner_all ON silver_aa_internal.quality_scores;
DROP POLICY IF EXISTS raw_tours_cis_owner_all ON silver_aa_internal.raw_tours;
DROP POLICY IF EXISTS seo_context_cis_owner_all ON silver_aa_internal.seo_context;

ALTER DEFAULT PRIVILEGES FOR ROLE aa_cis_admin IN SCHEMA acp_contract, acp_deliver, acp_gold_output, acp_shared,
    acp_silver_s2, acp_silver_s3, acp_silver_s4, geo, gold_aa_internal, shared, silver_aa_internal
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO cis_app;
ALTER DEFAULT PRIVILEGES FOR ROLE aa_cis_admin IN SCHEMA acp_contract, acp_deliver, acp_gold_output, acp_shared,
    acp_silver_s2, acp_silver_s3, acp_silver_s4, geo, gold_aa_internal, shared, silver_aa_internal
    GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO cis_app;
ALTER DEFAULT PRIVILEGES FOR ROLE aa_cis_admin IN SCHEMA acp_contract, acp_deliver, acp_gold_output, acp_shared,
    acp_silver_s2, acp_silver_s3, acp_silver_s4, geo, gold_aa_internal, shared, silver_aa_internal
    GRANT EXECUTE ON FUNCTIONS TO cis_app;

ALTER DEFAULT PRIVILEGES FOR ROLE cis_owner IN SCHEMA acp_contract, acp_deliver, acp_gold_output, acp_shared,
    acp_silver_s2, acp_silver_s3, acp_silver_s4, geo, gold_aa_internal, shared, silver_aa_internal
    REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM cis_app;
ALTER DEFAULT PRIVILEGES FOR ROLE cis_owner IN SCHEMA acp_contract, acp_deliver, acp_gold_output, acp_shared,
    acp_silver_s2, acp_silver_s3, acp_silver_s4, geo, gold_aa_internal, shared, silver_aa_internal
    REVOKE USAGE, SELECT, UPDATE ON SEQUENCES FROM cis_app;
ALTER DEFAULT PRIVILEGES FOR ROLE cis_owner IN SCHEMA acp_contract, acp_deliver, acp_gold_output, acp_shared,
    acp_silver_s2, acp_silver_s3, acp_silver_s4, geo, gold_aa_internal, shared, silver_aa_internal
    REVOKE EXECUTE ON FUNCTIONS FROM cis_app;

REVOKE INSERT, UPDATE, DELETE ON shared.schema_versions FROM cis_app;

INSERT INTO shared.schema_versions (version, applied_at, description)
VALUES ('rl-0NN', now(), 'AA-860 (X1 S21 rollback): undo CIS 245, CIS schemas and objects back to aa_cis_admin, cis_owner policies dropped, default privileges of cis_app FOR ROLE aa_cis_admin')
ON CONFLICT (version) DO NOTHING;

DO $$
DECLARE
    all_schemas text[] := ARRAY['acp_contract', 'acp_deliver', 'acp_gold_output', 'acp_shared', 'acp_silver_s2',
                                'acp_silver_s3', 'acp_silver_s4', 'catalog', 'geo', 'gold_aa_internal', 'shared',
                                'silver_aa_internal'];
    stray       text;
    after_text  text;
BEGIN
    SELECT string_agg(o, ', ' ORDER BY o) INTO stray FROM (
        SELECT pg_catalog.format('schema %s', nspname) AS o FROM pg_catalog.pg_namespace
         WHERE nspname = ANY (all_schemas) AND nspowner <> 'aa_cis_admin'::regrole
        UNION ALL
        SELECT pg_catalog.format('%s %I.%I', c.relkind, n.nspname, c.relname)
          FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
         WHERE n.nspname = ANY (all_schemas) AND c.relowner = 'cis_owner'::regrole
        UNION ALL
        SELECT pg_catalog.format('routine %I.%I', n.nspname, f.proname)
          FROM pg_catalog.pg_proc f JOIN pg_catalog.pg_namespace n ON n.oid = f.pronamespace
         WHERE n.nspname = ANY (all_schemas) AND f.proowner = 'cis_owner'::regrole
        UNION ALL
        SELECT pg_catalog.format('type %I.%I', n.nspname, y.typname)
          FROM pg_catalog.pg_type y JOIN pg_catalog.pg_namespace n ON n.oid = y.typnamespace
         WHERE n.nspname = ANY (all_schemas) AND y.typowner = 'cis_owner'::regrole
        UNION ALL
        SELECT pg_catalog.format('statistics %I.%I', n.nspname, x.stxname)
          FROM pg_catalog.pg_statistic_ext x JOIN pg_catalog.pg_namespace n ON n.oid = x.stxnamespace
         WHERE n.nspname = ANY (all_schemas) AND x.stxowner = 'cis_owner'::regrole
    ) s;
    IF stray IS NOT NULL THEN
        RAISE EXCEPTION 'rl undo: still owned by cis_owner (or schema not the master''s; a kind this file does not move?): %', stray;
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_default_acl WHERE defaclrole = 'cis_owner'::regrole) THEN
        RAISE EXCEPTION 'rl undo: default privileges FOR ROLE cis_owner remain';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_catalog.pg_policy WHERE 'cis_owner'::regrole::oid = ANY (polroles)) THEN
        RAISE EXCEPTION 'rl undo: a policy TO cis_owner remains';
    END IF;
    IF (SELECT count(*) FROM pg_catalog.pg_default_acl d JOIN pg_catalog.pg_namespace n ON n.oid = d.defaclnamespace
         WHERE n.nspname = ANY (all_schemas) AND d.defaclrole = 'aa_cis_admin'::regrole) <> 33 THEN
        RAISE EXCEPTION 'rl undo: expected the 33 default-privilege rows FOR ROLE aa_cis_admin of CIS 244';
    END IF;

    SELECT coalesce(string_agg(p, E'\n' ORDER BY p), '') INTO after_text
    FROM (
        SELECT pg_catalog.format('schema %I: %s %s %s', n.nspname, a.grantee::regrole, a.privilege_type, a.is_grantable) AS p
          FROM pg_catalog.pg_namespace n,
               pg_catalog.aclexplode(coalesce(n.nspacl, pg_catalog.acldefault('n', n.nspowner))) a
         WHERE n.nspname = ANY (all_schemas) AND a.grantee <> n.nspowner
        UNION ALL
        SELECT pg_catalog.format('rel %I.%I: %s %s %s', n.nspname, c.relname, a.grantee::regrole, a.privilege_type, a.is_grantable)
          FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace,
               pg_catalog.aclexplode(coalesce(c.relacl, pg_catalog.acldefault(
                   CASE WHEN c.relkind = 'S' THEN 's'::"char" ELSE 'r'::"char" END, c.relowner))) a
         WHERE n.nspname = ANY (all_schemas) AND c.relkind IN ('r', 'p', 'v', 'm', 'f', 'S') AND a.grantee <> c.relowner
        UNION ALL
        SELECT pg_catalog.format('col %I.%I.%I: %s %s %s', n.nspname, c.relname, t.attname, a.grantee::regrole,
                                 a.privilege_type, a.is_grantable)
          FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
          JOIN pg_catalog.pg_attribute t ON t.attrelid = c.oid,
               pg_catalog.aclexplode(t.attacl) a
         WHERE n.nspname = ANY (all_schemas) AND t.attacl IS NOT NULL AND a.grantee <> c.relowner
        UNION ALL
        SELECT pg_catalog.format('routine %I.%I(%s): %s %s %s', n.nspname, f.proname,
                                 pg_catalog.pg_get_function_identity_arguments(f.oid), a.grantee::regrole,
                                 a.privilege_type, a.is_grantable)
          FROM pg_catalog.pg_proc f JOIN pg_catalog.pg_namespace n ON n.oid = f.pronamespace,
               pg_catalog.aclexplode(coalesce(f.proacl, pg_catalog.acldefault('f', f.proowner))) a
         WHERE n.nspname = ANY (all_schemas) AND a.grantee <> f.proowner
        UNION ALL
        SELECT pg_catalog.format('type %I.%I: %s %s %s', n.nspname, y.typname, a.grantee::regrole, a.privilege_type,
                                 a.is_grantable)
          FROM pg_catalog.pg_type y JOIN pg_catalog.pg_namespace n ON n.oid = y.typnamespace,
               pg_catalog.aclexplode(coalesce(y.typacl, pg_catalog.acldefault('T', y.typowner))) a
         WHERE n.nspname = ANY (all_schemas) AND a.grantee <> y.typowner
    ) s;
    IF after_text IS DISTINCT FROM current_setting('rl_undo_245.privileges') THEN
        RAISE EXCEPTION 'rl undo: privileges of a non-owner role changed with the transfer back';
    END IF;
END $$;

COMMIT;
