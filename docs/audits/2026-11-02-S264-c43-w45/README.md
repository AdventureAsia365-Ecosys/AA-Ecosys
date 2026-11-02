# C4.3 weekly DB review — W45 (S264, 02/11/2026)

Probe: DB Migrate `mode=run-script` `aa838_capacity_probe.py` (read-only catalog and `pg_stat_statements`), 00:21Z.
Raw output: `probe-2026-11-02.txt`.

- 9,735 statements tracked (2,056 deallocated, `stats_reset` 07/10, so numbers are cumulative; compare deltas with W44).
- Lock waits 0, deadlocks 0, bloat 0, transactions > 60 s 0, cache hit 99.14 %, connections 7/181.
- C1.2 targets: tenant reads p95 ~111 ms (< 150), job claim mean 1.1 ms (< 20), Booking p95 < 1 ms (< 100), admin cost
  aggregate 69 new calls, mean ~217 ms (< 1 s). TripPlanner place read: 777 new calls since W44, new-call mean ~82 ms
  (cumulative still 295 ms from before TP #181).
- The ~4.9 s p95 line on `catalog_views` is the `PREPARE aa995_view_…_n25` probe of Infra #494 (60 measurement runs, not
  app traffic).
- **No target missed**, so no C1.2a escalation.
