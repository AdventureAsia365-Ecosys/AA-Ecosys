# AA-1032 — Implementation notes (root repo, lane: ship tools, scope parts 4 and 6)

Scope: turn the S263 orchestrator helpers written ad hoc in `.tmp-session/S263/` (`merge_all.sh`, `train.sh`,
`copy_apply.sh`, `open_prs.py`, `prstat.sh`) into maintained, tested tools under `tools/github/`, update skills
`aa-ship` and `aa-session` to use them, and add the MFA expiry note + reminder to the session start. Parts 1–3 and 5
of the issue run in other lanes (`AA-1032-<lane>.md` where they keep notes).

## Decisions

- **Python stdlib, not bash**, for the four new tools (`ship_merge.py`, `ship_train.py`, `ship_copy_apply.py`,
  `ship_open_prs.py`) plus `ship_common.py`. Every external command goes through a `Runner`, so the tests script `gh`,
  `aws` and `as-app.sh` without a network, and run real `git` in temporary repositories for the rebase logic. Names
  use underscores (importable by the tests); the issue's "ship-merge" etc. map to `ship_merge.py` etc.
- **Gate reads `statusCheckRollup`, every check counts.** Green = SUCCESS / NEUTRAL / SKIPPED (StatusContext:
  SUCCESS). Anything else completed is red, including CANCELLED. A re-run of the same check (same workflow + name)
  replaces the older run, so a run cancelled by concurrency and then re-run is not red; a latest run that is
  CANCELLED is. No check at all after 3 minutes is a refusal (every repo has at least gitleaks).
- **Extra refusals in the gate:** draft, base not the default branch (a stacked PR still on its parent would merge
  into the parent), DIRTY, and files deleted by the PR (`--allow-deletes` to accept) — the silent-revert class of
  lessons S250/S253.
- **Non-queue repos merge with `--match-head-commit <gated head>`**, so a push after the gate makes the merge fail
  instead of merging an ungated head. Queue repos still go through `mergeq.sh` (it re-reads required checks and owns
  the queue wait); `ship_merge.py` re-reads the PR state after it (lesson S255 race).
- **Parallelism:** one worker per queue-repo PR (lesson S257); PRs of one non-queue repo run in order (strict
  protection / BEHIND). `--serial` for dependent PRs.
- **Train own-commit count** is computed once before any rebase (`<branch below>..<branch>`, first branch
  `origin/<default>..<branch>`), overridable as `branch:pr:N`. Each step: fetch → refuse rebase in progress, modified
  tracked files, or remote commits missing locally → `rebase --onto origin/<default> <branch>~N <branch>` → check the
  count again → retarget + ready → push `--force-with-lease=<branch>:<remote SHA read after fetch>` → gate on the
  pushed head (`expect_head`) → merge.
- **Own DB Migrate run:** a local `flock` around list-before / dispatch / identify, plus a match on the run title
  `DB Migrate <mode> <owner>/<file>`. The title needs a `run-name` in Infra `db-migrate.yml` (separate Infra PR in this
  lane). Until it is merged, the tool takes the single new untitled run since the dispatch and refuses when there are
  two. The time filter has 300 s slack (WSL clock skew); the before-set is what tells runs apart.
- **Copy PR lookup** by `headRefName` in state all: OPEN wins, then the latest MERGED; CLOSED is ignored (S263 had
  closed duplicates, e.g. Infra #591 closed / #592 merged for cis-329). No PR but the file on Infra main is accepted.
- **Class from the file header on Infra main**, not from PR labels (labels can lag): expand → Migration Apply applies
  it, no dispatch, readiness checked; destructive → refused without `--allow-destructive`; else contract → dispatch.
- **Works beside the contract auto-apply lane (part 1):** before an apply dispatch the tool reads `/health/ready` once
  and skips the dispatch when the key is already registered; a red run (exit 17, apply lock held by Migration Apply)
  is accepted with a warning when the key shows up within 5 minutes.
- **`dbmig.sh` kept as the entry point** (docs and runbooks name it) but now delegates to
  `ship_copy_apply.py --no-copy`, so its old "last run != before" logic (same race) is gone. With `--no-copy` the call
  is an explicit dispatch: expand and destructive files are dispatched as before.
- **Readiness** from the owner app's `/health/ready`: `status`, `schema_version`, and whether the key (`NNN`, `bk-NNN`,
  `crm-NNN`) is in `registered_keys`. TripPlanner and roles have no endpoint: the tool says so and does not fail.
- **open_prs validates all PRs before pushing any** (all-or-nothing, the list is in merge order), never force-pushes,
  reuses an open PR of the branch, appends the Claude Code attribution line only when missing, and replaces the
  S263 one-off `EXTRA_REFS` hack (hard-coded "Refs AA-642") with `--extra-refs`.
- **MFA:** `ship_common.mfa_expiry` reads `aws configure export-credentials --format process` and keeps only
  `Expiration`. `python3 tools/github/ship_common.py mfa` prints the session-start line (expiry, minutes left, remind
  time = expiry − 30 min). Tools warn when < 30 min are left (train: < 60 min).
- **CI:** the tests run in the root Docs lint workflow (new path `tools/github/**`, new step), the same pattern as
  `tools/linear`.

## Changed

- `tools/github/dbmig.sh` rewritten as a wrapper (same usage; exit 5 added for a timeout).
- `tools/github/train-lib.sh` header points at the tool versions of `gate` / `waitcopy` / `restack`; the functions
  stay (`waitdeploy`, `merged` have no replacement).
- Skills: `aa-ship` §1 "Cách merge" + migration bullet, `references/merge-trains.md` rewritten around the tools,
  `aa-session` step 2 (MFA expiry + reminder) and `references/parallel-lanes.md` step 6 (`ship_open_prs.py`).
- `lessons.md`: the push-mid-rebase and queue-merge-race lessons name their guards (kept, the guard only works when the
  tools are used).
- Not done here: `prstat.sh` (a read-only status line) has no tool version; `ship_merge.py --check-only` covers its
  use. `.claude/settings*.json` untouched.

## Tradeoffs

- Matching runs by title needs the Infra `run-name`; without it two dispatches from different machines in the same
  minute are refused rather than guessed (safe, rare).
- The gate cannot see job tables or waves (needs DB access); `aa-ship` §2 still comes first for backend merges.
- Checks that register late (a `workflow_run` workflow) can be missed if the gate passes before they appear; the
  queue re-runs required checks, and Infra/root have few late checks.
- `--allow-deletes` is all-or-nothing per run; a PR that legitimately deletes files needs it explicitly.

## Should know

- Run the tools from the main checkout (`/home/nghiep/projects/AA-Ecosys`); `AA_ECOSYS_ROOT` overrides the root used
  for the dispatch lock and PR body temp files (`.tmp-session/`).
- Exit codes are shared: 0 ok, 1 git / run red, 2 usage or gh error, 3 red check, 4 refused / merge failed,
  5 timeout. A train or merge list stops at the first non-zero.
- `python -m unittest discover -s tools/github -p 'test_*.py'` — 48 offline tests.
