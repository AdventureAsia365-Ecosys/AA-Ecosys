# C4.3 weekly DB review — W47 (S282, 16/11/2026)

Probe: DB Migrate `mode=run-script` `aa838_capacity_probe.py` (read-only catalog and `pg_stat_statements`), run
43776407898, 15/11 23:45Z. Raw output: `probe-2026-11-16.txt`. Previous review: W46 (S280, 14/11 06:09Z), so the deltas
below cover about 41.6 hours.

- 9,943 statements tracked (24,883 deallocated, `stats_reset` 07/10: numbers are cumulative since then).
- Lock waits 0, blocked sessions 0, deadlocks 0, bloat 0 (no table above 20 % dead with ≥ 1,000 dead rows),
  transactions > 60 s 0, cache hit 99.69 %, client sessions 9 / 181 (ceiling 135). Per-role connection use at most
  17 % (`crm_app` 1 of 6).
- Database 2.25 GB (W46 2.24 GB). Biggest tables unchanged: `shared.decision_log` 584 MB,
  `acp_contract.atom_embedding` 454 MB, `shared.llm_call_log` 288 MB, `geo.tour_place` 220 MB.
- Ledger retention: nothing past its window except `shared.job` (2,705 rows past 30 days; `retention_job` still runs
  in `dry_run`, 2,292 candidates). Same open point as W46: a live run needs the retention owner's approval.
- C1.2 targets (worst statement p95 / mean):
  - tenant reads p95 ~0.2 ms (< 150 ms);
  - job claim mean 0.6 ms (< 20 ms); one long advisory-lock wait (max 45 s) inside the cumulative window;
  - Booking: no trip-case or customer statements (B2B-only, no traffic);
  - admin cost aggregates mean 4.2 ms, worst p95 ~688 ms (< 1 s);
  - `catalog_views` mean 16.5 ms, worst p95 ~750 ms (< 1 s).
- **No C1.2 target missed**, so no C1.2a escalation.

## Findings

1. **W46 fix holds:** the lifecycle `LAG_SQL` (CIS #1495) is no longer in the top 50 by total or mean time. Only one
   statement with ≥ 20 calls has a mean above 200 ms (finding 2).
2. **TripPlanner place read (`catalog.v_tour_place`, TripPlanner Lambda role) got slower on new calls:** 351 calls
   since W46 took 188 s, so the new-call mean is about **536 ms** (cumulative mean 225 → 235 ms; W45 new-call mean was
   ~82 ms). `geo.tour_place` shows 10,323 sequential scans, about one per call, and the statement spills to temp.
   No C1.2 target covers it, but it is the slowest machine-facing read. The caller is the CIS catalog HTTP reader
   (`services/catalog_http/reader.py`, `places`, role `aa_app_user`, about 525 rows per call), not the TripPlanner
   Lambda as W46 assumed.
   **EXPLAIN (ANALYZE, BUFFERS), 50 listed tours, warm cache** (`explain-places-50-tours.txt`, plan only):
   606 ms, 1,321 rows, all buffers hits. About half (~310 ms) is one lookup per output row on `geo.tour_place`
   (`tour_place_source_idx` on source_id + day_index, then `Filter: geo.name_norm(name) = geo.name_norm(place_name)`:
   0.23 ms × 1,321 loops); the rest is a parallel sequential scan and sort of all `acp_contract.tour_atoms` (~25,900
   rows, ~77 ms, the tour filter is not pushed below the merge join) and the per-tour spelling window (~150 ms).
   Fix direction: an index on `geo.tour_place (source_id, day_index, geo.name_norm(name))` (or a stored normalised
   name column) and pushing the tour filter into the atoms scan. Needs a CIS migration; proposed as a follow-up.
3. **CRM polling volume:** the CRM proposal lookup (`crm.proposal` join, 0.5 ms) ran about 150,000 times in 41.6 h
   (about one call per second) and returned 27 rows in total since the stats reset; the `crm.tenant` status check ran
   about 6 times per second. Cheap per call (DB time ~3 s/h), so no action now; worth a look when the CRM job cadence
   is next tuned.
4. `retention_job` keeps running in `dry_run` with 2,292 candidates (unchanged owner decision, as W46).
