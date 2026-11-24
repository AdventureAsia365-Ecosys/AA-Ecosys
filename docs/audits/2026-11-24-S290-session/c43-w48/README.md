# C4.3 weekly DB review — W48 (S290, 24/11/2026)

Probe: DB Migrate `mode=run-script` `aa838_capacity_probe.py` (read-only catalog and `pg_stat_statements`), run
45334290224, 24/11 05:35Z. Raw output: `probe-2026-11-24.txt`. Previous review: W47 (S282, probe 15/11 23:45Z), so the
deltas below cover about 197.8 hours (8.2 days). "New-call mean" = (change in total time) / (change in calls) between
the two probes; the probe's p95 is mean + 2 × stddev over all calls since `stats_reset`.

- 9,888 statements tracked (43,441 deallocated, up from 24,883: about 18,600 evictions in 8 days, see finding 5;
  `stats_reset` 07/10, numbers are cumulative since then). Five statements in the W47 lists were evicted and re-entered,
  so their counters restarted and have no delta.
- Lock waits 0, blocked sessions 0, deadlocks 0, bloat 0 (no table above 20 % dead with ≥ 1,000 dead rows),
  transactions > 60 s 0, cache hit 99.73 %, client sessions 16 / 181 (ceiling 135). Per-role connection use at most
  33 % (`crm_app` 2 of 6). No restart since 28/10.
- Database 2.33 GB (W47 2.25 GB, about +10 MB/day). Biggest tables unchanged: `shared.decision_log` 591 MB,
  `acp_contract.atom_embedding` 456 MB, `shared.llm_call_log` 304 MB, `geo.tour_place` 221 MB. A quiet week for AI:
  `llm_call_log` got 11,859 rows in the last 7 days (W47 127,413). DB time grew about 17 s per hour of wall time;
  `crm_app` (35.4 %) and `aa_app_user` (35.5 %) now carry the most cumulative time.
- Ledger retention: nothing past its window except `shared.job` (1,708 rows older than 30 days by `created_at`, W47
  2,705). Since W47 `retention_job` runs **live** on schedule (approved; the last run deleted 33 of 33 candidates, about
  2,600 rows deleted since W47). The rows left are most likely kept by its own rules: it keys on `finished_at`, keeps
  failed and cancelled jobs 90 days, and never deletes a job that a content piece, a tenant tour version or a child job
  still references. `decision_log`, `llm_call_log` and `tenant_api_usage` stay in `dry_run` with 0 candidates.
- C1.2 targets (worst statement p95 / mean):
  - tenant reads: worst p95 **~155 ms (objective < 150 ms)**, SLI mean 7.0 ms over 17,917 calls (finding 1);
    tenant tour versions worst p95 ~56 ms;
  - job claim mean 0.5 ms (< 20 ms); new-call mean about 0.01 ms over 146,782 calls; the max advisory-lock wait
    (45 s) is still the old one, so no new long wait;
  - Booking: trip-case statements appear for the first time (13 statements, 324 calls, worst p95 ~2.7 ms, < 100 ms);
    no customer statements;
  - TripPlanner: browse reads worst p95 ~95 ms (< 300 ms), outbox p95 ~0.1 ms (< 500 ms);
  - admin cost aggregates mean 4.9 ms, worst p95 ~278 ms (< 1 s, finding 3); admin usage view p95 ~0.2 ms;
  - `catalog_views` mean 16.5 ms, worst p95 ~707 ms (< 1 s; cumulative, mostly calls from before the AA-1107 fix).
- **One C1.2 target missed, first week:** CIS tenant reads (finding 1). C1.2a escalates after **two consecutive**
  weekly misses, so no escalation this week; W49 decides. The query and a fix direction are below, ready for the tech
  lead if W49 confirms the miss.

## Findings

1. **Tenant served-badge lookup over the tenant-read objective:** `REQUEST_TOURS_SQL`
   (`shared/tour_liveness.py`, `request_tours`: the tour each angle-gate request is about and its liveness, used by the
   served badges on `/v1` lists (`api/routers/_served.py`) and the publish / write / angle-gate 409 checks), role
   `aa_app_user`: 806 calls, mean 121.6 ms, p95 ~155 ms, max 234 ms, about 8 rows per call, all buffer hits (about
   29,000 buffers per call, so the time is CPU). It is new in the lists this week (W47 saw one tenant-read statement;
   this week 30). The plain liveness read of the same view (`SERVED_STATES_SQL`, 2,147 calls) takes 9.4 ms, so most
   of the cost is the AA-1057 Subject rule: the served-member subqueries in the `CASE` / `COALESCE`, evaluated per
   request row, plus the `v_tour_liveness` join on an expression key (`COALESCE(source_group_id, tour_id)::text`).
   Next step: an `EXPLAIN (ANALYZE, BUFFERS)` of one typical call through DB Migrate `run-script` (plan only, no row
   values in the file), then compute the representative tour once (a `LATERAL` per request) and evaluate the Subject
   rule only when that tour is retired. Needs a CIS change; proposed as a follow-up.
