# C4.3 weekly DB review — W46 (S280, 14/11/2026)

Probe: DB Migrate `mode=run-script` `aa838_capacity_probe.py` (read-only catalog and `pg_stat_statements`), run
43564841238, 06:09Z. Raw output: `probe-2026-11-14.txt`. W45 was the last review (S264, 02/11); W46 was due from 09/11.

- 9,710 statements tracked (21,048 deallocated, `stats_reset` 07/10, so numbers are cumulative since then).
- Lock waits 0, blocked sessions 0, deadlocks 0, bloat 0 (no table above 20 % dead with ≥ 1,000 dead rows),
  transactions > 60 s 0, cache hit 99.69 %, client sessions 13 / 181 (ceiling 135).
- Database 2.24 GB; biggest tables `shared.decision_log` 584 MB, `acp_contract.atom_embedding` 454 MB,
  `shared.llm_call_log` 287 MB. Ledger retention rows: none older than their window except `shared.job`
  (2,516 rows past 30 days; `retention_job` still runs in `dry_run`, 2,238 candidates).
- C1.2 targets (worst statement p95 / mean):
  - tenant reads p95 ~3.5 ms (< 150 ms);
  - job claim mean 0.7 ms (< 20 ms);
  - Booking: no trip-case or customer statements in the window (B2B-only, no traffic);
  - admin cost aggregates mean 5.3 ms, worst p95 ~741 ms (< 1 s);
  - `catalog_views` mean 17.1 ms, worst p95 ~735 ms (W45 4.9 s was the Infra #494 probe).
- **No C1.2 target missed**, so no C1.2a escalation.

## Findings

1. **`services/recompute/lifecycle.py` `LAG_SQL` (AA-1056, CIS #1404, live since 09/11)**: the top statement by total
   time: 1,473 calls (about one every 5 minutes from the ops sampler and the Data coverage source), mean 2.33 s, p95
   ~5.4 s, 3,433 s of DB time, ~2.6 M buffer hits per call. A correlated subquery reads `shared.job` once per lifecycle
   event. Fix in this session: read the succeeded `recompute` jobs once and join (no schema change), with a test.
2. TripPlanner place read (`catalog` place rows, role of the TripPlanner Lambda): 10,568 calls, mean 225 ms, p95
   ~735 ms, `temp` spills. No C1.2 target is set for it; watch at W47 (the W45 new-call mean was ~82 ms).
3. `retention_job` keeps running in `dry_run` while 2,516 `shared.job` rows are past the 30-day window: an approval to
   run it live belongs to the retention owner (not changed here).

## Fix verified live (S280)

CIS #1495 (`191c1c4e`, deployed with `a2094087`): `LAG_SQL` on Dev 2.0–6.3 ms over three runs (64 events, 0
waiting), `EXPLAIN (ANALYZE, BUFFERS)` 134 shared buffer hits, execution 1.2 ms (before: mean 2.33 s, ~2.6 M hits).
Check at W47: the statement's mean for calls after the deploy should stay in single-digit ms.
