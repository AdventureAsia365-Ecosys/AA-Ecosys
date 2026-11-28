---
id: SEC-07
title: Create and install the GitHub Apps for agents and bots
description: Step-by-step browser and CLI guide to create the aa-agent and aa-ci-bot GitHub Apps, install them, store their keys, run the identity test PR, and rotate or revoke them (ADR 0011).
type: how-to
status: active
owner: nghiep
audience: [engineer, devops, agent]
applies_to: [ecosystem]
last_reviewed: 2026-10-22
review_every_days: 90
last_tested: 2026-10-22
tested_where: dev-acc2
tested_evidence: AA-901 Linear comment (identity test PR, installation listing)
related: [SEC-02, SEC-05, SEC-06, AA-901, AA-891, AA-878, AA-880]
---

# Create and install the GitHub Apps for agents and bots

> [!NOTE]
> Run for real on 2026-10-22 (S247): `aa-agent` (app id 5421824) and `aa-ecosys-ci-bot` (app id 5421877; the
> name `aa-ci-bot` was taken, so the fallback name is live) are created and installed on the five repos; keys stored
> as described below; the identity test PR is in the AA-901 evidence. Wherever this page says `aa-ci-bot`, the live
> App is `aa-ecosys-ci-bot`.

The decisions behind each setting are in [ADR 0011](../adr/0011-github-app-identity-and-merge-rights.md) (identity,
permissions, keys, merge rights) and [ADR 0014](../adr/0014-repo-visibility-and-github-plan.md) (what GitHub Free
enforces where).

> **Tóm tắt (VI):** tech lead tạo 2 GitHub App trên trình duyệt (`aa-agent` cho phiên agent, `aa-ci-bot` cho
> release-please và PR docs từ Infra), cài lên 5 repo, tải private key; key `aa-agent` cất vào Secrets Manager acc2,
> key `aa-ci-bot` cất vào GitHub secret từng repo; xoá file `.pem`. Sau đó agent điều phối chạy PR thử bằng App và
> thêm dòng vào secrets register. Không đổi branch protection.

## Who does what

| Part | Who | Where |
|---|---|---|
| 1–3 Create and install `aa-agent`, download its key | The tech lead | Browser, org admin `pqnghiep1354` |
| 4 Store the `aa-agent` key, fill `apps.env` | The tech lead or the orchestrator | WSL terminal |
| 5 Create and install `aa-ci-bot`, store its key | The tech lead (browser), the tech lead or the orchestrator (CLI) | Browser, WSL terminal |
| 6 Identity test PR | Orchestrator (main session; subagents are blocked by the hook) | WSL terminal |
| 7 Secrets register rows | Orchestrator | Root repo PR |

Cost: 0 USD on GitHub; about 0.40 USD a month for the one Secrets Manager secret.

## Before you start

1. Confirm the AWS account.

   ```bash
   aws sts get-caller-identity --profile aa365-admin
   ```

   Expected: the acc2 account from the [onboarding account map](../onboarding.md). Abort if it shows another account.

2. Confirm your GitHub login is an org admin.

   ```bash
   gh api orgs/AdventureAsia365-Ecosys/memberships/pqnghiep1354 --jq .role
   ```

   Expected: `admin`.

## 1. Create the `aa-agent` App

1. Open `https://github.com/organizations/AdventureAsia365-Ecosys/settings/apps/new` (org Settings → Developer
   settings → GitHub Apps → New GitHub App).
2. **GitHub App name:** `aa-agent`. App names are unique across all of GitHub; if it is taken, use
   `aa-ecosys-agent` and write the real name in the secrets register (part 7).
3. **Homepage URL:** `https://github.com/AdventureAsia365-Ecosys`.
4. **Identifying and authorizing users:** leave **Callback URL** empty; leave **Request user authorization (OAuth)
   during installation** and **Enable Device Flow** unticked.
5. **Post installation:** leave empty.
6. **Webhook:** untick **Active**.
7. **Repository permissions** (leave every other one at "No access"):

   | Permission | Access |
   |---|---|
   | Actions | Read and write |
   | Checks | Read-only |
   | Commit statuses | Read-only |
   | Contents | Read and write |
   | Issues | Read-only |
   | Metadata | Read-only (set automatically) |
   | Pull requests | Read and write |
   | Workflows | Read and write |

