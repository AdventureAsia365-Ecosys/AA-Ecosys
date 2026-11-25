# AA-1024: ship tool guards from the S285-S294 lessons (lane l11-ship-guards, S294)

Four lessons were still "Guard: pending" or "none": a second PR-opener run opened duplicates of merged PRs (S292, root
#1000 and CIS #1683), lane bodies named other issue ids and the PR title check refused them (S292, two root PRs), two
wave runs on one Partner PR broke its merge push (S285, Partner #357), and an app PR whose "Vendored CIS copies" check
reads root master ran before the root PR merged (S282, Partner #325 and root #832). S294 added a fifth: the scheduled
guard report showed Catalogue and Image Scan red after a green hand dispatch had already fixed them. This lane turns
them into checks in the three root tools; `ship_common.py` is untouched (lane l9 owns it in this wave).

## Decisions

- **PR opener, merged branch**: one `gh pr list --state merged --head <branch>` per PR before validation. A hit is a
  `SKIP` line (not a refusal), so the rest of the lane still opens and the exit stays 0; "every chosen branch already
  merged" says so and exits 0. A failed lookup refuses that PR (exit 4): opening blind is how the duplicates happened.
- **PR opener, body rules read the final body**: `validate()` now checks `final_body()`, the text `gh pr create`
  receives (after `--refs`, `--extra-refs`, the skip-integration note and the attribution line). Before, the raw lane
  body was checked, so `--extra-refs` could not rescue a body with no Refs line (S294), and the orchestrator could not
  accept a mentioned id by adding it to the Refs line.
- **`--refs`**: a body with no Refs line gets `Refs AA-<n>[, AA-<m>]` as its first line (the lane rule asks for the
  Refs line first); on a body that has one the ids join its id list, like `--extra-refs`. The missing-Refs refusal
  names the flag.
- **Stray ids**: the existing `stray_issue_ids()` rule (same as every repo's `pr-title.yml`) already refused them; the
  new test covers the S292 shape (history told with other ids) and the opt-in through `--extra-refs`.
- **project-template**: `NO_ISSUE_ID_REPOS`. No Refs line needed, any `AA-<n>` in the title or body refused (the repo's
  denylist would fail the PR anyway), and `--refs` / `--extra-refs` are not applied there (a warning says so), so one
  `--extra-refs` for a whole wave does not break the template PR.
- **Wave, per-PR lock**: `fcntl.flock` on `.tmp-session/ship-locks/<Repo>-<n>.lock` (under `ROOT`, so every worktree
  copy of the tool shares it). flock dies with the process, so a killed run leaves no stale lock and no pid check is
  needed; the file holds pid, start time and argv for the refusal message. All locks are taken before anything else
  (after the plan print); one busy PR refuses the whole wave (exit 4) and releases what it took. `--dry-run` and
  `--check-only` take none (they merge and push nothing).
- **Wave, `@after=<Repo>#<pr>`**: an entry with `#` in the `@after=` list is a PR, anything else a migration, so the
  two mix. A PR in the wave is waited on through its `merge_done` event; one outside the wave must already be MERGED at
  start (`check_pr_holds`, exit 2). Self-waits and circles (also through a migration another PR applies) are refused
  at parse time, because a circle would hang the workers.
- **Re-run after the dependency merged**: the app PR's checks usually ran before the root merge, and the gate refuses
  a red check at once, so waiting alone is not enough. Once the PRs it waits for merged, the latest red run per
  (workflow, event) on its head is re-run once (`gh run rerun <id> --failed` through `as-app.sh`), then a 30 s settle,
  then the normal gate. A refused re-run is a WARN with the hand command and the gate reports the red check. A head
  that the stacked-branch restack just pushed runs every check anew, so no re-run then.
- **Scheduled guard report**: for a red latest scheduled run only, one lookup of that workflow's runs on the default
  branch (`actions/workflows/<id>/runs?branch=<default>`); the newest green `workflow_dispatch` or `push` run created
  after it marks the row `superseded (green <event> <time>)`, not counted red. A failed lookup leaves it red.

## Changed

- Only `tools/github/` (the opener, the wave shipper, the scheduled guard report and their tests) and the tools
  README; `ship_common.py` untouched as the lane brief asks.

## Tradeoffs

- A merged branch is skipped, not refused: the S292 case was a re-run of a partly shipped lane, where refusing would
  block the PRs that still need opening.
- The lock is per PR, not per wave: two waves on different PRs still run side by side, as before.
- Re-running only the red runs (not every run) keeps CI cost at the S282 case; a pending run is left to the gate.
- `--check-only` holds no lock: a check-only read beside a real run is harmless and useful while waiting.

## Should know

- The App needs `actions: write` for the re-run; if the installation lacks it the WARN line names the hand command.
- No setting was added: the 30 s re-run settle is a tool timing constant like the existing `SETTLE_SECONDS`, not a
  product threshold.
- The lessons (S282, S285, S292 x2) can be marked guarded at close by the orchestrator; this lane does not edit
  `lessons.md`.
