# ADR 0021 — GitHub organisation security and CI/CD hygiene: org-level controls first, repos stay public, zero added cost

- **Status:** **Accepted** (tech lead, S273, 08/11/2026): decisions 1–6. Decision 7 records the evaluation; it buys
  nothing. Rollout (S273): layers 1–4 of decision 5 and the artifact-retention check of decision 4 are built (see the
  Rollout column); the org settings of decision 2 and the App permission of layer 3 wait for the tech lead.
- **Amends:** [ADR 0014](0014-repo-visibility-and-github-plan.md) decision 4 (the prod trigger). Org-level controls
  come first at the trigger. Making repos private is the last option, and it needs a new decision with a cost line.
- **Respects, unchanged:** ADR 0014 decisions 1–3 and Amendment 2 (full-history scan before any visibility switch),
  [ADR 0011](0011-github-app-identity-and-merge-rights.md) (agent identity and merge rights), DM-6.10 and SEC-06
  (what may live in a public repo), the cost rule (no paid service without an explicit yes on that item).
- **Scope:** the GitHub organisation AdventureAsia365-Ecosys and its six repos (AA-Ecosys, AA-CIS-App, AA-Booking,
  AA-Partner, AA-TripPlanner-Web, AA-CIS-Infra): org settings, Actions policy, CI caches, external downloads in CI, and
  the path from public to private.

## Context

**Measured on 08/11/2026 (S273):**

- Plan GitHub Free; 2 members, 0 outside collaborators; 2FA required; base repository permission `read`.
- All six repos: secret scanning and push protection on, Dependabot security updates on, `CODEOWNERS` present.
- Gaps: members may create public repositories (not changeable on the Free plan) and change repository visibility. New repositories do not get secret
  scanning, push protection or Dependabot alerts by default. The org Actions policy (allowed actions, default
  `GITHUB_TOKEN` permissions) could not be read with the token in use (needs `admin:org`). It is listed in the
  follow-ups as "verify".
- Actions caches: AA-CIS-App 10.7 GB, over the 10 GB per-repository limit (GitHub then evicts the least recently used
  entries). AA-Booking was at 9.2 GB. About 7.5 GB of the CIS cache sat on pull-request and merge-queue refs. After
  the S273 clean-up, CIS was at 5.8 GB and Booking at 5.2 GB.
