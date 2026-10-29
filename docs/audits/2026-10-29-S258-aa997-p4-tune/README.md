# AA-997 — tuning the strict geocode rule on the P4 sample (S258)

Session S258, 29/10/2026. Agent: Claude Code (AA-997 lane). Issue: AA-997 (input to AA-990 `recheck_14`). Cost: $0
(no LLM call, no geocoder call, no DB write).

**Status: rule `aa997.3` is written and unit-tested, but it is NOT measured on the real sample yet.** The P4 sample
(the routes of each verified row) is only in the database, and this lane cannot run ECS exec. This folder has the
read-only dump and the offline sweep. Both were run end to end on synthetic data and on an in-memory copy of the
tables, and the rebuild matched the deployed code (`REPRO` 0 mismatches). The live numbers go in §4 after the
orchestrator runs the runbook (root `.tmp-session/S258/aa997/RUNBOOK.md`).

| file | what it is |
|---|---|
| `README.md` | this report |
| `build_p4_dump.py` | builds `aa997_p4_dump.py` from the committed S257 interim audit script |
| `aa997_p4_dump.py` | READ-ONLY ECS-exec script that dumps the P4 sample as gzip+base64 JSON lines |
| `p4_tune.py` | the offline evaluator: decodes the dump, rebuilds the routes, checks it matches production, then sweeps the rule knobs |
| `selftest_fake_dump.py` | a local harness: runs the dump script against an in-memory copy of the tables |
| `p4_sample.json`, `p4_tune_out.txt`, `p4_tune_summary.json` | added after the live run |

## 1. Starting point (S257 re-audit, part P4)

`relocate.rejudge`, the deployed strict rule `aa997.2` with live routes, was run over the S254 verified rows that
Geoapify now locates:

| | n | refused | share |
|---|---|---|---|
| correct rows | 251 | 34 | **13.5 %** (gate ≤ 2 %) |
| wrong rows | 30 | 5 | 16.7 % |

Correct rows refused, by reason: `off_route` 17, `ambiguous_route` 10, `site_type` 4, `name` 3. Wrong rows refused:
`site_type` 3, `ambiguous_route` 1, `off_route` 1. Correct rows refused, as samples: Malabar Hill, Chawri Bazaar,
Karol Bagh market, Delhi Airport, Lahore GPO and Pingyao (`off_route`); Hong Kong, Dolma La, Mount Kailash and
Doi Tung (`ambiguous_route`); Horombo Hut (`site_type`); "agricultural flatlands surrounding Yangpyeong" (`name`).

## 2. Root cause (from reading the code)

A route is built from the located overnight stops of days d-1..d+1 of every tour day that uses the name
(`store.route_anchors`), and the row itself is left out. It shows where the place is only when day d has **its own**
located night stop. Without that stop, the route is just the neighbouring nights, and the distance measures travel:

- **departure or arrival day**: Delhi Airport. The last day has no night, so the route is the night before in
  Jaipur, about 240 km away. aa997.2 refuses anything more than 150 km off the route;
- **flight or overnight train**: Pingyao, and the city sites of tours that arrive by train;
- **trek nights at huts with no located point**: the Kailash kora and Dolma La. The route becomes Saga or Lhasa,
  400–1,000 km away, which looks like a homonym to `ambiguous_route`;
- **the place is that night's stop**: Hong Kong. It is left out of its own route, so the route is the nights before
  and after, hundreds of km away.

The homonyms the checks were written for (Xi'an's Bell Tower on a Beijing key, Mumbai's Princess Street on a Kochi
tour) do have the day's own night stop on the route.

The 3 `name` refusals come from a different gap. The re-judge re-applies v1's name check to the stored answer, but it
cannot rebuild the text that was judged. One case is a Korean name accepted on its native-script query, where Latin
tokens give similarity 0. v1 passed these answers when it accepted them.

## 3. Rule `aa997.3` (CIS branch `feat/aa997-rule-v3-tune`, commit `dfff53d2`)

aa997.3 runs the same checks as aa997.2, with these knobs set (`geomatch.StrictParams`):

| knob | aa997.2 | aa997.3 | effect |
|---|---|---|---|
| `anchored_only` | off | **on** | `ambiguous_route`, `hint_disagree` and the re-judge's off-route check only use routes that include the day's own located night stop (`guards.TourRoute.anchored`) |
| `rejudge_off_route_km` | 150 | **300** | the re-judge's off-route check uses the homonym distance (`AMBIGUOUS_ROUTE_KM`) |
| `rejudge_v1_checks` | on | **off** | the v1 name and type checks become `unjudged` (`kept_unjudged`, no re-search) instead of refused |
| `per_tour`, `ambiguous_km`, `ambiguous_miss_div`, `site_admin_named` | — | unchanged | swept by `p4_tune.py` only |

`site_type` stays as it is. In S257 it refused 4 correct rows and 3 wrong ones, so dropping it would lose most of the
wrong-row catches.

