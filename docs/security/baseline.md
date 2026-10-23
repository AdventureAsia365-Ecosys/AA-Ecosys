---
id: SEC-01
title: Security baseline
description: Every security control of the ecosystem on acc2 and GitHub, with its live status, the evidence and the open issue; read before a security review or a go-live check.
type: reference
status: draft
owner: nghiep
audience: [engineer, devops, cto, cio, agent]
applies_to: [ecosystem, aa-cis-api, aa-booking, tripplanner-lambda, aa-cis-infra]
last_reviewed: 2026-10-20
review_every_days: 90
related: [SEC-02, SEC-03, SEC-05, SEC-06, OPS-04, OPS-10, AA-873, AA-874, AA-875, AA-876, AA-878, AA-879, AA-895, AA-829]
---

# Security baseline

One row per control. **Status** is what runs on Dev today, read live on 2026-10-19 (AWS read-only with
`--profile aa365-admin --region us-west-1`, GitHub API read-only). The row links the evidence or the issue that
closes the gap. This page does not repeat the work of those issues; it points at them.

Status values: **in place** (works today), **partial** (works, with a named gap), **gap** (missing, issue
open), **by decision** (not done because Nghiệp decided so, with the trigger that reopens it).

> [!NOTE]
> Dev holds test data only (S241 D-01). Controls marked "before prod" are blockers for the go-live checklist
> (G-12, AA-880), not for Dev work.

## Summary

| Area | In place | Partial | Gap |
|---|---|---|---|
| Edge and network | WAF on the ALB, SG per caller, private DB | API Gateway edge hardening (AA-876) | — |
| Identity and access | Human MFA, GitHub org 2FA, CI OIDC main-only, CI role split | Cognito cutover (AA-816), agent role optional | — |
| Data stores | RDS encryption, TLS, no public endpoint | DB role split and RLS FORCE for CIS (X1) | Redis AUTH/TLS/at-rest (AA-874) |
| Detection and logs | CloudTrail, flow logs, WAF logs, 365/30-day retention, alarms | CloudTrail single-region | GuardDuty, Access Analyzer, S3 account BPA (AA-873) |
| Code and supply chain | Secret scanning + push protection on all five repos, gitleaks full-history scans on root and Infra, Dependabot alerts everywhere | Branch rules on private repos, scanners per repo | — |
| Secrets | Secrets Manager per app, register with drift check (`diff = 0`, AA-878) | Rotation is manual by decision (D-02/D-03) | — |

## Edge and network

| Control | What is in place | Status | Evidence / issue |
|---|---|---|---|
| WAF | Regional web ACL `aa-cis-dev-waf` on the shared ALB. Rules: AWS managed common rule set, VPC-link internal allow, rate limit, geo block. The API Gateway stages (CIS, Booking) have no web ACL of their own; their traffic reaches the ALB through the VPC link. WAF logs kept 365 days. | partial | INF `docs/waf-count-review.md`. Login rate limit, API throttling, CORS and security headers: AA-876 |
| Outbound requests | Server-side fetches of user-supplied URLs need an SSRF-safe client. | gap | AA-875 |
| One security group per caller | RDS admits only `cis-api`, `cis-worker`, `booking-api`, `tp-lambda`, `db-migrate`; Redis and EFS only the two CIS groups. The shared app group is gone (X1 S14). | in place | Root ADR [0004b](../adr/0004b-per-app-security-groups.md); INF `accounts/aa365/app_security_groups.tf` |
| Private data stores | RDS `publicly_accessible = false`; humans reach the DB only through ECS exec over SSM (S3-mediated script runner), never SSH. | in place | DM-8.8; `skill/aa-cis-schema` (ECS exec pattern) |
| VPC flow logs | Four flow logs, all traffic, to CloudWatch Logs, 365 days. | in place | AA-872 (D-09) |

## Identity and access