- On 08/11 GitHub throttled unauthenticated release downloads. Three tools that CI fetched from `github.com/.../releases`
  on every job were affected: the spaCy model wheel, the lychee binary and the Syft installer. PRs were ejected from
  the merge queues for hours. spaCy and lychee are now cached, sha256-pinned and fetched through an authenticated
  `gh release download` (AA-CIS-App #1388; lychee in five repos). Syft is not yet covered.

**CI volume depends on development pace, not on production traffic.** October 2026 was the busiest build month:
1,991 merged PRs, about 82,600 runner minutes (about 41 minutes per PR before the S271 CI trim). Production traffic
adds no CI minutes. The pace of change does.

| Phase | Merged PRs per month (est.) | Runner minutes per month (est., about 20 min per PR after S271) |
|---|---|---|
| Build burst (Oct 2026) | ~2,000 | ~80,000 (measured) |
| Normal after go-live | 150–300 | 3,000–6,000 |
| Maintenance | 50–100 | 1,000–2,000 |

These are estimates for planning, not measurements. Re-measure from the org billing usage every month (C8 review).

**What a private repository loses on GitHub Free** (GitHub docs, checked 08/11/2026; re-check before any switch):

| Feature | Public (any plan) | Private on Free |
|---|---|---|
| Merge queue (CIS, Booking, Partner ship through it) | yes | only on Enterprise Cloud |
| Branch protection and rulesets (required checks) | yes | needs Team or higher |
| Environments and environment secrets | yes | needs Team or higher; required reviewers only on Enterprise |
| Secret scanning, push protection, CodeQL | free | paid add-ons (Secret Protection, Code Security), per active committer |
| Runner minutes | free | a monthly allowance (2,000 minutes on Free), then billed |
| Workflows that read another repo | `GITHUB_TOKEN` or no token works | needs an App or fine-grained token for each private repo |

So making the code repos private would remove the controls that enforce review and CI today. In the normal and
maintenance phases it would also add a monthly bill, even though those phases need fewer minutes.

## Decisions

### 1. Repos stay public; visibility is not the security control

Security does not depend on the source being hidden. It rests on what is already enforced: no secret in git (push
protection and gitleaks in CI), the public-safe writing rule (DM-6.10, SEC-06), OIDC to AWS with trust limited to
`main` or a named environment, least-privilege GitHub Apps (ADR 0011), branch protection and merge queues (free while
public), and `CODEOWNERS`.

### 2. Organisation-level hardening, free on the Free plan

The tech lead (org owner) applies these once. Each is a setting, not a purchase:

1. Only owners change repository visibility, delete or transfer repositories (Member privileges: visibility change
   and deletion/transfer unticked). On the Free plan GitHub does not let an org stop members from creating public
   repositories (the setting is locked, checked in the org settings on 08/11/2026). Compensation: the member list
   stays minimal (two accounts today), visibility of existing repositories cannot be changed by members, and the
   daily hygiene check (decision 5, layer 3) flags any repository that is new or public and not in the known list.
2. Defaults for new repositories: secret scanning, push protection and Dependabot alerts on.
3. Actions policy:
   - allow GitHub-owned actions plus an explicit list of third-party actions pinned by full SHA;
   - default `GITHUB_TOKEN` permissions read-only;
   - require approval before workflows run for first-time contributors.
4. Personal access tokens: fine-grained tokens need owner approval for org access; classic tokens are refused for the
   org where GitHub offers the setting.
5. GitHub Apps reviewed once per quarter with the access review (DM-8.10): only the permissions in use stay.
6. **Actions and Packages spending limit set to 0 USD**, so no feature or overage can create a bill without a new
   decision.
7. 2FA requirement kept.

### 3. Confidential material never goes into the code repos

Security reports with privilege paths, inventories, `terraform.tfvars` values and anything a customer contract calls
confidential stay out of all six repos: in Linear, the local secret manager folder, or AWS Secrets Manager. If such
material ever needs version control, it goes into **one small private repository** (free on the Free plan) that no CI
gate depends on. The code repos stay public. That repository does not exist today. It is created only when the first
such file needs history.

### 4. Private-ready engineering, done now, free

These keep any later visibility switch from breaking CI. Each one is also good practice while public:

- Every workflow that reads another repository uses a GitHub App installation token (`aa-ecosys-ci-bot`, read-only
  contents) instead of relying on public access.
- No CI step depends on an unauthenticated download. External tools are cached, sha256-pinned and fetched with an
  authenticated client (decision 5).
- Artifact retention is short (default 14 days unless a workflow states why it needs longer). Checked by workflow
  lint rule WL7 (warn): an `actions/upload-artifact` step without `retention-days`, or above 14 days without a
  `# retention: <why>` comment, is a warning (`tools/github/ci_hygiene.py`; root Workflow Lint and the daily hygiene
  run). On 08/11/2026: 36 upload steps in the six repos, 10 warnings left after the root fix; WL7 moves into the shared
  `workflow_lint.py` in one wave once they are cleared.
- Runner minutes are tracked in the monthly C8 review against the phase table above.

### 5. CI/CD hygiene in four automated layers

Nobody checks these by hand. The session start only reads the result.

| Layer | What it does | Rollout |
|---|---|---|
| 1. Policy as code at PR time | A workflow lint fails a PR that adds an external download without cache + sha256 pin + authenticated fetch, or an unpinned third-party action | warn mode first, then enforced |
| 2. Event and schedule clean-up | A closed PR's caches are deleted. A daily job deletes merge-queue caches older than 2 hours. Caches are saved only on the default branch; PRs and merge-queue runs restore them | at once |
| 3. Alerts as one issue | A daily job measures cache use per repo (threshold 8 GB of the 10 GB limit), stale caches and uncached downloads, and lists public repositories not in the known list. It opens or updates one issue per finding type and closes it when the finding clears. It reads through an App token with read-only Actions permission | built S273: root `.github/workflows/ci-hygiene.yml` (daily) + `tools/github/hygiene_issues.py`. Until the App has Actions read and its id/key are set in the root repo, the run measures only the root's own caches and keeps a "needs permission" issue open |
| 4. Dependency updates | Dependabot for actions, pip and npm (already on). A scheduled check opens an issue (not a PR) when a self-managed pin (lychee, spaCy model, Syft, Trivy, actionlint, oasdiff, the gitleaks image) has a newer release. No auto-merge for third-party updates: CI and review first | built S273: the same workflow, weekly, `tools/github/pin_freshness.py`; one issue per outdated pin |

The root tool `tools/github/ci_hygiene.py` holds the checks (layers 1 and 3) and can also be run by hand;
`tools/github/pin_freshness.py` holds layer 4. Layer 4 opens an issue rather than a PR (S273): moving a pin needs a new
sha256 checked against the release's own checksums file in every repo that carries it, which is a reviewed wave.

### 6. Cost guard

This ADR adds **0 USD**. Every control is a setting, a workflow on free public runners, or code. The spending limit
(decision 2.6) keeps it that way.

### 7. Evaluated, not chosen: making repositories private

Making repositories private is reconsidered only on one of these triggers:

1. a customer contract or audit requires private source;
2. a security finding shows that public source exposes a risk that decisions 1–4 cannot remove.

The options then, each with a cost line to approve first:

1. Make private only the repository the trigger names, and keep the others public.
2. GitHub Team for branch protection and environments on private repositories. It has no merge queue, and required
   reviewers still need Enterprise.
3. Enterprise Cloud, which also keeps merge queues.

Use the phase table to size runner minutes, not the build-burst month. Self-hosted runners are allowed only on private
repositories (on public repositories anyone's PR could run code on them).

## Consequences

- No new monthly cost. Visibility stays as today. The settings in decision 2 close the "member makes a repository public
  by mistake" gap.
- CI depends less on GitHub's public download path and keeps its caches inside the 10 GB limit without manual clean-up.
- Org settings and the spending limit need an org owner. The agent's tokens cannot change them, by design.
- A later switch to private is a planned, costed decision, not an emergency.

## Alternatives considered

- **Make all six repos private now:** rejected. It removes merge queues, branch protection and free secret scanning
  on the Free plan, and adds a runner bill, with no customer or audit asking for it.
- **Move every confidential document into the root repo and make only the root private:** rejected for now. The root
  is the shared documentation home, and its CI gates and bots read it. Decision 3 keeps confidential material out of
  git, or in a separate small private repository when history is needed.

## Follow-ups

- Tech lead (org owner): apply decision 2 in the org settings, then confirm by reading them back with a token that has
  `admin:org`. The Actions policy values are not readable today.
- Agent: layers 1–4 (AA-1024 lanes l12, l14, l15, l19): built S273; artifact retention: WL7 warns (S273), the
  remaining warnings in the five app/infra repos and the move of WL7 into `workflow_lint.py` are one wave; App-token
  reads for cross-repository workflows.
- Tech lead: give `aa-ecosys-ci-bot` the repository permission **Actions: Read-only**, install it on all six repos,
  create the root environment `ci-hygiene` with deployment branches limited to `master`, store the secret
  `AA_CI_BOT_PRIVATE_KEY` in that environment (never at repo level: the key can write to the child repos) and set the
  root repo variable `AA_CI_BOT_APP_ID`, so the daily hygiene run reads every repo's caches (until then it opens a
  "needs permission" issue that says the same; steps in docs/security/github-apps.md part 5).
- Monthly C8 review: runner minutes per phase, cache use per repo, Actions storage.
- Re-check the private-on-Free feature table against GitHub's plan documentation before any visibility decision.
