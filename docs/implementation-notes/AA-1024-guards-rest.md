# AA-1024: the rest of the lessons-to-guards design (lane l8-lessons-guards-rest, S272)

S271 built about half of the guards in the lessons-guards design (`docs/audits/2026-11-07-S271-lessons-to-guards/`,
guards G1-G22, and the critic's weak and missing lists). This lane checked every guard against `master` / `main` of
the repo it names, then built the ones that were missing. Earlier lanes: `AA-1024-l21-guards-root.md` (root, S271)
and the child-repo notes `AA-1024-l22-guards.md` (CIS), `AA-1024-s271-guards-infra.md` (Infra).

## Step 1: what was on main before this lane

Checked on origin/master (root 2e7e510e) and origin/main of each child repo (CIS 8e148fe4, Booking c9305c4,
Partner 38f99f53, TripPlanner 91d0608, Infra 75ddf66), 07/11/2026.

| Guard | Shipped | Evidence |
|---|---|---|
| G1 ship-wave + SHIP-1 | yes | `tools/github/ship_wave.py`, `tools/github/mergeq.sh:68` (DIRTY exit 4), `.claude/hooks/aa_shell_guard.py` SHIP-1, `as-app.sh` merge gate (`AA_SHIP_GATED`); no `.tmp-session` merge scripts in `.claude/settings.json` |
| G2 shell guard | partly | PKILL-1, ZSH-1, ENV-1 in `aa_shell_guard.py`; WT-1, BG-1 and TF-1 were dropped in S271 (critic: the planned regexes misfired) |
| G3 raw ECS exec refusal + ecsx hardening | no | only the subagent hook refuses `execute-command` (`subagent-guardrails.sh:22`); ecsx has no auto-resume, no local output file, no heartbeat, no timeout check |
| G4 RAM guard | yes | `aa_shell_guard.py` RAM-1, `lane_start_guard.py` lane RAM gate |
| G5 hook tests in root CI | yes | `.github/workflows/docs-lint.yml` "Claude hook tests", `.claude/hooks/test_settings_hooks.py` |
| G6 pre-push installed + integration + pinned venv | partly | (1) `tools/github/ship_open_prs.py` core.hooksPath check (#603); (2) CIS `scripts/pre-push.sh --integration` stamp (#1360); (3) `scripts/export_openapi.py` still only prints the versions; (4) no `pythonpath` in CIS `pyproject.toml` |
| G7 ORDER BY uuid lint | yes | `tests/unit/test_aa1024_sql_order_stability.py` in CIS, Booking (`backend/`), Partner (`api/`) |
| G8 304 LATER scanner + nightly | yes | CIS `tests/unit/test_aa1024_replay_later_list.py`, `.github/workflows/nightly-integration.yml` |
| G9 Terraform lock wait | yes | Infra `tools/terraform/tests/test_workflow_tf_locking.py` (lock wait instead of a plan concurrency group) |
| G10 dangling migration references | yes | `.github/scripts/migration_refs.py` in CIS, Booking, Partner, TripPlanner |
| G11 PR text guard + Done-evidence audit | no | `pr-title.yml` only in Booking, Partner, TripPlanner and only refuses `[AA-n]`; none in root, CIS, Infra; no `done_audit.py` |
| G12 master plan gate | yes | `.claude/hooks/lane_start_guard.py` (the publish stamp was left out) |
| G13 IAM trust inventory | yes | Infra `tools/terraform/iam_trust_inventory.py` (+ allowlist, tests); lessons.md cites it |
| G14 gitleaks before push + scan status | no | Booking, Partner, TripPlanner, Infra and root pre-push run gitleaks; CIS `scripts/pre-push.sh` does not; no session-start status of scheduled guard runs |
| G15 workflow lint | partly | Infra `.github/scripts/workflow_lint.py` + `workflow-lint.yml`; nothing in root, CIS, Booking, Partner, TripPlanner |
| G16 replay failures are errors | yes | CIS `tests/integration/_replay_guard.py` |
| G17 wave stop flags enforced | no | CIS `scripts/aa645/wave_report.py` computes `stop_conditions` and always exits 0 |
| G18 one cost source | no | no `tools/llm/spend_by_stage.py` / `cost_estimate.py` |
| G19 Stop hook | no | no Stop hook in `.claude/settings.json` |
| G20 lane resume state | no | `tools/workflows/lane.js` says it in prose only |
| G21 PII hook --check + safe DRY RUN snippet | no | no `--check` mode; `destructive-ops.md` has no pin snippet |
| G22 lessons lint + sweep | partly | `tools/docs/check_lessons.py` (+ weekly `--sweep`); a child-repo guard path is not checked in CI (no checkout there) |

## Step 2: after this lane

| Guard | Now | What this lane added (root unless named) |
|---|---|---|
| G1 | yes | nothing |
| G2 | yes | `aa_shell_guard.py` WT-1 (worktree path), BG-1 (silent background chain), TF-1 (Terraform apply off `main`) |
| G3 | yes | ECS-1 refuses a raw `execute-command` (typed or in a `.tmp-session` script); the ecsx wrapper (`tools/ecs/`) restarts a lost start once, keeps `.tmp-session/ecsx/<id>.out`, writes a heartbeat, refuses `ECSX_SCRIPT_TIMEOUT` > `ECSX_TIMEOUT`; its tests run in docs-lint. CIS: the deploy gate (`/admin/job-runner/deploy-gate`, read by the CI guard) blocks while a heartbeat younger than 120 s has no `.done` (`shared/jobs/exec_heartbeat.py`; the api reads S3 with its task role, which already has `s3:ListBucket`, so no Infra grant) |
| G4 | yes | RAM-1 now also counts a push, the PR opener, the wave shipper and `scripts/pre-push.sh` as heavy, and a running pre-push hook as a heavy process (the S272 crash) |
| G5 | yes | the new tests run in the existing docs-lint steps; new step "LLM spend tools tests" |
| G6 | yes | CIS: `export_openapi.py` refuses unpinned FastAPI / Pydantic (exit 2), `pythonpath = ["."]` (parts 1 and 2 shipped in S271) |
| G11 | yes | root `pr-title.yml`; the same file in CIS and Infra (new) and Booking, Partner, TripPlanner (ids anywhere in the title, ids outside the Refs line); the PR opener refuses stray ids; `tools/linear/done_audit.py`. Left: making `PR title` a required check in CIS / Infra (ruleset, tech lead) |
| G14 | yes | the PR opener runs gitleaks v8.30.1 on every branch with the BASE's rules before any push; CIS `scripts/pre-push.sh` runs the same scan on every push (a fix-up push to a PR branch too); `tools/github/guard_runs.py` in the session-start status |
| G15 | yes | `.github/workflows/workflow-lint.yml` + `.github/scripts/workflow_lint.py` (+ unittest file) in root, CIS, Booking, Partner, TripPlanner: pinned actionlint 1.7.12, then WL2 Playwright on ubuntu-24.04, WL3 `npm ci` with a tracked lockfile, WL1 no sensitive `vars.*`. One script in all six repos (Infra's, gained `--skip`, comment-aware Playwright, unchecked matrix dirs). Booking and Partner run `--skip WL1` until their 7 `vars.AWS_ROLE_ARN` uses move to a secret (repo settings, tech lead). actionlint fixed two CIS errors (undeclared inherited secret) |
| G17 | yes | CIS `wave_report.py`: flags `pending` while the wave's tours have queued / running jobs (exit 5), exit 3 on a true flag; `POST /admin/waves` recomputes the newest wave's flags (`services/waves/quality.py`, moved from the script, no migration) and answers 409 on true / pending / not computable unless `stop_override` quotes the tech lead's approval; wave runbook updated |
| G18 | yes | `tools/llm/spend_by_stage.py`, `tools/llm/cost_estimate.py` (+ tests, CI step); the wave runbook quotes only them |
| G19 | yes | Stop hook `stop-open-work.sh` / `stop_open_work.py` registered in `.claude/settings.json` |
| G20 | yes | `lane_start_guard.py` refuses a relaunch on an existing worktree without `resume: true`; `lane.js` asks for `resumed_state` |
| G21 | yes | `pilot_pii_guard.py --check`; pin snippet in `destructive-ops.md` |
| G22 | yes | `check_lessons.py` checks a child-repo guard path on that repo's `main` through the GitHub API in CI (`LESSONS_REMOTE_CHECK=1`) |
| S272 GIT_DIR | yes | `.githooks/pre-push` cds to the top level and unsets `git rev-parse --local-env-vars`; `scripts/pre-push.sh` unsets them again and its self-test checks it; every root test helper that runs git in a temporary repo drops them; `tools/github/test_git_env_isolation.py` (scan, hook end to end, the S272 fixture shape against a sentinel repo) |

Guards G7, G8, G9, G10, G12, G13, G16 were already on main (Step 1) and are unchanged.

## Decisions

- GIT_DIR guard: the variable list is git's own (`git rev-parse --local-env-vars`): bash scripts call it, Python
  helpers carry the static tuple, and a test fails when a newer git reports a variable the tuple lacks.
- GIT_DIR guard: each test helper scrubs at import, not only the hook, so a helper run from another hook context is
  safe too.
- RAM-1: `--no-verify`, `--dry-run` and delete-only pushes are light (no hook runs); the PR opener and the wave shipper
  with `--dry-run` / `--check-only` too.
- G14: the PR opener reads `.gitleaks.toml` / `.gitleaksignore` from the BASE ref (as CI does, so a branch cannot
  allowlist its own leak). A missing binary is a refusal with the install line; `AA_SKIP_GITLEAKS=1` skips with a
  warning. The binary is found at `AA_GITLEAKS`, on PATH, or at `.tmp-session/gitleaks-8301/gitleaks`.
- G18: a row's LLM / non-LLM column comes from its role (writer / judge / validate / embed = LLM; decide, data, guard =
  non-LLM; an unknown role is "other", never LLM). Shadow calls are billed, so they count in the total and are shown
  apart. The total says TOTAL only with `SPEND_WRITE_FAILURES=0`; else LOWER BOUND with the Logs Insights command for
  the window (CIS log group `/ecs/aa-cis-dev`, from Infra `modules/ecs`).
- G18: `cost_estimate.py` divides by distinct tours over the whole stage (a second COUNT DISTINCT query), not by the
  largest per-model count; no priced call in the window = exit 3, no number.
- G22: an API error on the remote check is a warning, not a failure (a rate limit must not block a docs PR).
- Lessons: 20 lines moved to `guards.md`, each tagged "(guard mới S272, AA-1024)"; two new S272 lessons (GIT_DIR, the
  push RAM crash) go straight to `guards.md` because their guard ships in the same PR.

## Changed (vs the design)

- G11: the root PR title workflow is new here; the body rule exempts bot PRs (Dependabot, release-please, `bot/*`),
  whose generated bodies cite issues.
- G14: the design's "session-start status of secret-scan-history" became `guard_runs.py`, which lists every scheduled
  workflow's latest run (Secret Scan history, nightly integration, docs-lint sweep, Infra probes), red first.
- G17 / G3 / G15 (review fix pass): built in full, except WL1 in Booking / Partner, which waits on a repo-settings
  step (vars.AWS_ROLE_ARN to a secret). G3's deploy-gate read moved from "CI with an Infra ListBucket grant" to the API's
  own gate answer, which the CI guard already reads.
- Stop hook (review fix pass): only the LAST line counts and only an offer to stop / a request to go on that ends it; a
  paid-run or MFA approval question never blocks; dependency waits (sau khi, chỉ khi, after, once, until) are blocked
  markers.
- Lane start guard (review fix pass): a `resumeFromRunId` relaunch passes (the workflow replays its journal); only a
  fresh launch on an existing worktree needs `resume: true`.
- PR text rule (review fix pass): an id the Refs line names may appear anywhere; ids in file paths are ignored; bots
  are exempted by login / head branch, never by `user.type` (the orchestrator's App is a Bot).
- docs-lint now runs the ecsx tests and triggers on `.githooks/**`, `scripts/pre-push.sh`, `tools/ecs|kit|llm-core|adr/**`.

## Tradeoffs

- RAM-1 on every push: an orchestrator push on a loaded machine is refused until memory frees (or `AA_RAM_OVERRIDE=1`,
  logged). A refused push costs a minute; a VM restart cost every lane (S272).
- gitleaks in the PR opener adds about a second per PR and needs the binary on the machine.

## Should know

- `tools/kit/test_kit_sync.sh` fails 9 of 20 cases on master too (it runs the wrapper of the current CIS checkout,
  which no longer knows the `portal` consumer); not touched here.
- The root pre-push runs only the docs and contracts checks; the hook, ship tool and LLM tool tests run in CI
  (docs-lint.yml). Locally: `python3 -m unittest discover -s <dir> -p 'test_*.py'` per directory.
- Child PRs of this lane: CIS (G17, G11, G6, G14, G3 c, G15), Booking / Partner / TripPlanner (G11, G15), Infra (G11,
  G15 script). Merge the child PR-title
  PRs before or with this root PR: `guards.md` cites their `pr-title.yml`.
