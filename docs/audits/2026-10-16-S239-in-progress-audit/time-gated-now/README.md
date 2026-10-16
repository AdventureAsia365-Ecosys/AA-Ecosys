# Time-gated checks run now (S239, 16/10/2026)

Dev has no real users or traffic, so the date gates on AA-828 (17/10) and AA-833 (22/10) were
checked now instead of waited out. All AWS calls read-only, account 005097885195 (acc2), profile
`aa365-admin`, checked at ~03:30Z 16/10.

## AA-828 — cost by App tag + per-app budgets

Cost Explorer, DAILY, UnblendedCost, grouped by tag `App` (`aa828-ce-by-app.json`):

| Day (UTC) | untagged (`App$`) | cis | shared | tripplanner | booking |
|---|---|---|---|---|---|
| 14/10 | 6.405 | 0 | 0 | 0 | 0 |
| 15/10 | 3.986 | 0.049 | 0.103 | 0.014 | 0.003 |
| 16/10 | no data yet (CE lags ~24 h; re-pulled 03:59Z, still empty: `aa828-ce-by-app-0405Z.json`) | | | | |

- 15/10 already shows tagged spend in all four App values. The tag was activated during 15/10, so
  only the hours after activation carry it (~4 % of the day). `ce get-tags` returns
  `"", booking, cis, shared, tripplanner`.
- 15/10 by service (`aa828-ce-2026-10-15-by-app-service.json`): the untagged rest is ECS 1.22,
  ELB 0.66, RDS 0.51, CloudWatch 0.34, ElastiCache 0.29, VPC 0.21, EC2-Other 0.21, WAF 0.17,
  Secrets Manager 0.17. These are the same resources that carry a tagged line after activation
  (ELB/WAF/EC2-Other → shared, ElastiCache/ECS/API GW → cis), so this is the activation cut-off,
  not missing tags.
- Resource tags confirmed live: RDS `aa-cis-dev-db` App=shared; ECS services `aa-cis-dev-api`,
  `aa-cis-dev-worker` App=cis and `aa-booking-dev-api` App=booking, all `propagateTags=SERVICE`,
  and the running tasks carry the tag (CIS tasks started 16/10 03:23Z, booking 15/10 15:33Z).
  CIS ECS tasks running before 03:23Z 16/10 may have had no task tag, so part of 16/10 ECS can
  still show untagged.
- Budgets (`aa828-budgets.json`), October-to-date CalculatedSpend:

| Budget | Limit USD | Actual USD |
|---|---|---|
| aa-cis-dev-monthly-app-cis | 150 | 0.049 |
| aa-cis-dev-monthly-app-shared | 50 | 0.103 |
| aa-cis-dev-monthly-app-tripplanner | 25 | 0.014 |
| aa-cis-dev-monthly-app-booking | 25 | 0.003 |
| aa-cis-dev-monthly-total | 250 | 80.038 (forecast 180.64) |

Verdict: the "Cost Explorer by App is not ~$0" check passes now; each per-app budget is already
reading non-zero spend. A first full tagged day (16/10) lands in CE ~17/10 and is a nice-to-have
number, not a gate. Not covered here: CloudTrail log bucket tag (after AA-806 drift) and forecast
alerts, which are the other open items on AA-828.

## AA-833 — TripPlanner browse/assembly throttles

Config: `aa-tripplanner-dev-browse` reserved concurrency 15, `aa-tripplanner-dev-assembly` 5
(sum 20, inside the tripplanner role CONNECTION LIMIT 30). Alarms: Throttles Sum > 5 per 300 s,
2 of 3 datapoints, missing = notBreaching.

Since 15/10 12:35Z (`aa833-history-*.json`, `aa833-before-*.json`):

| | browse | assembly |
|---|---|---|
| Alarm state | OK (since 15/10 11:09Z) | OK (since 14/10 15:48Z) |
| StateUpdate items since 12:35Z | 0 | 0 |
| Throttles (sum) | 0 | 0 |
| Errors (sum) | 0 | 0 |
| Invocations | 1165 | 54 |
| ConcurrentExecutions (max, hourly) | 5 | 2 |

### Controlled burst (run 16/10 03:56:30–03:57:41Z)

`python3 -I aa833-burst.py 15 60 aa833-burst-result.json`: 15 workers, 60 s, round-robin over the 14
query shapes from `frontend/lib/api.ts` + `lib/catalog.ts` against
`https://tripplanner.lumiguides.it.com/api/browse`. Post-check ran 10 min later
(`aa833-postcheck.sh 2026-10-16T03:56:00Z`, output in `aa833-postcheck-output.txt`, `aa833-after-*.json`).