**Expected result, before the live sweep.** The anchored-route rule targets the 27 route refusals (17 + 10), and
turning off the v1 re-check removes the 3 `name` refusals. If all of the route refusals belong to the gap classes
above, the correct rows refused fall to the 4 `site_type` rows: 4 / 251 = 1.6 %, which passes. The wrong-row catches
would be the 3 `site_type` rows plus whichever route catches had anchored routes. **This is an estimate.**
`p4_tune.py` prints the measured numbers.

The rule sits behind the same switches as aa997.2: `accept_rule` (`place_relocate` payload and endpoint) and
`GEOCODER_ACCEPT_RULE` (new names). Both default to `v1`. `relocate.RULE_VERSION` stays `aa997.2`.

## 4. Live result (to fill in from `p4_tune_out.txt`)

| rule | correct refused | wrong refused | gate |
|---|---|---|---|
| aa997.2 (deployed; must match S257: 34/251, 5/30) | {{V2_C}} | {{V2_E}} | FAIL |
| aa997.3 (branch preset) | {{V3_C}} | {{V3_E}} | {{V3_GATE}} |
| best variant in the sweep | {{BEST_C}} | {{BEST_E}} | {{BEST_GATE}} ({{BEST_KNOBS}}) |

`REPRO` line: {{REPRO}}. aa997.3 still refuses these correct rows: {{V3_STILL}}. Wrong-row catches lost compared with
aa997.2: {{V3_LOST}}.

How to decide:
- `P4 GATE aa997.3 PASS` with no important lost catch → the CIS PR can merge.
- FAIL with a passing `BEST` → set `STRICT_PARAMS[ACCEPT_RULE_V3]` in `services/places/geomatch.py` to the BEST
  knobs, run `tests/unit/test_aa997_v3_rule.py` again, then run the sweep again.
- No passing variant → leave aa997.3 off and send the refused rows to the hide policy / review list instead.

## 5. Method (`p4_tune.py`)

1. **Dump** (read-only, `aa997_p4_dump.py`, login `cis_app`, one `READ ONLY` transaction that is rolled back): the
   S257 interim re-score of the 600 verified rows (part 2, unchanged) picks the rows that are correct or wrong today
   and located by `geoapify`. For each row the dump records:
   - the destination row, with `geocoder_meta` cut down to the keys `rejudge` reads;
   - the name keys (`relocate._keys_by_destination`);
   - every overnight anchor for days d-1..d+1 of each (tour, day) that uses a key, with its `located_by`, suspect,
     merged and line flags;
   - the routes and the re-judge outcome that the **deployed** code produces.
2. **Rebuild check (`REPRO`)**: the script rebuilds the routes from the raw anchors the same way the deployed code
   does: trusted anchors only, the batch's rows left out, repeated consecutive stops dropped. The routes and the
   aa997.2 outcomes must match the deployed ones exactly before the sweep counts.
3. **Sweep**: 576 knob combinations. For each, the script counts correct rows refused (gate ≤ 2 %) and wrong rows
   still refused. Passing variants are ranked by most wrong rows caught, then fewest correct rows refused, then fewest
   knob changes.
4. **Diagnostics**: for every correct row aa997.2 refuses, the script prints the reason, how many of its routes are
   anchored, and the distance to the nearest route (all routes and anchored only).

Limits:
- The sample is small, with 30 wrong rows, so one catch is 3.3 points. The S254 labels are reviewer judgements, and
  the expected points are approximate.
- A tune on the labelled sample can overfit. Before switching the rule on, the census over every native Geoapify row
  (lesson AA-985 / AA-779: after loosening a check, look at what it now wrongly keeps) is the dry run in §6.

## 6. After the CIS deploy (orchestrator)

- Census, report only (no call, no write): `POST /admin/places/relocate`
  `{"mode":"dry_run","located_by":["llm"],"recheck":["geoapify"],"accept_rule":"aa997.3"}` and the same request with
  `"aa997.2"`. Compare `rejudge_confirmed.refused` / `refused_by` across the ~4,000 native rows.
- Only after both P4 PASS and the census are read: use `accept_rule: "aa997.3"` for the `confirmed` recheck, or set
  `GEOCODER_ACCEPT_RULE=aa997.3` for new names (⚠️ the env name contains underscores: set it in the task
  definition).

## 7. The queued relocate job and AA-990

- The job `place_relocate` queued for 30/10 00:13Z belongs to the aa997.1 chain. S256 re-queued it at the credit
  stop, before the aa997.2 deploy, so its payload has no `rule_version`. The deployed code (`RULE_VERSION`
  `aa997.2`) refuses it with `refused_rule_version_changed`. It stops without sending a request or writing anything,
  and this branch does not change that. The ~2,221 untouched `llm` rows then need a **new** dry run followed by an
  apply. Check script: root `.tmp-session/S258/aa997/check_relocate_queue.py`.
- AA-990 `recheck_14` needs the places of the 14 + 2 tours to be geocoder-confirmed. S257 found route 13/16 and
  all-confirmed 1/16. What helps: (a) the new relocate chain for untouched `llm` places; (b) a strategy-v2 recheck of
  `llm_point` / `off_route` places; (c) fixing the rest by hand in `/admin/places`. The script
  `.tmp-session/S258/aa997/recheck_14_v2.py` lists every unconfirmed place of each tour and which of these routes it
  needs, using TripPlanner's day denominator.
