# ADR 0011 — GitHub App identity for agents and bots, and merge rights per risk tier

- **Status:** Proposed (22/10/2026, S247). Nghiệp accepts after the Apps exist and the test PR passes (AA-901).
- **Scope:** AA-Ecosys: all five repos of org AdventureAsia365-Ecosys (AA-Ecosys, AA-CIS-App, AA-Booking,
  AA-TripPlanner-Web, AA-CIS-Infra); agent sessions (Claude Code, Kiro); CI workflows that write to another repo or open
  release PRs.
- **Amends / Supersedes:** none. It records how D-13 / DM-11.5 is carried out on GitHub.
- **Implements:** S241 D-13 (merge rights by risk tier; dev phase self-merge), DM-11.5 (data standards v1.1, S243 N-1),
  S241 D-15 (agent keeps `aa365-admin` on AWS: this ADR covers GitHub only), S243 N-6 (create U-25).
- **Related:** [ADR 0014](0014-repo-visibility-and-github-plan.md) (what GitHub Free can enforce where), AA-891
  (release-please), AA-878 (secrets register), AA-880 (prod blueprint, the prod trigger). Setup guide:
  [`security/github-apps.md`](../security/github-apps.md).
- **Related Linear:** AA-901 (U-25).

## Context

Every GitHub action by an agent or a bot runs as Nghiệp's personal account `pqnghiep1354`: the local `gh` OAuth token
for agent sessions, and the fine-grained PAT `ROOT_REPO_DOCS_TOKEN` for the AA-CIS-Infra workflows that open root PRs
(DB Schema Dump, Docs Gen). Three problems follow:

1. **Audit.** A PR, a merge or a workflow dispatch by an agent cannot be told apart from one by Nghiệp.
2. **Release PRs do not run CI.** release-please (AA-891) opens its release PR. With the default `GITHUB_TOKEN` that PR
   triggers no workflow, so the required checks never report and the PR cannot merge (GitHub does not start workflows
   from events made with `GITHUB_TOKEN`).
3. **The prod gate cannot work.** From the first prod (D-13), Nghiệp approves risky PRs. GitHub does not let an author
   approve their own PR; if the agent opens PRs as Nghiệp, Nghiệp can never give the required approval.

The PAT is also long-lived, tied to one person and listed as an open item in the secrets register.

## Decisions

### 1. Two GitHub Apps owned by the organization

