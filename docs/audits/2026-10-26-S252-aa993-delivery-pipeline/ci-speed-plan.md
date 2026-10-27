# AA-993 slice 6: CI speed plan

Scope: AA-CIS-App, AA-Booking, AA-Partner, AA-TripPlanner-Web and AA-CIS-Infra. All numbers are minutes of PR wall time unless marked otherwise. Savings use the verifier's corrected figures, not the original estimates. All app repos are public, so runner minutes cost nothing. Only critical-path minutes count as speed.

## 1. Baseline

PR wall time runs from when the run is created to when the last required job finishes. "Queue" is the time from run creation to the first job starting.

| Repo | Runs sampled | Median | p90 | Critical path | Queue (median / p90) |
|---|---|---|---|---|---|
| AA-CIS-App | 24 (22 PR + 2 merge_group) | 10.66 | 11.30 | `Unit Tests` was last in 24/24 runs. Step `Run unit tests` takes 9.77 min (one serial pytest process, 16,454 tests, C-tracer coverage, about 48 s of collection). Next longest is `Integration Tests` at 3.30. | 0.05 / 0.07 |
| AA-Booking | 24 | 3.09 | 3.92 | `Unit Tests` was last in 24/24 runs (job 3.02, step 164 s). Next is `Integration Tests` at 1.60. | 0.05 / 0.57. Job-level wait for `Unit Tests` has a p90 of 2.50 and a max of 4.30. |
| AA-Partner | 25 | 3.17 | 3.82 | `Unit Tests` was last in 23/25 runs (job 3.12, step 167 s). `Integration Tests` (1.83) was last in 2/25. | 3 s / 12 s. Job-level wait p90 is 22 to 39 s. |
| AA-TripPlanner-Web | 25 (14 of them on release-please PR #155) | 1.62 (dev PRs 1.55) | 2.05 (dev 1.83) | `Migrations (lint, PG 15 replay)` was last in 18/25 runs (1.57). Its `Catalog-view SQL` step takes 61 s, about 43 s of which is `test_vector_topk_pg.py` rebuilding its database for every test. | 3 s / 17 s |
| AA-CIS-Infra | 27 rounds (133 runs) | 1.08 | 1.30 | `Terraform Plan (dev)` was last in 26/27 rounds (63 s: plan 32, init 14, validate 4). No checks are required. | 3 s / 8 s. Time to green has a p90 of 30.4 min, caused by the copy guard waiting on the owner repo's merge (11/27 rounds) and one state-lock collision. |

Context that applies to all repos:
- **Runner speed varies a lot.** The same CIS suite ran anywhere from 6.3 to 11.6 min. Compare step medians, never single runs.
- **The merge queue doubles the cost.** CIS, Booking and Partner run CI twice per merged PR: once on the PR and once on merge_group. Every critical-path saving there counts twice per merge.
- **Contention is outside these fixes.** The org is on GitHub Free, which caps it at 20 concurrent jobs across all repos. That cap causes the p90 tails, and none of the changes below fix it.

## 2. Verified ideas (verdict.real = true)

Overall ranking by corrected critical-path minutes saved per run:

1. CIS-1: 4.5
2. CIS-2: 2.3 (on top of CIS-1)
3. BK-2: 1.3
4. P3: 1.1
5. P2: 1.1 (does not add to P3)
6. BK-1: 0.9 (does not add to BK-2)
7. TP-1: 0.35
8. I2: 0.35 in eligible rounds, about 0.1 averaged
9. CIS-3: 0.3
10. I1: 0.3 amortized (tail only)
11. I7: 0.3 (do not adopt: weakens a gate)
12. P1: 0.25 (about 0 after P3)
13. BK-3: 0.1 (about 0 after BK-2)
14. P7: 0.1
15. I4: 0.1 (not yet measured)
16. I8: 0.06
17. P4: 0.05 amortized (removes a flaky test)

Zero wall-time saving, but still worth doing as hygiene or confirmed as "no change": CIS-4, CIS-5, CIS-6, BK-4, P10, P11, P6, TP-8.

### AA-CIS-App: `.github/workflows/ci.yml`

| ID | Saved | Exact change | Risk | Gate impact |
|---|---|---|---|---|
| CIS-1 | 4.5 | In job `test-unit`, step `Run unit tests`, add `env: COVERAGE_CORE: sysmon`. Pin `coverage==7.17.0` in `requirements.txt` (today it arrives unpinned through pytest-cov 5.0.0). Leave `Q0 red on base` alone: it runs without `--cov`. | Low. A local A/B gave the same covered-line set (11,262 lines, zero differences) and a 402 s → 207 s full-suite run. The coverage margin is thin (85.64% against a floor of 85), so the first PR must print the same ratchet total as main. | None |
| CIS-2 | 2.3 (after CIS-1; capped by Integration at 3.3) | Install `pytest-xdist==3.8.0` in the CI step or a dev requirements file, not in `requirements.txt` (that file feeds the production image). Run `pytest tests/unit/ tests/acp/ -n 4 --dist loadfile --cov=services --cov=shared --cov-report=xml:coverage.xml ...` as one invocation. Use `-n 4`, not `-n auto`. Test fixes go in the same PR: (a) fixed UUIDs or `ids=` in `test_aa210_batch_id_guard` (line 15) and `test_aa978_tenant_membership_contract` (lines 42, 187, 294); (b) full stub column sets in `test_aa797_tenant_admin::TestListTenants::test_default_is_active_only_and_status_derived` and `test_aa798_admin_billing_real_cost::TestNoInventedPlan::test_admin_tenant_list_null_plan`; (c) an autouse fixture in `tests/unit/conftest.py` that resets `services/acp_publish/daily_limit.py::_column` (a process-global cache with a 300 s TTL). | Medium-low. Without the fixes, the required `Unit Tests` check goes red at random and blocks the merge queue. Run the suite under xdist at least 3 times on the PR. | None. The same 16,467 tests run under the same job name. Line-rate goes from 0.8564 to 0.8578 only because the acp tests are now measured. |
| CIS-3 | 0.3 (Unit job only today; the Integration half matters once CIS-2 makes Integration the floor, not measured) | Replace `setup-python` with `cache: pip` plus `pip install`, using `astral-sh/setup-uv@<SHA>` (keep the default cache pruning) and `uv pip install --system -r requirements.txt`. In Integration, run a second `uv pip install --system -r tests/integration/requirements-integration.txt` in the same order as today. Optionally set `UV_COMPILE_BYTECODE=1`. | Low. About 16 floor-only specs resolve fresh on every run with pip or uv alike. Pin the action by SHA. | None |
| CIS-4 | 0 (saves 3.9 runner-min per 100 runs) | Add top-level `concurrency: { group: ci-${{ github.event_name == 'pull_request' && github.event.pull_request.number \|\| github.run_id }}, cancel-in-progress: ${{ github.event_name == 'pull_request' }} }`. Do not key it on `github.ref`: that would serialise main pushes and cancel the pending ones. | Very low | None. merge_group runs get their own group. |
| CIS-5 | 0 (saves about 20 runner-min per merge) | Keep `push: main`, but guard the heavy jobs with `if: github.event_name != 'push'`. Keep a cheap push job that warms the Trivy DB and npm caches and runs Security Audit and Trivy, or add a nightly schedule for those. Do not drop the push trigger entirely. | Low. Push runs on main are the only writer of caches every branch can reuse (`cache-trivy-<date>`, `node-cache-*`), and the repo cache already sits at 10.77 GB against a 10 GB limit. | None in the guarded form |
| CIS-6 | 0 (saves about 17.7 runner-min per release-PR rerun; eases the 20-job org cap) | On `test-unit`, `test-integration`, `docker-build`, `frontend-build` and `portal-build`, add `if: ${{ github.event_name != 'pull_request' \|\| !(startsWith(github.head_ref, 'release-please--') && github.event.pull_request.user.login == 'aa-ecosys-ci-bot[bot]' && github.event.pull_request.head.repo.full_name == github.repository) }}`. Optionally add a Lint step that fails if the release PR touches anything other than `CHANGELOG.md`, `.release-please-manifest.json` or `api/version.py`. | Low to medium | **Weakens the PR-level gate.** merge_group still runs every job, but an admin can bypass the queue (RepositoryRole 5, `enforce_admins=false`) and land code whose required tests never ran. |

### AA-Booking: `.github/workflows/ci.yml`

| ID | Saved | Exact change | Risk | Gate impact |
|---|---|---|---|---|
| BK-2 | 1.3 median (1.15 mean; capped by Integration at 1.60) | Add a pinned `pytest-xdist` (3.8.0, with execnet 2.1.2) to `backend/requirements-dev.txt`. Change the Unit command to `pytest tests/unit -n 4 --tb=short --cov=app --cov-report=term-missing --cov-fail-under=90`. Integration Tests stays serial (one shared Postgres). | Low to medium. Locally: 1,498 passed in about 42 s twice, coverage 93.50% both times. Run 2 to 3 times on the PR. | None |
| BK-1 | 0.9 alone; does not add to BK-2 | Add `COVERAGE_CORE: sysmon` to the `Run unit tests` env, next to `ENVIRONMENT: test`. Ship it with BK-2 anyway: under xdist it cuts worker CPU (locally 45 s → 35 s), which leaves headroom against the Integration floor on slow runners. | Low. The report was identical file by file, missed line numbers included. | None |
| BK-3 | 0.1 serial; about 0 after BK-2 | In `backend/tests/unit/test_openapi_export.py`, build the spec once in a module-scoped fixture and keep one test that calls it twice to prove determinism. | Low | None |
| BK-4 | 0 (removes 7 duplicate jobs per merge) | After at least 5 green merge_group runs (there are 0 so far), remove `push: branches: [main]` and add a nightly `schedule:` plus `workflow_dispatch` to `ci.yml`. | Medium. Admin bypass (ruleset 25884452) would otherwise leave a commit on main with no CI. | None, provided the schedule is added |

### AA-Partner

| ID | Saved | File | Exact change | Risk | Gate impact |
|---|---|---|---|---|---|
| P3 | 1.1 (capped by Integration at about 1.83) | `.github/workflows/ci.yml`, job `test-unit` | Add `env: COVERAGE_CORE: sysmon` to `Run unit tests`. Measured locally: 132.6 s → 76.9 s, with the same 91.90% (18,392 statements, 1,490 missed). | Low | None |
| P2 | 1.1 alone; adds 0.1 or less after P3 | `ci.yml` and `api/requirements-dev.txt` | Pin `pytest-xdist`, then run `pytest tests/unit -n 4 --dist loadfile --tb=short --cov=app --cov-report=term-missing --cov-fail-under=90`. Integration stays serial (`crm_ci` is a shared DB). **Deferred:** only adopt if the post-P3 numbers still show Unit finishing last in more than half the runs. | Medium (passed 3 local runs) | None |
| P1 | 0.25; about 0 after P3 | `api/tests/unit/test_code_rules.py` | Decorate `_modules()` with `@functools.cache`, return a tuple, and add a comment that the trees are shared and read-only. | Low | None |
| P7 | 0.1 | `ci.yml` (`test-unit`, `test-integration`) | Cache `api/.venv`, keyed on `steps.<setup-python>.outputs.python-version`, the runner image, and `hashFiles('api/requirements.txt','api/requirements-dev.txt')`. A uv install is an equal alternative. **Deferred:** after P3 the Integration install (9 to 13 s) sits on the floor, so this is the half that would count. | Low, but only with the full-version key. A `3.12` key leaves a dangling interpreter. | None |
| P4 | 0.05 amortized (avoids rare 25-min reruns and merge-queue ejections) | `api/tests/integration/test_job_runner.py` | In `test_production_schedule_leaves_the_queue_idle_for_deploys_and_db_migrate`, set `fixed = datetime.now(UTC).replace(minute=30, second=0, microsecond=0)` once and pass `now=lambda: fixed` to both workers. Do not change `INFRA_JOB_BUSY_SQL`: it is a verbatim copy of the Infra check. | Low | None |
| P10 | 0 (not a required check; portal smoke loop about 1.7 min faster on average, 7 to 17 min on bad-mirror days) | `.github/workflows/ui-smoke-portal.yml` | Replace `npx playwright install --with-deps chromium` with `npx playwright install chromium`, or keep a guarded `timeout 90 npx playwright install-deps chromium \|\| true`. Do not use the container variant: it has no `gh`, so the PR comment step is skipped without any error. | Low (missing CJK/Thai fonts only change how failure screenshots look) | None |
| P11 | 0 (one fewer runner per run) | `ci.yml` | Fold Portal Lint into Portal Build. Put the ESLint step last with `continue-on-error: true` and `if: ${{ !cancelled() && steps.install.outcome == 'success' }}`, delete the `portal-lint` job, and update the CI header comment and `CONTEXT.md` line 309. | Low (Portal Lint is not a required check) | None |
| P6 | 0 | n/a | No change. The 21-migration replay costs 1.26 s. | n/a | n/a |

### AA-TripPlanner-Web

| ID | Saved | File | Exact change | Risk | Gate impact |
|---|---|---|---|---|---|
| TP-1 | 0.35 median wall (28 s off the Migrations job) | `backend/tests/test_vector_topk_pg.py` | Add a sync, module-scoped template fixture (using `asyncio.run`) that creates `tp_aa712_tpl_<uuid>`, applies SCHEMA, runs `_load` and ANALYZE, then closes every connection. The function-scoped `db` fixture becomes `CREATE DATABASE "<name>" TEMPLATE "<tpl>"`. Drop the template in a `finally` at module teardown. Do not use xdist: it breaks the `PASSED` grep guard. | Low to medium (the template must have no open sessions) | None |
| TP-8 | 0 | n/a | No change: the migration replay takes 4.4 s. Before TripPlanner joins a merge queue, it needs `merge_group` on `ci.yml` and a merge_group path for gitleaks. | n/a | n/a |

### AA-CIS-Infra: `.github/workflows/terraform-plan.yml`

| ID | Saved | Exact change | Risk | Gate impact |
|---|---|---|---|---|
| I2 | 0.35 in about 8/27 rounds (non-Terraform PRs where the copy guard passes first time), about 0.1 averaged | Add a `changes` job (SHA-pinned `dorny/paths-filter` or `git diff --name-only`) matching `accounts/**`, `modules/**`, `tools/terraform/**`, `tools/identity/**` and `.github/workflows/terraform-plan.yml`. `tools/identity/**` is needed because `e2e_mailbox.tf` reads `crm_e2e_users.json`. The plan job gets `needs: changes` and `if: needs.changes.outputs.tf == 'true'`. Add `pull-requests: read`. Use a job-level `if`, never `on.paths`. A side benefit: db-only PRs no longer take the state lock. | Low to medium | Non-Terraform PRs lose the drift signal, which does not depend on what the PR changes anyway. No checks are required. |
| I1 | 0.3 amortized (a collision round drops from 4–46 min to about 1.7 min) | Change to `terraform plan -lock-timeout=5m`. Not on init, not `-lock=false`, and no workflow-level concurrency group. | Low. A stale lock still fails, just after 5 min. | None |
| I4 | 0.1 (not measured) | Add `-parallelism=20` to the plan command (not 30: Route53, CloudWatch and API Gateway throttle). | Low to medium. Revert if the plan step does not drop or `ThrottlingException` or retry lines appear. | None |
| I8 | 0.06 | Delete the `Terraform Validate` step. `terraform plan` validates first. | Very low | None |
| I7 | 0.3 | `-refresh=false`. **Do not adopt.** | High | **Weakens a gate:** removes drift detection from the only pre-merge infra check. |

## 3. Rejected ideas

- **CIS-7 (migration snapshot):** Integration Tests is not on the critical path and the replay takes about 3.5 s. A snapshot keyed on migrations would miss changes to `conftest.py`.
- **CIS-8 (buildx gha cache):** Docker Build Check (2.2) never decides the wall time, and the repo cache is already over 10 GB, so entries would thrash. Revisit only after Unit and Integration are both under 2.2 min.
- **BK-5 (light CI on the release PR):** Weakens a gate while admin bypass is live and before any merge_group run exists. The `!` condition is invalid YAML. The contention benefit is not shown in the data.
- **BK-6 (postgres:15-alpine):** The image pull is about 4 s, so it saves about 1 s, and it moves collation away from RDS.
- **BK-7 (migration snapshot):** The replay takes under 1 s, and a snapshot would skip the X1 XD8 role-ownership checks.
- **P5 (shard Integration):** Integration is not critical. Even after P1 to P3 the gain is 0.3 to 0.5 min, which the aggregator's queue p90 cancels out.
- **P8 (skip heavy jobs on the release PR):** It overlaps about 9% of runs for 2 to 3 s each, and the `changes` job with `needs:` would add latency to every PR.
- **P9 (drop push:main CI):** Admin bypass is live. The push run is the only writer of main-scoped pip, npm and Trivy caches and of the SBOM per commit. Saving is about 0.
- **P12 (merge-queue settings and gitleaks merge_group):** Already done: Partner #87 is merged and ruleset 25884449 is live with these settings.
- **TP-2 (pip cache in the Migrations job):** A cached install is no faster (9 to 10 s either way), net 1 to 2 s. The pytest 8.3.3 vs 9.0.3 mismatch is worth fixing as a correctness cleanup, not as a speed item.
- **TP-3 (drop the redundant apt-get update):** The index download just moves to the pgdg script's update. The real saving is about 1 s.
- **TP-4 (pgvector service container):** About 5 s net, within noise. Adds a Docker Hub dependency, a digest to maintain and a collation change.
- **TP-5 (concurrency group and dropping branch pushes):** There were 0 superseded runs to cancel, and the proposed key would serialise main CI behind deploy-lambdas.
- **TP-6 (skip CI on the release PR):** Release-PR runs delay no dev PR. A branch-name skip can be spoofed, and option (b) leaves a stale changelog.
- **TP-7 (cache .next/cache):** The Turbopack build cache is opt-in and not enabled. Cache restore and save cancel the 2 to 3 s gain.
- **I3 (Terraform provider cache):** Nothing writes a main-scoped cache, so about 90% of runs miss and each miss saves a 150 MB entry. Net about 0. A warm-on-main variant is a different change worth about 0.1 min.
- **I5 (parallel owner fetch in the copy guard):** The copy guard finishes before Terraform Plan in every `--all` run, so it saves 0 today.
- **I6 (per-PR concurrency on the plan):** It would never have cancelled anything observed, the lock collisions are between different PRs, and cancelling a run can leave a stale S3 lock.

## 4. PR plan (ordered)

Rules for every PR below:
- **Workflow changes need independent review.** Any PR touching `.github/workflows/` is in the CI/workflow risk class: it gets a review from `kiro-reviewer` or an independent subagent before merge. The orchestrator merges: CIS, Booking and Partner through `tools/github/mergeq.sh`; TripPlanner and Infra with `gh pr merge --squash`.
- **No secret-scan change.** No PR touches `secret-scan.yml`. If scope ever reaches it, stop and get the human label first.
- **Commit format:** `chore:` or `fix:` subject, body `Refs AA-993`.

**Re-measure method (the same for every PR).** Take at least 10 completed first-attempt runs of the gating workflow (`ci.yml`, or `terraform-plan.yml` for Infra) on commits that contain the change. Include pull_request and merge_group runs, exclude cancelled runs, and report release-please runs separately.
- Wall time: run `created_at` → `completed_at` of the last required job.
- Critical path: the last required job to finish.
- Queue: run `created_at` → first job `started_at`.
- Also record the median of the targeted step.
- Commands: `gh run list -R AdventureAsia365-Ecosys/<repo> -w <file> -e pull_request -s completed -L 40 --json databaseId,createdAt,attempt,headBranch` and `gh api repos/AdventureAsia365-Ecosys/<repo>/actions/runs/<id>/jobs`.
- Compare step medians, because runner speed varies by up to 1.7x.

| # | Repo / PR | Contents | Files | Review class | Expected after | Extra re-measure check |
|---|---|---|---|---|---|---|
| 1 | CIS PR-1 | CIS-1, CIS-3, CIS-4 | `ci.yml`, `requirements.txt` | Workflow → independent review | Unit step 9.77 → about 5.0. Median wall 10.66 → about 5.9 (p90 about 6.5). Merge path about 21.3 → about 11.8. | Ratchet total equals main (85.64%). Install step about 0.25. |
| 2 | Booking PR-1 | BK-2, BK-1 | `ci.yml`, `backend/requirements-dev.txt` | Workflow → independent review | Unit job 3.02 → about 1.2–1.4. Wall 3.09 → about 1.8. Integration becomes the critical path. | Coverage 93.50% unchanged. 2 to 3 xdist runs on the PR before merge. |
| 3 | Partner PR-1 | P3, P1, P4 | `ci.yml`, `test_code_rules.py`, `test_job_runner.py` | Workflow → independent review | Unit job 3.12 → about 2.0. Wall 3.17 → about 2.05. Integration is last in most runs. | TOTAL 91.90% unchanged. |
| 4 | TripPlanner PR-1 | TP-1 | `backend/tests/test_vector_topk_pg.py` (test code only) | Normal (self-review, CI green, 2 to 3 runs) | Catalog-view step 61 s → about 33 s. Wall 1.62 → about 1.27 (dev PRs 1.55 → about 1.2). | All 30 tests PASSED and the grep guard holds. |
| 5 | Infra PR-1 | I1, I8, I4 | `terraform-plan.yml` | Workflow → independent review | Plan job 63 s → about 55 s. Wall 1.08 → about 1.0. Collision rounds about 1.7 min. | No `ThrottlingException` or retry lines across 5 or more runs; revert I4 if any appear. |
| 6 | CIS PR-2 (after #1 is re-measured) | CIS-2 plus test fixes | `ci.yml`, `tests/unit/conftest.py`, 4 test files, dev requirements | Workflow → independent review | Unit job about 6.0 → about 2.9–3.4. Wall about 5.9 → about 3.5 (Integration 3.3 becomes the floor). Merge path about 7.0. | xdist suite green at least 3 times on the PR. Line-rate about 0.8578. |
| 7 | Infra PR-2 | I2 | `terraform-plan.yml` | Workflow → independent review | First-pass wall on non-Terraform PRs 66 s → about 42 s. Overall median about 0.75. | A PR touching only `tools/identity/crm_e2e_users.json` still runs the plan. |
| 8 | Partner PR-2 | P10, P11 | `ui-smoke-portal.yml`, `ci.yml`, `CONTEXT.md` | Workflow → independent review | UI smoke p90 468 s → about 180 s. CI jobs per run 11 → 10. PR wall unchanged. | At least 10 portal smoke runs. |
| 9 | Booking PR-2 (gated: at least 5 green merge_group runs) | BK-4 plus nightly schedule | `ci.yml` | Workflow → independent review | Wall unchanged. 7 fewer jobs per merge. | merge_group runs stay green and the nightly run fires. |
| 10 | CIS PR-3 (optional, runner minutes only) | CIS-5 (guarded push), CIS-6 (guarded release-PR skip) | `ci.yml` | Workflow → independent review. CIS-6 weakens a PR-level gate, so it needs an explicit decision before merge. | Wall unchanged. About 20 runner-min saved per merge and about 17.7 per release-PR rerun. | Main still seeds the `cache-trivy-*` and `node-cache-*` caches. |

Deferred, to re-evaluate from the post-merge numbers: P2 (only if Unit is still last in more than half the Partner runs after P3), P7 (Integration install once it is the floor), BK-3 (only if BK-2 is dropped).

## 5. Expected median wall, before → after

| Repo | Before (median / p90) | After (median) | Delivered by | New critical path |
|---|---|---|---|---|
| AA-CIS-App | 10.66 / 11.30 | about 5.9 after PR-1, about 3.5 after PR-2. Merge path (PR + merge_group) about 21.3 → about 7.0. | PR 1, PR 6 | Integration Tests (about 3.3) |
| AA-Booking | 3.09 / 3.92 | about 1.8. Merge path once merge_group runs: about 6.2 → about 3.6. | PR 2 | Integration Tests (1.60) |
| AA-Partner | 3.17 / 3.82 | about 2.05. Merge path about 6.3 → about 4.1. | PR 3 | Integration Tests (1.83) |
| AA-TripPlanner-Web | 1.62 / 2.05 (dev PRs 1.55) | about 1.27 (dev PRs about 1.2) | PR 4 | Migrations (about 1.1), with Frontend (0.73) next |
| AA-CIS-Infra | 1.08 / 1.30 (first pass) | about 0.75 overall: non-Terraform PRs about 0.7, Terraform PRs about 1.0. The time-to-green tail stays set by owner-repo merge waits; lock collisions drop to about 1.7. | PR 5, PR 7 | Terraform Plan on Terraform PRs; the copy guard or the docs checks otherwise |

The "after" figures come from the corrected verdicts and have not been measured on CI yet. Each one is confirmed only by the at-least-10-run re-measure above. The p90 tails caused by the org-wide limit of 20 concurrent jobs are outside this plan.