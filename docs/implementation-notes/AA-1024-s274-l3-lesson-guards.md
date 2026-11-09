# AA-1024 — S274 lane l3: four pending S273 lessons become guards

## Decisions
- **Merge-queue exit 4 (lesson S273, four CIS PRs queued at once).** Two layers: `tools/github/mergeq.sh` gets
  `held()` (queue `entries` of `mergeQueue(branch: main)` plus unfinished `merge_group` runs whose head branch is
  `gh-readonly-queue/main/pr-<n>-`), read before it prints "not merged and not in the queue"; while either holds the PR
  it keeps waiting. `ship_merge.py` adds the same read (`queue_hold`, `_wait_out_queue`) when the queue wrapper exits 4
  with that line and the PR is not merged. Other exit-4 reasons (DIRTY, enqueue failed, "dropped") are not
  second-guessed. A failed read counts as "nothing holds it" (the old verdict stands, never an endless wait); the wait
  is bounded by `--queue-timeout`.
- **PIPE-1 in `.claude/hooks/aa_shell_guard.py`.** Refuses `<ship step> ... | tail|head|tee ... && <next>` without
  pipefail. Ship steps: the `ship_*.py` tools, the migration dispatcher, the merge-queue wrapper and the App wrapper.
  Pipefail counts when set earlier in the same shell text (`set -o pipefail`, `set -euo pipefail`, `setopt pipefail`)
  or on the `bash -o pipefail -c` that runs the text (new `Text.pipefail`). Subshells, groups and `$(...)` are
  transparent (their status is the pipeline's). `grep` is not a sink (it keeps its own code).
- **WL8 in `tools/github/ci_hygiene.py`.** No allow-list file existed in the repo (the org setting is not readable with
  the CI or local token: admin:org), so `tools/github/actions-allowlist.txt` is new: the record of the org setting, one
  GitHub pattern per line, seeded from the third-party `uses:` on the six default branches (8 actions) plus
  `aquasecurity/setup-trivy@*` (run inside trivy-action). WL8 follows each third-party composite action at its pinned
  SHA (contents API, 3 levels) and flags any direct or nested `uses:` no line covers, whatever the step's `if:`.
  RED in the session table and a new `actions-not-allowed` issue type in `hygiene_issues.py`. An action file that
  cannot be read is a `???` line (`wl8_unread`), not RED.

## Changed
- The lane brief said "the org Actions allow-list file the tool already uses"; there was none, so the file is created
  here and must be kept equal to the org setting by the org owner (the file's header says so).
- Lessons: the four lines in `skill/aa-lessons/lessons.md` now name their guards.

## Tradeoffs
- PIPE-1 includes the App wrapper (a push piped through tail, then `&&` opening the PR): the transcript replay finds
  80 hits, 67 of them that push-then-open shape. Same failure class (a red pre-push still opens a PR on the old remote
  head); the fix is one `set -o pipefail;` prefix.
- WL8 matches GitHub's pattern semantics with `fnmatch` (case-sensitive; `owner/repo@*` does not cover
  `owner/repo/sub@ref`). Patterns are `@*` rather than SHAs: the SHA pin lives in the workflows (Dependabot moves it).

## Should know
- Live check (read-only, local checkouts): `python3 tools/github/ci_hygiene.py --json --no-org --local-root .` gives
  `wl8: []` for all six repos with the shipped list; without the setup-trivy line it reports exactly the S273 case
  (AA-CIS-App ci.yml trivy-action -> setup-trivy).
- The merge-queue wrapper tests run the real script against a scripted `gh` and a no-op `sleep` on PATH
  (`test_ship_merge.py` `MergeqScriptTest`), so the shell path is covered, not only the Python wrapper.
