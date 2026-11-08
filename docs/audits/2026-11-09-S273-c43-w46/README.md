# C4.3 weekly DB review — W46 (S273, 08–09/11/2026)

Probe: DB Migrate `mode=run-script` `aa838_capacity_probe.py` (read-only catalog and `pg_stat_statements`), 17:02Z on
08/11 (00:02 on 09/11, +07). Raw output: `probe-2026-11-08.txt`. Compared with W45 (`../2026-11-02-S264-c43-w45/`).

- Lock waits 0, deadlocks 0, bloat 0, transactions > 60 s 0, cache hit 99.31 % (W45 99.14 %), connections 14/181
  (a W2 generation run, a platform recompute and three lanes' CI were active).
- Database 1,629.6 MB (+57 MB in a week).
- C1.2 targets:
  - Job claim mean 0.8 ms (< 20).
  - Admin cost aggregate (`llm_call_log`) worst statement p95 ~697 ms (< 1 s). The heaviest is the per-provider month
    spend sum: 1,323 calls, mean 109 ms.
  - Booking: no tracked statement this week (evicted, see below).
  - Tenant reads (`acp_shared.*`): the worst statement p95 ~170 ms is above the 150 ms target, but it is a 17-call
    staff read of `content_piece` joined to `angle_gate_request` (mean 31 ms; the W2 split-plan / held-out reads of
    this session), not tenant HTTP traffic. **No C1.2a escalation**; recheck in W47.
  - `catalog_views` worst p95 ~666 ms, down from ~4.9 s in W45 (that was the Infra #494 probe).
- 0 statements with calls >= 20 and mean > 200 ms (W45: 2).

## Finding: `pg_stat_statements` churn

`dealloc` went from 2,056 (W45) to 9,122 in one week, with `pg_stat_statements.max = 10000`. Statements are being
evicted, so the cumulative numbers above cover a shorter, uneven window. Example: tenant reads show 6,323 calls vs
114,596 in W45. The likely sources are the many ad-hoc S273 scripts (ECS exec and run-script) and test probes, each
with its own statement text. Options for the tech lead: raise `pg_stat_statements.max` to 20,000 (static parameter:
it needs a DB reboot in a quiet window; memory cost about 10 MB), or keep 10,000 and read the weekly numbers as
"top statements since the last eviction" only. No change made.

## Retention

The `shared.job` retention run is still in dry run (610 candidates, 1,717 rows older than the 30-day window). Only
`retention_cost_explorer_snapshot` runs live. Unchanged since W45.
