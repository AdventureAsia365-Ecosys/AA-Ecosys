# GitHub ship tools

Orchestrator helpers for pushing, merging and migrating across the AA_Ecosys repos. Every write to GitHub goes
through the org App `aa-agent` (`as-app.sh`, ADR 0011), which reads its key from Secrets Manager: a live MFA
session for `aa365-admin` is needed (renew with `aws sts get-caller-identity --profile aa365-admin`). Orchestrator
only: these tools push, merge and dispatch inside their own subprocesses, where the subagent guardrail hook cannot see
the command, so `.claude/hooks/subagent-guardrails.sh` refuses any subagent Bash command that names one of them
(`ship_merge/train/copy_apply/open_prs/wave.py`, `mergeq.sh`, `dbmig.sh`, `train-lib.sh`, `as-app.sh`; the `test_ship_*.py`
tests stay open; red-team cases in `.claude/hooks/test_subagent_guardrails.sh`). The process these
tools serve, and when to use each: skill `aa-ship` (§1 "Cách merge", `references/merge-trains.md`).

| Tool | What it does |
|---|---|
| `as-app.sh [--repos a,b] -- <cmd>` | runs one command with an `aa-agent` installation token |
| `mergeq.sh <Repo> <pr> [--dequeue]` | merge-queue enqueue and wait (CIS, Booking, Partner); used by `ship_merge.py` |
| `ship_merge.py <targets>` | gate + merge one or more PRs (below) |
| `ship_wave.py <targets>` | a whole wave: independent PRs in parallel, migration chains in order, one deploy wait per app (below) |
| `ship_train.py <Repo> <worktree> <branch>:<pr>[:<own>] ...` | stacked branches, bottom first (below) |
| `ship_copy_apply.py <owner> <NNN>` | Infra copy PR + DB Migrate on that file + readiness (below) |
| `dbmig.sh <owner>/<file or NNN> <check or apply>` | DB Migrate on a file already on Infra main (`ship_copy_apply.py --no-copy`) |
| `ship_open_prs.py <journal or wf_ id>` | push lane branches and open their PRs from a workflow journal (below) |
| `train-lib.sh` | shell functions for a background train; `waitdeploy` waits for a `git_sha` on a health endpoint |
| `guard_runs.py [--json]` | session start, read-only: the latest scheduled run of every workflow in the 6 repos, red first |
| `ci_hygiene.py [--json] [--clean]` | session start: Actions cache usage vs the 10 GB cap per repo, stale pull request / merge-queue caches (`--clean` deletes only those), uncached external downloads in workflows (WL5), artifact retention (WL7, warn), public org repositories not in the known list; read-only without `--clean`. `--retention-scan <checkout>` prints WL7 warnings for one checkout (root Workflow Lint) |
| `pin_freshness.py [--json]` | read-only: self-managed pins (release-bin and lychee `pins.txt`, spaCy wheel URL, ghcr image tags) of the six repos vs the newest GitHub release |
| `hygiene_issues.py sync --kind hygiene\|pins --report <json> [--apply]` | turns a `ci_hygiene.py` / `pin_freshness.py` report into one root issue per finding type (open, update, close); plan only without `--apply`. `read-failures --kind ... --report <json>` lists the failed reads (exit 3 when there is one). Run by the CI hygiene workflow |

All Python tools are stdlib only, print no token, key or credential, and warn when the MFA session ends within
30 minutes (only the `Expiration` field of `aws configure export-credentials` is read). Run them from the main
checkout: `python3 tools/github/<tool>.py --help`.

## ship_merge.py

`python3 tools/github/ship_merge.py 'AA-CIS-App 1230' AA-CIS-Infra#585 root#438 tp#208`

- Waits for the PR's checks and merges only when **every** check is green (success, neutral or skipped), required or
  not. S263: CIS #1225 went through the merge queue with a red non-required "Migration preflight".
