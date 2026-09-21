-- AA-603 — DROP the dead N7/N8 produce-flow tables.
-- Run ONLY after PR #413 (code removal) is merged + deployed to Dev (done: taskDef 313,
-- rollout COMPLETED, removed routes verified 404, kept routes verified live).
--
-- Context: these 5 tables backed the dead N7/N8 "produce" flow (write path gone since
-- admin_produce.py was deleted). Verified on the live Dev DB: all 5 hold 0 rows, the feedback
-- loop never ran (every tour_atoms.weight still 1.0), and no ramp/reallocation was ever recorded.
-- The last code that referenced them (content_metrics.py, trust_ramp.py, acp_health.py,
-- allocator persistence) was removed in PR #413.
--
-- KEEP acp_deliver.tenant_tour_pages — still written by the live F6 gate + public trip page
-- (v1_trip_page.py). NOT dropped here.
--
-- Runs as one transaction. The pre-DROP guard aborts if any table is unexpectedly non-empty.
-- Connect via cistunnel: psql -h localhost -p 15432 -U aa_cis_admin -d aa_cis_dev

\pset pager off

BEGIN;

-- Guard: refuse to drop if any table has rows (defends against a race since the last check).
DO $$
DECLARE
    n bigint;
BEGIN
    SELECT
        (SELECT count(*) FROM acp_deliver.pieces)
      + (SELECT count(*) FROM acp_deliver.packets)
      + (SELECT count(*) FROM acp_shared.acp_v2_slots)
      + (SELECT count(*) FROM acp_shared.acp_v2_runs)
      + (SELECT count(*) FROM acp_shared.content_metric_snapshot)
    INTO n;
    IF n <> 0 THEN
        RAISE EXCEPTION 'ABORT: expected 0 rows across the 5 tables, found %', n;
    END IF;
END $$;

-- DROP in FK-dependency order (child -> parent). CASCADE covers any FK/index/constraint left.
DROP TABLE IF EXISTS acp_shared.content_metric_snapshot CASCADE;  -- FK -> acp_deliver.pieces
DROP TABLE IF EXISTS acp_deliver.pieces               CASCADE;  -- FK -> packets, acp_v2_slots, acp_v2_runs
DROP TABLE IF EXISTS acp_deliver.packets              CASCADE;  -- FK -> acp_v2_runs
DROP TABLE IF EXISTS acp_shared.acp_v2_slots          CASCADE;  -- FK -> acp_v2_runs
DROP TABLE IF EXISTS acp_shared.acp_v2_runs           CASCADE;

-- Verify: all 5 must be gone, tenant_tour_pages must remain.
SELECT table_schema, table_name
FROM information_schema.tables
WHERE (table_schema, table_name) IN (
    ('acp_deliver','pieces'), ('acp_deliver','packets'),
    ('acp_shared','acp_v2_slots'), ('acp_shared','acp_v2_runs'),
    ('acp_shared','content_metric_snapshot'), ('acp_deliver','tenant_tour_pages'))
ORDER BY table_schema, table_name;
-- Expected: exactly ONE row -> (acp_deliver, tenant_tour_pages)

-- AA-603 — applied after dry-run PASS (guard passed, 5 DROP TABLE ok, verify left only
-- tenant_tour_pages). Nghiep approved. S191.
COMMIT;
