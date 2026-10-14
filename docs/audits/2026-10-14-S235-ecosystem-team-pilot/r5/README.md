# S235 T9 checkpoint r5 — prepared, NOT run

This round writes n=20 pieces on the same 6 requests and angles as S234 r4. It verifies AA-776, AA-786, AA-774, AA-773 and AA-775 live (plus AA-785), and compares with S234 r1–r4.

The paid steps are the orchestrator's. The scripts here were only compiled and dry-run locally ($0).

| File | What | Paid? |
|---|---|---|
| `r5_run.py` | Driver: `init`, `preflight`, `regen` (Terra LinkedIn angles), `write --trial 3`, `write`, `status`, `cancel`. Hard stop at **$1.50** cumulative. State is kept in `checkpoint_r5.json`. | regen ~$0.02; writes ~$1.15 |
| `r5_export.py` | Read-only export of the pieces through S3 + ECS exec (SELECT in a read-only txn). Output goes to S3 JSON, then to `pieces_<label>.json`. | $0 |
| `r5_measure.py` | Deterministic metrics, r4 vs r5, with targets (met / not met). | $0 |
| `r5_panel.md` | Panel brief: 4 lenses, fidelity, and product-truth (reverse flips). Runs as local agents. | $0 |

**How it runs ("chạy bằng gì").**
- Every piece goes through the real tenant path, `POST /v1/content-writing/requests/{id}/write`, as a `t9_write` job on **aa-cis-dev-worker**.
- The Terra regen goes through admin `regenerate-angles` as a `t8_angles` job on the worker.
- The laptop only enqueues and polls. Nothing runs inside the api task except the read-only export SELECT.

## Run order (all from WSL, one-line commands)

```bash
cd /home/nghiep/projects/AA-Ecosys/.tmp-session/s235/r5
export CQ_SECRET=$(aws secretsmanager get-secret-value --secret-id aa-cis/dev/admin-secret --profile aa365-admin --region us-west-1 --query SecretString --output text)
```

0. **Pre-conditions (orchestrator).**
   - AA-773 and AA-775 are merged and deployed. AA-774/776/785/786 are already on main.
   - Deploy Dev reached COMPLETED on api AND worker, at the same SHA.
   - Record whether AA-785/786 went in first.
   - Do not deploy anything while r5 jobs run.
1. `python3 r5_run.py init` — creates `checkpoint_r5.json` from `../../s234/checkpoint_r4.json`: the same 6 request_ids and chosen angles, and 0 pieces. $0.
2. `python3 r5_run.py preflight --expect-sha <merged main sha>` — checks that `/admin/job-runner/deploy-gate` shows 0 queued/running jobs, that api and worker run the same image, and that rollout is COMPLETED. $0. **Stop if it fails.**
3. Baseline export (read-only, $0). Use `--label r4` so it does not overwrite r5 files:
   `python3 r5_export.py --state ../../s234/checkpoint_r4.json --label r4 --out pieces_r4_full.json`
4. `python3 r5_run.py regen` — regenerates the Terra LinkedIn angles (~$0.02) and chooses the recommended one. It prints the old and the new angle; record it as the confound.
5. `python3 r5_run.py write --trial 3` writes 3 pieces: Terra LinkedIn on the new angle, an A&H blog, and a Trail Pulse LinkedIn. Cost is ~$0.20; it takes ~5–10 min. Then **STOP and check the trial**:
   - `python3 r5_export.py --label r5_trial --out pieces_r5_trial.json`
   - `cd /home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App && ENVIRONMENT=test PYTHONPATH=. .venv/bin/python /home/nghiep/projects/AA-Ecosys/.tmp-session/s235/r5/r5_measure.py r5_trial=/home/nghiep/projects/AA-Ecosys/.tmp-session/s235/r5/pieces_r5_trial.json`
   - Go on only if:
     - the blog seed has `Status: OFFERED` lines;
     - there are 0 visiting/practical bullets;
     - `f9_prompt_versions == ["f9_v1.1"]`;
     - there are 0 citation notes;
     - cost per blog ≤ ~$0.15 and per LinkedIn post ≤ ~$0.05.
6. `python3 r5_run.py write` — fills up to 20 pieces (the trial pieces count). This is ~$0.95 more; it takes ~25–40 min with 6 requests in parallel and one piece in flight per request. Under the hard stop it cancels the open jobs and exits with code 2.
   - Re-running continues where it left off.
   - `python3 r5_run.py status` shows per-piece status and cost.
   - `python3 r5_run.py cancel` is the emergency stop.
7. `python3 r5_export.py` — writes `pieces_r5.json` and prints pieces $ + regen $.
8. Measure, then set `--out` for the panel:
   `cd /home/nghiep/projects/AA-Ecosys/apps/AA-CIS-App && ENVIRONMENT=test PYTHONPATH=. .venv/bin/python /home/nghiep/projects/AA-Ecosys/.tmp-session/s235/r5/r5_measure.py r4_s234=/home/nghiep/projects/AA-Ecosys/.tmp-session/s234/pieces_r4.json r4=/home/nghiep/projects/AA-Ecosys/.tmp-session/s235/r5/pieces_r4_full.json r5=/home/nghiep/projects/AA-Ecosys/.tmp-session/s235/r5/pieces_r5.json --out /home/nghiep/projects/AA-Ecosys/.tmp-session/s235/r5/measure_r5.json`