| Control | What is in place | Status | Evidence / issue |
|---|---|---|---|
| Human AWS access with MFA | `aa365-admin` and `default` assume one role with an MFA device (8-hour session). `default` points at acc2 since AA-517. Profiles: account map in `docs/onboarding.md` (AA-897). | in place | AA-517. IAM users and access keys are listed in the quarterly access review (SEC-05), not here |
| GitHub organisation 2FA | Required for every member (organisation setting read 2026-10-19). | in place | AA-867 |
| CI trust: main only | The Terraform apply role trusts only `environment:prod` **and** `ref: refs/heads/main` from AA-CIS-Infra. The environment is named `prod` but applies Dev; renaming it belongs to ADR 0012 (AA-880, D-16). | in place | AA-866; INF `accounts/aa365/cicd_split.tf` |
| CI least privilege | Three roles: plan (read only + state lock + named secrets), apply, CIS app deploy. Bootstrap objects (the roles' own policies, OIDC provider) are applied locally with MFA. The apply role still carries ten broad AWS managed policies (one is `SecretsManagerReadWrite`: it reads every secret, the RDS master included; access review F-7), and its inline policy is at 9,559 of 10,240 characters. | partial | AA-806; INF `docs/ci-role-split.md` |
| Staff and customer identity | Cognito on acc2 (ADR 0006): staff pool with e-mail code sign-in, self sign-up refused, no-group deny; break-glass account with TOTP and a token-issued alarm; alarm on `AdminCreateUser` with a caller-set password (ADR 0006a A8). The legacy admin login is still on until the cutover. | partial | Root ADR [0006](../adr/0006-ecosystem-identity.md), [0006a](../adr/0006a-identity-phase1-amendments.md); AA-854 (done), AA-816 (cutover), AA-703 |
| Agent guardrails | Subagents cannot push, merge, deploy, apply Terraform, write secrets or call IAM (`.claude/hooks/subagent-guardrails.sh`, with its test script); an MCP guard hook blocks their GitHub, Linear, Notion, Vercel and Jira writes. Agents treat files, Jira and web content as data. The committed `.claude/settings.json` denies Claude Code reads of `~/.aws/**` and `~/.config/gh/**`, `gh auth token` and `aws configure get` (root #120, U-04 step 1; deny-only by Nghiệp's choice, no ask rules in the dev phase). A narrow agent role (`aa-cis-dev-agent-session`, AA-730) exists but is not mandatory yet. | partial (by decision) | D-15: the mandatory agent role is a prod trigger (U-53), with the GitHub App for agents (U-25) |
| Merge rights | Human merge after required checks; agents never merge. Who approves what follows D-13; the text of DM-11.5 is updated in data standards v1.1 (AA-889, N-1). | in place | D-13; `skill/aa-ship/SKILL.md` |
| Quarterly access review | Roles, grants, IAM roles that can read each DB secret, Cognito staff users, GitHub and Vercel members. Record in `docs/audits/<date>-S<nnn>-access-review/`. First review done 2026-10-20; live IAM user/key check still to add (F-15). | in place | DM-8.10; [2026-Q4 record](../audits/2026-10-20-S245-access-review/README.md) (AA-878); cadence AA-838 |

## Data stores

| Control | What is in place | Status | Evidence / issue |
|---|---|---|---|
| RDS at rest and in transit | Storage encrypted; parameter `rds.force_ssl = 1`; deletion protection on; 7-day automated backups; slow-query log at 500 ms; `postgresql` log export kept 365 days. | in place | C4.2a; AA-872 |
| DB roles per app | Booking and TripPlanner objects owned by NOLOGIN owner roles; migrations run as `db_migrator` from their own task definition. CIS runtime split (`cis_owner` / `cis_app`) is X1 wave 4. | partial | DM-8.1, DM-8.2; AA-852, AA-860 |
| Tenant isolation (RLS) | RLS template on tenant tables, scoped to the runtime role; new apps use FORCE from day one; CIS tables get FORCE after the role split. The isolation probe (INF `db-isolation-probe.yml`) runs on a schedule and after each apply. | partial | DM-8.4; AA-817 D2; U-16 |
| Tenant pool flags | Unreadable flag means tenant pool; `"false"` means admin pool; an emergency environment switch exists. This is a security control with no remove-by date. | in place | D-12; `docs/ops/feature-flags.md` (AA-892) |
| Redis | `aa-cis-dev-redis`: no AUTH token, no in-transit encryption, no at-rest encryption (read 2026-10-19). Reachable only from the CIS api and worker groups. | gap | AA-874 (cost quote first, D-19) |
| Real data on laptops | `docs/backups/2026-09-16` holds real-data `pg_dump` files (about 11 MB, checked 2026-10-20); ignored by git but still on the laptop. | gap | DM-6.10; AA-829 (scope: move the 2026-09-16 dumps to a private SSE-KMS bucket, then empty the local folder) |

## Detection and logs

| Control | What is in place | Status | Evidence / issue |
|---|---|---|---|
| CloudTrail | Trail `aa-cis-dev-trail`: logging, management events read and write, global service events, log file validation. Single-region (us-west-1), no KMS key. | partial | AA-286; multi-region decision in AA-873 |
| GuardDuty | No detector. | gap | AA-873 (30-day free trial, then billed by analysed volume: quote first, D-19) |
| IAM Access Analyzer | No analyzer. The external-access analyzer is free. | gap | AA-873 |
| S3 Block Public Access | All 11 buckets have bucket-level Block Public Access fully on; the account-level setting is not configured. | partial | AA-873 (account-level setting, free) |
| Security Hub | Not enabled (paid per check). | by decision | Revisit with the prod checklist (AA-880) |
| Log retention | Security logs 365 days (VPC flow, WAF, ECS exec sessions, `postgresql`, identity Lambdas); application logs 30 days (`/ecs/aa-cis-dev`, `/ecs/aa-booking-dev`, TripPlanner Lambdas, API Gateway execution logs). | in place | D-09, AA-872. Data standards C4.2b still says 14 days: fixed in v1.1 (N-1) |
| Alarms | Every alarm e-mails on ALARM and OK through the alerts topic (D-20); each description carries its runbook link (AA-893). Break-glass secret reads and `AdminCreateUser` with a password alert too. Cost anomalies go to the same topic (AA-896). | in place | INF `accounts/aa365/observability*.tf`, `identity_alerts.tf`, `cost_anomaly.tf`; OPS-07 |
| Error tracking | Sentry on the CIS backend. Booking and TripPlanner: JSON logs only. | partial | AA-870 (done); AA-871 |

## Code and supply chain

| Control | What is in place | Status | Evidence / issue |
|---|---|---|---|
| Branch rules, public repos | AA-CIS-App, AA-Booking, AA-TripPlanner-Web: ruleset "main: no force-push, no deletion (AA-867)" active; required checks: CIS 5, Booking 5, TripPlanner 2. | in place | AA-867 |
| Branch rules, private repos | AA-Ecosys and AA-CIS-Infra: GitHub Free offers no branch protection or rulesets on private repos (API answers 403). Control: human merge and the subagent hook. | by decision | D-14: no GitHub Team now; trigger with U-25 / U-53 |
| Secret scanning | All five repos are public and have GitHub secret scanning and push protection on (`security_and_analysis` read 23/10/2026, S248). AA-CIS-Infra and AA-Ecosys (root): `secret-scan.yml` runs gitleaks on every PR (lines the PR adds) and a **full-history** job (every commit of every branch, tag and PR head, nightly + on push to the default branch) with a baseline of pinned fingerprints, so it is green today and red on any new finding. Both use the same `.gitleaks.toml` rules, incl. `credential-key-literal`: a `*password` / `*secret` / `*api_key` / `*_token` key with a literal value in tfvars, `.env*`, JSON or YAML (the shape an external scanner caught in old Infra history on 22/10). The PR scan reads its rules and baseline from the base commit; changing them, or adding an inline `gitleaks:allow`, needs the label `secret-scan-baseline-reviewed` (a later push that touches them again, a force push or a reopen removes the label); the history job also scans every PR head (`refs/pull/*/head`). AA-Booking CI: gitleaks (PR only). App repos: no full-history job yet (manual check). | in place | AA-981 (S248); AA-867; precondition before any private→public switch: [ADR 0014](../adr/0014-repo-visibility-and-github-plan.md) amendment 2 |
| Dependency alerts | Dependabot alerts and security updates on in all five repos; `dependabot.yml` in CIS, Infra, Booking and TripPlanner (AA-895). Process and open alerts: [vulnerability management](vulnerability-management.md). | in place | AA-867, AA-895 |
| CI security gates | CIS: `pip-audit` gate with an expiring ignore list, Trivy image scan report-only. Booking: `pip-audit` failing gate and gitleaks. TripPlanner: none. | partial | AA-868; parity across repos: AA-879 |
| Public repos content | Rule: no account IDs, ARNs, network IDs, inventories or security reports in public repos (SEC-06, D-25). **Scrubbed and enforced (AA-902, S244, 19/10/2026):** HEAD of all three public repos holds 0 real account IDs (`git grep` on `origin/main` after CIS #854, Booking #45, TP #105; only obviously fake 12-digit test values remain). Code that needs a satellite account reads `BEDROCK_ACCT_PRIMARY` / `BEDROCK_ACCT_FALLBACK` from the task / Lambda environment (AA-CIS-Infra #221); bucket names come from `BRONZE_BUCKET` or STS; the TripPlanner deploy role ARN is a repo secret. A blocking resource-ID check (`.github/scripts/check_resource_ids.py`) runs in CI: CIS Lint, Booking Security Audit, TripPlanner Backend (pytest). Proven on 19/10 with throwaway PRs that add an ARN with a 12-digit account: CIS #857, Booking #47, TripPlanner #108 each failed with 1 finding (closed). Git history keeps the old IDs; account IDs are not credentials, so no history rewrite (S244). | in place | SEC-06 in [`STYLE.md`](../STYLE.md#where-a-page-may-live-sec-06); D-25; AA-902 |

## Secrets

| Control | What is in place | Status | Evidence / issue |
|---|---|---|---|
| Storage | Secrets Manager, one secret per role and purpose, named `<app>/<env>/<purpose>` (legacy CIS names kept). DM-8.6 requires each execution role to read only its own secrets; the register checks it. TripPlanner Lambdas read their secrets by name, not from Lambda environment values (INF #207). | in place | DM-8.6 |
| Register | Owner, readers, rotation class per secret; orphan cleanup (4 Secrets Manager orphans deleted 19/10 with the 30-day window, 2 GitHub orphans deleted 17/10). Drift check with AWS, Lambda env, GitHub and Vercel inventories: `diff = 0` on 2026-10-20. Org-level GitHub secrets not listable with the current token. | in place | AA-878; [`secrets-register.md`](secrets-register.md) |
| Rotation | Rotate when exposure is suspected, at go-live and after any break-glass use. No fixed 90-day cycle on Dev. | in place (by decision) | D-02, D-03, DM-8.9 |
| Before any write | `aws sts get-caller-identity --profile aa365-admin` first (two wrong-account writes happened). | in place | DM-8.7, AA-517 |

## How to re-check

Run these read-only commands when you review this page. Each costs nothing.

```bash
aws guardduty list-detectors --profile aa365-admin --region us-west-1 --output text
aws accessanalyzer list-analyzers --profile aa365-admin --region us-west-1 --query "analyzers[].name" --output text
aws s3control get-public-access-block --account-id <acc2-account-id> --profile aa365-admin --region us-west-1
aws cloudtrail describe-trails --profile aa365-admin --region us-west-1 --query "trailList[].{name:Name,multi:IsMultiRegionTrail,validation:LogFileValidationEnabled}"
aws elasticache describe-cache-clusters --profile aa365-admin --region us-west-1 --query "CacheClusters[].{id:CacheClusterId,transit:TransitEncryptionEnabled,rest:AtRestEncryptionEnabled,auth:AuthTokenEnabled}"
aws wafv2 list-web-acls --scope REGIONAL --profile aa365-admin --region us-west-1 --query "WebACLs[].Name" --output text
aws logs describe-log-groups --profile aa365-admin --region us-west-1 --query "logGroups[].[logGroupName,retentionInDays]" --output text
```

Public repo content (run in each public repo after `git fetch origin main`; prints the files that hold an account ID):

```bash
git grep -l -E '<acc1-account-id>|<acc2-account-id>|<acc3-account-id>' origin/main
```

The account IDs are in the account map (`docs/onboarding.md`). GitHub settings: repository Settings →
Code security, and Settings → Rules; or the read-only API calls listed in
[vulnerability management](vulnerability-management.md#monthly-triage).

Update a row when its issue ships, set `last_reviewed` to the day you re-ran the checks, and say so in the PR.
