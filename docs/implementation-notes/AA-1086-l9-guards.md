# S281 lane l9 — tooling guards for four session lessons (root repo)

Scope: root repo tooling only (`tools/github`, `tools/uat`, `scripts/pre-push.sh`, `.claude/hooks`, skills, lessons
log). The lessons came from the S281 pending file: the mise gitleaks shim (pre-push and the PR opener), migration
applies refused while a tour lifecycle drill kept `shared.job` busy, a PASS UAT take lost with its worktree, and the
agency time zone in AA-Partner date tests (already fixed in AA-Partner #314).

## Decisions

- **One resolver module, `tools/github/gitleaks_resolve.py`**, not a function inside `ship_common.py`: the root
  pre-push is bash and calls it as a CLI, the PR opener imports it; keeping it stdlib and standalone means the hook
  does not import the ship tools (which the subagent hook guards by name).
- **Order:** `AA_GITLEAKS` (wins as given when it runs; the caller still checks the version), then
  `<root>/.tmp-session/gitleaks-8301/gitleaks` only at the CI pin, then every `gitleaks` on PATH (first at the pin,
  else the first working one so the caller can report the version gap). A candidate whose `gitleaks version` fails
  or prints no version is skipped and named in the message.
- **Pre-push looks in two roots:** the checkout it runs in and the clone's main checkout (`git rev-parse
  --git-common-dir`), because a lane worktree has no `.tmp-session` of its own. No working gitleaks is a skip with the
  reason (as before for a missing binary), never a block: CI's Secret Scan still runs.
- **Busy job tables are read from the refusal, not the database:** the wave tool has no AWS. `ship_copy_apply`
  recognises the DB Migrate run's own lines (`exit code: 7`, `##[error]apply refused: a job table is busy`,
  `MIGRATE ERROR: refusing apply — busy`), anchored at the line start like the lock-held check so the printed step
  script does not match, and builds the kinds from the last `MIGRATE busy:` report per table.
- **Exit 7 = held** for both `ship_copy_apply` and `ship_wave` (same number as DB Migrate's own refusal). In the wave a
  real failure (1-5) anywhere wins over 7, so a hold never hides a failure; a held migration holds the owner's higher
  numbers (owner order) and the `@after=` PRs on them, which report "held", not "skipped".
- **Resumable means "run the same command again":** merged PRs are reported as already merged by the merge gate and a
  registered key is not dispatched again, so no state file is needed.
- **`--wait-idle N`** re-dispatches the held apply up to N times; the 5-minute spacing is a CLI flag of orchestrator
  tooling (`--wait-idle-interval`, hidden), not an app threshold: there is no admin settings page for root tools.
- **UAT marker = `out/packages/<stem>.uploaded`** (JSON: zip name, size, sha256, remote, time), written only after
  `rclone check --one-way --include <stem>.zip` exits 0. A zip changed after the check is pending again.
- **The cleanup guard is a hook rule (`aa_shell_guard` UAT-1)** on `git worktree remove` and `rm -r`, because no
  session cleanup tool exists: the session skill step 7 says "dọn worktree" and agents run the git command by hand.
  Override, logged: `AA_UAT_DISCARD_TAKES=1`.

## Changed

- `ship_open_prs.gitleaks_bin()` now takes the runner and returns the resolver's result (path, version, skipped).
- `ship_copy_apply.main()` gained an optional `report` dict (the wave reads `held` from it); the default wave apply
  function returns `(exit, held kinds)`; a test apply function may still return a bare int.
- The wave plan prints a note about the idle rule whenever the wave applies migrations.
- Docs lint runs the new UAT check tests and its path filter includes the tool (the hook tests load it).

## Tradeoffs

- The hook loads `tools/uat/check_takes_uploaded.py` by path from its own checkout; if it cannot load, the rule
  passes (fail open, like every rule of the hook).
- The main checkout's `tools/uat/out` still lists older PASS takes without markers (packaged before the marker
  existed); the rule only fires on removing a directory, and the main checkout is never removed.
- `tools/linear/linear_export.py` still resolves gitleaks its own way (`GITLEAKS_BIN`, then PATH): same shim risk,
  left as a follow-up to keep this lane to the named tools.

## Should know

- Lessons written to `skill/aa-lessons/lessons.md` (three under "Vận hành", one under "Verify và Done"); the
  orchestrator drops the matching lines from the session pending file. The ruleset-token lesson of the same pending
  file stays with the orchestrator (`none:` guard, not in this lane).
- Tests: `python -m unittest discover -s tools/github -p 'test_*.py'`, `.claude/hooks`, and
  `tools/uat/tests/test_check_takes_uploaded.py`; `scripts/pre-push.sh --self-test` covers the bash wiring.