- A green read is confirmed: checks of `needs:` jobs and `workflow_run` workflows are created late, so the gate reads
  again 25 s later, needs the same set of checks still green, and needs every workflow run on the head commit
  (`gh run list --commit <head>`, latest run per workflow and event) finished and green.
- Refuses a draft PR, a PR whose base is not the default branch, a DIRTY PR, and a PR that deletes files (a squash
  from a stale base shows up as deletions) unless `--allow-deletes`.
- CIS, Booking and Partner merge through the queue (`mergeq.sh`, one worker per PR in parallel); TripPlanner, Infra
  and the root repo squash with `--match-head-commit` (the head that was gated), one PR per repo at a time.
- `--check-only` gates and reports; `--serial` keeps the given order and stops at the first failure.
- Exit 0 merged, 3 a red check (or none reported), 4 refused or merge failed, 5 still pending at `--timeout`.
- The gate does not read job tables or waves: `aa-ship` §2 still comes first for backend merges.
- AA-1024: `as-app.sh` refuses `gh pr merge` unless this gate passed (it sets `AA_SHIP_GATED`; `--disable-auto` stays
  open), and the same merge through the API: `gh api` with a writing method on `pulls/<n>/merge`, or `gh api graphql`
  with `mergePullRequest` / `enqueuePullRequest` (also from a `-F query=@file` / `--input` body; a GET of the merge
  endpoint and `dequeuePullRequest` stay open). The Claude hook `.claude/hooks/aa_shell_guard.py` (SHIP-1) refuses the
  same API forms, a raw `gh pr merge`, `mergeq.sh` run by
  hand, `ship_merge.py` in a shell loop or twice in one command, and running a hand-written `.tmp-session` script that
  merges. `mergeq.sh` exits 4 at once when the PR turns DIRTY while it waits.

## ship_wave.py

`python3 tools/github/ship_wave.py cis#1350 'cis#1349>apply:cis/383,cis/384' 'cis#1351@after=cis/384' root#601 --wait-deploy`

- One call per wave (lessons S257, S271: a hand-written script that waited for each PR and its deploy before the next
  took ~4 h for 7 PRs instead of ~1 h). Every PR without `@after=` is gated and merged at once by `ship_merge.merge_one`,
  one worker per PR (non-queue repos: one squash at a time per repo).
- `>apply:<owner>/<NNN>[,...]` marks a migration-only PR: after it merges, its migrations go onto Dev through
  `ship_copy_apply.py`, one owner's numbers in order as one batch. `@after=<owner>/<NNN>` holds a code PR until those
  are registered; a hold on a migration nothing in the wave applies must already be registered on Dev (else exit 2).
- A failure stops only what depends on it (a red migration PR skips its held PRs; independent PRs go on).
- `--wait-deploy` waits once per deployed app (CIS, Booking, Partner) at the end, until the health `git_sha` contains
  every merge of the wave (GitHub compare). `--dry-run` prints the plan; `--check-only` gates and merges nothing.
- Exit 0 all merged/applied/deployed, 2 usage or unapplied hold, 3 red check, 4 refused / merge or apply failed /
  skipped, 5 timeout.

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
- Owner order: before it merges a copy PR, and before an apply dispatch, it refuses (exit 4) while an open
  `bot/migration-copy/<owner>-<lower NNN>` PR exists, or while the owner's `/health/ready` lacks the key of a lower
  file on Infra main (above `keys_baseline`; CIS 263) or cannot be read. Applying 331 while 330 waits leaves 330
  out-of-order for auto-apply (AA-920). `--allow-out-of-order` bypasses this, and with it the ordering that Migration
  Sync and Migration Apply keep: use it only for a file you know is independent. `dbmig.sh` passes the flag through.
