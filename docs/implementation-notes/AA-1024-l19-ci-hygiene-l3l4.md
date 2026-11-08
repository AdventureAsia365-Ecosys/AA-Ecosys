# AA-1024 lane l19 (S273): CI hygiene layers 3 and 4, artifact retention (root ADR 0021)

## Problem

ADR 0021 decision 5 asks for four automated hygiene layers. Layers 1 and 2 (workflow lint WL4/WL5/WL6 at PR time,
event and schedule cache clean-up) shipped in lanes l12, l14 and l15. Layer 3 (one issue per finding type, daily) and
layer 4 (a scheduled check of self-managed pins) did not exist, and decision 4's "artifact retention 14 days unless a
workflow says why" had no check. `ci_hygiene.py` measured everything at session start only, from the orchestrator's
own `gh` login.

## Decisions

- **One root workflow, two checks:** `.github/workflows/ci-hygiene.yml`, schedule daily 04:17 UTC (caches, after every
  repo's 02:41 Cache cleanup) and weekly Monday 04:47 UTC (pins), plus `workflow_dispatch` (`check`: caches / pins /
  both; `apply` off prints the plan only). A small `plan` job turns the event into a matrix list, because `matrix` is
  not available in a job-level `if:`.
- **The App key lives only in the root environment `ci-hygiene` (deployment branches: master only)** (review fix,
  S273). `aa-ecosys-ci-bot` has Contents / Pull requests / Issues write on the child repos and can merge there
  (ADR 0011a). A repo-level secret in the public root repo would be readable by a workflow edited on any branch an
  agent pushes (no required CI on root), whatever the job's `if:` says. The environment's branch rule is enforced by
  GitHub before the job starts, the same pattern as the app repos' `release` environment. Environment secrets are not
  visible in workflow-level `env`, so "is the App configured" is a step inside the job. A unit test
  (`test_hygiene_issues.Workflow`) keeps the key out of workflow-level env and in the environment job only.
- **Red comes from the report, not from the check's exit code** (review fix, S273). Both checks exit 1 for a finding
  before they look at failed reads, so a day with a finding and an unreadable repo / org list / upstream release was
  green. `hygiene_issues.py read-failures` lists the failed reads (unreadable repos; caches: org list error or
  missing; pins: any upstream `unknown`) and exits 3; the Measure step sets `degraded` from it (or from exit 2) and
  the last step fails the run. A cache list that returned 403 is not a failed read: it has the `needs-permission`
  issue, and the run stays green until the tech lead grants the permission (otherwise every day is red for a known,
  tracked gap).
- **Measure and write are separate steps with separate tokens.** Reads use an `aa-ecosys-ci-bot` installation token
  minted with read-only Actions + Contents + Pull requests on the six repos (`permission-*` inputs narrow the App's
  write permissions to reads). Issue writes use the run's `GITHUB_TOKEN` with `issues: write` on this repo only, so
  the App never writes here.
- **Degrade instead of failing on permissions.** The App has no Actions permission today (docs/security/github-apps.md
  part 5) and the root repo has no `AA_CI_BOT_APP_ID` / `AA_CI_BOT_PRIVATE_KEY` (checked 08/11). The workflow tries
  the App with Actions read, then the App without it, then `GITHUB_TOKEN`. `ci_hygiene.py` no longer drops a repo when
  only its cache list returns HTTP 403: the row gets `cache_error` and its workflows are still scanned. The sync then
  opens the `needs-permission` issue whose text lists exactly what the tech lead must grant, worded by token source.
- **Issue identity = label + title marker.** Labels `ci-hygiene` and `ci-pin-update`; markers `[ci-hygiene:<type>]`
  and `[ci-pin:<key>]` at the end of the title. One open issue per marker; a duplicate from a race is closed as "not
  planned" and the oldest kept. Closed issues are history: a finding that comes back opens a new issue.
- **Three-way status per type: present / absent / unknown.** Only `absent` closes an issue. A failed read (repo
  unreadable, cache 403, org list error, upstream release lookup error) makes the type `unknown`, which leaves the
  issue as it is. A present finding is still reported when other repos were not measured, with a "Not measured" note.
- **Bodies are deterministic.** The body is built from the finding only; the run link sits on a `_Last change:` line
  that the comparison ignores, so an unchanged finding is a no-op (no daily edit).
- **Stale-cache floor 1 GB per repo.** A live run at midday on 08/11 showed AA-CIS-App with 0.50 GB of idle
  merge-queue caches between the daily clean-ups; a 0.5 GB floor would open and close the issue every few days.
