# ADR 0014 — Repo visibility and GitHub plan: app repos public, root and Infra private, GitHub Free

- **Status:** Proposed (22/10/2026, S247). Records S241 D-14 / D-25 as an ADR; Nghiệp accepts (AA-901).
  Amended 22/10/2026 (S247): root and Infra made **public** for now, see "Amendment (S247, 22/10/2026)" below.
  Amended 23/10/2026 (S248, AA-981): visibility-switch precondition and secret scanning, see "Amendment 2" below.
- **Scope:** AA-Ecosys: org AdventureAsia365-Ecosys and its repos (AA-Ecosys, AA-CIS-App, AA-Booking,
  AA-TripPlanner-Web, AA-CIS-Infra, and AA-Partner when it is created under [ADR 0010](0010-aa-partner-app.md)).
- **Amends / Supersedes:** none.
- **Implements:** S241 D-14 / D-25 (app repos public, root private, GitHub Free; root made private 17/10/2026), DM-6.10
  (no account IDs, ARNs, network IDs, inventories or security reports in public repos), SEC-06
  ([where a page may live](../STYLE.md#where-a-page-may-live-sec-06)).
- **Related:** [ADR 0011](0011-github-app-identity-and-merge-rights.md) (agent identity and merge rights; the prod gate
  this ADR has to make enforceable), AA-880 (prod blueprint, the trigger), AA-866 (`main`-only secrets and OIDC trust).
- **Related Linear:** AA-901 (U-25), AA-981 (secret scanning guard).

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
- Moving a repo between public and private is an ADR amendment, not a settings change. Going from private to
  public has a precondition (Amendment 2): a full-history scan with the repo rules and rotation of every real finding
  **before** the switch.

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
| Secret scanning | GitHub secret scanning and push protection (free on public) + gitleaks in CI | gitleaks in CI: PR scan (`secret-scan.yml`) + full-history job (`secret-scan-history.yml`), in all six repos (AA-981); GitHub secret scanning only while the repo is public (paid on private) |

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

## Amendment (S247, 22/10/2026): root and Infra public until the coding phase ends

Decided by Nghiệp on 22/10/2026:

- **What changed:** AA-Ecosys (root) and AA-CIS-Infra were switched from private to **public**. The private repos'
  GitHub Free Actions minutes ran out on 22/10/2026, which blocked Terraform Apply and DB Migrate on AA-CIS-Infra.
  Decision 1's table stays the target; this is a temporary exception to it.
- **Consequence:** the DM-6.10 content of these two repos (account IDs, ARNs, network IDs, inventories, security
  reports, registers by name) is now public, in the current tree and in the whole git history.
- **Scan before the switch:** a full-history gitleaks scan of the root repo found no credential. In AA-CIS-Infra the
  history holds an old committed variables file that contains a DataForSEO
  API password and a `database_url` for the acc1 RDS that was destroyed on 09/07/2026 (AA-271), so that DSN no longer
  opens anything. Rotating the DataForSEO password is recommended; Nghiệp accepted the risk and chose not to rotate
  now (tracked in the [secrets register](../security/secrets-register.md), DataForSEO vendor row).
- **No secret in new commits:** while the repos are public, every commit to root and Infra is held to the public-repo
  rule (no credential, JWT, API key, cookie or tenant API key; gitleaks before committing audits and exports).
- **Plan:** both repos go back to private when the coding phase ends (Nghiệp). At that point, re-decide between
  paying for Actions minutes (budget) and a self-hosted runner for the private repos, and amend this ADR again.

## Amendment 2 (S248, 23/10/2026): precondition for a visibility switch, secret scanning on

Why: on 22/10/2026 an external scanner (GitGuardian) flagged a credential in AA-CIS-Infra history a few hours after
the switch to public. It sat in an old committed variables file that had left `main` earlier, but history kept it.
The pre-switch scan of S247 missed it: it ran gitleaks with the default rules, which do not flag `name = "value"` in
a tfvars file, and Infra's own PR check only reads the lines a PR adds. Handling of the historical findings is
tracked in the private record (Linear AA-981), not in this public page.

- **Precondition before any private → public switch** (a repo, or a fork or mirror of one):
  1. run a full-history gitleaks scan **with the repo's `.gitleaks.toml`** (not the default rules alone), over every
     branch, tag and pull request head (`refs/pull/*/head`, closed PRs included; a `git clone --mirror` has them):
     `git` mode with `--log-opts="--all --full-history --diff-filter=uxdb --diff-merges=remerge --no-renames"` and
     `* diff` in the git attributes file (gitleaks' default plus type changes, renamed files read whole, every file
     as text even with a NUL byte, and the content of merge commits; the rules are the gitleaks v8.30.1 defaults
     copied into `.gitleaks.toml` without gitleaks' global path allowlist, which skips text files such as `.svg`; no merge with three or more parents; check the log for git errors,
     gitleaks exits 0 when git fails; local command: header of the root `secret-scan.yml`);
  2. treat each finding as real until shown otherwise; **rotate** every real credential **before** the switch (a
     history rewrite is not enough: forks, caches and the GitHub event API keep old commits);
  3. pin the rotated or false-positive findings by fingerprint in `.gitleaksignore`, with a comment, so the
     full-history job starts green;
  4. right after the switch, turn on GitHub secret scanning and push protection (repo Settings → Code security, or
     the `security_and_analysis` field of the repos API) and read both back.
- **Public → private** (the plan when the coding phase ends): GitHub secret scanning stops on Free private repos;
  the gitleaks PR and full-history jobs stay and become the only scanner. They use private Actions minutes (about a
  minute a night per repo), to count in the re-decision above.
- **State on 23/10/2026:** all five repos are public with secret scanning and push protection on. Root and Infra
  run `secret-scan.yml` and `secret-scan-history.yml`: a PR scan (on `pull_request_target`, so GitHub always runs the
  base branch's copy of it; it also scans a squash preview of the PR) that reads its rules and baseline from the base commit (a PR that changes them
  needs the label `secret-scan-baseline-reviewed`), and a nightly full-history scan over branches, tags and PR
  heads, merge commits, renames and type changes included. A red result means the value is public: rotate it, even
  if it was force-pushed away. Same rules in both, incl. `credential-key-literal` for credential-named keys with literal values in tfvars,
  `.env*`, JSON and YAML. Historical findings are pinned by fingerprint.
- **Not yet covered:** the three app repos (AA-CIS-App, AA-Booking, AA-TripPlanner-Web) and AA-Partner have no
  full-history job; their full-history check with these rules is still a manual step (lesson log, AA-981).

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