| Resource | Requests | 200 | 500 | 503 |
|---|---|---|---|---|
| tiles | 630 | 630 | 0 | 0 |
| catalog-tours | 381 | 381 | 0 | 0 |
| by-country | 380 | 380 | 0 | 0 |
| countries | 127 | 127 | 0 | 0 |
| routes | 126 | 126 | 0 | 0 |
| **search** | **126** | **16** | **61** | **49** |
| Total | 1770 (29.5 rps) | 1660 | 61 | 49 |

4xx: 0. 429: 0. 5xx: 110, all on `search`. Client latency p50 0.19 s, p95 0.76 s, max 13.7 s.

Lambda `aa-tripplanner-dev-browse` (03:56–03:58Z): Invocations 191, **Throttles 99**, **Errors 117**,
ConcurrentExecutions max 15 (= reserved 15), duration p50 5.4 s / p95 11.8 s / max 13.1 s
(`aa833-burst-lambda-errors.txt`). Assembly: 0 invocations, 0 throttles.

**Alarm flipped:** `aa-tripplanner-dev-browse-throttles` OK → ALARM at 04:02:32Z ("2 out of the last 3
datapoints [21.0 (03:57), 78.0 (03:52)] > 5"), action SNS `aa-cis-dev-acp-alerts` (so the alert
e-mail went out; it was this test). It went back ALARM → OK at 04:21:32Z (19 min), only once a real
0-throttle datapoint arrived (04:16Z); while browse had no traffic the missing datapoints alone did not
clear it (`aa833-final-history-aa-tripplanner-dev-browse-throttles.json`).
`aa-tripplanner-dev-assembly-throttles` stayed OK, 0 flips.

#### Root cause: search = Bedrock embed quota, not Lambda concurrency
- All 117 Lambda errors are one line: `BedrockError: All models failed for stage 'tp_search_embed':
  cohere-embed-v4@acc2: ThrottlingException (reached max retries: 4)`.
- Bedrock quota on acc2 us-west-1 (`aa833-bedrock-cohere-embed-quotas-acc2.json`):
  **Cohere Embed V4 cross-region = 20 requests/min** (300k tokens/min). The burst sent 126 searches/min;
  16 succeeded, which is that quota.
- Every search request embeds the query live (`backend/browse/search.py`, no query-vector cache, same
  `q=hanoi` re-embedded 126 times). The route `tp_search_embed` has one model with one account
  (`_COHERE = {"acc2": "us.cohere.embed-v4:0"}` in `backend/shared/llm_gateway.py`), so there is no
  fallback. boto retries (4) hold each Lambda instance for 5–13 s, so 15 search requests in flight fill
  the reserved concurrency 15 and every other browse call that misses the Vercel cache is throttled
  (99 throttles, the 503s).
- The non-search paths did not fail because they were Vercel CDN hits after the first request
  (`x-vercel-cache: HIT`, `age` ≈ burst start, `public, max-age=1800`). So this burst did **not**
  re-test Lambda/DB capacity for uncached tiles/catalog-tours at 15 concurrent; it tested search.
- `tp_component_embed` and any other Cohere Embed v4 caller on acc2 share the same 20 RPM.

#### Caveat
An unidentified parallel load started at 03:56:04Z (marker `aa833-burst-start.txt`, not written by
this lane; Lambda logs show 59 invocations 03:56:00–03:56:30Z, before this burst started). The Lambda
counts above include it. The root cause does not change: any search load > 20/min hits the quota.

#### Verdict for AA-833
The original AA-833 problem (catalog views slow → browse throttled at concurrency 15) did not come
back in 26 h of quiet traffic (0 throttles, 0 flips 15/10 12:35Z → 16/10 03:56Z). Under a search
burst the browse Lambda throttles and the alarm flips, because of the Bedrock embed quota.
Not closable as "never flipped". Proposed follow-up (new issue, ask Nghiệp first):
1. Cache query embeddings (e.g. by normalized `q`, in-Lambda LRU + DB table) and/or debounce search
   on the client.
2. Fail fast on embed `ThrottlingException` (no 4 boto retries, low `read_timeout`) and return a
   clean 503/429 from search only, so one stage cannot starve the reserved concurrency.
3. Add a fallback for `tp_search_embed` (Cohere profile on acc3/acc1 satellite, same model so vectors
   stay compatible) and/or a higher quota. On acc2 the `us.` cross-region RPM (20) is **not adjustable**;
   the *global* cross-region RPM (20) is adjustable, so a raise needs the `global.` inference profile.
4. Optional: the throttle alarm could watch `Errors` by stage separately so a Bedrock quota event is
   named as such.
