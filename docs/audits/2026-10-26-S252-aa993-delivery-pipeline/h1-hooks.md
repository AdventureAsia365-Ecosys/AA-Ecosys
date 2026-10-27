# AA-993 H1 — pre-push hook, root repo (implementation notes)

Slice H1 of the AA-993 design (`design.md` in this folder, sections "D5 — Pre-push hooks" and "Phase B / H1").
Local only: no workflow file changed. Files: `scripts/pre-push.sh`, `scripts/install-hooks.sh`, `.githooks/pre-push`.

## Decisions

- **Checks come from the two required-path workflows, copied command by command.** `docs-lint.yml`: lint-tool unit
  tests, front-matter, PRD refs, ADR index, single-line AWS CLI, alarm runbook links, resource IDs (warn-only, never
  fails, as in CI), markdownlint-cli2 0.23.2 (the version the pinned action uses), lychee offline.
  `contracts.yml`: contract and ADR unit tests, `check_contracts.py`, `check_adr_numbers.py`. Each check prints the
  workflow step it mirrors.
- **Fast mode selects by the workflows' own path filters** on `git diff --name-only origin/master...HEAD`
  (`$AA_PREPUSH_BASE` overrides the base; `core.quotePath=false`, so non-ASCII paths match). A selected workflow
  runs all its checks, unit tests included: CI runs them on every trigger and they read live repo content
  (`docs/contracts`, `docs/adr`, `docs/templates`). If the diff fails (no merge base, shallow clone), every check
  runs. markdownlint runs on the changed `docs/**/*.md` files only, and on the whole glob when
  `.markdownlint-cli2.jsonc` or `docs-lint.yml` changed. The config's `ignores` still apply to explicit paths
  (checked: a journal page passed on the command line is not linted).
- **`check_adr_numbers.py --base origin/master` locally**; in `--ci` it uses `$BASE_SHA` like `contracts.yml`.
- **gitleaks is a local extra**, run on `origin/master..HEAD` only when a `gitleaks` binary is on PATH. `--ci` never
  runs it: CI keeps its own `pull_request_target` job, which reads the rules from the base commit (a PR must not be
  able to weaken it), so H2 must not move it into the script.
- **Python deps in a venv inside the common git dir** (`.git/aa-prepush/venv`), created by `install-hooks.sh` from
  `tools/docs/requirements.txt` + `tools/contracts/requirements.txt`. Never tracked, no `.gitignore` change, shared
  by every worktree. Reason: the system Python here has jsonschema 4.10 without `referencing`, so
  `check_contracts.py` fails outside a venv. `$AA_PREPUSH_PYTHON` overrides.
- **Missing optional binaries are skipped locally, red in `--ci`.** lychee and gitleaks are not installed on this
  machine; the hook prints "skip … CI still runs it" plus the install step (lychee v0.24.2, the lychee-action
  v2.9.0 default; gitleaks v8.30.1, the `secret-scan.yml` image; Node for npx). A present binary with another
  version warns (fails under `--ci`). The summary reads "passed with N skipped (CI still runs: …)". A missing Python dependency is a failure (with the install
  command), because it is a setup error, not an optional tool.
- **Hook input:** `.githooks/pre-push` passes git's stdin through; a push that only deletes refs exits 0 at once,
  and a push of a ref that is not HEAD prints a note (the checks read the checked-out tree). Uncommitted changes
  print a note too.
- `--plan` prints the selected checks without running anything; `--self-test` runs 32 fixtures (no lint tool
  invoked): check selection (unit-test rule, non-ASCII and spaced names), failure propagation through `run_check`
  and the summary, a missing tool (skip locally, fail under `--ci`), and hook input that only deletes refs.

## Review fixes (second commit)

- `set -euo pipefail` in the script and the hook; commands whose failure is data use `|| rc=$?` / `|| true`.
- `git diff` failure no longer lets a push through with only gitleaks planned: it switches to a full run.
- `.githooks/pre-push` blocks (exit 1, with the fix and the bypass) when `scripts/pre-push.sh` is missing, and runs
  it through `bash`, so a lost exec bit does not matter.
- `install-hooks.sh` recreates the venv (`--clear`) when it has no pip (a first `venv` without `python3-venv`).
- Cost of the wider unit-test rule: contract unit tests 8.3 s, ADR unit tests 0.2 s (measured 27/10).

## Changed vs. the spec

- The root repo has no coverage step, so `--full` here is "every check on the whole repo" (the CI-equivalent run).
- Not in this slice: the `aa-ship` note and root `tools/metrics/lead.py` / `ci_times.py` listed under H1 in the
  design (separate root change; the orchestrator owns `skill/aa-ship`). Recorded as a follow-up in the S252
  checklist so they do not drop.

## Tradeoffs

- No lychee locally: link breaks are still caught by CI only. Installing lychee (a single binary) turns the check on
  with no script change.
- `tools/finops/` and `tools/data/` tests are not in any root workflow, so the hook does not run them either (the
  hook mirrors CI; it does not add gates).

## Measured (27/10/2026, WSL2, throwaway clone with the hook installed)

| Run | Checks | Wall time |
|---|---|---|
| `--self-test` | 32 fixtures (after the review fixes) | 0.5 s |
| fast, diff touches `scripts/` only | gitleaks (skipped) | 0.36 s |
| fast, one clean catalog page (`docs/README.md`) | 9 selected, 7 ran | 2.5 s |
| fast, planted error (multi-line `aws` command in `docs/README.md`) | blocked, exit 1 | 2.3 s |
| `--full` | 14 selected, 12 ran | 15.5 s (contracts unit tests 11 s) |

The planted-error run printed `FAIL aws-multiline [CI: docs-lint.yml: Single-line AWS CLI]`, the exact command, and
the bypass line `git push --no-verify`. shellcheck 0.11.0 (`-S warning`, and at the default level) reports nothing
on the three files.

## Should know

- Install: `scripts/install-hooks.sh` (sets `core.hooksPath=.githooks` for the whole clone, all worktrees). A
  worktree on a branch older than this change has no `.githooks/pre-push`, so git runs no hook there.
- Full run on a push: `AA_PREPUSH=full git push`. Bypass once: `git push --no-verify`. Remove:
  `scripts/install-hooks.sh --uninstall` (or `git config --unset core.hooksPath`).
- H2 (CI calls `scripts/pre-push.sh --full --ci`) must give the runner lychee and Node, or keep the lychee and
  markdownlint action steps and exclude those two ids; and add `scripts/pre-push.sh` + `.githooks/` to CODEOWNERS.