8. **Organization permissions** and **Account permissions:** leave all at "No access".
9. **Where can this GitHub App be installed?** choose **Only on this account**.
10. Click **Create GitHub App**.

Expected: the App's settings page opens and shows **App ID** (a number) and **Client ID**. Note the App ID.

Verify: the page header reads `aa-agent` and **Public link** ends in `/apps/aa-agent`.

Rollback: App settings → **Advanced** → **Delete GitHub App**.

## 2. Generate the `aa-agent` private key

1. On the same page, section **Private keys**, click **Generate a private key**.
2. The browser downloads `<app-slug>.<date>.private-key.pem` to the Windows Downloads folder. From WSL it is
   `/mnt/c/Users/<windows-user>/Downloads/<pem-file>`.

Expected: **Private keys** lists one key with its SHA256 fingerprint.

Rule: do not open, copy, paste or commit the `.pem`. It goes into the store in part 4 and is then shredded.

## 3. Install `aa-agent` on the five repos

1. App settings → **Install App** → **Install** next to AdventureAsia365-Ecosys.
2. Choose **Only select repositories** and pick `AA-Ecosys`, `AA-CIS-App`, `AA-Booking`, `AA-TripPlanner-Web`,
   `AA-CIS-Infra`.
3. Review the permission list (it matches part 1) and click **Install**.

Expected: org Settings → **GitHub Apps** → **Installed GitHub Apps** lists `aa-agent` with "5 selected repositories".

Rollback: the same page → **Configure** → **Uninstall** (or **Suspend** to stop it at once and keep the settings).

## 4. Store the `aa-agent` key and fill `apps.env`

1. Store the key in Secrets Manager acc2.

   ```bash
   aws secretsmanager create-secret --name aa-ecosys/github/aa-agent-app-key --description "Private key of the aa-agent GitHub App (ADR 0011, AA-901)" --secret-string file:///mnt/c/Users/<windows-user>/Downloads/<pem-file> --profile aa365-admin --region us-west-1 # WRITE
   ```

   Expected: JSON with `ARN`, `Name` and `VersionId`.

2. Shred the downloaded file.

   ```bash
   shred -u /mnt/c/Users/<windows-user>/Downloads/<pem-file> # WRITE
   ```

   Verify: `ls /mnt/c/Users/<windows-user>/Downloads/ | grep -c private-key` prints `0`. Empty the Windows Recycle
   Bin if the file was ever deleted from Explorer instead.

3. Check the secret without reading its value.

   ```bash
   aws secretsmanager describe-secret --secret-id aa-ecosys/github/aa-agent-app-key --profile aa365-admin --region us-west-1 --query "{name:Name,changed:LastChangedDate}"
   ```

4. Put the App ID into `tools/github/apps.env` in the root repo (line `agent_app_id=`) through a normal root PR. The
   App ID is not a secret.
5. Let `git` use the `gh` token, once per laptop, so `as-app.sh -- git push` pushes as the App.

   ```bash
   gh auth setup-git
   ```

6. Test the helper.

   ```bash
   tools/github/as-app.sh -- gh api /installation/repositories --jq '.repositories[].name'
   ```

   Expected: the five repo names. If it says the App has no installation, part 3 is not done.

Rollback: delete the secret (7-day recovery window) and revert the `apps.env` line.

```bash
aws secretsmanager delete-secret --secret-id aa-ecosys/github/aa-agent-app-key --recovery-window-in-days 7 --profile aa365-admin --region us-west-1 # WRITE
```

## 5. Create, install and store `aa-ci-bot`

1. Repeat part 1 with **GitHub App name** `aa-ci-bot` (fallback `aa-ecosys-ci-bot`) and only these repository
   permissions:

   | Permission | Access |
   |---|---|
   | Contents | Read and write |
   | Issues | Read and write (release-please labels) |
   | Metadata | Read-only |
   | Pull requests | Read and write |
   | Actions | Read-only (the root CI hygiene run reads the caches of the six repos) |
   | Secrets | Read-only (the weekly Secret rotation check lists secret names and `updated_at`; the API never returns a value) |
   | Environments | Read-only (the same check, for environment secrets) |

   No Workflows, no write on Actions, Secrets or Environments, no organization permissions, no webhook, **Only on this
   account**. Adding a permission later: App settings → **Permissions & events** → save, then accept the update on
   the org installation (org Settings → **GitHub Apps** → **Configure** → **Review request**).

