---
id: SEC-05-yyyyqn
title: Access review <YYYY>-Q<n>
description: <One sentence - who and what can reach each app (GitHub, Vercel, AWS IAM, Cognito, DB roles, secrets) on the review date, and the findings.>
type: report
status: draft
owner: nghiep
audience: [engineer, devops, cto, agent]
applies_to: [ecosystem, aa-cis-api, aa-booking, tripplanner-lambda, aa-partner, aa-cis-infra]
last_reviewed: 2026-10-28
review_every_days: 90
related: [SEC-01, SEC-02, SEC-05, AA-838]
---

# Access review <YYYY>-Q<n>

<!-- The quarterly access review of data standards Part B, DM-8.10 (docs/architecture/data-standards/02-data-management.md).
Save it as docs/audits/<date>-S<nnn>-access-review/README.md with a root PR; list it in docs/security/README.md (SEC-05).
Run it in the first session of each quarter. Claude Code drafts, Nghiep approves. The body MAY be written in
Vietnamese (audits for Nghiep, language convention N-7). Worked example: docs/audits/2026-10-20-S245-access-review/.
Never write a secret value, e-mail address, account ID or ARN here: names of roles, pools, projects and secrets,
counts, groups, enabled flags only; Cognito users by role and e-mail domain. Delete this comment. -->

Date: <DD/MM/YYYY> (S<nnn>). Agent: <Claude Code / Kiro>, read-only. Cost: <USD>.
Previous review: <link>. Next: first session of <YYYY>-Q<n+1> (DM-8.10, 90 days).

## 1. Sources

| Part | Source (read-only, date) | Note |
|---|---|---|
| GitHub org + repos | `gh api` GET: org members and admins, teams, outside collaborators, invitations, app installations; per repo collaborators, deploy keys, webhooks, environments | |
| GitHub secrets | Names per repo / environment / Dependabot / org | names only |
| Vercel | team members, projects, env var names and targets (never decrypted) | |
| AWS IAM | Terraform on AA-CIS-Infra `origin/main` + live read-only `aws iam` (single-line, by the orchestrator) | |
| Cognito | user pools, groups, users per group (counts, enabled flag, e-mail domain) | |
| DB roles | `docs/architecture/db-schema-reference.md` sections Roles and Default privileges (dump of <date>) | no DB query needed |
| Secrets | `docs/security/secrets-register.md` (drift check result) | |

## 2. GitHub

| Item | State on <date> | Change since last review |
|---|---|---|
| Org members / admins | | |
| Teams, outside collaborators, pending invitations | | |
| 2FA required; default member permission; members can create repos | | |
| Collaborators per repo | | |
| Deploy keys / webhooks | | |
| GitHub Apps installed (repository scope) | | |
| Environments and their protection rules | | |
| Secrets vs register | | |

## 3. Vercel

| Item | State | Change |
|---|---|---|
| Team members / access groups | | |
| Projects | | |
| Secret-bearing env vars vs register; Vercel warnings (e.g. readable secret) | | |

## 4. AWS IAM (acc2, plus the LLM satellite accounts)

### 4.1 People

<Which humans and agents reach each account and through which profile / role (MFA, session length); IAM users and
access keys found live.>

### 4.2 Machine roles and the secrets each can read

| Role (name) | Used by | Secrets it can read |
|---|---|---|

### 4.3 Live cross-check still open

<Read-only live checks the orchestrator runs (single-line commands), and their result.>

## 5. Cognito

| Pool | Users | Groups (members / enabled) | MFA |
|---|---|---|---|

| Role of the person | E-mail domain | Groups | Enabled? | Remark |
|---|---|---|---|---|

Legacy sign-in accounts (`shared.admin_users`): <counts by role / active, e2e accounts by username only>.

## 6. DB roles (shared RDS)

| Role | Login / attributes | Member of | Connection limit | Schemas and grants | Default ACLs | Remark |
|---|---|---|---|---|---|---|

Unused roles, grants wider than DM-8 allows, roles that can read another app's schema: <list>.

## 7. Findings

| # | Finding | Severity | Action (who, needs Nghiep's approval?) | Issue |
|---|---|---|---|---|
| F-1 | | | | |

## 8. Closed since the last review

| Finding (last review) | How it was closed | Evidence |
|---|---|---|

## 9. Next time

<What to do differently, scripts to reuse, checks that could become automatic.>