| App | Used by | Installed on | Repository permissions |
|---|---|---|---|
| `aa-agent` | The orchestrating agent session (Claude Code or Kiro, main session only) | All five repos | Contents RW, Pull requests RW, Workflows RW, Actions RW, Checks R, Commit statuses R, Issues R, Metadata R |
| `aa-ci-bot` | CI workflows: release-please in the app repos (and Infra if it adopts it); the Infra workflows that open root PRs | AA-CIS-App, AA-Booking, AA-TripPlanner-Web, AA-Partner, AA-CIS-Infra, AA-Ecosys (AA-Partner row fixed S252, ADR 0016 decision 13: already installed, release PRs such as #64 come from `aa-ecosys-ci-bot[bot]`) | Contents RW, Pull requests RW, Issues RW (release-please labels), Metadata R |

- Both Apps are **private** to the org ("Only on this account"), have **no webhook**, no callback URL, no user
  authorization (no OAuth on behalf of users) and **no organization permissions**.
- Neither App gets `Administration`, `Secrets`, `Environments`, `Members` or `Deployments`. Branch protection, rulesets,
  secrets and environments stay with Nghiệp's personal login, so a leaked App key cannot weaken a gate or read a secret.
- `Workflows RW` on `aa-agent` is needed because agents edit `.github/workflows/*` in normal PRs; `Actions RW` because
  the orchestrator dispatches DB Migrate and DB Schema Dump. `aa-ci-bot` has neither: release-please only touches the
  CHANGELOG, the manifest and the version files.
- Every token is an **installation access token** (1 hour). No App is used with a long-lived token. When minting, a
  workflow narrows the token to the repos and permissions of that job (`repositories`, `permission-*` inputs of
  `actions/create-github-app-token`), for example Infra's docs job asks for `AA-Ecosys` with Contents and Pull
  requests write only.
- Cost: 0 USD on GitHub. One Secrets Manager secret for the agent key: about 0.40 USD a month.

### 2. Where the keys live

| Key | Store | Readers |
|---|---|---|
| `aa-agent` private key | Secrets Manager acc2, `aa-ecosys/github/aa-agent-app-key` | The agent session through `tools/github/as-app.sh` (profile `aa365-admin`); CloudTrail records each read |
| `aa-agent` App ID and installation ID | Not secret; kept in the helper's config (`tools/github/apps.env`) | — |
| `aa-ci-bot` private key | GitHub secret `AA_CI_BOT_PRIVATE_KEY` in each consuming repo, in an environment with a `main`-only branch policy where the repo's plan allows it (public repos); repo-level with a `main`-only job guard otherwise (lesson S241 AA-866) | The release-please job and the Infra docs jobs on `main` |
| `aa-ci-bot` App ID | GitHub variable `AA_CI_BOT_APP_ID` (not a secret) | Same jobs |

- The `.pem` file downloaded from GitHub is copied into the store, then shredded on the laptop. It is never committed,
  pasted in chat or printed in a transcript.
- The helper reads the key into memory, signs the App JWT with `openssl`, exchanges it for an installation token and
  runs **one** command with that token in `GH_TOKEN`. It never echoes the token.
- All four names get rows in the secrets register (AA-878) when the Apps are created; `ROOT_REPO_DOCS_TOKEN` is marked
  `deleted` and its PAT revoked once the Infra docs workflows use `aa-ci-bot`.

### 3. Who acts as which identity

| Action | Identity |
|---|---|
| Agent pushes a branch, opens, comments on or merges a PR, dispatches a workflow | `aa-agent[bot]` via the helper |
| release-please release PR, Infra root docs PRs | `aa-ci-bot[bot]` |
| Branch protection, rulesets, repo settings, GitHub secrets and variables, App settings and keys | Nghiệp (`pqnghiep1354`), by hand or a script he runs |
| Commits | The commit author stays the git author of the session (Nghiệp, with the agent's `Co-Authored-By` line); the push and the PR carry the App identity |

- Subagents never merge, push or open PRs, whatever token they could reach: the hook
  `.claude/hooks/subagent-guardrails.sh` blocks the commands, not the identity.
- Release PRs from `aa-ci-bot` have no `Refs AA-xxx` (the exception AA-891 writes into `skill/aa-ship` §1).

### 4. Merge rights per risk tier (D-13, DM-11.5)

| Phase | Normal PR | Risky PR (Terraform/IAM, migration/schema, auth/security, CI/workflow/secret, data deletion) |
|---|---|---|
| **Dev (now)** | `aa-agent` merges after green CI | `aa-agent` merges after green CI and an agent review (`kiro-reviewer` or an independent review subagent) |
| **From the first prod or the first paying tenant** | `aa-agent` merges after green CI | Nghiệp approves, then `aa-agent` merges. Enforced by CODEOWNERS on the risky paths plus "Require review from Code Owners" on the protected branch (public repos; private repos per ADR 0014) |

- CODEOWNERS files exist from now in all five repos (AA-901), owner `@pqnghiep1354`, on the risky paths only (no `*`
  catch-all). In the dev phase they change nothing: branch protection does not require code-owner review, so the file
  only adds a review request on PRs the App opens.
- Turning the gate on is a prod-trigger step owned by AA-880: enable "Require review from Code Owners" and "Require
  approval of the most recent reviewable push", and do not list `aa-agent` as a bypass actor.

### 5. Rotation and revocation

- No calendar rotation on Dev (same rule as other secrets, D-02/D-03). Rotate an App key when it may have leaked, at
  go-live (AA-880) and when someone who could read it leaves.
- Rotation without downtime: generate a second private key on the App page, store it (Secrets Manager or the GitHub
  secret), run one token mint and one read call with it, then delete the old key on the App page. An App can hold
  several keys at once.
- Emergency: suspend the installation (org settings → GitHub Apps → Configure → Suspend), or delete the key on the App
  page. Both take effect at once; open tokens die within the hour.

### 6. Audit

- PRs, comments, merges and pushes show `aa-agent[bot]` or `aa-ci-bot[bot]` on the timeline and in the API.
- The organization audit log records App creation, installation, permission changes and key generation or deletion.
- CloudTrail on acc2 records every `GetSecretValue` on the agent key.
- The quarterly access review (DM-8.10, SEC-05) lists both Apps: installed repos, permissions, key count and age.

## Consequences

- **Positive:**
  - agent and bot actions are separable from Nghiệp's in every timeline and log;
  - release PRs run the required checks, which unblocks AA-891;
  - the prod gate becomes possible: the App is the author, Nghiệp the approver;
  - no long-lived token for the root docs PRs once `ROOT_REPO_DOCS_TOKEN` is retired.
- **Negative / cost:**
  - two Apps and their keys to keep (a few minutes in the browser, one access-review line each);
  - the agent needs the helper for GitHub writes; plain `gh` still uses Nghiệp's login until the session sets the
    App as its default (convention first; a hook check is a follow-up);
  - *(est., per month)*: 0 USD GitHub; about 0.40 USD for one Secrets Manager secret.

## Alternatives considered

- **One App for agents and CI.** Fewer keys, but a key leaked from a CI secret could push workflow files and dispatch
  workflows on every repo. Rejected for blast radius and for a less clear audit trail.
- **A machine user (second GitHub account) with a PAT.** Uses a seat-like account, a long-lived token and a password
  plus 2FA to keep. Rejected: GitHub's recommended pattern for automation is an App.
- **Fine-grained PATs for release-please.** Works (AA-891 fallback) but stays tied to Nghiệp's account and expires on a
  calendar. Kept only as the fallback if this ADR is not accepted.
- **Keep everything on Nghiệp's login.** Rejected: the three problems in Context stay.

## Follow-ups

- AA-901: Nghiệp creates and installs both Apps (guide), stores the keys; the orchestrator runs the test PR with the
  helper and adds the register rows.
- AA-891: release-please workflows mint the `aa-ci-bot` token; first release PR runs the required checks.
- AA-CIS-Infra: switch `db-schema-dump.yml` and `docs-gen.yml` (Contents and Pull requests write) and
  `migration-copy-guard.yml` (Contents read) from `ROOT_REPO_DOCS_TOKEN` to an `aa-ci-bot` token for `AA-Ecosys`, then
  delete the secret and revoke the PAT.
- AA-880 (prod trigger): turn on code-owner review on the public repos, apply ADR 0014's private-repo choice.
- On acceptance: status line here and in the index; handbook §6.5 and the U-25 row.
