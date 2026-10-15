# AA-805 live evidence (S237, lane tripplanner item 1)

- **Agent:** Claude Code (sub-agent, task tp-805). **Date:** 2026-10-14, 15:38–15:50 UTC.
- **Targets:** TripPlanner prod alias `https://aa-tripplanner.vercel.app` (BFF `/api/browse`, `/api/trip`),
  TripPlanner API GW `9vqkfbukvh` (read-only AWS describe), Booking Dev API
  `https://9z3xnalp59.execute-api.us-west-1.amazonaws.com/dev` (git_sha `4063c3a`, task def `aa-booking-dev-api:6`, staff
  token from the CIS E2E admin; the secret was read into memory only and never printed).
- **Deployed TripPlanner code:** `main` 8149f46 (#74); assembly Lambda LastModified 2026-10-14T13:04:16Z.
- **Rules kept:** HTTP + read-only AWS only. No Lambda invoke, no AWS writes, no DB access.
- **LLM spend in this run:** 30 `tp_search_embed` query embeds (< $0.01) for the search set. No `/narrate` call reached the
  model: every `/narrate` call was on an empty trip (400 before any model call) or from a foreign session (403).

## Booking E2E window (tell the Booking lane)

| Event | UTC |
|---|---|
| E2E start (apply-route) | **2026-10-14T15:47:14Z** |
| Send to advisor answered 200 | 2026-10-14T15:47:16Z |
| Booking case TC-000002 created by the intake poller | 2026-10-14T15:48:20Z |
| E2E end (case read back) | **2026-10-14T15:49:04Z** |

Booking ran `aa-booking-dev-api:6` (rollout COMPLETED) the whole time. The Booking lane can now deploy bk-007.

## Verdict per Done-when line

The issue's Done-when: *"Throttle + ownership + cap verified live; cache hit rate visible; search returns no inactive
tours on a 30-query labelled set (Claude panel); outbox payload version 1.1."* The S237 lane plan adds: Booking legs in
ascending day order and the AI-assisted label.

| # | Line | Verdict | Evidence |
|---|---|---|---|
| 1 | Throttle live | **Config PASS; 429 behaviour not captured** | §1 |
| 2 | Session ownership live | **PASS** | §2 |
| 3 | Spend cap live | **Partly: config shown; `llm_spend_daily` rows still need a DB read** | §3 |
| 4 | Cache hit rate visible | **Open: documented in README; the two-call live proof was not run** | §4 |
| 5 | Search: 0 inactive tours on the 30-query labelled set | **Partly: live run 30/30 HTTP 200 is saved; the inactive-tour join needs a DB read** | §5 |
| 6 | Outbox payload version 1.1 | **PASS** | §6 |
| 7 | Booking legs in ascending day order (S235 bug) | **PASS** | §6 |
| 8 | "AI-assisted" label | **PASS** | §7 |

No Done-when line **failed**, so this branch changes no code. It adds the labelled set, a shape test for it and a README
section on how to read the guards. Lines 1, 3, 4 and 5 still need a step that this sub-agent could not take (see
"Still needed"). **AA-805 must not be set to Done yet.**

---

## 1. Throttle

Read-only `aws apigatewayv2 get-stages --api-id 9vqkfbukvh` and `get-routes`:

```
$default  DefaultRouteSettings  rate 500 / burst 1000
          RouteSettings  "POST /trip/{trip_id}/narrate"  rate 2.0 / burst 5
                         "GET /browse/search"            rate 10.0 / burst 20
          LastUpdated 2026-10-14T11:27:46Z   (Infra #103)
routes:   POST /trip/{trip_id}/narrate -> integrations/txthbva (assembly)
          GET /browse/search            -> integrations/yz5o60b (browse)
          ANY /trip/{proxy+}, ANY /browse/{proxy+}
```

The throttled routes exist as their own route keys, so the route settings apply. A route setting has no effect when only
the `{proxy+}` route exists. Account Lambda concurrency is still **10**, because the quota case is still open.

**Behaviour not captured.** At 15:42:23Z a burst of 12 parallel `/narrate` calls was sent to an empty trip
(`6b6dbe88-…`, no model call possible). The status codes were not collected, and the auto-mode permission classifier
blocked the repeat run that would have counted them. To close this line, Nghiệp (or the orchestrator) runs one burst of
about 10 parallel `POST /api/trip {"op":"narrate"}` calls on an empty trip and expects a mix of `400 empty_trip` and `429`.

## 2. Session ownership: PASS

```
trip 537dd314-ce28-434c-9a30-953065f2acb5   owner session 628a66cc-…   foreign session 8c71f93b-…   15:43:00Z
POST /api/trip {"op":"add", owner, component c938e068-… (Paro)}        -> 200
POST /api/trip {"op":"narrate", foreign session, "mode":"compose"}     -> 403
{"error": "forbidden", "detail": "this trip belongs to another session"}
```

The check runs before any itinerary read or model call (`backend/assembly/handler.py` `_trip_owner`).

## 3. Spend cap

- `aws lambda get-function-configuration aa-tripplanner-dev-assembly`: `TP_DAILY_SPEND_CAP_USD` is **not set**, so the
  code default **5.0 USD/day** applies to `tp_compose` + `tp_search_embed` (`backend/config.py:111`,
  `llm_gateway.ONLINE_STAGES`). `NARRATION_CACHE_TTL_HOURS` is not set either, so the default is 168 h.
- Today's `tripplanner.llm_spend_daily` rows and `budget_status()` can only be read in the DB, and this sub-agent did not
  run a DB read. Still needed: read `day, stage, cost_usd, calls, unpriced_calls` for the last 3 UTC days, then compare
  today's sum over the two stages with 5.0. Today's 30 search embeds plus earlier traffic should show non-zero
  `tp_search_embed` calls.
- The "over the cap" path (search 503, narration `ai_budget_exhausted`) is covered by unit tests only. Forcing it live
  would need a Lambda env change, which is an AWS write and out of scope.

## 4. Cache hit rate

- README now has the section "Reading the AI guards (AA-805)". It names the SQL surface (`tripplanner.narration_cache`:
  rows, `sum(hits)`, rows with `hits > 0`, `max(last_hit_at)`) and says that a cached `/narrate` answer carries
  `"cached": true`.
- **Live proof not run.** The plan was to ask the owner session of trip `537dd314-…` for `/narrate` twice and expect
  `cached:false` then `cached:true`. The auto-mode permission classifier blocked that call, so it was not run in any other
  form.
- **Trap for whoever runs it:** a whole-tour apply-route (for example the Bhutan 7-day trip) is narrated entirely from AA
  master day text (`source: master`). Master text is **never cached** (`narration_cache.CACHEABLE_SOURCES = (llm, mixed)`),
  so that trip can never show a hit. Use a trip where at least one day has no master text (`source` `llm`/`mixed`). Each
  such call costs about $0.01–0.02 on `tp_compose`.

## 5. Search: 30-query labelled set

- Set: `backend/tests/fixtures/search_labelled_30.json` in the TripPlanner repo (branch `chore/aa-805-evidence`). It has
  30 queries over the 11 planner countries (place, activity and theme queries), each labelled with expected countries
  and a minimum top-5 hit count. **Labelled by one Claude Code agent, not a panel.** Say so in the Linear comment, or run
  a panel later.
- Runner: `aa805_search_run.py` (in this folder). It uses the public BFF only, one request at a time.
  Raw output: `aa805_search_results.json`. Run 15:44:20Z–15:46:41Z.

```
ok_200: 30 / 30      every query returned 60 destinations
relevance (top-5 in labelled country): 24 / 30
 FAIL  8 Chitwan jungle safari   Laos, Nepal, Sri Lanka, Nepal, India
 FAIL 15 Kyoto temples           Japan x3, then Nepal, South Korea   (3/4)
 FAIL 16 Mount Fuji              Japan x2, Laos, China, Taiwan
 FAIL 24 Chiang Mai              Thailand, Laos, Laos, Thailand, Laos
 FAIL 25 Thai cooking class      all Laos ("Tamarind Cooking Class" …)
 FAIL 27 Ladakh monasteries      Bhutan/Nepal monasteries (no Ladakh place in the planner)
```

  Relevance is **not** a Done-when criterion and is reported for information only. The misses are catalog coverage
  (Chitwan, Ladakh and Fuji are thin or missing, and Thailand has 248 components against Laos's 428), not a ranking bug.
  This is input for AA-712 / the CIS place pipeline.
- **Inactive-tour check: not done here.** `/browse/search` returns destinations, not tours, and no HTTP surface maps a
  destination to its source tours. The check needs one read-only query over the 30 runs' destination ids (the
  `destination_ids` arrays in `aa805_search_results.json`, 0 violations expected): each returned destination must have
  ≥1 component with an embedding whose `source_tour_id` is a `gold_aa_internal.published_tours` row with
  `master_status = 'active' AND deleted_at IS NULL`. Run it under the AA tenant, `app.tenant_id` = `00000000-…-0001`.
  Add a negative control: count the destinations whose embedded components all belong to inactive or deleted tours, and
  confirm that none of them is among the returned ids. This sub-agent wrote no script that reads the DB credentials,
  because the permission classifier refused it. The orchestrator runs the query with its usual ECS-exec pattern.

## 6. Booking E2E: legs in day order + payload version 1.1: PASS

```
GET /api/browse?resource=routes&country=Bhutan&days=7  -> 200, proposal 1 = whole tour 22174c35-… "Bhutan: Mountain Walks & Valleys — 7 Days"
trip af88e0d8-3df7-42f3-b74e-09e6103bec33
POST /api/trip {"op":"apply_route", 5 component ids in day order}  -> 200
  day 1 Kuenselphodrang statue  (tour day 1)
  day 2 Tashichhodzong          (tour day 2)
  day 3 Haa valley              (tour day 3)
  day 4 Haa valley              (tour day 4)
  day 5 Chele La Pass           (tour day 7; tour days 5-6 have no component)
POST /api/trip {"op":"send", customer "S237 E2E Test" <e2e-s237+booking@adventure.asia>, consent}  -> 200
  {"status": "sent", "handoff_id": 139, "already_sent": false}

Booking GET /booking/trip-cases?source=tripplanner  -> TC-000002 new_inquiry 15:48:20Z (TC-000001 = S235)
Booking GET /booking/trip-cases/TC-000002:
  legs: position 1  tour 22174c35-…  day_from 1  day_to 4
        position 2  tour 22174c35-…  day_from 7  day_to 7
  inquiry_snapshot.contract_version: "1.1"
  inquiry_snapshot.days: 1 Kuenselphodrang statue, 2 Tashichhodzong, 3 Haa valley, 4 Haa valley, 5 Chele La Pass
```

- **Leg order:** positions 1→2 follow day_from 1→7. In S235 (TC-000001) the same route gave positions with days 3–4, 7,
  2, 1. The fix from #71 holds live. Day 7 is its own leg because tour days 5–6 have no pinned component, which is the
  expected shape. The Booking API sorts legs by `day_from, position`, so the check above is that both orders agree.
- **Payload version:** Booking stores `contract_version` from the payload's `version`. It reads "1.1" (TC-000001 was "1"),
  and Booking `SUPPORTED_VERSIONS = ("1", "1.1")`. The outbox column `tripplanner.outbox.schema_version` stays the
  integer major (1) by design (implementation notes, S236).
- The Booking side is read through its staff API (HTTP). Inbox status and the raw outbox row were not read, because they
  are DB-only. The case would not exist unless the inbox event had been processed.
- Test data left on Dev: TripPlanner trips `af88e0d8-…` (sent), `537dd314-…`, `6b6dbe88-…` (empty), Booking case
  **TC-000002** and its lead customer "S237 E2E Test". Archive or keep them as E2E fixtures as Nghiệp prefers.

## 7. AI-assisted label: PASS

```
curl https://aa-tripplanner.vercel.app/       -> 200, contains "AI-assisted" (header pill + title
                                                 "Suggestions, search and some narration are AI-assisted. An Adventure Asia advisor reviews every trip.")
                                                 and the trust strip "AI-assisted itineraries, reviewed by advisors"
curl https://aa-tripplanner.vercel.app/plan   -> 200, same header pill + title
```

The `/narrate` response also carries `ai_generated` (source `llm`/`mixed`).

---

## Still needed before AA-805 can be set to Done (orchestrator / Nghiệp)

1. **Throttle 429:** one burst of about 10 parallel narrate calls on an empty trip. Expect some 429 responses. $0.
2. **Cache hit:** two identical `/narrate` calls by the owner on a trip that has at least one non-master day. Expect
   `cached:false` then `cached:true`, and `narration_cache` showing `hits > 0`. About $0.02.
3. **DB read (read-only, ECS exec):** today's `llm_spend_daily` against the 5.0 cap, the `narration_cache` summary, and
   the inactive-tour join plus negative control over `aa805_search_results.json`. Optionally also the TC-000002
   `booking.inbox_events.contract_version`.
4. Post the evidence comment on AA-805 (lines 2, 6, 7 and 8 pass now; add 1, 3, 4 and 5 when done). Set Done by hand.