- **Layer 4 opens issues, not PRs** (the lane brief; ADR 0021 layer 4 said "opens a PR"; the ADR text now says issue).
  A pin moves in every repo that carries it, with a new sha256 checked against the release's own checksums file:
  that is a reviewed wave, not something a bot can verify. Sources: release-bin `pins.txt`, lychee `pins.txt`,
  `requirements*.txt` URL pins (the spaCy model), and `ghcr.io/<o>/<n>:<tag>@sha256:` images (the gitleaks image).
  The newest release is the highest non-draft, non-prerelease tag with the same prefix (`v`, `lychee-v`,
  `en_core_web_sm-`), so `lychee-lib-v*` and other spaCy models never count. A URL outside GitHub releases (the
  Session Manager plugin on S3) is listed as "manual" and never opens an issue.
- **WL7 lives in `ci_hygiene.py`, not in `workflow_lint.py`, for now.** `workflow_lint.py` must stay identical in the
  six repos and this lane edits the root only. WL7 runs as a warn-only step in the root Workflow Lint
  (`ci_hygiene.py --retention-scan .`, `::warning` annotations, exit 0) and in every `ci_hygiene.py` run over the six
  repos (count in the table, lines with `--verbose`). The rule: an `actions/upload-artifact` step needs
  `retention-days` of 14 or less, or a `# retention: <why>` comment inside the step or right above it; an expression
  value passes (cannot be checked).

## Changed

- `tools/github/ci_hygiene.py`: WL7 (`retention_findings`, `--retention-scan`), org public-repository check
  (`org_check`, `unknown_public`, `--no-org`; an unknown public repo makes the run RED), cache 403 → `cache_error`,
  `warn_gb` and `org` in the JSON, shared `tree_paths` / `read_remote` helpers.
- `tools/github/pin_freshness.py` (new): layer 4 discovery and release lookup, table or `--json`, `--local-root`.
- `tools/github/hygiene_issues.py` (new): report → findings → plan → `gh issue` writes; Markdown summary for the run.
- `.github/workflows/ci-hygiene.yml` (new); `.github/workflows/workflow-lint.yml` (WL7 warn step, trigger on
  `tools/github/ci_hygiene.py`); `.github/workflows/docs-lint.yml` (freshness artifact 30 → 14 days).
- Tests: `test_ci_hygiene.py` (+9), `test_pin_freshness.py` (8), `test_hygiene_issues.py` (24: +6 read failures,
  +2 workflow guards), fake `gh` only.
- ADR 0021 Status and Rollout lines; `tools/github/README.md`; docs/security/github-apps.md part 5 (root
  `ci-hygiene` environment, Actions read).

## Tradeoffs

- One issue per finding type (not per repo) keeps the issue list short; the body names every repo. A repo-level split
  would mean six times the issues for the same root cause (usually one workflow pattern copied to every repo).
- Org check reads `orgs/<org>/repos`: public repositories are visible to any token, so the check works with the
  fallback token too. A private repository created by a member is not flagged (not a public-exposure risk).
- Environment vs a second, read-only App: a dedicated App with only Actions + Contents read would keep any
  write-capable key out of the root repo entirely, but it is one more App, key and installation for the tech lead to
  create and rotate. The master-only environment closes the branch path at no cost; the dedicated App stays an option
  if root `master` itself is ever considered untrusted. Each run of the environment job records a deployment entry
  in the repo (harmless noise on a public repo).
- No auto-clean in the scheduled run: deleting caches needs `actions: write` on every repo; the per-repo Cache
  cleanup workflows already hold that right for their own repo.

## Should know

- Live counts on 08/11 (read-only, orchestrator `gh` login): caches CIS 7.18 GB, Booking 5.50, TripPlanner 3.02,
  Partner 2.29, root 0.03, Infra 0.01; no WL5, no unknown public repo. Pins outdated: syft 1.54.0 → 1.57.0, trivy
  0.70.0 → 0.76.2, oasdiff 1.33.0 → 1.36.0 (12 places each); actionlint, lychee, gitleaks, spaCy model current.
- WL7 over the six default branches (36 `upload-artifact` steps): 11 warnings, 10 after this PR (root fixed). CIS 1
  (ci.yml SBOM, no retention-days), Booking 2, Partner 2 (ci.yml without retention-days, docs-lint 30 days),
  TripPlanner 1 (docs-lint 30 days), Infra 4 (three DB probes and docs-lint at 30 days).
- `plan-sync.yml` already reads `AA_CI_BOT_PRIVATE_KEY` at repo level (not set on root today): a follow-up moves it
  to an environment as well; this lane does not touch it.
- Until the tech lead grants Actions read to the App, creates the `ci-hygiene` environment (master only) with the key
  in it and sets the App id variable in the root repo, the first scheduled run
  opens `needs-permission` and leaves the cache types `unknown` for the five other repos (the root's own caches are
  measured with `GITHUB_TOKEN`). Downloads, org and pins work with the fallback token.