2. **AA-1107 fixed the catalog places read (W47 finding 2):** CIS #1533 (`Refs AA-1107`, migrations 431 index
   `geo.tour_place (source_id, day_index, geo.name_norm(name))` and 432 atoms per tour, day heading once, `name_norm`
   ASCII path) merged 16/11 about 01:50Z, two hours after the W47 probe, and is live (the index is in the 24/11 schema
   dump). `catalog.v_tour_place` (`aa_app_user`): 1,683 calls since W47 took 235 s, so the new-call mean is about
   **140 ms** (W47 window 536 ms; cumulative mean 235 → 222 ms), with about 1,265 rows per call (W47 average about
   525) and no new temp spill (`aa_app_user` temp blocks unchanged). The new-call p95 is roughly 255 ms (derived from
   the change in mean and stddev). This matches the post-fix plan in W47's `explain-places-after-aa1107.txt` (143 ms
   for 50 tours). `catalog.v_tour_day` also improved: new-call mean about 24 ms (cumulative 35.6 ms). The places read
   is still the top statement by total time, but its cumulative p95 will fall only slowly; a C4.3a reset after the next
   capacity review clears the old calls.
3. **Anomaly-breaker baseline query reads and spills:** `BASELINE_SQL` (`shared/llm_client/anomaly_breaker.py`,
   AA-1126, CIS #1566, live since 17/11), role `cis_app`: 2,148 calls, mean 145 ms, p95 ~278 ms, max 752 ms. It
   accounts for almost all `cis_app` disk reads and temp writes this week (288,949 blocks read, 368,842 temp blocks,
   about 3 GB of temp). It runs about 300 times a day although the baseline is cached per process per app and UTC
   day. Within the admin cost objective (< 1 s), but it sits on the AI gateway path. Fix direction: filter
   `shared.llm_call_log` on the raw `app` column (or a stored app column) rather than the
   `coalesce(app, quality_signal ->> 'app', 'cis')` expression, read the baseline days from `shared.llm_call_daily`
   once they are rolled up, and check why the per-process cache misses this often. The two admin tenant cost sums in
   `api/routers/admin.py` (`tenant_id = $1 OR ($2 AND tenant_id IS NULL)`, 15 calls each, 120–145 ms, about 13,000
   blocks read per call) scan the ledger for the same reason (the `OR` defeats the `(tenant_id, created_at)` index);
   cheap at 15 calls. The W47 cost-aggregate worst case (`shared.ai_usage_hourly` upsert, p95 ~688 ms) was evicted
   and re-entered; its new entry shows mean 4.2 ms, p95 ~27 ms over 436 calls.
4. **CRM polling volume keeps growing (W47 finding 3):** the CRM proposal lookup ran 721,181 times in 197.8 h (about
   one call per second) and still returned no new row (27 rows in total since the stats reset); its new-call mean rose
   to 0.78 ms (cumulative 0.5 ms) as each call now touches about 1,020 buffers (about 645 on average before), so the
   cost grows with the table. The `crm.tenant` status check ran about 6.4 times per second, and the `crm.job`
   retention `DELETE` about every 7 s (103,518 calls, new-call mean 3.2 ms, up from 2.1 ms). `crm_app` used about
   1,670 s of DB time in the window (about 8.4 s per hour), half of all new DB time. Still cheap; when the CRM job
   cadence is next tuned: an index or a longer interval for the proposal poll, and run the job retention `DELETE` once
   a minute or less.
5. **`pg_stat_statements` churn hides history:** `crm_app` holds 8,927 of the 9,888 tracked statements
   (`pg_stat_statements.max` = 10,000), and about 18,600 entries were evicted in 8 days. Evictions reset the counters
   of rarely called statements of every app (three `cis_app` statements this week), which breaks the week-over-week
   deltas C4.3 relies on. Likely sources are CRM statements whose text differs per call; utility statements are not
   normalised, for example the portability restore drill's uniquely named temp table (`CREATE TEMP TABLE {temp}`,
   `api/app/portability/restore_drill.py`). To confirm: a probe section counting `crm_app` statements by their first
   40 characters. If confirmed, use a fixed temp table name or `pg_stat_statements.track_utility = off`. Statement texts
   built with literal values would also put those values into `pg_stat_statements` (C4.2c), so the check is worth
   doing even if the churn turns out harmless.
6. **Booking season-calendar sync retries the same plans:** `assign_default_calendars`
   (`backend/app/pricing/season_sync.py`, AA-1128 B1, live since 18/11) read `catalog.v_tour` one plan at a time 29,200
   times (mean 10.3 ms, about 2,700 buffers for a one-row lookup) and then the first-day place 23,577 times, but only
   650 of those reads found a destination. Plans whose first day has no destination are picked again on every run (the
   salt only rotates the order). About 330 s of DB time since 18/11 (about 2 s per hour); no Booking objective is
   affected. Fix direction: record the outcome per plan (`no_destination` / `no_tour` with a checked time) and recheck
   only when the plan's catalog content changes or after a set interval.

## Proposed follow-ups

- CIS: faster `REQUEST_TOURS_SQL` (finding 1). If W49 still shows the tenant-read miss, raise it to the tech lead
  under C1.2a with this query and fix (ask before creating the Linear issue). W49 should judge on the new-call figures,
  since the cumulative p95 moves slowly.
- CIS: sargable anomaly-breaker baseline and admin tenant cost sums, plus the cache-miss check (finding 3).
- Probe (AA-CIS-Infra `db/scripts/aa838_capacity_probe.py`): add the per-role statement-prefix count of finding 5 and
  the delta columns this review computes by hand (calls and total time against the previous probe).
- CRM: proposal poll index or interval, and a slower job retention `DELETE` (finding 4); fixed temp table name in the
  restore drill if finding 5 confirms it.
- Booking: remember the season-sync outcome per plan (finding 6).
