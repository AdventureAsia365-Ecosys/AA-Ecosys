# AA-847 — places L4 read model, parity, content validity, `PLACES_SOURCE=cis` flip (S246)

Agent: Claude Code. Evidence folder for AA-847 (plan slices A–H). Code lives in the app and Infra repos; this
folder holds the tools that only the orchestrator runs and the outputs they produce.

## Files

| File | What |
|---|---|
| `gen_probe_sql.py` | Copies the TripPlanner reader SQL (browse + assembly, legacy + cis) into the AA-CIS-Infra probe between markers, with the TripPlanner commit (`ast`, no import). Works on TripPlanner before and after slice 6c. `--check` diffs. |
| `http_parity.py` | Through the TripPlanner BFF (no secret): every browse reader with a cache-buster, ≤ 8 searches (Cohere quota), 20 seeded AA-674 pin sets on fresh guest drafts (coverage, suggestions, activities; **never** hand-off / inquiry; narration only with `--narrate`), `compare` legacy vs cis, `burst` (no search, rate-capped). |
| `probe-*.txt` | (to add) `SCRIPT` lines of each probe run: baseline, after CIS 253, after the paid run, after the flip. |
| `http-*.json`, `burst.json` | (to add) the HTTP runs and the post-flip burst. |
| `validity-*.json`, screenshots | (to add) `/admin/places` snapshot before / after the fixes; `/`, `/destinations/laos`, `/destinations/vietnam`, `/plan` after the flip. |

## Branches (all local, pushed by the orchestrator)

| Repo | Branch | Content | Merge when |
|---|---|---|---|
| AA-CIS-Infra | `feat/aa-847-places-probe` | probe + component id-map fill (dry run) + tests + notes | first (baseline probe) |
| AA-CIS-Infra | `feat/aa-847-catalog-253-copy` | CIS 253 byte copy | after review; then DB Migrate check / apply |
| AA-CIS-Infra | `feat/aa-847-tp017-copy` | TripPlanner tp-017 byte copy | after the TripPlanner tp-017 PR |
| AA-CIS-Infra | `feat/aa-847-contract-pins` | pin `catalog.graph.v1.1`, register TripPlanner's `catalog.tour.v1.1` copy | right after TripPlanner 6c merges |
| AA-CIS-Infra | `feat/aa-847-cis-254-copy` | CIS 254 copy + rules / owners annotations | after the flip + burst |
| AA-CIS-App | `feat/aa-847-places-validity` | slice C (validity gate, fixes, `/admin/places`) + notes | any time; deploy before the paid run |
| AA-CIS-App | `feat/aa-847-places-l4` | CIS 253 + test | after 253 is applied on Dev |
| AA-CIS-App | `feat/aa-847-revoke-tp-raw-grants` | CIS 254 + test | after 254 is applied (after the flip) |
| AA-TripPlanner-Web | `feat/aa-847-tp017-component-id-map` | tp-017 + replay tests | before 6c; apply via DB Migrate |
| AA-TripPlanner-Web | `feat/aa-847-slice-6c` | slice 6c + map precision / attribution + AA-674 property test | after 253 and tp-017 are applied |
| root | `feat/aa-847-places-l4` | this folder, contract `catalog.graph.v1.1`, ownership doc, ADR 0007 amendment | any time |

## Order (the flip window is back to back)

1. Probe baseline (`run-script`, read-only) → save `probe-baseline.txt`; read the parity / qual lines.
2. 253: review → Infra copy → `check` → `apply` (idle) → merge `bot/db-schema-reference` → probe again: every
   `SCRIPT fingerprint` equal to the baseline, timings re-read. Iterate with CIS 255+ (barrier off on graph views,
   graph.v1.1 columns, expression index) only if the probe says so.
3. Slice C deploy (api + worker, same SHA) → `/admin/places` verify → fixes for Laos (dry run, then apply) → report.
4. tp-017: TripPlanner PR + Infra copy → apply. Then TripPlanner 6c merges and deploys (no-op while `legacy`).
5. Paid place run (AA-905; quote first, 3-tour trial, ≤ 50 per batch, not during HTTP parity) → validity fixes →
   graph build → probe: `coverage_gate missing_in_cis_live=0`, parity green on post-run data.
6. Flip window: fill dry run → fill apply PR (`READ_ONLY = False`) → Terraform `tripplanner_places_source = "cis"`
   (Nghiệp types the lines, AA-CIS-Infra notes) → CDN invalidation → `http_parity.py run --label cis`, `compare`,
   `burst` → screenshots. Rollback: `legacy`.
7. 254: Infra copy → apply; CIS PR merges.

## Done-when mapping

1. Parity after L4: probe `SCRIPT parity` (target max(1.5 × legacy, 200 ms), S237 aggregation), re-confirmed after
   the paid run; real HTTP 200 on cis proven right after the flip (`http_parity.py compare`). The probe replaces the
   S237 parity runner (cannot run since X1 S19).
2. Report live on `/admin/places`, every duration mismatch listed with a reason code (`ranged_heading`,
   `missing_day_numbers`, `duration_text_vs_days`, `extra_days`).
3. No duplicate and no trail pin on the HCM Trail and Kuang Si tours: probe section 4 on the cis views after the
   fixes + a TripPlanner screenshot after the flip. Gate = `summary.gate.pass` on `/admin/places` for those tours'
   countries: the blocking reason codes are `near_duplicate`, `linear_feature`, `area_feature`
   (`validity.GATE_REASONS`); `same_destination_names` (one pin, several spellings — what Kuang Si becomes after the
   dedupe), V1 duration and V4 day text are informational and never block.
4. `cis` live on **both** Lambdas (TripPlanner CONTEXT: the component ids change, so browse and assembly flip
   together), post-flip parity, the four pages 200 with screenshots.
5. **Open until Nghiệp approves the change of acceptance criteria.** Proposed replacement of the 7-day window (Dev:
   no waiting): the post-flip burst with 0 rows of `aa-tripplanner-dev-browse-throttles` and 0 Lambda Errors over
   the run window, and no rollback.

## Waiting on Nghiệp

- Linear-feature display: proposed **hidden** (no pin, no circle; name kept in the day text); area features drawn as
  areas. One constant to flip if a circle is preferred. Hiding is global (`shared.destinations.geo_status =
  'suspect'`) and sticky: every re-locate of a linear-feature name hides it again (`store._write_point`). If the
  circle option wins, flip the constant and undo the hide fixes already applied; to un-hide one place, an admin sets
  it `manual`, or the next locate re-hides it.
- Approve the paid-run quote (AA-905).
- Type the Terraform `tripplanner_places_source` / `PLACES_SOURCE` lines (underscore names).
- Amend Done-when line 5 as above.
- Whether CIS 254 also revokes 216 (`v_active_tour_atoms`, no TripPlanner reader left).
