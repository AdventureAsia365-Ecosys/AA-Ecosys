---
id: GUIDE-01
title: "Onboarding: accounts and access"
description: Every account a new engineer or operator needs, who grants it, how to check it works, and the only AWS account-map table in the docs.
type: tutorial
status: draft
owner: nghiep
audience: [engineer, devops]
applies_to: [ecosystem]
last_reviewed: 2026-10-19
review_every_days: 90
related: [GUIDE-10, GUIDE-05, GUIDE-02, TPL-02, AA-897, AA-517]
---

# Onboarding: accounts and access

This page lists the accounts you need to work on AA-Ecosys, who grants each one and the command or page that proves
it works. It also holds the **only** AWS account-map table in the docs; every other page links to
[Account map](#account-map). For the learning path (what to read and build in week one) open the
[new engineer guide](guides/new-engineer.md).

Today the team is Nghiệp plus AI agents, so **Nghiệp grants every access below**. Ask him in one message with the
list of accounts you need.

## Account map

All infrastructure lives in **acc2**. acc1 and acc3 only host the Bedrock "satellite" roles that let acc2 call
chat models, plus read-only Cost Explorer roles (ecosystem architecture §4.3, §4.4).

| Name | AWS account ID | Region | CLI profile | Holds | Notes |
|---|---|---|---|---|---|
| **acc2** - main | 005097885195 | us-west-1 | `aa365-admin` (also `default`) | Everything: VPC, RDS, ECS, Lambda, API Gateway, S3, Cognito, SES, alarms, budgets | Member account under a reseller (TrueIDC); Bedrock chat models are blocked here, Cohere embeddings are allowed |
| **acc3** - LLM satellite, primary | 786888028788 | us-west-1 | `nghiep_aa365` | Role `AA3-Bedrock-Invoker`, Bedrock batch roles, Cost Explorer reader | Terraform root `accounts/acc3-bedrock/`, applied by a human |
| **acc1** - LLM satellite, fallback | 867490540162 | us-west-1 | `pqnghiep-admin` | Role `AA-Bedrock-Invoker`, Cost Explorer reader | Its old compute was destroyed (AA-271); the account stays on purpose. Terraform root `accounts/acc1-bedrock/` |

> [!WARNING]
> The `default` profile points at **acc2** since AA-517 (2026-09-02). Before that it was a static acc1 key and caused
> two wrong-account Secrets Manager writes. Do not point `default` anywhere else, and still pass `--profile` on every
> command.

The old Quanskill accounts and their `aa-dev`, `aa-stg`, `aa-prod` profiles (ap-southeast-1) are **not** part of
AA-Ecosys. Never deploy there.

Prod does not exist yet. It will be a separate RDS instance on acc2 (ADR 0001, data standards C7.2a, decision
D-17), dated when go-live is set (AA-880). Dev holds **test data only** (D-01).

## Accounts you need

| # | Account | What for | Granted by | Check it works |
|---|---|---|---|---|
| 1 | **AWS acc2** (IAM identity + MFA) | CLI reads, ECS exec, Terraform plan | Nghiệp | `aws sts get-caller-identity --profile aa365-admin` prints the acc2 ID |
| 2 | AWS acc3 / acc1 | Only for Bedrock satellite Terraform | Nghiệp, rarely needed | `aws sts get-caller-identity --profile nghiep_aa365` |
| 3 | **GitHub** org `AdventureAsia365-Ecosys` | Code, PRs, CI | Nghiệp (org owner) | You see the private repos `AA-Ecosys` and `AA-CIS-Infra` |
| 4 | **CIS staff account** (Cognito WORKFORCE) | Admin console, Booking admin | An owner, on CIS admin → Platform → Staff | The invite e-mail arrives; "Sign in with company email" works |
| 5 | Vercel team | Frontend deploy logs, env var names | Nghiệp | You see `aa-cis-frontend`, `aa-cis-portal`, `aa-booking-admin` and the TripPlanner project |
| 6 | **Linear** workspace and team `AA_Ecosys` | Work items | Nghiệp | You see the four projects (see the [PM guide](guides/pm.md)) |
| 7 | Notion workspace `AA_Ecosys`, page Program Brain | Session memory (`memory.md`) | Nghiệp | You can open Program Brain → memory.md |
| 8 | Jira (Adventure Asia site, projects PR, KAN, CON) | Requests from Ms. Thư | Nghiệp asks Ms. Thư | You can read the PR project |
| 9 | Sentry org | Error reports for CIS | Nghiệp | You see projects `aa-cis-api` and `aa-cis-frontend` |
| 10 | Google Drive folder AdventureAsia | Files shared with Ms. Thư, photo originals | Nghiệp | You can open the folder |

Use your `@adventure.asia` address everywhere. GitHub requires 2FA for the org; use an authenticator app or a
passkey, never SMS (AA-867).

## Set up the AWS CLI

1. Install AWS CLI v2 inside WSL2 (Ubuntu), not in Windows.
2. Nghiệp gives you an IAM identity with MFA on acc2. Name the profile that assumes your role **`aa365-admin`**:
   every doc, skill and script uses that name. Use `region = us-west-1`.
3. Check it:

   ```bash
   aws sts get-caller-identity --profile aa365-admin
   ```

   Expected: `"Account"` is the acc2 ID in the [account map](#account-map). Anything else: stop and fix the profile.
4. Terraform and boto3 need the MFA session exported as environment variables:

   ```bash
   export $(aws configure export-credentials --profile aa365-admin --format env | xargs) && unset AWS_PROFILE
   ```

Rules that bite on day one (full list in [STYLE](STYLE.md#commands)):

- **One AWS CLI command per line.** A `\` line continuation hangs WSL2.
- Always pass `--profile` and `--region`.
- Run `aws sts get-caller-identity --profile aa365-admin` before any command that creates or changes something.
- Never print a secret value (`get-secret-value`) into a terminal you share, a chat or a file. Secret **names** are fine.
- Reach the database only through the S3-mediated ECS exec pattern over SSM, never SSH and never a public endpoint
  (`skill/aa-cis-schema`, data standards DM-8.8).

## Set up git and the workspace

1. Sign in once with `gh auth login`, then clone into WSL, never a Windows UNC path (`\\wsl.localhost\...` gives "dubious ownership" errors):

   ```bash
   mkdir -p ~/projects/AA-Ecosys && cd ~/projects/AA-Ecosys
   gh repo clone AdventureAsia365-Ecosys/AA-Ecosys .
   gh repo clone AdventureAsia365-Ecosys/AA-CIS-App apps/AA-CIS-App
   gh repo clone AdventureAsia365-Ecosys/AA-Booking apps/AA-Booking
   gh repo clone AdventureAsia365-Ecosys/AA-TripPlanner-Web apps/AA-TripPlanner-Web
   gh repo clone AdventureAsia365-Ecosys/AA-CIS-Infra infra/AA-CIS-Infra
   ```

2. Each folder is its own repo with its own `.git`. The root repo `AA-Ecosys` uses `master`; the four others use
   `main`.
3. Scratch files go in `.tmp-session/` inside the workspace (git-ignored), never in your home folder.

## Get a CIS staff account

1. An owner (today Nghiệp) adds you on CIS admin → **Platform → Staff** with your `@adventure.asia` e-mail and a
   role (`admin`, `reviewer` or `content`; a Booking role if you need the Booking admin).
2. You get an invite e-mail. Open `https://aa-cis.lumiguides.it.com`, choose **Sign in with company email** and type
   the one-time code sent to you (sign-in page `staff-auth.lumiguides.it.com`, ADR 0006a).
3. Only owners change roles. If your role looks wrong, ask Nghiệp; do not use the legacy password form.

## Leaving or changing role

An owner disables the staff row (never deletes it; history stays) and Nghiệp removes the AWS identity, GitHub
membership and SaaS seats in the same session. The quarterly access review (data standards DM-8.10) checks
that nothing was missed.

## Related

- [New engineer guide](guides/new-engineer.md), [DevOps guide](guides/devops.md)
- [Agent instruction index](agents.md)
- [Style guide](STYLE.md), [glossary](glossary.md)
