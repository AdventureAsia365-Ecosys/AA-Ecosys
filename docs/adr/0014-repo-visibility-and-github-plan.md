# ADR 0014 — Repo visibility and GitHub plan: app repos public, root and Infra private, GitHub Free

- **Status:** Proposed (22/10/2026, S247). Records S241 D-14 / D-25 as an ADR; Nghiệp accepts (AA-901).
- **Scope:** AA-Ecosys: org AdventureAsia365-Ecosys and its repos (AA-Ecosys, AA-CIS-App, AA-Booking,
  AA-TripPlanner-Web, AA-CIS-Infra, and AA-Partner when it is created under [ADR 0010](0010-aa-partner-app.md)).
- **Amends / Supersedes:** none.
- **Implements:** S241 D-14 / D-25 (app repos public, root private, GitHub Free; root made private 17/10/2026), DM-6.10
  (no account IDs, ARNs, network IDs, inventories or security reports in public repos), SEC-06
  ([where a page may live](../STYLE.md#where-a-page-may-live-sec-06)).
- **Related:** [ADR 0011](0011-github-app-identity-and-merge-rights.md) (agent identity and merge rights; the prod gate
  this ADR has to make enforceable), AA-880 (prod blueprint, the trigger), AA-866 (`main`-only secrets and OIDC trust).
- **Related Linear:** AA-901 (U-25).

## Context

The org is on **GitHub Free**. On Free, several controls work only in public repositories (checked 22/10/2026 with
read-only `gh api` calls):

- Branch protection on AA-Ecosys and AA-CIS-Infra answers `403 Upgrade to GitHub Pro or make this repository public`.
- The three public app repos have branch protection on `main` with required checks (AA-CIS-App 5, AA-Booking 5,
  AA-TripPlanner-Web 3) and no required reviews.
- AA-CIS-Infra's `prod` environment exists but cannot carry a deployment-branch rule or a required reviewer
  (comment in `terraform-apply.yml`, AA-866).
- Code owners, rulesets and environment protection rules follow the same split: public repos on Free, private repos
  only on a paid plan.

Actions minutes are unlimited on public repos and 2,000 a month on private ones. In September the app repos used
about 8,245 minutes; on private repos that would cost about 37 USD a month (D-14 record, S241).

ADR 0011 needs an enforced human review on risky PRs from the first prod. This ADR says where GitHub can enforce it
and what stands in for it where GitHub cannot.

## Decisions

### 1. Visibility per repo

| Repo | Visibility | Why |
|---|---|---|
| AA-CIS-App, AA-Booking, AA-TripPlanner-Web | **public** | Free CI minutes, branch protection and code owners on Free; code holds no account data (DM-6.10 scans in CI) |
| AA-Partner (when created) | **public** | Same as the other apps (ADR 0010 decision 1) |
| AA-Ecosys (root) | **private** | Account map, security and infra reports, audits, registers by name, commercial notes (D-25) |
| AA-CIS-Infra | **private** | Terraform with account IDs, ARNs and network IDs; generated IAM and network tables |

- A new app repo is public by default; a new repo that holds infrastructure, operations or business records is private.
- Moving a repo between public and private is an ADR amendment, not a settings change.

### 2. Plan: GitHub Free

- The org stays on GitHub Free (0 USD). GitHub Team, Enterprise and GitHub Advanced Security for private repos are not
  bought now (handbook "not now" list).

### 3. What enforces the gates on each side

| Control | Public app repos | Private repos (root, Infra) |
|---|---|---|
| Required status checks before merge | branch protection (live) | none on GitHub; the agent runs the checks and reads the result before `gh pr merge` (root rule); Infra CI runs on every PR |
| Human review of risky PRs (from prod, ADR 0011 decision 4) | CODEOWNERS + "Require review from Code Owners" | not enforceable by GitHub on Free; see decision 4 |
| Secrets only for `main` | environment with a `main`-only branch policy | repo or environment secret plus a job guard `if: github.ref == 'refs/heads/main'` (AA-866) |
| AWS access from CI | OIDC trust limited to `refs/heads/main` or a named environment | same; the apply role's trust is the real fence |
| Secret scanning | GitHub secret scanning (free on public) + gitleaks in CI | gitleaks in CI (root docs-lint, Infra secret-scan) |

### 4. Prod trigger: re-decide for the private repos

At the first prod or the first paying tenant (AA-880), Nghiệp picks one of these for AA-CIS-Infra and the root repo,
with this ADR amended to record it:

| Option | What it gives | Cost (list price, check before buying) |
|---|---|---|
| **A. GitHub Team for the org** | Branch protection, code-owner review, rulesets and environment reviewers on the private repos | about 4 USD per user per month; 1–2 seats |
| **B. Stay on Free, add compensating controls** | Terraform Apply and DB Migrate `apply` run only from a manual dispatch by Nghiệp (`github.actor` check in the job) or need a second, approver-held input; risky root PRs listed in the session report for review after merge | 0 USD |
| C. Make Infra public | Free enforcement | Rejected: account IDs, ARNs and inventories would be public (DM-6.10) |

- Default proposal at the trigger: **B** while Nghiệp is the only engineer; **A** when a second person gets write
  access or a customer audit asks for enforced review evidence.

## Consequences

- **Positive:**
  - 0 USD for GitHub; CI minutes on the app repos stay free;
  - ADR 0011's prod gate is enforceable on the public app repos with no purchase;
  - the decision is written down, so a later settings change cannot silently flip a repo.
- **Negative / cost:**
  - root and Infra have no GitHub-enforced checks or reviews; the gates there are workflow guards, OIDC trust and agent
    discipline;
  - the CODEOWNERS files in root and Infra are ready but inert until option A;
  - public repos need the DM-6.10 hygiene on every PR (resource-ID scans already run in CI).
- *(est., per month)*: 0 USD now; option A about 4–8 USD if chosen at the trigger.

## Alternatives considered

- **Everything private on GitHub Team now.** About 37 USD a month in Actions minutes plus seats, for gates the dev
  phase does not use (D-13 self-merge). Rejected (D-14).
- **Everything public.** Rejected: the root repo holds commercial notes and security reports, Infra holds account
  identifiers (D-25, DM-6.10).
- **Infra public with identifiers moved to variables.** Large refactor of Terraform and generated docs for little gain
  while option B costs nothing. Not now.

## Follow-ups

- AA-880: at the trigger, choose A or B for the private repos and amend this ADR; turn on code-owner review on the
  public repos (ADR 0011).
- AA-933: AA-Partner created public with branch protection and the DM-6.10 scan from the first commit.
- On acceptance: status line here and in the index; handbook D-14 row links this ADR.
