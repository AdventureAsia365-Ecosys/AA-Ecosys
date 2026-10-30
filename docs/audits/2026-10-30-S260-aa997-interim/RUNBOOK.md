# AA-997 / AA-990 — S260 audit runbook (orchestrator)

Every step is read-only and costs $0: no LLM call, no Geoapify call, no DB write. Each script opens one read-only
transaction as `cis_app` (the container's `DATABASE_URL`, `ssl="require"`) and rolls it back at the end.
Run everything from `/home/nghiep/projects/AA-Ecosys`. ECS exec is for the orchestrator only (the subagent hook blocks it).

| file | what it is |
|---|---|
| `audit_relocated.py` | the audit script you run (built from `audit_relocated.src.py`, with the 600 S254 verified rows embedded, ~105 KB) |
| `audit_relocated.src.py`, `build_audit_relocated.py` | the source and the builder (it reuses `row()` from the S257 interim builder) |
| `recheck_14.py` | AA-990 recheck_14 on current data (the S258 v2 logic, updated for the current chain) |
| `selftest/fake_audit.py` | local test with a fake connection: `apps/AA-CIS-App/.venv/bin/python .tmp-session/S260/aa997/selftest/fake_audit.py audit` (or `r14`) |

## 0. When to run

The chain is not done yet. Day 1 (30/10) processed 830 of 2,221 rows, and the next job is queued for 31/10 00:12Z.
- If you run the audit **before** the chain finishes, the numbers are interim. The `J open` line still lists a queued
  job, and `S left_for_chain` is > 0.
- For the **final** reading, run it once `J open` is `[]` and `S left_for_chain` is 0, or close to it (the rows
  left are ones the job cannot take).
- Running it during a relocate run is safe. It only reads, and the REPEATABLE READ snapshot keeps it consistent.

## 1. Run (preferred: the ecsx wrapper, which returns ALL output through S3)

```
tools/ecs/ecsx.sh .tmp-session/S260/aa997/audit_relocated.py > .tmp-session/S260/aa997/audit-out.txt
tools/ecs/ecsx.sh .tmp-session/S260/aa997/recheck_14.py > .tmp-session/S260/aa997/r14-out.txt
grep -E "^(GATE|R rows|R proxy|L overall|L group|L projection|J open|S left_for_chain)" .tmp-session/S260/aa997/audit-out.txt
grep -E "^(RECHECK14|TOUR)" .tmp-session/S260/aa997/r14-out.txt
```

The default run needs no `VAR=value`. Optional knobs (`tools/ecs/ecsx.sh <script> VAR=value`):
`SINCE=2026-10-30T00:00:00`, `STAMP_V=aa997.2`, `ACCEPT=aa997.3`, `SAMPLE_N=40`, `FULL=1` (one `ROW` JSON line per
processed row, ~2,000 lines, for an offline pass), `MOVE_KM=1.0`, `JOBS_SINCE=2026-10-28`, `SEED=s260`.
⚠️ Several of these names contain underscores (CLAUDE.md "env var corruption" rule). Type them by hand and do not
copy them from rendered Markdown.

## 1b. Fallback: the raw S3-mediated pattern (CLAUDE.md, one line per command)

Use this only if `ecsx.sh` fails. The SSM terminal can drop long stdout, so keep `FULL` off.
```
aws sts get-caller-identity --profile aa365-admin
aws s3 cp .tmp-session/S260/aa997/audit_relocated.py s3://aa-cis-bronze-005097885195/scripts/aa997_audit_relocated.py --profile aa365-admin --region us-west-1
URL=$(aws s3 presign s3://aa-cis-bronze-005097885195/scripts/aa997_audit_relocated.py --profile aa365-admin --region us-west-1 --expires-in 300)
TASK_ARN=$(aws ecs list-tasks --cluster aa-cis-dev-cluster --service-name aa-cis-dev-api --profile aa365-admin --region us-west-1 --query 'taskArns[0]' --output text)
aws ecs execute-command --cluster aa-cis-dev-cluster --task $TASK_ARN --container api --interactive --command "sh -c 'curl -s \"$URL\" -o /tmp/s.py && cd /app && python3 /tmp/s.py'" --profile aa365-admin --region us-west-1
aws s3 rm s3://aa-cis-bronze-005097885195/scripts/aa997_audit_relocated.py --profile aa365-admin --region us-west-1
```
For recheck_14, run the same six lines with `recheck_14.py` / `aa990_recheck_14.py`.

## 2. Reading audit_relocated against the ≥ 90 % bar

**The bar is the `GATE` line**: `GATE AA-997 accuracy flag-strat X% PASS|FAIL (bar 90%); projection Y% (cross-check)`.
It is the S257 interim-audit metric. The 600 rows verified in S254 are re-scored on today's points, with a site
tolerance of 4 km and 5 km for other places, and the result is stratified by flag status. S254 was 75.4 %, and S257
on 29/10 was 77.7 % ±4.1. `L overall` repeats the S254 baseline: it must still print 75.4 % / 74.8 %, or the
re-score is broken. `L projection` is the per-cell projection over every resolved row (S257: ~79.5 %). It is a
cross-check, not the gate.

Read the gate with these rules in mind:
- The re-score counts a wrong pin as wrong (`unchanged_flagged`) even when it now carries `review_reason`
  `llm_point` / `off_route`, or is hidden. Only a moved point that lands within tolerance of the S254 `expected`
  point turns an error into a correct row. The flags make a wrong pin visible, but they do not raise this number.
- `L group chain` is the subset of labelled rows the current chain processed. `L chain_by_outcome` gives correct/n
  per outcome, and `L chain_wrong` lists the regressed or still-wrong ones to read.
- An estimate, not a result: day 1 confirmed 220 of 830 rows (~27 %), and the rest kept the model's point. The S257
  cells were geoapify 93 %, untouched llm 63 % and relocate-flagged 66 %. At those rates the overall figure will
  most likely stay near 80 % when the chain ends. If it FAILs, the levers are the ones in the S257 README §7 (hide
  policy, `mapbox` rows, admin fixes). Pick them from the `R by_country` and `R flags_by_class` lines.

**The proxy block** (`R …` lines, chain rows only, no labels) is the S258 method on the current point:
- `R rows`: n, merged, `by_class` (moved = confirmed and moved > MOVE_KM / confirmed in place / rejected =
  llm_point + off_route + weak_confirm / non_place / unchanged), `by_outcome`, the accept rule in the stamps (it should be
  all `aa997.3`, except `non_place`, which stamps none: `-`).
- `R proxy`: `plausible_confirmed_or_moved` is the share of geocoder-written points that pass every proxy: in
  country (bbox + polygon), on or within a day trip of an anchored route, no `admin_answer`, no `collapse`. It
  should be high, ≥ 90 %. `plausible_rejected_kept_model_point` is how often the model point that was kept still
  looks right. `unjudged` rows have no route to judge against.
- `R flags_by_class`:
  - `reject_unanchored`: an off_route flag with no anchored route. This is the flight / arrival-day class, the 21 of
    the 33 S259 samples. These flags are probably false.
  - `reject_on_route`: the kept point sits on the route.
  - `admin_answer`: a site answered by a city or suburb (Urumqi airport → Urumqi).
  - `collapse`: three or more names on one point (the Irkutsk centroid).
  - `big_move`: a move of more than 100 km.
  - `country_off`: the point is outside its ISO country.
- `R moved_km`: the move buckets, plus `moved_closer_to_anchored_route` (the share of moves that got closer to the
  route; it should be most of them).
- `R changed_since_stamp`: confirmed rows whose point changed after the stamp (an admin fix or a later geocode).

**Line-by-line reading**: each `SAMPLE` line (~40, deterministic by `SEED`, quotas moved 12 / confirmed 6 /
off_route 7 / llm_point 9 / weak_confirm 2 / non_place 3 / unchanged 1; an unfilled quota goes to the biggest
strata) carries tour, day, kind, name, ISO, outcome, old / new point, the geocoder label (name / type / match / sim),
`geo_km`, the route distances (`r_anch` anchored, `r_all` all), flags, `px`, and an `osm` link. Mark each row right
or wrong. To turn the sample into a chain accuracy, take right/n per stratum × that stratum's size from
`R rows.by_outcome` (split confirmed into moved / in place with `by_class`), and divide by the processed pins
(non_place excluded). `WATCH` lines (≤ 30) are moved or confirmed rows the proxy doubts. Read them all: each one is a
possible regression, meaning the geocoder moved a pin to the wrong place.

`geo_km` is the distance from the model's point to the geocoder's point (for confirmed rows, the stamp's `moved_km`).
`llm_point` / `off_route` stamps keep no geocoder coordinate, so it is null there.

## 3. Reading recheck_14

- `RECHECK14 route ok x/16 · all-confirmed y/16 (loose z/16)`. The S257 baseline was route 13/16 and all-confirmed
  1/16. `all-confirmed` is strict (S258 v2): every component and night is linked, `geoapify`/`manual`, not suspect,
  and has no `review_reason`. `loose` is the S257 P3 rule, which allows a `review_reason`.
- `TOUR …` lines show `pending_chain` = places the queued chain will still take. If that is > 0, run again after the
  chain ends.
- `NEED` lines name the next step for each unconfirmed place:
  - `relocate chain pending`: the chain will take it; wait.
  - `chain flagged llm_point|off_route`: the geocoder found no match; fix it in `/admin/places` or apply the hide
    policy.
  - `old-rule flagged … (aa997.1)`: needs a recheck run (`recheck` llm_point/off_route, strategy v2, aa997.3; dry
    run first).
  - `unlinked`, `hidden`, `mapbox`, `flagged <reason>`: admin.
- AA-990 can close recheck_14 only on tours with `route=Y` and `all_confirmed=Y`. List the rest by NEED bucket
  (`SUMMARY.next_steps`).

## 4. Served pins vs all rows, and the hide_flagged lever (S260 lane L11)

`audit_relocated.py` now ends with a `V` section and a `SERVED` line (read-only, $0, same transaction):

```
grep -E "^(GATE|SERVED|V served|V hide_candidates|V accuracy|V projection)" .tmp-session/S260/aa997/audit-out.txt
```

- `GATE` is unchanged: the S257 "all rows" metric. A wrong point counts wrong even when flagged or hidden, so the
  hide pass does NOT move it.
- `SERVED …` is what readers show: destinations present in `catalog.v_tour_component` / `v_tour_stop` /
  `v_tour_place` (they drop suspect + merged rows). A served non-place is an error; a hidden row leaves the
  denominator. Three states: `served_now`, `served_if_hide` (rows the hide_flagged pass would hide: relocate stamp
  outcome in `HIDE_OUTCOMES`, still flagged, still on the model's point), `served_if_hide_np` (+ the opt-in non_place
  hide). Each gives correct ±CI, error, labelled n and `coverage` (served share of the population). `V projection`
  is the cell projection over the served population of each state.
- `V served.source` says which views cis_app could read; `fallback_linked_rows` = no view readable, every linked
  destination counted (live or not). `V served.hide_sql` says whether the deployed `relocate._HIDE_FLAGGED_SQL` or the
  audit's copy was used (identical text; after the CIS deploy it is the deployed one).
- Knobs (type by hand, underscores): `HIDE_OUTCOMES=llm_point,off_route` (add `weak_confirm`), `HIDE_STAMP_V=aa997.2`
  (empty = any version), `HIDE_ACCEPT=aa997.3` (empty = any).

### The hide_flagged pass (after the CIS PR is deployed; no paid call, no model call)

All through `POST /admin/places/relocate` (admin BFF or the admin secret; ops.write). Each call queues one
`place_relocate` job; read its result with `GET /admin/job-runner/jobs/{id}`.

1. Report (no write): `{"mode":"hide_flagged"}` — defaults `outcomes` = llm_point + off_route, any stamp version,
   any accept rule, all countries. Narrow with `"stamp_versions":["aa997.2"]`, `"stamp_accept":"aa997.3"`,
   `"country":"India"`, `"outcomes":["llm_point","off_route","weak_confirm"]`. Result: `rows`, `linked`,
   `by_country`, `by_outcome`, `by_reason`, `by_stamp_version`, `by_located_by`, `restored_skipped` (rows a person
   restored: never hidden again by this pass), 25 `samples` spread over countries.
2. Read the samples (osm links: lat/lng in each sample), then confirm with THE SAME selection:
   `{"mode":"hide_flagged","confirm":true}` (+ the same narrowing keys). 409 when the latest report has another
   selection. The job refuses `refused_selection_grew` when more rows match than that report (the chain added rows
   since): run the report again. Result: `hidden`, `changed_since_report`, `audit_rows` (one acp_shared.audit_log row
   per 100 rows, action `places.relocate.hide_flagged`, with the ids). It queues `tour_graph_build`.
3. Undo: all rows → `{"mode":"unhide","by":["aa997.3-flagged"]}` (optionally `"country"`); one row (the review
   list restore) → `{"mode":"unhide","destination_ids":["<uuid>"]}`. By stamp, only rows still flagged for the reason
   they were hidden are reverted (`kept_reason_changed` counts the others); an explicit `destination_ids` restore
   reverts its rows whatever the reason now (`restored_reason_changed`). The stamp keeps `unhidden_at` /
   `unhidden_by`; audited (`places.relocate.unhide`).
4. A restore lasts: later hide_flagged reports / confirms skip rows a person unhid (`restored_skipped`) until a
   relocate run judges the row again (its relocate stamp newer than `unhidden_at`). After a mistaken bulk undo the
   rows therefore stay shown until the next relocate pass re-judges them.
5. A hidden row that a later relocate run confirms (recheck) is shown again automatically (`unhidden_by`
   `relocate:confirmed`). One the recheck flags again with another reason (the aa997.1 `llm_point` / `off_route`
   rows of §3: llm_point → off_route / non_place:*) stays hidden and its hide stamp takes the new reason
   (`reason_was` / `reason_by` keep the change), so step 3 still reverts it. The recheck of §3 can therefore run
   before or after this pass. There is no point-edit screen in /admin/places today, so the single-row restore is the
   `destination_ids` unhide above.

Run the audit again after step 2: `SERVED … now` should then read what `if hide_flagged` read before.

## 5. Confirm rules after the S260 review fixes (CIS #1178)

- A `hide_flagged` confirm needs a **succeeded report younger than 6 h** with the **same selection** (outcomes,
  stamp_versions, stamp_accept, country, **located_by** — default `["llm"]` only; Mapbox rows are left alone unless
  asked), and **no `place_relocate` apply queued or running** (409 `apply_job` otherwise: wait for the chain to end).
- Confirm hides only rows that are in both the report and the current selection with an unchanged digest; the result
  lists `dropped_ids` and `new_since_report` (never hidden).
- Restore one row: `{"mode":"unhide","destination_ids":["<uuid>"]}` → `unhidden_by = restore:<actor>`, sticky
  (later hide passes skip it until a newer relocate judgement). A bulk unhide (`by` stamp) writes `unhide:<actor>` and
  is NOT sticky, so a mistaken hide can be rolled back and redone.
