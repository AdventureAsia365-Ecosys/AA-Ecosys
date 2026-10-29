# S258 milestone evidence: M1b (AA-879) and M2a (AA-779 / AA-780)

Read-only check, 29/10/2026 21:45–21:55 +07, by the S258 "evidence-mermaid" lane (Claude Code). Sources: `gh api`
(branch protection, rulesets, check runs, workflow runs, repo settings) and `git` history on `origin/main`. No AWS
call, no LLM call, no GitHub write. Cost $0.

`origin/main` at the time of the check: AA-CIS-App `fb683750`, AA-Booking `73a9caf1`, AA-TripPlanner-Web `25e80647`,
AA-Partner `f6fb2c80`, AA-CIS-Infra `621085df`.

Raw data: [`data/branch-protection.json`](data/branch-protection.json) (branch protection + active rulesets + the
check runs of each repo's latest merged PR), [`data/gate-count.json`](data/gate-count.json) (gate registry counts),
[`data/count_gates.py`](data/count_gates.py) (the script that produced the gate counts).

## Verdicts

| Milestone | Criterion (plan.json) | Verdict | Tick in `plan.json` |
|---|---|---|---|
| M1b | AA-879: branch protection + required checks the same in the 4 app repos (AA-Partner included from the day it was created), scheduled Terraform drift job green once | **Not met.** Part A (protection) is met for the core policy, with 6 parity gaps (G1–G6). Part B fails: **no scheduled Terraform drift job exists** in AA-CIS-Infra | stays `false` |
| M2a | AA-779 / AA-780: no new gates for 4 weeks (the registry count does not grow) | **On track, not yet met (time-bound).** 0 new gates since the freeze started (S246, 21/10); the active gate count fell 28 → 26. The 4-week window ends about 18/11 | stays `false` until a recount on or after 18/11 |

## M1b — AA-879 branch protection parity

### What all four app repos share (met)

| Setting | AA-CIS-App | AA-Booking | AA-TripPlanner-Web | AA-Partner |
|---|---|---|---|---|
| Branch protection on `main` | yes | yes | yes | yes |
| Force-push / deletion of `main` blocked | yes (protection + ruleset) | yes (protection + ruleset) | yes (protection + ruleset) | yes (protection only) |
| Merge methods | squash only | squash only | squash only | squash only |
| Delete branch on merge | yes | yes | yes | yes |
| Required: `Security Audit`, `gitleaks` | yes | yes | yes | yes |
| Required: build / test of every deployable part | Lint, Unit Tests, Integration Tests, Docker Build Check, Frontend Build, Frontend Lint | Lint, Unit Tests, Integration Tests, Docker Build Check, Frontend Build | Backend (pytest), Frontend (lint + build), Migrations (lint, PG 15 replay) | Lint, Unit Tests, Integration Tests, Docker Build Check, Portal Build, Web Build |
| Every required check green on the latest merged PR | #1149: 8/8 | #147: 7/7 | #188: 5/5 | #122: 10/10 |
| Required reviews / enforce for admins | none / off | none / off | none / off | none / off |
| Every `main` commit since 22/10 came through a PR | 206/206 | 83/83 | 56/56 | yes (the only other commits are the repo's "Initial commit" and the portal history imported from AA-CIS-App, AA-979) |

AA-Partner was created 22/10/2026 23:50 UTC. Its first PR (#1, merged 23/10 02:53 UTC by the `aa-agent` App) already
ran Lint, Unit Tests, Integration Tests, Docker Build Check, Security Audit, Docs lint and PR title, all green. The
date the protection itself was switched on cannot be read back: the org audit-log API is Enterprise-only (404).

The check names differ by stack (TripPlanner has one backend and one frontend job, CIS / Booking / Partner split them
per tool). That is expected; parity here means "every deployable part has a required build + test check, plus the
shared `Security Audit` and `gitleaks`", which holds.

### Parity gaps

| # | Gap | Repos | Why it matters | Proposed fix (GitHub settings or a small CI PR, $0) |
|---|---|---|---|---|
| G1 | `Docs lint` and `PR title` are required only in AA-Partner. Booking and TripPlanner run both workflows on every PR (their files even say the merge queue "waits for the required" check) but branch protection does not list them. AA-CIS-App has no docs-lint or PR-title workflow at all | CIS, Booking, TripPlanner | A red docs lint or a `Fixes AA-…` / `[AA-…]` PR title merges anyway in 3 of 4 repos | Add `Docs lint` + `PR title` to the required checks of Booking and TripPlanner; port both workflows to CIS (copies of Booking's), then require them. AA-888 left this as an owner option; this criterion makes it needed |
| G2 | "Require branches to be up to date" is off in TripPlanner (on in the other three) and TripPlanner has no merge queue | TripPlanner | Two green PRs can merge on a stale base and break `main` together. CIS / Booking / Partner are covered by the merge queue | Turn on `strict`, or add the same merge-queue ruleset as the other three (AA-889 / AA-993) |
| G3 | CodeQL default setup is `not-configured` in AA-Partner (`configured` in the other three) | Partner | No code-scanning alerts for the CRM API, web and portal code (public repo, free) | Enable CodeQL default setup on AA-Partner |
| G4 | No "no force-push, no deletion (AA-867)" ruleset in AA-Partner | Partner | Same effect today through branch protection; differs only in form, so a later protection edit could drop it unnoticed | Add the same ruleset (deletion + non_fast_forward on `~DEFAULT_BRANCH`) |
| G5 | "Require linear history" is on only in AA-Partner | CIS, Booking, TripPlanner | Small: squash-only already gives a linear `main` | Turn it on in the other three, or off in Partner, so the four match |
| G6 | `Migration preflight` (CIS, Booking, Partner), `Vendored CIS copies` (Booking, Partner) and `OpenAPI breaking changes` (CIS, Booking) run on PRs but are required nowhere | CIS, Booking, Partner | A red preflight or a drifted vendored copy does not block the merge (S256 saw a red "Vendored CIS copies" in Partner #111) | Decide per check; at least `Migration preflight` should be required where it runs |

### Scheduled Terraform drift job (not met)

- AA-CIS-Infra has 29 workflows; none runs `terraform plan` on a schedule. `terraform-plan.yml` ("Terraform Plan
  (dev)") triggers on `pull_request` only, and its plan has no `-detailed-exitcode`, so even a PR run is green when
  the plan shows changes.
- The last 100 scheduled runs in AA-CIS-Infra come from 13 workflows (schema dump, isolation / freshness / liveness
  probes, connection budget, copy guards, docs gen, docs lint, secret scan, CRM key policy diff, migration apply /
  sync). None is a Terraform plan.
- The S246 master-plan audit already recorded this ("No scheduled Terraform drift detection",
  `docs/audits/2026-10-21-S246-master-plan/plan-and-status.json`); no PR has added one since (PR search "drift" in
  AA-CIS-Infra: only schema-drift and ERD-drift PRs).
- Good news for the fix: the plan role `aa-cis-infra-tf-plan` already trusts the `ref:refs/heads/main` subject (added
  for the nightly docs-gen, AA-893) and has `ReadOnlyAccess`. A scheduled workflow on `main` can assume it **without
  any IAM or Terraform change**.

Proposed job (one AA-CIS-Infra PR, workflow only): `.github/workflows/terraform-drift.yml`, `schedule` weekly (plus
`workflow_dispatch`), same init as `terraform-plan.yml`, `terraform plan -lock=false -detailed-exitcode -input=false`;
exit 0 = green, exit 2 = drift → job fails and the plan summary goes to the step summary, exit 1 = error. Weekly
rather than nightly because each plan makes about 10k CloudTrail management events (S255 FinOps audit §7), which would
matter once GuardDuty is on. After merge: one `workflow_dispatch` run green closes part B.

## M2a — AA-779 / AA-780 no new gates

The gate registry is `services/quality/taxonomy.yaml` (`gates:` map) with the constants in
`services/quality/registry.py` (AA-926, CIS #982, created 25/10/2026). The freeze is "no new gate, regex, lexicon or
repair loop for 4 weeks" from S246 / S247 (`docs/audits/2026-10-24-S250-s251-go-no-go/numbers.json`), i.e. from
21/10 to about 18/11 (the S257 AA-789 design reads it the same way: "no new gate and no new hold path before 18/11").

### Registry, commit by commit (all commits that touched `taxonomy.yaml`)

| Commit | Date | Entries | Active gates | Retired gates | Flags | Telemetry | Enforce detectors |
|---|---|---|---|---|---|---|---|
| `a8ec0fe4` registry created (#982) | 25/10 | 42 | **28** | 5 | 5 | 4 | 38 |
| `12b36a6b` per-finding severity (#992) | 25/10 | 43 | **26** | 8 | 5 | 4 | 37 |
| `3994a1a8` admin i18n (#1129, labels only) | 29/10 | 43 | **26** | 8 | 5 | 4 | 37 |

\#992 is a merge, not a new gate: AA-924 folded `F2_banned_patterns`, `F2_brand_forbidden` and the F15 stock list into
one ledger entry `F2_lexicon`, and retired `F2_banned_patterns`, `F2_brand_forbidden` and `F15_voice_warn`
(28 − 3 + 1 = 26). The entry total grew by one only because retired names stay in the registry for old ledgers. The
other sections did not change: 32 classes, 25 Jev questions, 3 chips, 3 code checks, 11 aliases. No open CIS PR
touches `taxonomy.yaml` or `registry.py`.

### Before the registry existed (code proxy)

For dates before 25/10 the script counts how many of today's 26 active gate names already appear as string literals
in `services/` or `api/` on `origin/main` at that date:

| Date | Commit | Today's active gates already in code | Missing |
|---|---|---|---|
| 01/10 (4 weeks before today) | `b1c4b9d7` | 8 | 18, all added 13/10–20/10 (below) |
| 21/10 (freeze start, S246) | `47ae118f` | 25 | `F2_lexicon` only (the #992 merge) |
| 24/10 (day before the registry) | `32ca42d7` | 25 | `F2_lexicon` only |
| 29/10 (today) | `fb683750` | 26 | — |

Gates added between 01/10 and the freeze: `F0_complete`, `F11_brand_name`, `F12_scope`, `F13_hygiene`, `F13_leak`,
`F13_repeat`, `F14_social_shape`, `F14_first_line`, `F15_voice`, `F16_faq`, `F17_trip_fact`, `F18_rarity` (13/10, T9
rounds AA-768 / AA-771, tenant brand pack), `F19_authenticity`, `T3_grounding` (15/10), `F2_platform_truth`,
`F2_superlatives`, `F2_style_warn` (20/10, CIS #869). So read literally as "the 4 weeks before 29/10", the count did
grow (8 → 26), but every addition predates the freeze; read as the criterion means it (4 weeks from the freeze start),
the count has not grown: 0 new gates and −2 active since 21/10.

Limits of the proxy: a gate whose name is built at run time would not show up; before #982 every gate name was a
plain literal or a `*_GATE = "…"` constant, so the proxy found them.

## Re-run

All single-line, read-only:

```bash
gh api repos/AdventureAsia365-Ecosys/AA-Partner/branches/main/protection --jq '.required_status_checks.contexts'
gh api repos/AdventureAsia365-Ecosys/AA-TripPlanner-Web/rulesets --jq '[.[]|{name,enforcement}]'
gh api repos/AdventureAsia365-Ecosys/AA-Partner/code-scanning/default-setup --jq .state
gh api repos/AdventureAsia365-Ecosys/AA-CIS-Infra/actions/workflows --jq '.workflows[]|.path'
python3 docs/audits/2026-10-29-S258-milestone-evidence/data/count_gates.py apps/AA-CIS-App
```

## Also checked in this lane: row 0v Mermaid labels (AA-898 follow-up)

Already fixed on `main`, no code change needed. CIS #1128 (`5b13ccf9`, 29/10 01:52 UTC, "fix: Mermaid labels in the
docs reader never break mid-word") sets `flowchart.wrappingWidth` per diagram from the widest word of the source
(`frontend/lib/mermaidWrap.ts`, clamp 200–480 px, unit-tested), and the S256 live check
(`docs/audits/2026-10-29-S256-ui-evidence/` row 7d, screenshot `07d-docs-mermaid-after.png`) read all 28 SVG labels
of `docs/ecosystem-architecture.md`: every break is at a space. The longest single token in any Mermaid block under
`docs/` is 39 characters (`gold_aa_internal.tenant_tour_versions`, about 310 px at 16 px), well under the 480 px cap.
The backlog row still says so (`docs/backlog/README.md` row 0v).
