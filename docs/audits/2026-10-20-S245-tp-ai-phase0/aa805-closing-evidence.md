# AA-805 closing evidence (S245, TripPlanner AI Phase 0)

- **Agent:** Claude Code (sub-agent, lane `tpai`, session S245). **Run window:** 2026-10-19 23:28 to 23:39 UTC
  (20/10 morning, Vietnam time).
- **Builds on:** `docs/audits/2026-10-14-S237-lane-backlog/aa805-evidence.md`. Lines 2, 6, 7 and 8 (ownership, payload
  1.1, leg order, AI-assisted label) passed there. This file covers the four open lines: 1, 3, 4 and 5.
- **Deployed TripPlanner:** `main` b79ec48. The assembly Lambda was last modified 2026-10-19T13:32Z (Deploy Lambdas
  run on #109). No TripPlanner PR was open and no deploy was running during the checks, so they do not overlap the
  AA-909 handler work.
- **Rules kept:** public HTTP plus read-only AWS describes only (`apigatewayv2 get-api/get-stage`,
  `lambda get-account-settings/get-function-concurrency/get-function-configuration`). No Lambda invoke, no AWS write,
  no DB access from this machine. The DB half is a read-only DB Migrate run-script (§DB below), still to be dispatched.
- **Model spend in this run:** no `tp_compose` call. Every `/narrate` that reached the Lambda as the owner came back
  `source: master`, which makes no model call. Up to 30 `tp_search_embed` query embeds were made for the search set
  (< $0.01; some may have been container cache hits). The ~65 throttle probes were rejected at API Gateway (429), by
  Lambda reserved concurrency (503), or by the edge-key check (401) before any DB or model work.

## Verdict per open Done-when line

| # | Line | Verdict | Evidence |
|---|---|---|---|
| 1 | Throttle verified live (429 on `/narrate`) | **PASS: 429 captured.** Note: the limit is looser than configured, see §1 | §1 |
| 2 | Session ownership (re-check after AA-827) | **PASS** (401 without a cookie, 403 with a foreign session) | §2 |
| 3 | Spend cap: `llm_spend_daily` rows against the 5.0 USD cap | **PASS:** `tripplanner.llm_spend_daily` has rows (19/10 `tp_search_embed` 34 calls, 0.000015 USD, 0 unpriced) matching `shared.llm_call_log`; today's online spend 0.000000 vs cap 5.0 → `under_cap=True`. The hard stop itself stays covered by unit tests (as in S237) | §DB |
| 4 | Cache hit rate visible (cached:false, then cached:true) | **PASS** on a DB-listed candidate (`own_day_missing`): narrate #1 `source: llm, cached: false`, narrate #2 same itinerary `cached: true` (00:48:11Z, `aa805_cache_results_final.json`). Before this run `narration_cache` was empty (all earlier trips resolved to `source: master`, never cached) | §3, §DB |
| 5 | Search returns no inactive tours (30-query set) | **PASS:** 725/725 returned destinations exist and each has an active, embedded component (`without_active_component=0`); every embedded component is active (3905 embedded, 0 not active). Caveat: the negative control is empty (`inactive_only_destinations=0`), so the filter is shown as a necessary condition on today's catalog, not exercised against an inactive-only destination. The 30-query set was labelled by one agent, not a panel | §4, §DB |

**All five open lines pass** (S245, 20/10/2026). DB evidence: DB Migrate run-script run 39349512417 (read-only, master via `tp_owner`), lines in `aa805_db_script_lines.txt`.

---

## 1. Throttle on `POST /trip/{trip_id}/narrate`

Config, read-only (unchanged since Infra #103): the stage `$default` route setting is `POST /trip/{trip_id}/narrate`
rate 2.0 / burst 5 and `GET /browse/search` 10 / 20, with a default of 500 / 1000 (LastUpdated
2026-10-14T11:27:46Z). Account Lambda `ConcurrentExecutions` is 1000. The **assembly Lambda has reserved concurrency
5**.

Probes went straight at the HTTP API (`https://9vqkfbukvh.execute-api.us-west-1.amazonaws.com`, no edge key) on a
random trip UUID. Requests that pass API Gateway reach the Lambda, which rejects them at the edge-key check (401) with
no DB or model work.

| Run (UTC) | Shape | 401 (passed API GW) | 429 (API GW throttle) | 503 (Lambda throttled) |
|---|---|---|---|---|
| 23:28:00–03 | 15 parallel | 5 | 1 | 9 |
| 23:28:17–18 | 20 parallel | 15 | 3 | 2 |
| 23:28:41–46 | 30 requests over ~4.5 s (~6.7 rps) | 22 | 8 | 0 |

- Body of a 429: `{"message":"Too Many Requests"}`, from API Gateway. Body of a 503: `{"message":"Service Unavailable"}`,
  which API Gateway returns when the Lambda is throttled by its reserved concurrency of 5.
- One real narrate through the BFF also got a **429**, at 23:30:55Z. It was a single owner call, about 2 minutes
  after the bursts (cache try 3, `aa805_cache_results_try3.json`). The identical retry 14 s later got 200 (try 4).
- **Reading:** both guards are live. But API Gateway enforces the per-route bucket only approximately. The sustained
  run let about 4.9 rps through against the configured 2 rps (expected about 14 of 30, got 22), and a lone call was once
  refused. The hard cap on concurrent narrations is the Lambda's reserved concurrency (5), which answers 503 rather
  than 429. This does not fail the Done-when line, which asks for 429 behaviour on `/narrate`. It is worth one line in
  the Linear comment: the frontend narrate call should treat 429 and 503 as "busy, retry" (today only
  `lib/catalog.ts` retries 429/502/503, for browse).
- Raw status codes: `throttle_burst1_codes.txt` (run 1), `throttle_sustained_codes.txt` (run 3). Run 2's bodies were
  read live (counts above). The burst command was one line:
  `seq 1 15 | xargs -P 15 -I{} curl -s -o /dev/null -w "{} %{http_code}\n" -X POST -H 'content-type: application/json' -d '{"session_id":"00000000-0000-4000-8000-000000000000","mode":"compose"}' "https://9vqkfbukvh.execute-api.us-west-1.amazonaws.com/trip/$TRIP/narrate"`.

## 2. Session ownership after AA-827: PASS

Runner: `aa805_cache_run.py` (public BFF, one cookie jar per client, same-origin `Origin` header). Output:
`aa805_cache_results_try1.json`, trip `eec79780-bfb8-48af-b26f-701e6e47bd5e`, 23:29:46–48Z.

```
owner   add 9fbb2463-… (Loolecondera Tea Estate, Sri Lanka)          -> 200  (middleware minted the guest cookie)
owner   add da757bdd-… (Gobi Cashmere, Mongolia)                     -> 200
owner   narrate compose                                              -> 200  source=master cached=false
foreign client, NO cookie, owner's session_id                         -> 401  {"error":"cookies_required"}
foreign client, own session + own cookie (after an add on its own trip) -> 403  {"error":"forbidden","detail":"this trip belongs to another session"}
```

The 401 is the Lambda's `guest_session_invalid` as the BFF maps it for a token minted on the same request
(`mapMintedDenial` returns `cookies_required`). Both denials come before any itinerary read or model call.

## 3. Narration cache: not provable over HTTP with the trips tried

Five owner trips, 33 components, 10 countries (Sri Lanka, Mongolia, Japan, South Korea, Nepal, China, Bhutan, India,
Thailand, Laos). Every `/narrate compose` answered `source: master`, `cached: false`:

| Try | Trip | Components | Narrate #1 |
|---|---|---|---|
| 1 | `eec79780-…` | 2 | 200 master (1502 chars) |
| 2 | `7d819aca-…` | 1 (Azuma foothills, Japan) | 200 master |
| 3 | `7341e6dd-…` | 8 | **429** (API Gateway, see §1) |
| 4 | `5e1f2e06-…` | the same 8 | 200 master (6211 chars) |
| 5 | `2d4a346e-…` | 12 | 200 master (9807 chars) |

Why: since AA-819, `master_content.resolve_days` gives every trip day the AA master text of the component's own tour
day, or of another day of the same tour that names the stop, or the own day's text as it is. A day goes to the model
only when its tour has no parseable `Day N` text for it. Master narrations are never cached
(`narration_cache.CACHEABLE_SOURCES = ("llm", "mixed")`). So with these components there was nothing to cache, and
each call cost $0.

What closes the line:
1. The DB run (§DB, section 4 of the script) lists components whose tour day has no master text (`SCRIPT candidate
   kind=… component=<id>`), and prints the `narration_cache` summary (rows, hits, rows hit) from earlier real traffic.
2. If it lists candidates: `python3 aa805_cache_run.py <candidate id> [<candidate id>]` from this folder. Expect
   `narrate #1` `source llm|mixed cached:false`, then `narrate #2` `cached:true`, then the 401/403 pair. Cost about
   $0.01–0.02 (one `tp_compose`). A re-run of the DB script then shows `hits > 0`.
3. If it lists none (`no_structured_text=0 own_day_missing=0`): the cache path is dormant on Dev, because every planner
   narration is AA master text and spends nothing. Line 4 can then only be shown by the existing `narration_cache` rows
   (if any) plus the unit tests (`backend/tests/test_assembly.py` cache tests). Ask Nghiệp whether that is enough, or
   keep the line open until the catalog has a day without master text.

## 4. Search: 30-query labelled set, re-run live: 30/30 HTTP 200

Runner: `aa805_search_run.py` (the S237 runner, now also recording the `ranking` field). Raw output:
`aa805_search_results.json`, 23:32:01–23:34:18Z, public BFF, sequential. Fixture: TripPlanner
`backend/tests/fixtures/search_labelled_30.json` (main). **Labelled by one Claude Code agent (S237), not a Claude
panel.**

```
ok_200: 30 / 30     every query returned 60 destinations     ranking: semantic on all 30 (no keyword fallback)
relevance (top-5 in labelled country): 24 / 30   (same six misses as S237, for information only)
 FAIL  8 Chitwan jungle safari  2/3    FAIL 15 Kyoto temples 3/4   FAIL 16 Mount Fuji 2/3
 FAIL 24 Chiang Mai 2/4                FAIL 25 Thai cooking class 0/2   FAIL 27 Ladakh monasteries 0/3
distinct destination ids returned: 725 (S237: 724, overlap 723)   sha256_16 of the sorted id set: a0a419e9ccb805bf
```

All 30 queries used the semantic path, which only ranks components with an embedding and keeps a component only when
its source tour is an active, non-deleted AA published tour (`search.py` `ACTIVE_TOUR_SQL`). The DB join over the 725
ids is section 3 of the script below.

## DB: read-only run-script (to be dispatched)

Infra branch `chore/tp-ai-guards-read-script`: `db/scripts/aa805_ai_guards_read.py` (`READ_ONLY = True`), with
`db/tests/test_aa805_ai_guards_read.py`. It prints:

1. `SCRIPT spend …`: `tripplanner.llm_spend_daily` for the last 3 UTC days. `SCRIPT spend_log …`: the same stages in
   `shared.llm_call_log` (cross-check). `SCRIPT spend_today online_usd=<x> cap_usd=5.0 under_cap=<t|f>` (line 3).
2. `SCRIPT cache …` and `SCRIPT cache_total rows= hits= rows_hit=` from `tripplanner.narration_cache` (line 4).
3. `SCRIPT search returned=725 found=<n> without_active_component=<n>` (expect 0), plus `SCRIPT control
   inactive_only_destinations=<n> of_them_returned=<n>` (expect >0 and 0), ending with `SCRIPT verdict
   search_no_inactive=PASS|FAIL` (line 5).
4. `SCRIPT candidates …` and `SCRIPT candidate kind=… component=<id>`: inputs for §3.

The master sees every tenant's `published_tours` (the `cis_owner` policy is `USING true`), so each query names the AA
tenant itself, as well as setting `app.tenant_id`. That way it reads exactly what the TripPlanner Lambda reads. The SQL
was checked against a local PostgreSQL 16 with stub tables in a read-only session: a clean set gave PASS, and an
inactive-only destination plus a not-embedded one gave FAIL with both named.

**Results** (run 39349512417, 20/10/2026 ~00:45Z; full lines in `aa805_db_script_lines.txt`):

```
SCRIPT input returned_destinations=725 sha256_16=a0a419e9ccb805bf
SCRIPT spend day=2026-10-19 stage=tp_search_embed cost_usd=0.000015 calls=34 unpriced_calls=0
SCRIPT spend_log day=2026-10-19 stage=tp_search_embed calls=34 cost_usd=0.000015
SCRIPT spend_today online_usd=0.000000 cap_usd=5.0 under_cap=True
SCRIPT cache_total rows=0 hits=0 rows_hit=0
SCRIPT search returned=725 found=725 without_active_component=0
SCRIPT control inactive_only_destinations=0 of_them_returned=0
SCRIPT control components embedded=3905 embedded_not_active=0
SCRIPT candidates no_structured_text=0 own_day_missing=8
SCRIPT candidate kind=own_day_missing component=01bacbda-c8bd-49ae-9fd1-98d53f71f31d
SCRIPT candidate kind=own_day_missing component=268457fd-1af0-4f6a-89d8-d4b813db748a
SCRIPT candidate kind=own_day_missing component=26d26dc2-579f-4574-9775-90724954979e
SCRIPT candidate kind=own_day_missing component=74bd4aea-bce7-4807-90f3-bf5027f0e2df
SCRIPT candidate kind=own_day_missing component=8574d548-a9fe-4fdf-822f-f4dc8028d70f
SCRIPT verdict search_no_inactive=PASS control_has_inactive_only=False
```

## Test data left on Dev

TripPlanner trips from this run (guest sessions, no customer data, nothing sent to Booking): `eec79780-…`,
`7d819aca-…`, `7341e6dd-…`, `5e1f2e06-…`, `2d4a346e-…`, plus one single-component trip of the "foreign-own-session"
client. Throttle probes used random trip UUIDs and created nothing.