2. Repeat part 2 (one private key) and part 3 (install on the same five repos; `AA-Ecosys` is needed because the
   Infra docs workflows open PRs there).
3. One environment per repo holds the key (AA-1183): `ci-bot`, deployment branches = the default branch only
   (`master` in `AA-Ecosys`, `main` elsewhere), no required reviewers, no wait timer. The App id is the repo variable
   `AA_CI_BOT_APP_ID` (an identifier). Never at repo level: the key can write to the child repos, and a repo-level
   secret is readable by a workflow edited on any pushed branch, whatever its `if:` says. Every job that mints a
   ci-bot token names `environment: ci-bot`.
4. Create the six environments, store the key and set the variable in one go (dry run first, then `--apply`; the key
   is read from the file by `gh`, never printed):

   ```bash
   bash tools/security/ci_bot_key_consolidate.sh plan
   bash tools/security/ci_bot_key_consolidate.sh setup --pem /mnt/c/Users/<windows-user>/Downloads/<pem-file>
   bash tools/security/ci_bot_key_consolidate.sh setup --pem /mnt/c/Users/<windows-user>/Downloads/<pem-file> --apply --shred # WRITE
   ```

   Before AA-1183 the key sat in environment `release` (four app repos), `ci-hygiene` (root) and at repo level
   (AA-CIS-Infra); `ci_bot_key_consolidate.sh cleanup --apply` deletes those copies once every job that reads the
   key runs in `ci-bot`. It refuses earlier, and also whenever a workflow list or file cannot be read
   (`tools/security/ci_bot_workflows_ready.py` fails closed).
5. Shred the `.pem` as in part 4 step 2.

Verify (names only, no values):

```bash
bash tools/security/ci_bot_key_consolidate.sh plan
```

Expected: every repo shows the `ci-bot` environment with branches `[branch:<default branch>]`, rules
`[branch_policy]`, key `set`, and the repo variable `set`.

Rollback: delete the `ci-bot` environment secret of each repo (repo Settings → **Environments** → `ci-bot`), then
delete the App (part 1 rollback).

## 6. Identity test PR (Done-when of AA-901)

Run from the main session. Use a PR that has to be opened anyway, for example the AA-Booking `chore/codeowners`
branch if it is not pushed yet, or a one-line docs change.

```bash
tools/github/as-app.sh --repos AA-Booking -- git -C <booking-worktree> push -u origin <branch>
tools/github/as-app.sh --repos AA-Booking -- gh pr create --repo AdventureAsia365-Ecosys/AA-Booking --head <branch> --title "<conventional title>" --body-file <pr-body-file>
gh pr view <pr-number> --repo AdventureAsia365-Ecosys/AA-Booking --json author,statusCheckRollup --jq '{author: .author.login, checks: [.statusCheckRollup[].name]}'
```

Expected: `author` is `app/aa-agent` and `checks` lists the AA-Booking CI jobs (they started because an App token,
unlike `GITHUB_TOKEN`, triggers workflows).

Evidence: paste the `gh pr view` output into the AA-901 "Verified" comment and the session log.

Abort: if `author` is `pqnghiep1354`, the command ran without the helper; close the PR and re-run step 2.

## 7. Secrets register rows

Add these rows to [`secrets-register.yaml`](secrets-register.yaml) and the tables in
[`secrets-register.md`](secrets-register.md) (names and metadata only):

| Name | Store | Status |
|---|---|---|
| `aa-ecosys/github/aa-agent-app-key` | `secretsmanager:acc2` | keep |
| `AA_CI_BOT_PRIVATE_KEY` | `github:<repo>/ci-bot` for each of the six repos (AA-1183; before: `github:<app repo>/release`, `github:AA-Ecosys/ci-hygiene`, `github:AA-CIS-Infra`) | keep |
| GitHub App `aa-agent` (keys, installation) | `vendor:github` | keep |
| GitHub App `aa-ci-bot` (keys, installation) | `vendor:github` | keep |

