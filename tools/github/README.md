# GitHub ship tools

Orchestrator helpers for pushing, merging and migrating across the AA_Ecosys repos. Every write to GitHub goes
through the org App `aa-agent` (`as-app.sh`, ADR 0011), which reads its key from Secrets Manager: a live MFA
session for `aa365-admin` is needed (renew with `aws sts get-caller-identity --profile aa365-admin`). Subagents
cannot run the writing commands (the guardrail hook blocks push, merge and `gh workflow run`). The process these
tools serve, and when to use each: skill `aa-ship` (§1 "Cách merge", `references/merge-trains.md`).

| Tool | What it does |
|---|---|
| `as-app.sh [--repos a,b] -- <cmd>` | runs one command with an `aa-agent` installation token |
| `mergeq.sh <Repo> <pr> [--dequeue]` | merge-queue enqueue and wait (CIS, Booking, Partner); used by `ship_merge.py` |
| `ship_merge.py <targets>` | gate + merge one or more PRs (below) |
| `ship_train.py <Repo> <worktree> <branch>:<pr>[:<own>] ...` | stacked branches, bottom first (below) |
| `ship_copy_apply.py <owner> <NNN>` | Infra copy PR + DB Migrate on that file + readiness (below) |
| `dbmig.sh <owner>/<file or NNN> <check or apply>` | DB Migrate on a file already on Infra main (`ship_copy_apply.py --no-copy`) |
| `ship_open_prs.py <journal or wf_ id>` | push lane branches and open their PRs from a workflow journal (below) |
| `train-lib.sh` | shell functions for a background train; `waitdeploy` waits for a `git_sha` on a health endpoint |

All Python tools are stdlib only, print no token, key or credential, and warn when the MFA session ends within
30 minutes (only the `Expiration` field of `aws configure export-credentials` is read). Run them from the main
checkout: `python3 tools/github/<tool>.py --help`.

## ship_merge.py

`python3 tools/github/ship_merge.py 'AA-CIS-App 1230' AA-CIS-Infra#585 root#438 tp#208`

- Waits for the PR's checks and merges only when **every** check is green (success, neutral or skipped), required or
  not. S263: CIS #1225 went through the merge queue with a red non-required "Migration preflight".
- Refuses a draft PR, a PR whose base is not the default branch, a DIRTY PR, and a PR that deletes files (a squash
  from a stale base shows up as deletions) unless `--allow-deletes`.
- CIS, Booking and Partner merge through the queue (`mergeq.sh`, one worker per PR in parallel); TripPlanner, Infra
  and the root repo squash with `--match-head-commit` (the head that was gated), one PR per repo at a time.
- `--check-only` gates and reports; `--serial` keeps the given order and stops at the first failure.
- Exit 0 merged, 3 a red check (or none reported), 4 refused or merge failed, 5 still pending at `--timeout`.
- The gate does not read job tables or waves: `aa-ship` §2 still comes first for backend merges.

## ship_train.py

`python3 tools/github/ship_train.py AA-Partner <worktree> feat/aa-958-migration:175 feat/aa-958-code:176`

- Counts each branch's own commits once, before anything moves (`<branch below>..<branch>`; give `:<own>` to
  override), then per branch: fetch, refuse a rebase in progress, modified tracked files, or remote commits the local
  branch lacks; `git rebase --onto origin/<default> <branch>~<own> <branch>`; retarget the PR to the default branch
  and mark it ready; push with `--force-with-lease=<branch>:<remote SHA>`; gate and merge as `ship_merge.py`.
- Stops at the first conflict, red check or refusal. `--dry-run` prints the rebase plan.

## ship_copy_apply.py

`python3 tools/github/ship_copy_apply.py cis 330` (owners `cis`, `booking`/`bk`, `crm`, `tripplanner`/`tp`;
`roles` with `--no-copy`)

- Finds `bot/migration-copy/<owner>-<NNN>` in any state: an open PR is gated and merged, a merged one is fine,
  closed ones are ignored; waits up to `--copy-timeout` for the bot.
- Reads the file header on Infra main: expand files are left to Migration Apply (no dispatch, readiness is
  checked); destructive files are refused without `--allow-destructive`; contract files are dispatched.
- Follows **its own** DB Migrate run: under a local lock it notes the existing runs, dispatches, and takes the new run
  titled `DB Migrate <mode> <owner>/<file>` (Infra `run-name`); before that title exists it takes the one new run
  and refuses to guess between two. Then it polls that run, prints its conclusion and key log lines, and reads the
  owner app's `/health/ready` (`schema_version`, key in `registered_keys`).
- Exit 0 applied and registered, 1 run red or key missing, 2 dispatch/run not found, 3 copy PR red, 4 refused,
  5 timeout.

## ship_open_prs.py

`python3 tools/github/ship_open_prs.py wf_85982363-f71 [--only Infra] [--extra-refs AA-1032] [--dry-run]`

- Reads the lane journal (`tools/workflows/lane.js`): the `prs[]` of the last result that has them, in merge order;
  a result with `ready=false` is refused unless `--allow-not-ready`.
- Checks all PRs before pushing any: worktree and branch exist, branch ahead of `origin/<base>`, no rebase in
  progress, no modified tracked file, conventional title without an issue id, `Refs AA-<n>` in the body and no
  Fixes/Closes phrase. Deleted files are listed as a warning.
- Pushes (never forced), opens the PR with the lane's title and body (or reuses the branch's open PR), appends the
  Claude Code attribution line when missing, checks the author is the App, and prints each PR's `live_steps`.

## Tests

`python -m unittest discover -s tools/github -p 'test_*.py'` (offline: scripted `gh`/`aws`, real `git` in temporary
repositories). CI runs them in the root Docs lint workflow.