9. Run the panel per `r5_panel.md` (6 local agents plus synthesis, $0). The report goes to `docs/audits/2026-10-14-S235-ecosystem-team-pilot/r5/01-panel-r5.md`.
10. Draft one Linear comment per issue (met / not met with numbers). Do not post them before Nghiệp reviews.

## Expected cost

| Item | Expected | Basis |
|---|---|---|
| Terra LinkedIn angle regen (t8_angles) | ~$0.02 | One Sonnet call plus ≤4 Jev checks |
| 8 blogs | ~$0.85 | r4 mean $0.104 (max $0.119) |
| 12 LinkedIn | ~$0.31 | r4 mean $0.026 (max $0.037) |
| **Total** | **~$1.17** (plan cap ≤ $1.40) | Hard stop $1.50; reserve per piece: blog $0.15, LinkedIn $0.05 |
| Export / measure / panel | $0 | Read-only SELECT, local code, local agents |

Possible upward drift: AA-786 makes the judge also read the title and meta, and AA-773/775 add F17 findings, which can mean more `t9_repair` calls. That is why the trial comes first.

## What each metric proves (issue → metric → target)

| Issue | Metric (where it comes from) | Target | r4 |
|---|---|---|---|
| AA-776 | `repair_log` entries whose feedback is F4_seo_surface only (slug-only excluded) → `repair_mode == "seo_fields"`, no full rewrite (measure) | all; if none occur, say so and close on the unit tests | n/a |
| AA-786 | F9 violations mentioning citation/marker/`[R:`/`[F:` (measure) | 0 | – |
| AA-786 | `t10_judge` `quality_signal.prompt_version` in llm_call_log (export → measure) | only `f9_v1.1` | – |
| AA-786 | judge calls with `piece_tag_free=false` | 0 | – |
| AA-786 | LinkedIn held on F9_cta_fact (measure) | 0, unless `sentences_left` | 2/12 (#8, #12) |
| AA-785 | F1 violations on a year form (`1637–38`, `1630s`), across final + discarded ledgers + repair_log | 0 | S234 had 22 across 80 pieces |
| AA-774 | Seed "Place background" bullets of kind visiting/practical, using place_card kinds from the export (measure) | 0 | 8 per blog seed |
| AA-774 | Blogs with a permit/access sentence (`permit\|access requires\|multi-hour (horse\|reindeer) ride`) | 0/8 | **8/8** (dry run; the plan said 7/8) |
| AA-774 | Invented sub-activity per blog (panel, product-truth auditor) | ≤1/8 | rim walk, town tour, etc. on ~7/8 |
| AA-774 | LinkedIn light (panel) | ≥10/12 | 10/12 |
| AA-773 | Blogs whose seed carries `Status: OFFERED, NOT INCLUDED` | 8/8 | 0/8 |
| AA-773 | F17 "presents … as part of the plan" in final ledgers | 0 | r4 ledger: export with `--label r4` |
| AA-773 | Reverse flips in either direction (panel) | 0 | 4/8 blogs (#5, #14, #17, #18) |
| AA-773 | Blogs warned by `promises_an_option` | ≤2/8 (Nghiệp's call, may move to AA-787) | 8/8 per plan |
| AA-775 | Pace sentences per tenant: PACE_RE over `_body_spans`, CTA and `_cta_paraphrase` excluded — the `aa775_pace_replay.py` counter | Terra ≤2, A&H ≤1 | **Terra 10 (blog 6 + LinkedIn 4), A&H 2**, Trail 7 (dry run = replay) |
| AA-775 | Holds whose only blocking reason is an F17 pace_promise / LinkedIn pace_promise in the ledger | 0 / 0 | – |
| hygiene | S234 `measure_r4.py` core hard errors (unchanged script) | ≤4 (no regression) | **4**, 18/20 clean (dry run reproduces) |
| cost | Pipeline cost from llm_call_log by job | ≤ $1.40 | $1.15 |

Notes:
- **`optional_as_fixed_offline`** replays the shipped F17 optional-as-plan detector on the final text, so it can score r4 too. It finds **0/8 on r4**, although the r4 panel found boat-as-included in #5, #14 and #17: the detector misses hedges that sit in the same clause, as in "…and optionally on horseback". That is why the reverse-flip count is a panel check, not a regex.
- **Small sample.** n=8 blogs is small. Trust only the large deltas, and do not tune on the smaller ones (lesson S224/AA-346).

## Dry-run results (local, $0, on the aa-775 worktree code)

- `py_compile` passes for all 3 scripts.
- `r5_measure.py r4=../../s234/pieces_r4.json` reproduces r4:
  - hard errors 4 (18/20 clean);
  - pace sentences Terra 10 / A&H 2 / Trail 7 / WildKind 0, identical to `aa775_pace_replay_out.json`;
  - permit blogs 8/8;
  - Status: OFFERED 0/8.
- `r5_run.py init` was run against a scratch STATE path: 6 requests, trial targets = Terra LinkedIn, A&H blog, Trail LinkedIn; full target = 20.
- `r5_export.py --from-raw` post-processing and the `r5_measure.py` ledger paths (F1 year-form, F9 classes, F4-only → seo_fields, F17 optional/pace, promises_an_option) were exercised on a synthetic raw file.
- Not run (needs AWS / paid): preflight, regen, write, the ECS-exec export itself.