When the Infra docs workflows use `aa-ci-bot`: delete `ROOT_REPO_DOCS_TOKEN` from AA-CIS-Infra, revoke its PAT in
`https://github.com/settings/personal-access-tokens`, and mark the row `deleted` with the date.

## 8. ci-bot merges (ADR 0011a, AA-993)

[ADR 0011a](../adr/0011a-ci-bot-merges-copy-and-dump-prs.md) (Proposed) lets `aa-ecosys-ci-bot` squash-merge exactly
two kinds of PR; every other PR it opens is merged by a person or the orchestrating agent.

| PR | Where | Workflow | Token (minted in the job, `main` only) |
|---|---|---|---|
| Schema dump `bot/db-schema-reference` | root | AA-CIS-Infra `db-schema-dump.yml` publish job, only after an apply and only when clean (AA-993 M1) | root repo, Contents + Pull requests write (unchanged from AA-901) |
| Migration copy `bot/migration-copy/<owner>-<NNN>` | AA-CIS-Infra | `migration-sync.yml` (AA-993 M3, not built yet) | AA-CIS-Infra only, Contents + Pull requests write |

- No App is a bypass actor of the AA-CIS-Infra ruleset on `main` (`tools/github/infra-main-ruleset.json`, applied by
  `tools/github/db_auto_apply_gate.sh` with the tech lead's login): ci-bot reaches `main` only by merging a PR whose required
  checks are green.
- No app repo workflow mints a token for AA-CIS-Infra or the root repo. The one cross-repo app token is AA-CIS-App
  `kit-sync.yml` (ADR 0016 decision 6, AA-994 S3s): one token per consumer app repo (AA-Partner, AA-Booking,
  AA-TripPlanner-Web), Contents + Pull requests write, `ci-bot` environment (main only); it opens `bot/kit-sync`
  PRs and never merges them (ADR 0011a decision 3).
- Check: `gh pr view <n> --repo <repo> --json mergedBy --jq .mergedBy.login` shows `app/aa-ecosys-ci-bot`.
- Stop: revert the workflow change, or suspend the installation (part "Emergency stop").

## Add a repo later

No reinstall. Org Settings → **GitHub Apps** → **Configure** next to the App → **Select repositories** → add the
repo → **Save** (each App). Then add the repo to the lists in this page and in ADR 0011 if it changes the scope, and
for `aa-ecosys-ci-bot` add the repo to `REPOS` in `tools/security/ci_bot_key_consolidate.sh` and run its `setup`
with a new key from the App page (part 5 step 4), which also refreshes the other repos.

## Rotate a key

Trigger: a possible leak, go-live (AA-880), someone who could read it leaves (ADR 0011 decision 5), or the register's
365-day schedule (secrets register v2, class `scheduled`; the weekly Secret rotation check opens an issue 30 days
ahead).

1. App settings → **Private keys** → **Generate a private key** (the old key keeps working).
2. Store the new key: for `aa-agent`, `aws secretsmanager put-secret-value --secret-id aa-ecosys/github/aa-agent-app-key --secret-string file://<new-pem-path> --profile aa365-admin --region us-west-1 # WRITE`; for `aa-ci-bot`, `bash tools/security/ci_bot_key_consolidate.sh setup --pem <new-pem-path> --apply` (part 5 step 4).
3. Verify: `tools/github/as-app.sh -- gh api /installation/repositories --jq '.repositories | length'` prints `5`
   (`aa-agent`), or re-run the release workflow (`aa-ci-bot`).
4. Delete the old key on the App page (match the fingerprint), then shred the new `.pem`.
5. Record the rotation date in the register row.

## Emergency stop

- Suspend the installation: org Settings → **GitHub Apps** → **Configure** next to the App → **Suspend**. Every
  token stops working at once.
- Or delete the leaked key on the App page; tokens already minted die within the hour.
- Then rotate (above), note the event in `docs/ops/postmortems/` and the access review.