- Dev Migration Apply may apply the file itself (expand; contract when idle once AA-1032 part 1 lands): a key already
  in `registered_keys` is not dispatched. A red run passes (with a warning) only when its own log shows the apply
  lock was held (`exit code: 17`, nothing ran) and the key shows up within 5 minutes; any other red run is exit 1
  even when the key is registered (exit 9 commits and registers the file but needs hand cleanup), and the run's
  `exit code:` line is printed.
- Exit 0 applied and registered, 1 run red or key missing, 2 dispatch/run not found, 3 copy PR red, 4 refused
  (destructive, closed, out of order), 5 timeout.

## ship_open_prs.py

`python3 tools/github/ship_open_prs.py wf_85982363-f71 [--only Infra] [--extra-refs AA-1032] [--dry-run]`

- Reads the lane journal (`tools/workflows/lane.js`): the `prs[]` of the last result that has them, in merge order;
  a result with `ready=false` is refused unless `--allow-not-ready`.
- Checks all PRs before pushing any: worktree and branch exist, branch ahead of `origin/<base>`, no rebase in
  progress, no modified tracked file, conventional title without an issue id, `Refs AA-<n>` in the body and no
  Fixes/Closes phrase. Deleted files are listed as a warning.
- Pushes (never forced), opens the PR with the lane's title and body (or reuses the branch's open PR), appends the
  Claude Code attribution line when missing, checks the author is the App, and prints each PR's `live_steps`.

Pushes (S272): every push runs the repo's pre-push through `safe-hooks/pre-push`
(`git -c core.hooksPath=tools/github/safe-hooks push`), which drops `GIT_DIR` / `GIT_WORK_TREE` / `GIT_INDEX_FILE`
before running the repo's own `.githooks/pre-push`. Git exports them to a hook, and unit tests that run git in a temp
dir with them wrote into the real clone (core.bare, a fake user, fake commits, rewritten refs) in AA-CIS-App and the
root repo. The push limit is 900 s (`AA_PUSH_TIMEOUT`, 60..3600): the CIS fast hook runs ~5,000 unit tests.

## CI hygiene workflow (root ADR 0021 decision 5, layers 3 and 4)

`.github/workflows/ci-hygiene.yml`: daily 04:17 UTC `ci_hygiene.py --json` → `hygiene_issues.py sync --kind hygiene`;
weekly (Monday 04:47 UTC) `pin_freshness.py --json` → `hygiene_issues.py sync --kind pins`; `workflow_dispatch` with
`check` (caches / pins / both) and `apply` (off = plan in the run summary only).

- One open issue per finding type, found by label (`ci-hygiene`, `ci-pin-update`) and title marker
  (`[ci-hygiene:<type>]`, `[ci-pin:<key>]`). Types: `cache-over-threshold` (8 GB), `stale-caches` (1 GB or more in a
  repo), `external-downloads` (WL5), `unknown-public-repo`, `needs-permission`; pins: one per outdated pin key.
- Present → open, or edit when the finding changed; absent → close with a comment; unknown (a read failed) → leave.
  A run whose read failed ends red after the sync (`guard_runs.py` shows it at session start). Red is decided from
  the report (`hygiene_issues.py read-failures`), not from the check's exit code, which is 1 for any finding even when
  a read failed too.
- Reads: `aa-ecosys-ci-bot` token minted with Actions + Contents + Pull requests read, else the App without Actions,
  else `GITHUB_TOKEN` (root caches only); the `needs-permission` issue names what to grant. The App key sits only in
  the root environment `ci-hygiene` (deployment branches: master), never at repo level. Writes: `GITHUB_TOKEN`,
  `issues: write`, root repo only.
- By hand (read-only): `python3 tools/github/ci_hygiene.py --json > .tmp-session/r.json && python3
  tools/github/hygiene_issues.py sync --kind hygiene --report .tmp-session/r.json` prints the plan the workflow would apply.

## Tests

`python -m unittest discover -s tools/github -p 'test_*.py'` (offline: scripted `gh`/`aws`, real `git` in temporary
repositories). CI runs them in the root Docs lint workflow.
